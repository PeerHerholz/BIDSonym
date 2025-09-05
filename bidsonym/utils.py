import os
import sys
import json

import numpy as np
from glob import glob
import pandas as pd
from shutil import move

import nibabel as nib
from nibabel import load, Nifti1Image
from nilearn.image import math_img

import nipype.pipeline.engine as pe
from nipype import Function
from nipype.interfaces import utility as niu
from nipype.interfaces.fsl import BET

from bidsonym.reports import setup_logging


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


def copy_no_deid(bids_dir, subject_label, image_file, session=None):
    """
    Move original non-defaced images to sourcedata.

    Parameters
    ----------
    bids_dir : str
        Path to BIDS root directory.
    subject_label : str
        Label of subject to move (without 'sub-').
    image_file : str
        Original non-defaced image.
    session : str
        Session label (if applicable).

    Returns
    -------
    moved_img_path : str
        Path to moved original non-defaced image.
    """

    # Construct the destination path based on whether session data is provided
    if session is not None:
        # For multi-session studies, include session directory in path
        path = os.path.join(bids_dir, "sourcedata/bidsonym/sub-%s/ses-%s" % (subject_label, session))
    else:
        # For single-session studies, use subject directory only
        path = os.path.join(bids_dir, "sourcedata/bidsonym/sub-%s" % subject_label)
    
    # Extract just the filename from the full image file path
    # This removes the directory structure and keeps only the file name
    outfile = image_file[image_file.rfind('/') + 1:]

    # Safety check: ensure we don't accidentally overwrite existing non-de-identified data
    if os.path.isdir(path) is True:
        # Raise an exception if the directory already exists to prevent data loss
        raise Exception(
            "A directory to store non-de-identified images for subject %s already exists under %s.\n"
            "In order to avoid overwriting non-de-identified data, please evaluate the current state of the sourcedata and raw data"
            "" % (subject_label, path)
        )
    else:
        # Create the destination directory structure
        os.makedirs(path)
        
        # Move (not copy) the original image file to the new location
        # This preserves the original non-defaced data in sourcedata while
        # allowing the defaced version to replace it in the main BIDS structure
        move(image_file, os.path.join(path, outfile))

    # Construct the full path to the moved file
    moved_img_path = os.path.join(path, outfile)

    # Return the path where the original image was moved to
    return moved_img_path


def check_meta_data(bids_dir, subject_label, prob_fields=None):
    """
    Extract meta-data from image headers and json files and
    subsequently evaluate values based on default keys or
    user specified keys. Outputs are csv files containing
    DataFrames with keys, values and markers concerning values.

    Parameters
    ----------
    bids_dir : str
        Path to BIDS root directory.
    subject_label : str
        Label of subject to be checked (without 'sub-').
    prob_fields : list, optional
        List of meta-data keys ('str') that should be evaluated.
    """

    # Find all NIfTI image files for the specified subject
    list_subject_image_files = glob(os.path.join(bids_dir, 'sub-' + subject_label, '**/*.nii.gz'), recursive=True)
    
    # Find JSON metadata files at the task level (root of BIDS directory)
    list_task_meta_files = glob(os.path.join(bids_dir, '*json'))
    
    # Find JSON metadata files specific to the subject
    list_sub_meta_files = glob(os.path.join(bids_dir, 'sub-' + subject_label, '**/*.json'), recursive=True)
    
    # Combine both types of JSON files for comprehensive metadata checking
    list_meta_files = list_task_meta_files + list_sub_meta_files

    # Process each image file's header metadata
    for subject_image_file in list_subject_image_files:

        # Load the NIfTI file and extract header information
        header = nib.load(subject_image_file).header
        keys = []
        dat = []

        # Extract all key-value pairs from the header
        for key, data in zip(header.keys(), header.values()):
            keys.append(key)
            dat.append(data)
        
        # Create a DataFrame with header information and default 'no' for problematic flag
        header_df = pd.DataFrame({'header_data_field': keys, 'data': dat, 'problematic': 'no'})

        # Set up problematic fields list - always include 'descrip' field
        if prob_fields:
            # Add user-specified problematic fields to the default 'descrip' field
            prob_fields = prob_fields + ['descrip']
        else:
            # Use only the default 'descrip' field if no user fields specified
            prob_fields = ['descrip']

        # Check each header field against problematic fields list
        for index, row in header_df.iterrows():
            # Case-insensitive check if any problematic field name appears in header field name
            if any(i.lower() in row['header_data_field'] for i in prob_fields):
                row['problematic'] = 'maybe'
            else:
                row['problematic'] = 'no'

        # Save header analysis to CSV file in sourcedata directory
        # Extract filename without path and extension for output naming
        header_df.to_csv(os.path.join(bids_dir, 'sourcedata/bidsonym',
                                      'sub-%s' % subject_label,
                                      subject_image_file[subject_image_file.rfind('/') +
                                                         1:subject_image_file.rfind('.nii.gz')] +
                                      '_desc-headerinfo.csv'),
                         index=False)

    # Inform user about which metadata files will be processed
    print('the following meta-data files will be checked:')
    print(*list_meta_files, sep='\n')

    # Process each JSON metadata file
    for meta_file in list_meta_files:

        # Load and parse JSON metadata
        with open(meta_file, 'r') as json_file:
            meta_data = json.load(json_file)
            keys = []
            info = []
            
            # Extract all key-value pairs from JSON metadata
            for key, inf in zip(meta_data.keys(), meta_data.values()):
                keys.append(key)
                info.append(inf)
            
            # Create DataFrame with JSON metadata and default 'no' for problematic flag
            json_df = pd.DataFrame({'meta_data_field': keys, 'information': info, 'problematic': 'no'})

        # Define default list of potentially problematic fields that may contain identifying information
        list_general_prob_fields = ['AcquisitionTime', 'InstitutionAddress', 'InstitutionName',
                                    'InstitutionalDepartmentName', 'ProcedureStepDescription', 'ProtocolName',
                                    'PulseSequenceDetails', 'SeriesDescription', 'global']

        # Combine user-specified and default problematic fields
        if prob_fields:
            prob_fields = prob_fields + list_general_prob_fields
        else:
            prob_fields = list_general_prob_fields

        # Check each JSON field against problematic fields list
        for index, row in json_df.iterrows():
            # Exact match check (case-sensitive) for JSON field names
            if any(i in row['meta_data_field'] for i in prob_fields):
                row['problematic'] = 'maybe'
            else:
                row['problematic'] = 'no'

        # Save JSON metadata analysis to CSV file
        # Extract filename without path and extension for output naming
        json_df.to_csv(os.path.join(bids_dir, 'sourcedata/bidsonym', 'sub-%s' % subject_label,
                                    meta_file[meta_file.rfind('/') +
                                              1:meta_file.rfind('.json')] +
                                    '_desc-jsoninfo.csv'),
                       index=False)


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


def rename_non_deid(bids_dir, subject_label):
    """
    Rename original non-defaced images and meta-data json files
    to add respective identifier ('desc-nondeid').

    Parameters
    ----------
    bids_dir : str
        Path to BIDS root directory.
    subject_label : str
        Label of subject to be renamed (without 'sub-').
    """

    # Find all JSON metadata files in the subject's backup directory
    # Exclude files that already have the 'desc-nondeid' identifier to prevent double-processing
    list_meta_files = [fn for fn in glob(os.path.join(bids_dir, 'sourcedata/bidsonym/sub-'
                       + subject_label, '*json')) if not os.path.basename(fn).endswith('desc-nondeid.json')]
    
    # Find all NIfTI image files in the subject's backup directory
    # Exclude files that already have the 'desc-nondeid' identifier to prevent double-processing
    list_images_files = [fn for fn in glob(os.path.join(bids_dir, 'sourcedata/bidsonym/sub-'
                         + subject_label, '*nii.gz')) if not os.path.basename(fn).endswith('desc-nondeid.nii.gz')]

    # Rename all JSON metadata files to include the 'desc-nondeid' identifier
    for meta_data_file in list_meta_files:
        # Extract filename without extension and add the non-de-identified descriptor
        # This clearly marks these files as containing original, non-anonymized metadata
        meta_deid = meta_data_file[meta_data_file.rfind('/') +
                                   1:meta_data_file.rfind('.json')] + '_desc-nondeid.json'
        
        # Perform the rename operation in the same directory
        os.rename(meta_data_file, os.path.join(bids_dir, 'sourcedata/bidsonym/sub-' + subject_label, meta_deid))

    # Rename all NIfTI image files to include the 'desc-nondeid' identifier
    for image_file in list_images_files:
        # Extract filename without extension and add the non-de-identified descriptor
        # This clearly marks these files as containing original, non-defaced brain images
        image_deid = image_file[image_file.rfind('/') +
                                1:image_file.rfind('.nii.gz')] + '_desc-nondeid.nii.gz'
        
        # Perform the rename operation in the same directory
        os.rename(image_file, os.path.join(bids_dir, 'sourcedata/bidsonym/sub-' + subject_label, image_deid))


def brain_extraction_nb(image, subject_label, bids_dir):
    """
    Setup nobrainer brainextraction command.

    Parameters
    ----------
    image : str
        Path to image that should be defaced.
    outfile : str
        Name of the defaced file.
    bids_dir : str
        Path to BIDS root directory.
    """

    import os
    from subprocess import check_call

    # Construct the output path for the brain mask
    # The mask will be saved in the subject's backup directory with descriptive naming
    # Extract the base filename and add brain mask identifier and non-deid descriptor
    outfile = os.path.join(bids_dir, "sourcedata/bidsonym/sub-%s" % subject_label,
                           image[image.rfind('/') + 1:image.rfind('.nii')] + '_brainmask_desc-nondeid.nii.gz')

    # Construct the nobrainer command for brain extraction
    # nobrainer is a deep learning-based neuroimaging tool for brain extraction
    cmd = ['nobrainer',                    # Base command
           'predict',                      # Use prediction mode
           '--model=/opt/nobrainer/models/brain-extraction-unet-128iso-model.h5',  # Pre-trained U-Net model for brain extraction
           '--verbose',                    # Enable verbose output for debugging/monitoring
           image,                          # Input image file path
           outfile,                        # Output brain mask file path
           ]
    
    # Execute the nobrainer brain extraction command
    # check_call will raise an exception if the command fails (non-zero exit code)
    # This ensures the function fails fast if brain extraction doesn't work
    check_call(cmd)


def run_brain_extraction_nb(image, subject_label, bids_dir):
    """
    Setup and run nobrainer brainextraction workflow.

    Parameters
    ----------
    image : str
        Path to image that should be defaced.
    outfile : str
        Name of the defaced file.
    bids_dir : str
        Path to BIDS root directory.
    """

    # Create a Nipype workflow for brain extraction
    brainextraction_wf = pe.Workflow('brainextraction_wf')
    
    # Create an input node to handle input data
    # IdentityInterface passes data through without modification
    inputnode = pe.Node(niu.IdentityInterface(['in_file']),
                        name='inputnode')
    
    # Create a processing node that wraps the brain_extraction_nb function
    brainextraction = pe.Node(Function(input_names=['image', 'subject_label', 'bids_dir'],
                                       output_names=['outfile'],
                                       function=brain_extraction_nb),
                              name='brainextraction')
    
    # Connect the input node to the brain extraction node
    brainextraction_wf.connect([(inputnode, brainextraction, [('in_file', 'image')])])
    
    # Set the input data - the path to the image file to be processed
    inputnode.inputs.in_file = image
    
    # Set the subject label for the brain extraction node
    # This is used to construct proper output paths and filenames
    brainextraction.inputs.subject_label = subject_label
    
    # Set the BIDS directory path for the brain extraction node
    # This defines where output files should be stored
    brainextraction.inputs.bids_dir = bids_dir
    
    # Execute the workflow
    # This runs the entire pipeline: input -> brain extraction -> output
    brainextraction_wf.run()


def run_brain_extraction_bet(image, frac, subject_label, bids_dir):
    """
    Setup and FSLs brainextraction (BET) workflow.

    Parameters
    ----------
    image : str
        Path to image that should be defaced.
    frac : float
        Fractional intensity threshold (0 - 1).
    outfile : str
        Name of the defaced file.
    bids_dir : str
        Path to BIDS root directory.
    """

    import os

    # Construct the output path for the brain-extracted image
    # The output will be saved in the subject's backup directory with descriptive naming
    # Extract the base filename and add brain mask identifier and non-deid descriptor
    outfile = os.path.join(bids_dir, "sourcedata/bidsonym/sub-%s" % subject_label,
                           image[image.rfind('/') + 1:image.rfind('.nii')] + '_brainmask_desc-nondeid.nii.gz')

    # Create a Nipype workflow for FSL BET brain extraction
    # BET (Brain Extraction Tool) is FSL's classic brain extraction algorithm
    brainextraction_wf = pe.Workflow('brainextraction_wf')
    
    # Create an input node to handle input data
    # IdentityInterface passes data through without modification
    # This serves as the entry point for data into the workflow
    inputnode = pe.Node(niu.IdentityInterface(['in_file']),
                        name='inputnode')
    
    # Create a BET (Brain Extraction Tool) node from FSL
    # mask=False means we want the brain-extracted image, not just a binary mask
    # BET uses intensity-based thresholding and morphological operations for brain extraction
    bet = pe.Node(BET(mask=False), name='bet')
    
    # Connect the input node to the BET node
    # This creates a data flow: inputnode.in_file -> bet.in_file
    brainextraction_wf.connect([
        (inputnode, bet, [('in_file', 'in_file')])
    ])
    
    # Set the input data - the path to the image file to be processed
    inputnode.inputs.in_file = image
    
    # Set the fractional intensity threshold for BET
    # This parameter controls how aggressively BET removes non-brain tissue
    # Lower values (e.g., 0.1) = more conservative, higher values (e.g., 0.7) = more aggressive
    bet.inputs.frac = float(frac)
    
    # Set the output file path for the brain-extracted image
    bet.inputs.out_file = outfile
    
    # Execute the workflow
    # This runs the entire pipeline: input -> BET brain extraction -> output
    brainextraction_wf.run()


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

    # functionality copied from pydeface
    
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
        # Note: There's a typo here - should be get_fdata() not fget_data()
        outdata = infile_img.fget_data() * tmpdata

    # Create a new NIfTI image with the defaced data
    # Preserve the original image's spatial transformation (affine) and metadata (header)
    masked_brain = Nifti1Image(outdata, infile_img._affine,
                               infile_img._header)
    
    # Save the defaced image to the specified output file
    masked_brain.to_filename(outfile)


def clean_up_files(bids_dir, subject_label, session=None):
    """
    Restructure BIDSonym outcomes following BIDS conventions.

    Parameters
    ----------
    bids_dir : str
        Path to BIDS root directory.
    subject_label : str
        Label of subject to move (without 'sub-').
    session : str, optional
        If multiple sessions exist, create session specific
        structure.
    """

    # Create output paths based on whether session information is provided
    if session is not None:
        # For multi-session datasets, organize files by session
        out_path_images = os.path.join(bids_dir, "sourcedata/bidsonym/sub-%s/ses-%s/images"
                                       % (subject_label, session))
        out_path_info = os.path.join(bids_dir, "sourcedata/bidsonym/sub-%s/ses-%s/meta_data_info"
                                     % (subject_label, session))
        
        # Find all files for this specific subject and session combination
        # Look for NIfTI image files (original, defaced, brain masks, etc.)
        list_imaging_files = glob(os.path.join(bids_dir, 'sourcedata/bidsonym/sub-%s' % subject_label,
                                               'sub-' + subject_label + '_ses-' + session + '*.nii.gz'))
        
        # Find visualization files (PNG images showing before/after defacing)
        list_graphics = glob(os.path.join(bids_dir, 'sourcedata/bidsonym/sub-%s' % subject_label,
                                          'sub-' + subject_label + '_ses-' + session + '*.png'))
        
        # Find animated GIF files (showing defacing process or comparisons)
        list_gifs = glob(os.path.join(bids_dir, 'sourcedata/bidsonym/sub-%s' % subject_label,
                                      'sub-' + subject_label + '_ses-' + session + '*.gif'))
        
        # Find metadata analysis CSV files (from check_meta_data function)
        list_info_files = glob(os.path.join(bids_dir, 'sourcedata/bidsonym/sub-%s' % subject_label,
                                            'sub-' + subject_label + '_ses-' + session + '*.csv'))
        
        # Find JSON metadata files (original and modified)
        list_meta_files = glob(os.path.join(bids_dir, 'sourcedata/bidsonym/sub-%s' % subject_label,
                                            'sub-' + subject_label + '_ses-' + session + '*.json'))
    else:
        # For single-session datasets, organize files without session subdirectories
        out_path_images = os.path.join(bids_dir, "sourcedata/bidsonym/sub-%s/images" % subject_label)
        out_path_info = os.path.join(bids_dir, "sourcedata/bidsonym/sub-%s/meta_data_info" % subject_label)
        
        # Find all files for this subject (no session filtering)
        # Look for NIfTI image files in the subject's directory
        list_imaging_files = glob(os.path.join(bids_dir, 'sourcedata/bidsonym/sub-%s' % subject_label, '*.nii.gz'))
        
        # Find visualization PNG files
        list_graphics = glob(os.path.join(bids_dir, 'sourcedata/bidsonym/sub-%s' % subject_label, '*.png'))
        
        # Find animated GIF files
        list_gifs = glob(os.path.join(bids_dir, 'sourcedata/bidsonym/sub-%s' % subject_label, '*.gif'))
        
        # Find metadata analysis CSV files
        list_info_files = glob(os.path.join(bids_dir, 'sourcedata/bidsonym/sub-%s' % subject_label, '*.csv'))
        
        # Find JSON metadata files
        list_meta_files = glob(os.path.join(bids_dir, 'sourcedata/bidsonym/sub-%s' % subject_label, '*.json'))

    # Create output directories if they don't exist
    # Directory for image-related files (NIfTI, PNG, GIF)
    if os.path.isdir(out_path_images) is False:
        os.makedirs(out_path_images)
    
    # Directory for meta-data-related files (CSV, JSON)
    if os.path.isdir(out_path_info) is False:
        os.makedirs(out_path_info)

    # Combine all image-related files for organized moving
    # This includes original images, defaced images, brain masks, and visualizations
    images = list_imaging_files + list_graphics + list_gifs

    # Move all image-related files to the organized images directory
    for image_file in images:
        # Extract just the filename from the full path
        file_out = image_file[image_file.rfind('/') + 1:]
        # Move file to the organized images directory
        move(image_file, os.path.join(out_path_images, file_out))

    # Move all meta-data files to the organized info directory
    # This includes CSV analysis files and JSON metadata files
    for info_file in list_info_files + list_meta_files:
        # Extract just the filename from the full path
        file_out = info_file[info_file.rfind('/') + 1:]
        # Move file to the organized metadata info directory
        move(info_file, os.path.join(out_path_info, file_out))


def revert_bidsonym(bids_dir, subject_label, session=None, confirm=True):
    """
    Revert the BIDSonym process by copying back non-defaced images and
    metadata from sourcedata and removing all BIDSonym-generated files.

    This function performs a complete reversal of the BIDSonym anonymization
    process by restoring original files from the sourcedata backup and removing
    all defaced/de-identified files from the main BIDS structure.

    Parameters
    ----------
    bids_dir : str
        Path to BIDS root directory.
    subject_label : str
        Label of subject to restore (without 'sub-' prefix).
    session : str, optional
        Session label (if applicable, without 'ses-' prefix).
        If provided, only that specific session will be reverted.
    confirm : bool, optional
        If True, ask for user confirmation before proceeding.
        Default is True for safety to prevent accidental data loss.
    
    Returns
    -------
    bool
        True if reversion was successful, False otherwise.
    """
    
    import os
    import shutil
    from glob import glob
    from shutil import copy2
    
    # Set up logging system
    log_print, log_path = setup_logging(bids_dir, subject_label, session, "bidsonymrevert")
    
    # Build session description for messages
    session_desc = f" (session: {session})" if session is not None else ""
    
    # Display header with subject and session information
    log_print("BIDSonym Revert")
    log_print(f"Subject: sub-{subject_label}")
    
    # Build descriptive message including session if provided
    if session is not None:
        log_print(f"Session: ses-{session}")
        log_print("Processing multi-session dataset structure")
    else:
        log_print("Processing single-session dataset structure")
    
    if log_path:
        log_print(f"Log file created: {log_path}")
    
    # Define paths based on whether this is a session-specific or single-session dataset
    if session is not None:
        # Multi-session dataset: target specific session directory
        subject_dir = os.path.join(bids_dir, f"sub-{subject_label}", f"ses-{session}")
        sourcedata_subject_dir = os.path.join(bids_dir, "sourcedata", "bidsonym", f"sub-{subject_label}", f"ses-{session}")
        # Base directory contains all sessions for this subject
        sourcedata_base_dir = os.path.join(bids_dir, "sourcedata", "bidsonym", f"sub-{subject_label}")
    else:
        # Single-session dataset: target subject directory directly
        subject_dir = os.path.join(bids_dir, f"sub-{subject_label}")
        sourcedata_subject_dir = os.path.join(bids_dir, "sourcedata", "bidsonym", f"sub-{subject_label}")
        # Base and subject directories are the same for single-session
        sourcedata_base_dir = sourcedata_subject_dir
    
    # Display path information for transparency
    log_print(f"BIDS directory: {bids_dir}")
    log_print(f"Target subject directory: {subject_dir}")
    log_print(f"BIDSonym sourcedata directory: {sourcedata_base_dir}")
    log_print("-" * 60)
    
    # Check if sourcedata directory exists - this indicates BIDSonym was previously run
    log_print(f"\n Checking for BIDSonym backup data{session_desc}...")
    if not os.path.exists(sourcedata_base_dir):
        log_print(f"ERROR: No BIDSonym sourcedata found for subject {subject_label}{session_desc}", "ERROR")
        log_print(f"   Expected location: {sourcedata_base_dir}", "ERROR")
        log_print("   This indicates BIDSonym was never run on this subject, or", "ERROR")
        log_print("   the backup data has been manually removed.", "ERROR")
        return False
    else:
        log_print(f"Found BIDSonym backup directory: {sourcedata_base_dir}")
    
    # Find all original files in sourcedata directory tree
    # These files have 'desc-nondeid' identifier and represent the original, non-anonymized data
    log_print(f"\nScanning for original (non-anonymized) files{session_desc}...")
    
    # Look for files with 'desc-nondeid' identifier in the main sourcedata directory
    # Use recursive search to handle both organized and unorganized file structures
    original_images = glob(os.path.join(sourcedata_base_dir, "**/*desc-nondeid.nii.gz"), recursive=True)
    original_json_files = glob(os.path.join(sourcedata_base_dir, "**/*desc-nondeid.json"), recursive=True)
    
    # Also check organized subdirectories that may exist if clean_up_files was run
    # These subdirectories separate images from metadata for better organization
    images_subdir = os.path.join(sourcedata_base_dir, "images")
    metadata_subdir = os.path.join(sourcedata_base_dir, "meta_data_info")
    
    # Check if organized images subdirectory exists and scan it
    if os.path.exists(images_subdir):
        log_print(f"   Checking organized images subdirectory: {images_subdir}")
        additional_images = glob(os.path.join(images_subdir, "*desc-nondeid.nii.gz"))
        original_images.extend(additional_images)
        
    # Check if organized metadata subdirectory exists and scan it    
    if os.path.exists(metadata_subdir):
        log_print(f"   Checking organized metadata subdirectory: {metadata_subdir}")
        additional_json = glob(os.path.join(metadata_subdir, "*desc-nondeid.json"))
        original_json_files.extend(additional_json)
    
    # Find current defaced/modified files in main BIDS structure that need to be replaced
    # These are the anonymized files that will be removed and replaced with originals
    log_print(f"\nScanning current BIDS structure for files to replace{session_desc}...")
    if session is not None:
        # For session-specific reversion, only scan the target session directory
        log_print(f"   Scanning session-specific directory: {subject_dir}")
        current_images = glob(os.path.join(subject_dir, "**/*.nii.gz"), recursive=True)
        current_json_files = glob(os.path.join(subject_dir, "**/*.json"), recursive=True)
    else:
        # For single-session reversion, scan the entire subject directory
        log_print(f"   Scanning subject directory: {subject_dir}")
        current_images = glob(os.path.join(subject_dir, "**/*.nii.gz"), recursive=True)
        current_json_files = glob(os.path.join(subject_dir, "**/*.json"), recursive=True)
    
    # Validate that we found backup files to restore
    # If no original files are found, this suggests BIDSonym was never run or backup data is missing
    if not original_images and not original_json_files:
        log_print(f"  WARNING: No original files found in sourcedata for subject {subject_label}{session_desc}", "WARNING")
        log_print("   This may indicate that:", "WARNING")
        log_print("   - BIDSonym was not previously run on this subject/session", "WARNING")
        log_print("   - The backup files were manually removed", "WARNING")
        log_print("   - The BIDSonym process was incomplete or failed", "WARNING")
        log_print("   - Files may be in a different location or naming convention", "WARNING")
        return False
    
    # Display comprehensive summary of what will be restored
    log_print("\n REVERSION SUMMARY:")
    log_print("=" * 60)
    
    log_print(f" Original image files to restore: {len(original_images)}")
    if original_images:
        for img in original_images[:3]:  # Show first 3
            log_print(f"    {os.path.basename(img)}")
        if len(original_images) > 3:
            log_print(f"   ... and {len(original_images) - 3} more image files")
    
    log_print(f"\n Original JSON metadata files to restore: {len(original_json_files)}")
    if original_json_files:
        for json_file in original_json_files[:3]:  # Show first 3
            log_print(f"    {os.path.basename(json_file)}")
        if len(original_json_files) > 3:
            log_print(f"   ... and {len(original_json_files) - 3} more JSON files")
    
    log_print("\n  Current files to be removed:")
    log_print(f"   - {len(current_images)} defaced/modified image files")
    log_print(f"   - {len(current_json_files)} de-identified JSON files")
    
    log_print("\n Directories to be cleaned up:")
    log_print(f"   - {sourcedata_base_dir}")
    
    # Check if we'll remove the entire bidsonym directory structure
    # This helps inform the user about the scope of cleanup
    bidsonym_dir = os.path.join(bids_dir, "sourcedata", "bidsonym")
    remaining_subjects = []
    if os.path.exists(bidsonym_dir):
        # Find other subjects that have BIDSonym data (excluding current subject)
        remaining_subjects = [
            d for d in os.listdir(bidsonym_dir)
            if os.path.isdir(os.path.join(bidsonym_dir, d))
            and d != f"sub-{subject_label}"
        ]
    
    # Inform user about directory cleanup scope
    if not remaining_subjects:
        log_print(f"   - {bidsonym_dir} (no other subjects remain)")
        sourcedata_dir = os.path.join(bids_dir, "sourcedata")
        # Check if sourcedata will be completely empty after cleanup
        if os.path.exists(sourcedata_dir) and len(os.listdir(sourcedata_dir)) == 1:
            log_print(f"   - {sourcedata_dir} (will be empty)")
    else:
        log_print(f"   Note: {len(remaining_subjects)} other subjects remain in BIDSonym sourcedata")
    
    # Confirmation prompt with clear warning
    if confirm:
        log_print("\n" + "=" * 60)
        log_print("  IMPORTANT WARNING:")
        log_print("   This will permanently replace all defaced/de-identified files")
        log_print(f"   with the original non-anonymized versions for subject {subject_label}{session_desc}.")
        log_print("   This action cannot be undone!")
        if session is not None:
            log_print(f"   Only session '{session}' will be reverted for this subject.")
        else:
            log_print("   All sessions/data for this subject will be reverted.")
        log_print("=" * 60)
        
        # Note: We still need to use regular input() for user interaction
        response = input("\nType 'yes' to proceed with BIDSonym reversion: ")
        log_print(f"User response to confirmation prompt: '{response}'", "INFO")
        
        if response.lower() != 'yes':
            log_print(" BIDSonym reversion cancelled by user.", "INFO")
            return False
    
    try:
        # Step 1: Remove current defaced/modified files from main BIDS structure
        log_print(f"\n  STEP 1: Removing defaced/de-identified files{session_desc}...")
        log_print(f"   Cleaning up main BIDS directory: {subject_dir}")
        
        # Initialize counters to track removal progress
        removed_images = 0
        removed_json = 0
        
        # Remove all current image files (these are defaced/anonymized versions)
        for img_file in current_images:
            try:
                os.remove(img_file)
                removed_images += 1
                log_print(f"      Removed image: {os.path.basename(img_file)}")
            except OSError as e:
                log_print(f"       WARNING: Could not remove {os.path.basename(img_file)}: {e}", "WARNING")
        
        # Remove all current JSON files (these contain de-identified metadata)
        for json_file in current_json_files:
            try:
                os.remove(json_file)
                removed_json += 1
                log_print(f"      Removed JSON: {os.path.basename(json_file)}")
            except OSError as e:
                log_print(f"       WARNING: Could not remove {os.path.basename(json_file)}: {e}", "WARNING")
                
        log_print(f"   Summary: Removed {removed_images} images and {removed_json} JSON files")
        
        # Step 2: Restore original image files to their proper BIDS locations
        log_print(f"\n STEP 2: Restoring original image files{session_desc}...")
        log_print("   Copying from sourcedata back to main BIDS structure")
        
        # Initialize counter to track restoration progress
        restored_images = 0
        
        # Process each original image file found in sourcedata
        for original_img in original_images:
            # Remove the BIDSonym identifier to get the original BIDS filename
            original_basename = os.path.basename(original_img)
            restored_basename = original_basename.replace('_desc-nondeid', '')
            
            # Determine where this file should go in the BIDS structure
            # This logic handles files from both organized and unorganized sourcedata
            if "images/" in original_img:
                # File is in organized structure - extract just the filename
                relative_path = restored_basename
            else:
                # File is in root of subject sourcedata directory
                relative_path = restored_basename
            
            # Determine target directory based on BIDS file naming conventions
            # Use the base subject directory (which may include session)
            if session is not None:
                base_subject_dir = subject_dir
            else:
                base_subject_dir = subject_dir
                
            # Classify file type by filename patterns following BIDS conventions
            if 'T1w' in restored_basename or 'T2w' in restored_basename or 'FLAIR' in restored_basename:
                target_dir = os.path.join(base_subject_dir, 'anat')
                modality = "anatomical"
            elif 'bold' in restored_basename:
                target_dir = os.path.join(base_subject_dir, 'func')
                modality = "functional"
            elif 'dwi' in restored_basename:
                target_dir = os.path.join(base_subject_dir, 'dwi')
                modality = "diffusion"
            else:
                # Default to anat directory for unknown/unclassified image types
                target_dir = os.path.join(base_subject_dir, 'anat')
                modality = "anatomical (default)"
            
            # Create target directory if it doesn't exist (handles new directory structure)
            os.makedirs(target_dir, exist_ok=True)
            
            # Copy the original file back to its proper BIDS location
            target_path = os.path.join(target_dir, restored_basename)
            copy2(original_img, target_path)
            restored_images += 1
            log_print(f"      Restored {modality}: {restored_basename}")
        
        log_print(f"   Summary: Restored {restored_images} original image files")
        
        # Step 3: Restore original JSON metadata files
        log_print(f"\n STEP 3: Restoring original JSON metadata files{session_desc}...")
        log_print("   Restoring non-de-identified metadata")
        
        # Initialize counter to track JSON restoration progress
        restored_json = 0
        
        # Process each original JSON file found in sourcedata
        for original_json in original_json_files:
            # Determine the target path by removing the 'desc-nondeid' identifier
            original_basename = os.path.basename(original_json)
            restored_basename = original_basename.replace('_desc-nondeid', '')
            
            # Determine target directory (same logic as images)
            if session is not None:
                base_subject_dir = subject_dir
            else:
                base_subject_dir = subject_dir
                
            # Classify metadata type by filename patterns following BIDS conventions
            if 'T1w' in restored_basename or 'T2w' in restored_basename or 'FLAIR' in restored_basename:
                target_dir = os.path.join(base_subject_dir, 'anat')
                metadata_type = "anatomical"
            elif 'bold' in restored_basename:
                target_dir = os.path.join(base_subject_dir, 'func')
                metadata_type = "functional"
            elif 'dwi' in restored_basename:
                target_dir = os.path.join(base_subject_dir, 'dwi')
                metadata_type = "diffusion"
            else:
                # Check if it's a task-level JSON (should go to BIDS root)
                if original_basename.startswith('task-'):
                    target_dir = bids_dir
                    metadata_type = "task-level"
                else:
                    target_dir = os.path.join(base_subject_dir, 'anat')
                    metadata_type = "anatomical (default)"
            
            # Create target directory if it doesn't exist
            os.makedirs(target_dir, exist_ok=True)
            
            # Copy the original file back to its proper location
            target_path = os.path.join(target_dir, restored_basename)
            copy2(original_json, target_path)
            restored_json += 1
            log_print(f"      Restored {metadata_type} metadata: {restored_basename}")
        
        log_print(f"   Summary: Restored {restored_json} original JSON metadata files")
        
        # Step 4: Remove the entire BIDSonym sourcedata directory structure
        log_print("\n STEP 4: Cleaning up BIDSonym backup directories...")
        
        # Remove the subject's BIDSonym directory
        shutil.rmtree(sourcedata_base_dir)
        log_print(f"      Removed subject backup directory: {sourcedata_base_dir}")
        
        # Check if the parent sourcedata/bidsonym directory is now empty
        bidsonym_dir = os.path.join(bids_dir, "sourcedata", "bidsonym")
        if os.path.exists(bidsonym_dir) and not os.listdir(bidsonym_dir):
            shutil.rmtree(bidsonym_dir)
            log_print(f"      Removed empty BIDSonym directory: {bidsonym_dir}")
            
            # Check if sourcedata directory is now empty
            sourcedata_dir = os.path.join(bids_dir, "sourcedata")
            if os.path.exists(sourcedata_dir) and not os.listdir(sourcedata_dir):
                shutil.rmtree(sourcedata_dir)
                log_print(f"      Removed empty sourcedata directory: {sourcedata_dir}")
        else:
            remaining_subjects = [
                d for d in os.listdir(bidsonym_dir)
                if os.path.isdir(os.path.join(bidsonym_dir, d))
            ]
            log_print(f"      BIDSonym directory retained ({len(remaining_subjects)} other subjects remain)")
        
        # Final success message with summary
        log_print("\n" + "=" * 60)
        log_print(" REVERSION COMPLETED SUCCESSFULLY!")
        log_print(f"Subject: sub-{subject_label}{session_desc}")
        log_print("")
        log_print(" Summary:")
        log_print(f"  • Restored {restored_images} original image files")
        log_print(f"  • Restored {restored_json} original JSON metadata files") 
        log_print(f"  • Removed {removed_images + removed_json} anonymized files")
        log_print("  • Cleaned up backup directories")
        log_print("")
        log_print("  IMPORTANT: Your data is now in its original, non-anonymized state.")
        log_print(f"   All facial features and identifying metadata have been restored{session_desc}.")
        log_print("")
        if log_path:
            log_print(f" Log file saved: {log_path}")
        log_print("=" * 60)
        return True
        
    except Exception as e:
        log_print("\n" + "=" * 60, "ERROR")
        log_print(" ERROR DURING BIDSONYM REVERSION!", "ERROR")
        log_print(f"Subject: sub-{subject_label}{session_desc}", "ERROR")
        log_print("")
        log_print(f"Error details: {e}", "ERROR")
        log_print("")
        log_print("  IMPORTANT: The reversion process may be incomplete.", "ERROR")
        log_print("   Please manually check your dataset for:", "ERROR")
        log_print("   • Missing or corrupted files", "ERROR")
        log_print("   • Partially restored directories", "ERROR")
        log_print("   • Remaining BIDSonym backup files", "ERROR")
        log_print("")
        log_print(" Troubleshooting tips:", "ERROR")
        log_print("   • Check file permissions in BIDS and sourcedata directories", "ERROR")
        log_print("   • Verify sufficient disk space", "ERROR")
        log_print("   • Ensure no other processes are accessing the files", "ERROR")
        log_print("   • Consider running with confirm=False to bypass prompts", "ERROR")
        log_print("")
        if log_path:
            log_print(f" Error log saved: {log_path}", "ERROR")
        log_print("=" * 60, "ERROR")
        return False
