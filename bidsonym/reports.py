# Import all required modules at the top
import os
from datetime import datetime
from glob import glob
from os.path import join as opj
from shutil import move

import matplotlib.pyplot as plt
from matplotlib.pyplot import figure
import nipype.pipeline.engine as pe
from nipype import Function
from nipype.interfaces import utility as niu
from bids import BIDSLayout
from nilearn.plotting import find_cut_slices, plot_stat_map
import gif_your_nifti.core as gif2nif


def setup_logging(bids_dir, subject_label, session=None, 
                  operation="bidsonymrevert"):
    """
    Set up logging functionality for BIDSonym operations.
    
    Creates a BIDS-compliant log file and returns a logging function that 
    writes to both console and the log file with timestamps and severity levels.
    
    Parameters
    ----------
    bids_dir : str
        Path to BIDS root directory.
    subject_label : str
        Label of subject (without 'sub-' prefix).
    session : str, optional
        Session label (without 'ses-' prefix), if applicable.
    operation : str, optional
        Name of the operation being logged (default: 'bidsonymrevert').
        
    Returns
    -------
    tuple
        (log_print_function, log_file_path)
        log_print_function: Function to print and log messages
        log_file_path: Path to the created log file
    """
    
    # Create BIDS-compliant log filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    if session is not None:
        log_filename = (f"sub-{subject_label}_ses-{session}_desc-"
                        f"{operation}_{timestamp}.log")
    else:
        log_filename = (f"sub-{subject_label}_desc-{operation}_"
                        f"{timestamp}.log")
    
    # Create log directory following BIDS conventions with subject subdirectory
    log_base_dir = os.path.join(bids_dir, "sourcedata", "bidsonym", 
                                f"{operation}_logs")
    log_subject_dir = os.path.join(log_base_dir, f"sub-{subject_label}")
    os.makedirs(log_subject_dir, exist_ok=True)
    log_path = os.path.join(log_subject_dir, log_filename)
    
    # Initialize log file with header information
    try:
        with open(log_path, 'w', encoding='utf-8') as log_file:
            log_file.write("=" * 80 + '\n')
            log_file.write(f"BIDSonym {operation.title()} Log\n")
            log_file.write("=" * 80 + '\n')
            log_file.write(f"Timestamp: "
                           f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            log_file.write(f"Subject: sub-{subject_label}\n")
            if session is not None:
                log_file.write(f"Session: ses-{session}\n")
            log_file.write(f"BIDS Directory: {bids_dir}\n")
            log_file.write(f"Log File: {log_path}\n")
            log_file.write("=" * 80 + '\n\n')
        
        # Create the log_print function with access to log_path
        def log_print(message="", level="INFO"):
            """Print message to console and write to log file with timestamp 
            and level."""
            timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_message = f"[{timestamp_str}] [{level}] {message}"
            
            # Print to console (original behavior)
            print(message)
            
            # Write to log file
            try:
                with open(log_path, 'a', encoding='utf-8') as log_file:
                    log_file.write(log_message + '\n')
            except Exception as e:
                # If logging fails, at least show the error on console
                print(f"WARNING: Could not write to log file: {e}")
        
        return log_print, log_path
        
    except Exception as e:
        print(f"WARNING: Could not create log file {log_path}: {e}")
        
        # Fall back to regular print function if logging fails
        def log_print(message="", level="INFO"):
            print(message)
        
        return log_print, None


def plot_defaced(bids_dir, subject_label, session=None, t2w=None):
    """
    Plot brainmask created from original non-defaced image on defaced image
    to evaluate defacing performance.

    This function creates static plots showing the brain mask overlaid on the
    defaced images to visually assess the quality of the defacing process.
    The plots show axial, coronal, and sagittal views with the brain mask
    highlighting preserved brain regions.

    Parameters
    ----------
    bids_dir : str
        Path to BIDS root directory.
    subject_label : str
        Label of subject to be plotted (without 'sub-' prefix).
    session : str, optional
        If multiple sessions exist, create one plot per session.
        If None, processes all sessions for the subject.
    t2w : bool, optional
        If True and T2w/FLAIR images exist, create plots for those as well.
        Currently processes FLAIR images when t2w=True.

    Returns
    -------
    tuple
        (t1w_files, t2w_flag) - paths to processed T1w files and t2w parameter
    """

    # Initialize BIDS layout to query dataset structure
    layout = BIDSLayout(bids_dir)
    
    # Define path to BIDSonym sourcedata directory for this subject
    bidsonym_path = opj(bids_dir, f'sourcedata/bidsonym/sub-{subject_label}')

    # Query for T1w images based on session specification
    if session is not None:
        # Get T1w images for specific session
        defaced_t1w = layout.get(
            subject=subject_label, 
            extension='nii.gz', 
            suffix='T1w',
            return_type='filename', 
            session=session
        )
    else:
        # Get all T1w images for subject (all sessions)
        defaced_t1w = layout.get(
            subject=subject_label, 
            extension='nii.gz', 
            suffix='T1w',
            return_type='filename'
        )

    # Process each T1w image found
    for t1w in defaced_t1w:
        # Construct path to corresponding brain mask file
        # Extract filename and replace extension with brain mask naming convention
        brain_mask_pattern = (
            t1w[t1w.rfind('/') + 1:t1w.rfind('.nii')] + 
            '_brainmask_desc-nondeid.nii.gz'
        )
        brainmask_t1w = glob(opj(bidsonym_path, brain_mask_pattern))[0]
        
        # Create figure with subplots for three orthogonal views
        fig = figure(figsize=(15, 5))
        plt.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=-0.2, hspace=0)
        
        # Generate plots for each anatomical direction (sagittal, coronal, axial)
        for i, direction in enumerate(['x', 'y', 'z']):
            ax = fig.add_subplot(3, 1, i + 1)
            
            # Find optimal slice positions for this direction
            cuts = find_cut_slices(t1w, direction=direction, n_cuts=12)
            
            # Plot brain mask overlaid on defaced T1w image
            plot_stat_map(
                brainmask_t1w,           # Brain mask as overlay
                bg_img=t1w,              # Defaced T1w as background
                display_mode=direction,   # Anatomical direction
                cut_coords=cuts,         # Slice positions
                annotate=False,          # No anatomical annotations
                dim=-1,                  # Dim background slightly
                axes=ax,                 # Use specific subplot
                colorbar=False           # No colorbar
            )
        
        # Save the plot with descriptive filename
        output_filename = (
            t1w[t1w.rfind('/') + 1:t1w.rfind('.nii')] + 
            '_desc-brainmaskdeid.png'
        )
        plt.savefig(opj(bidsonym_path, output_filename))

    # Process T2w/FLAIR images if requested
    if t2w is not None:
        # Query for FLAIR images (T2w images are commented out)
        if session is not None:
            # Get FLAIR images for specific session
            defaced_flair = layout.get(
                subject=subject_label, 
                extension='nii.gz', 
                suffix='FLAIR',
                return_type='filename', 
                session=session
            )
        else:
            # Get all FLAIR images for subject
            defaced_flair = layout.get(
                subject=subject_label, 
                extension='nii.gz', 
                suffix='FLAIR',
                return_type='filename'
            )

        # Process each FLAIR image found
        for flair in defaced_flair:
            # Construct path to corresponding brain mask
            brain_mask_pattern = (
                flair[flair.rfind('/') + 1:flair.rfind('.nii')] + 
                '_brainmask_desc-nondeid.nii.gz'
            )
            brainmask_flair = glob(opj(bidsonym_path, brain_mask_pattern))[0]
            
            # Create figure with subplots (reusing previous figure structure)
            for i, direction in enumerate(['x', 'y', 'z']):
                ax = fig.add_subplot(3, 1, i + 1)
                
                # Find optimal slice positions for FLAIR image
                cuts = find_cut_slices(flair, direction=direction, n_cuts=12)
                
                # Plot brain mask overlaid on defaced FLAIR image
                plot_stat_map(
                    brainmask_flair,         # Brain mask as overlay
                    bg_img=flair,            # Defaced FLAIR as background
                    display_mode=direction,   # Anatomical direction
                    cut_coords=cuts,         # Slice positions
                    annotate=False,          # No anatomical annotations
                    dim=-1,                  # Dim background slightly
                    axes=ax,                 # Use specific subplot
                    colorbar=False           # No colorbar
                )
            
            # Save FLAIR plot with descriptive filename
            output_filename = (
                flair[flair.rfind('/') + 1:flair.rfind('.nii')] + 
                '_desc-brainmaskdeid.png'
            )
            plt.savefig(opj(bidsonym_path, output_filename))

    # Return processed files for potential downstream use
    return (t1w, t2w)


def gif_defaced(bids_dir, subject_label, session=None, t2w=None):
    """
    Create animated GIFs that loop through slices of defaced images in
    orthogonal directions (x, y, z).

    This function generates animated visualizations of the defaced images
    to provide a comprehensive view of the defacing quality across all
    slices in each anatomical direction.

    Parameters
    ----------
    bids_dir : str
        Path to BIDS root directory.
    subject_label : str
        Label of subject to be processed (without 'sub-' prefix).
    session : str, optional
        If multiple sessions exist, create one GIF per session.
        If None, processes all sessions for the subject.
    t2w : bool, optional
        If True and T2w images exist, create GIFs for T2w images as well.

    Notes
    -----
    The generated GIFs are initially created in the subject's anatomical
    directory and then moved to the BIDSonym sourcedata directory for
    organization and storage.
    """

    # Initialize BIDS layout to query dataset structure
    layout = BIDSLayout(bids_dir)
    
    # Define path to BIDSonym sourcedata directory for this subject
    bidsonym_path = opj(bids_dir, f'sourcedata/bidsonym/sub-{subject_label}')

    # Query for T1w images based on session specification
    if session is not None:
        # Get T1w images for specific session
        defaced_t1w = layout.get(
            subject=subject_label, 
            extension='nii.gz', 
            suffix='T1w',
            return_type='filename', 
            session=session
        )
        
        # Get T2w images for specific session if requested
        if t2w is not None:
            defaced_t2w = layout.get(
                subject=subject_label, 
                extension='nii.gz', 
                suffix='T2w',
                return_type='filename', 
                session=session
            )
    else:
        # Get all T1w images for subject (all sessions)
        defaced_t1w = layout.get(
            subject=subject_label, 
            extension='nii.gz', 
            suffix='T1w',
            return_type='filename'
        )
        
        # Get all T2w images for subject if requested
        # Note: There's an inconsistency here - session parameter is passed even when session is None
        if t2w is not None:
            defaced_t2w = layout.get(
                subject=subject_label, 
                extension='nii.gz', 
                suffix='T2w',
                return_type='filename', 
                session=session  # This should probably be removed when session is None
            )

    # Generate GIFs for all T1w images found
    for t1_image in defaced_t1w:
        # Create animated GIF showing slices through the T1w image
        gif2nif.write_gif_normal(t1_image)

    # Generate GIFs for T2w images if requested
    if t2w is not None:
        for t2_image in defaced_t2w:
            # Create animated GIF showing slices through the T2w image
            gif2nif.write_gif_normal(t2_image)

    # Locate and move generated GIF files to BIDSonym directory
    if session is not None:
        # Look for GIFs in session-specific anatomical directory
        gif_search_path = opj(
            bids_dir, 
            f'sub-{subject_label}/ses-{session}/anat',
            f'sub-{subject_label}*.gif'
        )
        list_gifs = glob(gif_search_path)
    else:
        # Look for GIFs in subject's anatomical directory
        gif_search_path = opj(
            bids_dir, 
            f'sub-{subject_label}/anat',
            f'sub-{subject_label}*.gif'
        )
        list_gifs = glob(gif_search_path)

    # Move all generated GIF files to BIDSonym sourcedata directory
    for gif_file in list_gifs:
        # Move GIF from original location to organized sourcedata location
        move(gif_file, bidsonym_path)


def create_graphics(bids_dir, subject_label, session=None, modalities=['T1w']):
    """
    Setup and run the graphics workflow which creates static plots and
    animated GIFs of defaced images for quality assessment.

    This function orchestrates the creation of visual reports by setting up
    a Nipype workflow that generates both static plots (with brain masks
    overlaid) and animated GIFs of the defaced images. Users can specify
    exactly which modalities to process.

    Parameters
    ----------
    bids_dir : str
        Path to BIDS root directory.
    subject_label : str
        Label of subject to be processed (without 'sub-' prefix).
    session : str, optional
        If multiple sessions exist, include them in workflow.
        If provided, only processes the specified session.
    modalities : list of str, optional
        List of image modalities to process. Default is ['T1w'].
        Supported modalities: 'T1w', 'T2w', 'FLAIR'.
        Examples: ['T1w'], ['T1w', 'T2w'], ['T1w', 'T2w', 'FLAIR']

    Notes
    -----
    The workflow uses Nipype for pipeline management, ensuring reproducible
    execution and proper dependency handling. Both static plots and GIF
    generation are enabled by default.

    Examples
    --------
    # Process only T1w images (default)
    create_graphics('/data/bids', 'sub001')
    
    # Process T1w and T2w images
    create_graphics('/data/bids', 'sub001', modalities=['T1w', 'T2w'])
    
    # Process only FLAIR images
    create_graphics('/data/bids', 'sub001', modalities=['FLAIR'])
    
    # Process all modalities for specific session
    create_graphics('/data/bids', 'sub001', session='01', modalities=['T1w', 'T2w', 'FLAIR'])
    """

    # Validate modalities parameter
    supported_modalities = ['T1w', 'T2w', 'FLAIR']
    if not modalities or not isinstance(modalities, list):
        print("Warning: No valid modalities selected. Defaulting to ['T1w'].")
        modalities = ['T1w']
    
    # Filter to only supported modalities
    valid_modalities = [mod for mod in modalities if mod in supported_modalities]
    if not valid_modalities:
        print("Warning: No valid modalities found. Defaulting to ['T1w'].")
        valid_modalities = ['T1w']

    # Create Nipype workflow for graphics generation
    report_wf = pe.Workflow('report_wf')

    # Define input node with all required parameters
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['bids_dir', 'subject_label', 'session', 'modalities']),
        name='inputnode'
    )
    
    # Create node for static plot generation
    plt_defaced = pe.Node(
        Function(
            input_names=['bids_dir', 'subject_label', 'session', 'modalities'],
            function=plot_defaced
        ),
        name='plt_defaced'
    )
    
    # Create node for GIF generation
    gf_defaced = pe.Node(
        Function(
            input_names=['bids_dir', 'subject_label', 'session', 'modalities'],
            function=gif_defaced
        ),
        name='gf_defaced'
    )

    # Connect mandatory inputs (bids_dir, subject_label, and modalities are always required)
    report_wf.connect([
        (inputnode, plt_defaced, [
            ('bids_dir', 'bids_dir'),
            ('subject_label', 'subject_label'),
            ('modalities', 'modalities')
        ]),
        (inputnode, gf_defaced, [
            ('bids_dir', 'bids_dir'),
            ('subject_label', 'subject_label'),
            ('modalities', 'modalities')
        ]),
    ])

    # Connect optional session input if provided
    if session:
        inputnode.inputs.session = session
        report_wf.connect([
            (inputnode, plt_defaced, [('session', 'session')]),
            (inputnode, gf_defaced, [('session', 'session')]),
        ])

    # Set all workflow inputs
    inputnode.inputs.bids_dir = bids_dir
    inputnode.inputs.subject_label = subject_label
    inputnode.inputs.modalities = valid_modalities
    
    # Display processing information
    print(f"Starting graphics workflow for subject {subject_label}")
    if session:
        print(f"Processing session: {session}")
    print(f"Processing modalities: {valid_modalities}")
    
    # Execute the complete workflow
    report_wf.run()
    print("Graphics workflow completed successfully")
