import os
import json

from glob import glob
from shutil import move

# Add any other missing imports if needed


def check_outpath(bids_dir, subject_label):
    """
    Check if output paths exist, if not create them.

    Parameters
    ----------
    bids_dir : str
        Path to BIDS root directory.
    subject_label : str
        Label of subject to be checked (without 'sub-').
    """

    # Construct the output path for the subject's processed data
    # Following BIDS structure: sourcedata/bidsonym/sub-{subject_label}
    # The subject_label should not include the 'sub-' prefix as it's added here
    out_path = os.path.join(bids_dir, "sourcedata/bidsonym/sub-%s" % subject_label)

    # Check if the directory doesn't exist
    if not os.path.isdir(out_path):
        # Create the directory (and any necessary parent directories)
        # makedirs() will create intermediate directories if they don't exist
        os.makedirs(out_path)


def run_brain_extraction_bet(image, frac, subject_label, bids_dir, session=None):
    """
    Setup and FSLs brainextraction (BET) workflow.
    """
    import os
    from nipype.interfaces.fsl import BET

    print("DEBUG: run_brain_extraction_bet called with:")
    print(f"  subject_label: {subject_label}")
    print(f"  session: {session}")
    print(f"  bids_dir: {bids_dir}")

    # Create output directory in session-aware anat subdirectory
    if session is not None:
        output_dir = os.path.join(bids_dir, 'sourcedata', 'bidsonym', f'sub-{subject_label}', f'ses-{session}', 'anat')
        print(f"DEBUG: Using session-aware output directory: {output_dir}")
    else:
        output_dir = os.path.join(bids_dir, 'sourcedata', 'bidsonym', f'sub-{subject_label}', 'anat')
        print(f"DEBUG: Using subject-level output directory: {output_dir}")
    
    # Ensure the anat directory exists
    os.makedirs(output_dir, exist_ok=True)
    print(f"DEBUG: Created/verified directory: {output_dir}")
    
    # Create output filename for brain mask
    input_basename = os.path.basename(image)
    if '_desc-nondeid' in input_basename:
        mask_basename = input_basename.replace('_desc-nondeid.nii.gz', '_brainmask_desc-nondeid.nii.gz')
    else:
        mask_basename = input_basename.replace('.nii.gz', '_brainmask_desc-nondeid.nii.gz')
    
    outfile = os.path.join(output_dir, mask_basename)
    print(f"DEBUG: Target brain mask file: {outfile}")

    # Create and run BET directly without complex workflow
    bet = BET()
    bet.inputs.in_file = image
    bet.inputs.frac = float(frac)
    bet.inputs.mask = True  # Generate binary mask
    bet.inputs.out_file = outfile.replace('.nii.gz', '')  # BET adds .nii.gz automatically
    
    try:
        # Execute BET directly
        result = bet.run()
        
        # Get the actual output file path from BET results
        actual_mask_file = result.outputs.mask_file
        print(f"DEBUG: BET created mask at: {actual_mask_file}")
        
        # Rename to our desired naming convention if different
        if actual_mask_file != outfile and os.path.exists(actual_mask_file):
            os.rename(actual_mask_file, outfile)
            print(f"DEBUG: Renamed {actual_mask_file} to {outfile}")
        
        print(f"Created brain mask: {outfile}")
        return outfile
        
    except Exception as e:
        print(f"Error running BET brain extraction: {e}")
        import traceback
        traceback.print_exc()
        return None


def check_meta_data(bids_dir, subject_label, prob_fields=None, session=None, modalities=None):
    """
    Check for potentially identifying metadata in JSON files and NIfTI headers for each defaced image individually.
    
    Parameters
    ----------
    bids_dir : str
        Path to BIDS root directory.
    subject_label : str
        Label of subject (without 'sub-' prefix).
    prob_fields : list, optional
        List of fields to check for identifying information.
    session : str, optional
        Session label (without 'ses-' prefix).
    modalities : list, optional
        List of modalities to check.
    
    Returns
    -------
    bool
        True if potentially identifying metadata found, False otherwise.
    """
    
    import os
    import json
    import pandas as pd
    import nibabel as nib
    from bids import BIDSLayout
    
    print("DEBUG: check_meta_data called with:")
    print(f"  subject_label: {subject_label}")
    print(f"  session: {session}")
    print(f"  bids_dir: {bids_dir}")
    
    # Default problematic fields if none provided
    if prob_fields is None:
        prob_fields = [
            'InstitutionName', 'InstitutionAddress', 'InstitutionalDepartmentName',
            'StationName', 'DeviceSerialNumber', 'PatientName', 'PatientID',
            'PatientBirthDate', 'PatientSex', 'PatientAge', 'PatientWeight',
            'StudyInstanceUID', 'SeriesInstanceUID', 'StudyDescription',
            'SeriesDescription', 'StudyID', 'AccessionNumber', 'ReferringPhysicianName',
            'PatientPosition', 'ImageComments', 'AcquisitionDateTime',
            'ContentDate', 'ContentTime', 'InstanceCreationDate', 'InstanceCreationTime'
        ]
    
    # Default modalities if none provided
    if modalities is None:
        modalities = ['T1w', 'T2w', 'FLAIR', 'dwi', 'func']
    
    print(f"Checking metadata for subject {subject_label}")
    if session:
        print(f"Session: {session}")
    
    # Initialize BIDS layout
    layout = BIDSLayout(bids_dir)
    
    # Find NIfTI files for this subject/session (these are the defaced images)
    if session is not None:
        nifti_files = layout.get(
            subject=subject_label,
            session=session,
            extension='nii.gz',
            return_type='filename'
        )
    else:
        nifti_files = layout.get(
            subject=subject_label,
            extension='nii.gz',
            return_type='filename'
        )
    
    # Filter by modalities if specified
    if modalities:
        filtered_files = []
        for nifti_file in nifti_files:
            for modality in modalities:
                if modality in nifti_file:
                    filtered_files.append(nifti_file)
                    break
        nifti_files = filtered_files
    
    print(f"Found {len(nifti_files)} NIfTI files to check")
    
    # Create output directory for metadata info files
    if session is not None:
        output_dir = os.path.join(bids_dir, 'sourcedata', 'bidsonym', 
                                  f'sub-{subject_label}', f'ses-{session}', 'meta_data_info')
        print(f"DEBUG: Using session-aware metadata directory: {output_dir}")
    else:
        output_dir = os.path.join(bids_dir, 'sourcedata', 'bidsonym', 
                                  f'sub-{subject_label}', 'meta_data_info')
        print(f"DEBUG: Using subject-level metadata directory: {output_dir}")
    
    os.makedirs(output_dir, exist_ok=True)
    
    overall_found_issues = False
    
    # Process each NIfTI file individually
    for nifti_file in nifti_files:
        print(f"\nChecking: {os.path.basename(nifti_file)}")
        
        # Parse filename to extract components for output naming
        basename = os.path.basename(nifti_file)
        
        # Extract components from filename
        # Expected format: sub-XX_[ses-YY_][run-ZZ_]modality.nii.gz
        filename_parts = {}
        filename_parts['subject'] = subject_label
        
        # Extract session if present
        if session is not None:
            filename_parts['session'] = session
        elif 'ses-' in basename:
            # Extract session from filename if not provided as parameter
            session_part = basename.split('ses-')[1].split('_')[0]
            filename_parts['session'] = session_part
        
        # Extract run if present
        if '_run-' in basename:
            run_part = basename.split('_run-')[1].split('_')[0]
            filename_parts['run'] = run_part
        
        # Extract modality (T1w, T2w, FLAIR, etc.)
        modality = None
        for mod in ['T1w', 'T2w', 'FLAIR', 'PD', 'PDT2', 'inplaneT1', 'inplaneT2', 
                    'angio', 'defacemask', 'SWI', 'bold', 'sbref', 'dwi']:
            if f'_{mod}.' in basename or basename.endswith(f'_{mod}.nii.gz'):
                modality = mod
                break
        
        if modality is None:
            print(f"  Warning: Could not determine modality for {basename}, skipping")
            continue
            
        filename_parts['modality'] = modality
        
        # Check JSON metadata if it exists
        json_file = nifti_file.replace('.nii.gz', '.json')
        json_metadata_results = []
        
        if os.path.exists(json_file):
            print(f"  Checking JSON: {os.path.basename(json_file)}")
            try:
                with open(json_file, 'r') as f:
                    metadata = json.load(f)
                
                # Check each field in the JSON file
                for field, value in metadata.items():
                    if field in prob_fields:
                        # Found a potentially identifying field
                        json_metadata_results.append({
                            'file': os.path.basename(json_file),
                            'field': field,
                            'value': str(value),
                            'severity': 'HIGH' if field in ['PatientName', 'PatientID', 'PatientBirthDate'] else 'MEDIUM'
                        })
                        print(f"    WARNING: Found {field}: {value}")
            
            except Exception as e:
                print(f"    ERROR: Could not read {json_file}: {e}")
        else:
            print("  No corresponding JSON file found")
        
        # Check NIfTI header information
        print(f"  Checking NIfTI header: {basename}")
        header_info_results = []
        
        try:
            # Load the NIfTI image
            nifti_img = nib.load(nifti_file)
            header = nifti_img.header
            
            # Extract header information
            header_data = {}
            
            # Basic header fields that might contain identifying information
            header_fields_to_check = [
                'descrip',      # Description field
                'aux_file',     # Auxiliary file name
                'intent_name',  # Intent name
                'db_name',      # Database name
            ]
            
            # Get all header information
            for field in header_fields_to_check:
                try:
                    if hasattr(header, field):
                        value = getattr(header, field)
                        if isinstance(value, bytes):
                            value = value.decode('utf-8', errors='ignore').strip('\x00')
                        elif isinstance(value, str):
                            value = value.strip('\x00')
                        
                        if value:  # Only include non-empty values
                            header_data[field] = str(value)
                except Exception as e:
                    print(f"    Warning: Could not extract {field}: {e}")
            
            # Additional header information that might be relevant
            try:
                # Get voxel sizes
                header_data['pixdim'] = str(header.get_zooms())
                # Get data type
                header_data['datatype'] = str(header.get_data_dtype())
                # Get image dimensions
                header_data['dim'] = str(header.get_data_shape())
                # Get qform and sform codes
                header_data['qform_code'] = str(header.get_qform(coded=True)[1])
                header_data['sform_code'] = str(header.get_sform(coded=True)[1])
            except Exception as e:
                print(f"    Warning: Could not extract additional header info: {e}")
            
            # Check for potentially identifying information in header fields
            for field, value in header_data.items():
                header_info_results.append({
                    'field': field,
                    'value': value
                })
                
                # Check if this field might contain identifying information
                if field in ['descrip', 'aux_file', 'intent_name', 'db_name'] and value:
                    # Look for potentially identifying patterns
                    identifying_patterns = ['patient', 'subject', 'name', 'id', 'date', 'time', 'hospital', 'clinic']
                    if any(pattern.lower() in value.lower() for pattern in identifying_patterns):
                        print(f"    WARNING: Header field '{field}' may contain identifying information: {value}")
                        overall_found_issues = True
                
        except Exception as e:
            print(f"    ERROR: Could not read NIfTI header for {nifti_file}: {e}")
        
        # Save JSON metadata results if any were found
        if json_metadata_results:
            overall_found_issues = True
            
            # Create DataFrame for JSON metadata results
            df_json = pd.DataFrame(json_metadata_results)
            
            # Construct output filename for JSON metadata
            output_parts = [f'sub-{subject_label}']
            
            if 'session' in filename_parts:
                output_parts.append(f'ses-{filename_parts["session"]}')
            
            if 'run' in filename_parts:
                output_parts.append(f'run-{filename_parts["run"]}')
            
            output_parts.append(modality)
            output_parts.append('desc-jsoninfo.csv')
            
            csv_filename = '_'.join(output_parts)
            csv_path = os.path.join(output_dir, csv_filename)
            
            # Save the JSON metadata results
            df_json.to_csv(csv_path, index=False)
            print(f'    JSON metadata results saved to: {csv_filename}')
        
        # Save header information results (always save, even if no identifying info found)
        if header_info_results:
            # Create DataFrame for header information
            df_header = pd.DataFrame(header_info_results)
            
            # Construct output filename for header information
            output_parts = [f'sub-{subject_label}']
            
            if 'session' in filename_parts:
                output_parts.append(f'ses-{filename_parts["session"]}')
            
            if 'run' in filename_parts:
                output_parts.append(f'run-{filename_parts["run"]}')
            
            output_parts.append(modality)
            output_parts.append('desc-headerinfo.csv')
            
            header_csv_filename = '_'.join(output_parts)
            header_csv_path = os.path.join(output_dir, header_csv_filename)
            
            # Save the header information results
            df_header.to_csv(header_csv_path, index=False)
            print(f'    Header information saved to: {header_csv_filename}')
        
        # Print summary for this file
        if not json_metadata_results:
            print(f'    SUCCESS: No identifying JSON metadata found in {basename}')
        
        print(f'    Header information extracted and saved for {basename}')
    
    # Print overall summary
    if overall_found_issues:
        print('\nWARNING: Found potentially identifying information!')
        print(f'   Individual results saved to: {output_dir}')
        print('   Please review the results and consider removing or anonymizing')
        print('   the identified fields before sharing this data.')
        return True
    else:
        print('\nSUCCESS: No potentially identifying metadata fields found in any files.')
        print('   Header information has been extracted and saved for all files.')
        print('   The checked files appear to be properly de-identified.')
        return False


def del_meta_data(bids_dir, subject_label, fields_del):
    """
    Delete values from specified keys in meta-data json files.

    Parameters
    ----------
    bids_dir : str
        Path to BIDS root directory.
    subject_label : str
        Label of subject to operate on (without 'sub-').
    fields_del : list
        List of meta-data keys ('str') which value should be removed.
    """

    # Define paths for storing backed-up metadata files
    path_task_meta = os.path.join(bids_dir, "sourcedata/bidsonym/")
    path_sub_meta = os.path.join(bids_dir, "sourcedata/bidsonym/sub-%s" % subject_label)
    
    # Find all JSON metadata files at task level and subject level
    list_task_meta_files = glob(os.path.join(bids_dir, '*json'))
    list_sub_meta_files = glob(os.path.join(bids_dir, 'sub-' + subject_label, '**/*.json'), recursive=True)

    # Combine both lists for comprehensive processing
    list_meta_files = list_task_meta_files + list_sub_meta_files

    # Move original task-level JSON files to backup location in sourcedata
    # This preserves the original metadata before de-identification
    for task_meta_data_file in list_task_meta_files:
        # Extract just the filename from the full path
        task_out = task_meta_data_file[task_meta_data_file.rfind('/') + 1:]
        # Move original file to backup location
        move(task_meta_data_file, os.path.join(path_task_meta, task_out))
    
    # Move original subject-level JSON files to backup location in sourcedata
    for sub_meta_data_file in list_sub_meta_files:
        # Extract just the filename from the full path
        sub_out = sub_meta_data_file[sub_meta_data_file.rfind('/') + 1:]
        # Move original file to backup location
        move(sub_meta_data_file, os.path.join(path_sub_meta, sub_out))

    # Find the backed-up JSON files in their new locations for processing
    list_task_meta_files_deid = glob(os.path.join(bids_dir, "sourcedata/bidsonym/", '*json'))
    list_sub_meta_files_deid = glob(os.path.join(bids_dir, "sourcedata/bidsonym/",
                                                 'sub-' + subject_label, '**/*.json'),
                                    recursive=True)
    
    # Combine backed-up files for de-identification processing
    list_meta_files_deid = list_task_meta_files_deid + list_sub_meta_files_deid

    # Store the fields to delete (redundant assignment, but kept for clarity)
    fields_del = fields_del

    # Print progress information for user
    print('working on %s' % subject_label)
    print('found the following meta-data files:')
    print(*list_meta_files, sep='\n')
    print('the following fields will be deleted:')
    print(*fields_del, sep='\n')

    # Sort both lists to ensure consistent pairing of original and backup files
    list_meta_files.sort()
    list_meta_files_deid.sort()

    # Process each pair of backed-up and original files
    for meta_file_deid, meta_file in zip(list_meta_files_deid, list_meta_files):
        # Load the backed-up JSON file for processing
        with open(meta_file_deid, 'r') as json_file:
            meta_data = json.load(json_file)
            
            # Process each field marked for deletion
            for field in fields_del:
                if field in meta_data:
                    # Replace the field value with a deletion marker instead of removing the key
                    # This maintains the JSON structure while indicating the field was anonymized
                    meta_data[field] = 'deleted_by_bidsonym'
                else:
                    # Inform user if a specified field doesn't exist in this file
                    print("The field you indicated to delete does not exist in %s" % meta_file_deid)
                    continue
        
        # Write the de-identified metadata back to the original file location
        # This replaces the original file with the anonymized version
        with open(meta_file, 'w') as json_output_file:
            print('writing %s' % meta_file)
            # Use indent=4 for human-readable formatting
            json.dump(meta_data, json_output_file, indent=4)


def copy_no_deid(bids_dir, subject_label, image_file, session=None):
    """
    Copy original non-deidentified image and JSON files to session-aware sourcedata directory.
    
    Parameters
    ----------
    bids_dir : str
        Path to BIDS root directory.
    subject_label : str
        Label of subject (without 'sub-' prefix).
    image_file : str
        Path to the image file to be copied.
    session : str, optional
        Session label (without 'ses-' prefix).
    
    Returns
    -------
    str
        Path to the copied non-deidentified image file.
    """
    
    import os
    from shutil import copy2
    from os.path import join as opj
    
    print("DEBUG: copy_no_deid called with:")
    print(f"  subject_label: {subject_label}")
    print(f"  session: {session}")
    print(f"  bids_dir: {bids_dir}")
    print(f"  image_file: {image_file}")
    
    # Create paths for session-aware organized structure
    if session is not None:
        # For session-based datasets, create anat subdirectory within session
        output_dir = opj(bids_dir, 'sourcedata', 'bidsonym', f'sub-{subject_label}', f'ses-{session}', 'anat')
        print(f"DEBUG: Using session-aware output directory: {output_dir}")
    else:
        # For single-session datasets, create anat subdirectory within subject
        output_dir = opj(bids_dir, 'sourcedata', 'bidsonym', f'sub-{subject_label}', 'anat')
        print(f"DEBUG: Using subject-level output directory: {output_dir}")
    
    # Ensure the anat output directory exists
    os.makedirs(output_dir, exist_ok=True)
    print(f"DEBUG: Created/verified directory: {output_dir}")
    
    # Extract filename and create desc-nondeid version
    original_basename = os.path.basename(image_file)
    nondeid_basename = original_basename.replace('.nii.gz', '_desc-nondeid.nii.gz')
    
    # Copy the NIfTI image file
    nondeid_image_path = opj(output_dir, nondeid_basename)
    if os.path.exists(nondeid_image_path):
        print(f"File already exists: {nondeid_image_path}, not overwritten.")
    else:
        copy2(image_file, nondeid_image_path)
        print(f"Copied original image to: {nondeid_image_path}")
    
    # Look for corresponding JSON file
    json_file = image_file.replace('.nii.gz', '.json')
    if os.path.exists(json_file):
        # Copy JSON file with desc-nondeid naming
        nondeid_json_basename = original_basename.replace('.nii.gz', '_desc-nondeid.json')
        nondeid_json_path = opj(output_dir, nondeid_json_basename)
        if os.path.exists(nondeid_json_path):
            print(f"File already exists: {nondeid_json_path}, not overwritten.")
        else:
            copy2(json_file, nondeid_json_path)
            print(f"Copied original JSON to: {nondeid_json_path}")
    else:
        print(f"No JSON file found for: {image_file}")
    
    return nondeid_image_path


def rename_non_deid(bids_dir, subject_label):
    """
    Rename non-deidentified files to include descriptive labels.
    
    Parameters
    ----------
    bids_dir : str
        Path to BIDS root directory.
    subject_label : str
        Label of subject (without 'sub-').
    """
    
    import os
    from glob import glob
    
    # Define the base sourcedata path for this subject
    sourcedata_base = os.path.join(bids_dir, "sourcedata", "bidsonym", f"sub-{subject_label}")
    
    if not os.path.exists(sourcedata_base):
        print(f"No sourcedata found for subject {subject_label}")
        return
    
    # Find all NIfTI and JSON files recursively in the subject's sourcedata directory
    # This will catch files in both session directories and subject root
    nifti_files = glob(os.path.join(sourcedata_base, "**", "*.nii.gz"), recursive=True)
    json_files = glob(os.path.join(sourcedata_base, "**", "*.json"), recursive=True)
    
    all_files = nifti_files + json_files
    
    print(f"Found {len(all_files)} files to rename for subject {subject_label}")
    
    # Rename each file to include the _desc-nondeid identifier
    for file_path in all_files:
        # Skip files that already have the descriptor
        if '_desc-nondeid' in file_path:
            continue
            
        # Get the directory and filename
        file_dir = os.path.dirname(file_path)
        filename = os.path.basename(file_path)
        
        # Insert _desc-nondeid before the file extension
        if filename.endswith('.nii.gz'):
            new_filename = filename.replace('.nii.gz', '_desc-nondeid.nii.gz')
        elif filename.endswith('.json'):
            new_filename = filename.replace('.json', '_desc-nondeid.json')
        else:
            continue  # Skip files with unexpected extensions
        
        new_file_path = os.path.join(file_dir, new_filename)
        
        try:
            os.rename(file_path, new_file_path)
            print(f"Renamed: {filename} -> {new_filename}")
        except OSError as e:
            print(f"Error renaming {filename}: {e}")


def deface_image(image, warped_mask, outfile):
    """
    Deface other contrast/modality image using the 
    defaced T1w image as deface mask.

    Parameters
    ----------
    image : str
        Path to image.
    warped_mask : str
        Path to warped defaced T1w image.
    outfile: str
        Name of the defaced file.
    """
    
    # Import all required modules within the function
    # This is necessary when the function is used as a Nipype Function node
    import numpy as np
    from nibabel import load, Nifti1Image
    from nilearn.image import math_img

    # Load the input image and the warped mask image
    infile_img = load(image)
    warped_mask_img = load(warped_mask)
    
    # Convert the warped mask to binary (0 or 1 values)
    # Any positive values in the mask become 1, others become 0
    warped_mask_img = math_img('img > 0', img=warped_mask_img)
    
    try:
        # Attempt to apply the mask by element-wise multiplication
        # This removes facial regions by setting them to 0
        outdata = infile_img.get_fdata().squeeze() * warped_mask_img.get_fdata()
    except ValueError:
        # Handle cases where image dimensions don't match
        # This typically happens with multi-volume/4D images

        # Create a stack of mask data to match the last dimension of the input image
        # This replicates the 3D mask across all volumes in a 4D image
        tmpdata = np.stack([warped_mask_img.get_fdata()] *
                           infile_img.get_fdata().shape[-1], axis=-1)
        
        # Apply the replicated mask to all volumes
        outdata = infile_img.get_fdata() * tmpdata

    # Create a new NIfTI image with the defaced data
    # Preserve the original image's spatial transformation (affine) and metadata (header)
    masked_brain = Nifti1Image(outdata, infile_img.affine,
                               infile_img.header)
    
    # Save the defaced image to the specified output file
    masked_brain.to_filename(outfile)


def validate_input_dir(exec_env, bids_dir, participant_label):
    """
    Validate BIDS directory and structure via the BIDS-validator.
    Functionality copied from fmriprep.

    Parameters
    ----------
    exec_env : str
        Environment BIDSonym is run in.
    bids_dir : str
        Path to BIDS root directory.
    participant_label: str
        Label(s) of subject to be checked (without 'sub-').
    """

    import tempfile
    import subprocess
    import sys
    import json
    
    # Configure the BIDS validator with a comprehensive list of warnings/errors to ignore
    # This allows validation to focus on structural issues while ignoring common
    # non-critical warnings that don't affect the defacing/anonymization process
    validator_config_dict = {
        "ignore": [
            "EVENTS_COLUMN_ONSET",           # Missing onset column in events files
            "EVENTS_COLUMN_DURATION",       # Missing duration column in events files
            "TSV_EQUAL_ROWS",               # Unequal number of rows in TSV files
            "TSV_EMPTY_CELL",               # Empty cells in TSV files
            "TSV_IMPROPER_NA",              # Improper N/A values in TSV files
            "VOLUME_COUNT_MISMATCH",        # Mismatch in volume counts between files
            "BVAL_MULTIPLE_ROWS",           # Multiple rows in bval files
            "BVEC_NUMBER_ROWS",             # Incorrect number of rows in bvec files
            "DWI_MISSING_BVAL",             # Missing bval files for DWI data
            "INCONSISTENT_SUBJECTS",        # Inconsistent subject information
            "INCONSISTENT_PARAMETERS",      # Inconsistent acquisition parameters
            "BVEC_ROW_LENGTH",              # Incorrect bvec row length
            "B_FILE",                       # Issues with b-files
            "PARTICIPANT_ID_COLUMN",        # Missing participant_id column
            "PARTICIPANT_ID_MISMATCH",      # Mismatch in participant IDs
            "TASK_NAME_MUST_DEFINE",        # Undefined task names
            "PHENOTYPE_SUBJECTS_MISSING",   # Missing subjects in phenotype files
            "STIMULUS_FILE_MISSING",        # Missing stimulus files
            "DWI_MISSING_BVEC",             # Missing bvec files for DWI data
            "EVENTS_TSV_MISSING",           # Missing events TSV files
            "TSV_IMPROPER_NA",              # Duplicate entry (intentional)
            "ACQTIME_FMT",                  # Acquisition time format issues
            "Participants age 89 or higher",  # Age-related warnings (privacy)
            "DATASET_DESCRIPTION_JSON_MISSING",  # Missing dataset description
            "FILENAME_COLUMN",              # Issues with filename columns
            "WRONG_NEW_LINE",               # Wrong newline characters
            "MISSING_TSV_COLUMN_CHANNELS",  # Missing channels column in TSV
            "MISSING_TSV_COLUMN_IEEG_CHANNELS",  # Missing iEEG channels column
            "MISSING_TSV_COLUMN_IEEG_ELECTRODES",  # Missing iEEG electrodes column
            "UNUSED_STIMULUS",              # Unused stimulus files
            "CHANNELS_COLUMN_SFREQ",        # Missing sampling frequency column
            "CHANNELS_COLUMN_LOWCUT",       # Missing low-cut filter column
            "CHANNELS_COLUMN_HIGHCUT",      # Missing high-cut filter column
            "CHANNELS_COLUMN_NOTCH",        # Missing notch filter column
            "CUSTOM_COLUMN_WITHOUT_DESCRIPTION",  # Custom columns without description
            "ACQTIME_FMT",                  # Duplicate entry (intentional)
            "SUSPICIOUSLY_LONG_EVENT_DESIGN",  # Unusually long event designs
            "SUSPICIOUSLY_SHORT_EVENT_DESIGN",  # Unusually short event designs
            "MALFORMED_BVEC",               # Malformed bvec files
            "MALFORMED_BVAL",               # Malformed bval files
            "MISSING_TSV_COLUMN_EEG_ELECTRODES",  # Missing EEG electrodes column
            "MISSING_SESSION"               # Missing session information
        ],
        "error": ["NO_T1W"],  # Still treat missing T1w images as errors (critical for defacing)
        "ignoredFiles": ['/dataset_description.json', '/participants.tsv']  # Skip these files
    }
    
    # Validate participant labels and limit validation to requested participants only
    if participant_label:
        # Get all subject directories in the BIDS dataset
        all_subs = set([s.name[4:] for s in bids_dir.glob('sub-*')])
        
        # Parse requested participant labels, handling both 'sub-' prefixed and plain labels
        selected_subs = set([s[4:] if s.startswith('sub-') else s
                             for s in participant_label])
        
        # Check for invalid participant labels (requested but not found in dataset)
        bad_labels = selected_subs.difference(all_subs)
        if bad_labels:
            # Create detailed error message with environment-specific troubleshooting
            error_msg = 'Data for requested participant(s) label(s) not found. Could ' \
                        'not find data for participant(s): %s. Please verify the requested ' \
                        'participant labels.'
            
            # Add Docker-specific troubleshooting information
            if exec_env == 'docker':
                error_msg += ' This error can be caused by the input data not being ' \
                             'accessible inside the docker container. Please make sure all ' \
                             'volumes are mounted properly (see https://docs.docker.com/' \
                             'engine/reference/commandline/run/#mount-volume--v---read-only)'
            
            # Add Singularity-specific troubleshooting information
            if exec_env == 'singularity':
                error_msg += ' This error can be caused by the input data not being ' \
                             'accessible inside the singularity container. Please make sure ' \
                             'all paths are mapped properly (see https://www.sylabs.io/' \
                             'guides/3.0/user-guide/bind_paths_and_mounts.html)'
            
            # Raise error with the list of problematic participant labels
            raise RuntimeError(error_msg % ','.join(bad_labels))

        # For participants not selected, add them to ignored files list
        # This optimizes validation by skipping unnecessary subjects
        ignored_subs = all_subs.difference(selected_subs)
        if ignored_subs:
            for sub in ignored_subs:
                # Use wildcard pattern to ignore entire subject directories
                validator_config_dict["ignoredFiles"].append("/sub-%s/**" % sub)
    
    # Run BIDS validation using temporary configuration file
    with tempfile.NamedTemporaryFile('w+') as temp:
        # Write the validator configuration to a temporary JSON file
        temp.write(json.dumps(validator_config_dict))
        temp.flush()
        
        try:
            # Execute BIDS validator with custom configuration
            # -c flag specifies the path to the configuration file
            subprocess.check_call(['bids-validator', bids_dir, '-c', temp.name])
        except FileNotFoundError:
            # Handle case where BIDS validator is not installed
            # Print to stderr to distinguish from normal output
            print("bids-validator does not appear to be installed", file=sys.stderr)


def clean_up_files(bids_dir, subject_label, session=None):
    """
    Restructure BIDSonym outcomes following BIDS conventions with session-aware organization.
    This function moves files that might be in the wrong locations to the correct subdirectories.
    
    Parameters
    ----------
    bids_dir : str
        Path to BIDS root directory.
    subject_label : str
        Label of subject (without 'sub-' prefix).
    session : str, optional
        Session label (without 'ses-' prefix).
    """
    
    import os
    from glob import glob
    from shutil import move
    
    print("DEBUG: clean_up_files called with:")
    print(f"  subject_label: {subject_label}")
    print(f"  session: {session}")
    print(f"  bids_dir: {bids_dir}")
    
    # Create output paths based on whether session information is provided
    if session is not None:
        session_path = os.path.join(bids_dir, f"sourcedata/bidsonym/sub-{subject_label}/ses-{session}")
        out_path_anat = os.path.join(session_path, "anat")
        out_path_qc = os.path.join(session_path, "QC")
        out_path_info = os.path.join(session_path, "meta_data_info")
        
        # Also check subject root for files that should be in session directories
        subject_root = os.path.join(bids_dir, f"sourcedata/bidsonym/sub-{subject_label}")
        print(f"DEBUG: Using session-aware structure: {session_path}")
    else:
        subject_path = os.path.join(bids_dir, f"sourcedata/bidsonym/sub-{subject_label}")
        out_path_anat = os.path.join(subject_path, "anat")
        out_path_qc = os.path.join(subject_path, "QC")
        out_path_info = os.path.join(subject_path, "meta_data_info")
        subject_root = subject_path
        print(f"DEBUG: Using subject-level structure: {subject_path}")

    # Create output directories if they don't exist
    os.makedirs(out_path_anat, exist_ok=True)
    os.makedirs(out_path_qc, exist_ok=True)
    os.makedirs(out_path_info, exist_ok=True)
    print("DEBUG: Created/verified directories: anat, QC, meta_data_info")

    # Look for files that might be in the wrong locations
    search_paths = [subject_root]
    if session is not None:
        # Also check the session root directory
        search_paths.append(os.path.join(bids_dir, f'sourcedata/bidsonym/sub-{subject_label}/ses-{session}'))

    for search_path in search_paths:
        if not os.path.exists(search_path):
            continue
            
        print(f"Checking for misplaced files in: {search_path}")

        # Find anatomical files (NIfTI and JSON with desc-nondeid) that are in root
        root_nii_files = glob(os.path.join(search_path, '*desc-nondeid.nii.gz'))
        root_json_files = glob(os.path.join(search_path, '*desc-nondeid.json'))
        root_brainmask_files = glob(os.path.join(search_path, '*brainmask*.nii.gz'))
        
        # Move anatomical files from root to anat directory
        anat_files_to_move = root_nii_files + root_json_files + root_brainmask_files
        for anat_file in anat_files_to_move:
            filename = os.path.basename(anat_file)
            target_path = os.path.join(out_path_anat, filename)
            if anat_file != target_path:  # Only move if not already in correct location
                try:
                    move(anat_file, target_path)
                    print(f"Moved {filename} to anat directory")
                except Exception as e:
                    print(f"Warning: Could not move {filename}: {e}")

        # Find QC files (PNG and GIF) that are in root
        root_png_files = glob(os.path.join(search_path, '*.png'))
        root_gif_files = glob(os.path.join(search_path, '*.gif'))
        
        # Move QC files from root to QC directory
        qc_files_to_move = root_png_files + root_gif_files
        for qc_file in qc_files_to_move:
            filename = os.path.basename(qc_file)
            target_path = os.path.join(out_path_qc, filename)
            if qc_file != target_path:  # Only move if not already in correct location
                try:
                    move(qc_file, target_path)
                    print(f"Moved {filename} to QC directory")
                except Exception as e:
                    print(f"Warning: Could not move {filename}: {e}")

        # Find metadata info files (CSV) that are in root
        root_csv_files = glob(os.path.join(search_path, '*.csv'))
        root_other_json_files = glob(os.path.join(search_path, '*.json'))
        # Filter out desc-nondeid JSON files (those go to anat)
        root_other_json_files = [f for f in root_other_json_files if 'desc-nondeid' not in f]
        
        # Move metadata info files from root to meta_data_info directory
        info_files_to_move = root_csv_files + root_other_json_files
        for info_file in info_files_to_move:
            filename = os.path.basename(info_file)
            target_path = os.path.join(out_path_info, filename)
            if info_file != target_path:  # Only move if not already in correct location
                try:
                    move(info_file, target_path)
                    print(f"Moved {filename} to meta_data_info directory")
                except Exception as e:
                    print(f"Warning: Could not move {filename}: {e}")

    print(f"File organization completed for subject {subject_label}")
    if session:
        print(f"Session: {session}")


def revert_bidsonym(bids_dir, subject_label, session=None, confirm=True):
    """
    Revert BIDSonym de-identification by restoring original files from sourcedata.
    
    Parameters
    ----------
    bids_dir : str
        Path to BIDS root directory.
    subject_label : str
        Label of subject (without 'sub-' prefix).
    session : str, optional
        Session label (without 'ses-' prefix). If None, reverts all sessions.
    confirm : bool, optional
        Whether to ask for confirmation before reverting (default: True).
        
    Returns
    -------
    bool
        True if reversion was successful, False otherwise.
    """
    
    import os
    from shutil import copy2
    from glob import glob
    
    print(f"Reverting BIDSonym for subject {subject_label}")
    if session:
        print(f"Session: {session}")
    
    # Define sourcedata paths
    if session is not None:
        sourcedata_path = os.path.join(bids_dir, 'sourcedata', 'bidsonym', 
                                       f'sub-{subject_label}', f'ses-{session}')
        bids_path = os.path.join(bids_dir, f'sub-{subject_label}', f'ses-{session}')
    else:
        sourcedata_path = os.path.join(bids_dir, 'sourcedata', 'bidsonym', 
                                       f'sub-{subject_label}')
        bids_path = os.path.join(bids_dir, f'sub-{subject_label}')
    
    # Check if sourcedata exists
    if not os.path.exists(sourcedata_path):
        print(f"No BIDSonym sourcedata found at: {sourcedata_path}")
        return False
    
    # Find original files to restore
    anat_sourcedata = os.path.join(sourcedata_path, 'anat')
    if not os.path.exists(anat_sourcedata):
        print(f"No anatomical sourcedata found at: {anat_sourcedata}")
        return False
    
    # Find all desc-nondeid files
    original_files = glob(os.path.join(anat_sourcedata, '*desc-nondeid.nii.gz'))
    original_json_files = glob(os.path.join(anat_sourcedata, '*desc-nondeid.json'))
    
    all_original_files = original_files + original_json_files
    
    if not all_original_files:
        print(f"No original files found to restore in: {anat_sourcedata}")
        return False
    
    print(f"Found {len(all_original_files)} original files to restore")
    
    # Ask for confirmation if requested
    if confirm:
        response = input("This will overwrite defaced files with original data. Continue? (y/N): ")
        if response.lower() not in ['y', 'yes']:
            print("Reversion cancelled")
            return False
    
    # Restore each file
    restored_count = 0
    for original_file in all_original_files:
        try:
            # Generate target filename (remove _desc-nondeid)
            basename = os.path.basename(original_file)
            if '_desc-nondeid.nii.gz' in basename:
                target_basename = basename.replace('_desc-nondeid.nii.gz', '.nii.gz')
            elif '_desc-nondeid.json' in basename:
                target_basename = basename.replace('_desc-nondeid.json', '.json')
            else:
                continue
            
            # Determine target path
            target_path = os.path.join(bids_path, 'anat', target_basename)
            
            # Ensure target directory exists
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            
            # Copy original file back to BIDS location
            copy2(original_file, target_path)
            print(f"Restored: {target_basename}")
            restored_count += 1
            
        except Exception as e:
            print(f"Error restoring {original_file}: {e}")
    
    print(f"Successfully restored {restored_count} files")
    return restored_count > 0

