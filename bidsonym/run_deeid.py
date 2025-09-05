import argparse
import os
import sys
from pathlib import Path
from bidsonym.defacing_algorithms import (run_pydeface, run_mri_deface,
                                          run_mridefacer, run_quickshear,
                                          run_deepdefacer, run_image_deface)
from bidsonym.utils import (check_outpath, copy_no_deid, check_meta_data,
                            del_meta_data, run_brain_extraction_nb,
                            run_brain_extraction_bet, validate_input_dir,
                            rename_non_deid, clean_up_files, revert_bidsonym)
from bidsonym.reports import create_graphics, setup_logging
from bids import BIDSLayout
from ._version import get_versions


def get_parser():
    """
    Parse command line arguments for BIDSonym de-identification workflow.
    
    Returns
    -------
    argparse.ArgumentParser
        Configured argument parser with all BIDSonym options.
    """

    __version__ = get_versions()['version']

    parser = argparse.ArgumentParser(
        description='a BIDS app for de-identification of neuroimaging data'
    )
    parser.add_argument(
        'bids_dir', action='store', type=Path,
        help='The directory with the input dataset '
             'formatted according to the BIDS standard.'
    )
    parser.add_argument(
        'analysis_level',
        help='Level of the analysis that will be performed. '
             'Multiple participant level analyses can be run independently '
             '(in parallel) using the same output_dir.',
        choices=['participant', 'group']
    )
    parser.add_argument(
        '--participant_label',
        help='The label(s) of the participant(s) that should be '
             'pseudonymized. The label corresponds to sub-<participant_label> '
             'from the BIDS spec (so it does not include "sub-"). If this '
             'parameter is not provided all subjects will be pseudonymized. '
             'Multiple participants can be specified with a space separated '
             'list.',
        nargs="+"
    )
    parser.add_argument(
        '--session',
        help='The label(s) of the session(s) that should be pseudonymized. '
             'The label corresponds to ses-<participant_label> from the BIDS '
             'spec (so it does not include "ses-"). If this parameter is not '
             'provided all sessions will be pseudonymized. Multiple sessions '
             'can be specified with a space separated list.',
        nargs="+"
    )
    parser.add_argument(
        '--deid', help='Approach to use for de-identification.',
        choices=['pydeface', 'mri_deface', 'quickshear', 'mridefacer']
    )
    
    # Updated: More flexible modality specification
    parser.add_argument(
        '--deface_t2w', action="store_true", default=False,
        help='Deface T2w images by using defaced T1w image as deface-mask.'
    )
    parser.add_argument(
        '--deface_flair', action="store_true", default=False,
        help='Deface FLAIR images by using defaced T1w image as deface-mask.'
    )
    parser.add_argument(
        '--modalities',
        help='Specify which image modalities to process for quality control '
             'visualizations. Default is T1w only. Multiple modalities can '
             'be specified.',
        nargs="+", default=['T1w'],
        choices=['T1w', 'T2w', 'FLAIR']
    )
    
    parser.add_argument(
        '--check_meta',
        help='Indicate which information from the image and .json meta-data '
             'files should be check for potentially problematic information. '
             'Indicate strings that should be searched for. The results will '
             'be saved to sourcedata/',
        nargs="+"
    )
    parser.add_argument(
        '--del_meta',
        help='Indicate if and which information from the .json meta-data '
             'files should be deleted. If so, the original .json files will '
             'be copied to sourcedata/',
        nargs="+"
    )
    parser.add_argument(
        '--brainextraction',
        help='What algorithm should be used for pre-defacing brain extraction '
             '(outputs will be used in quality control).',
        choices=['bet', 'nobrainer']
    )
    parser.add_argument(
        '--bet_frac',
        help='In case BET is used for pre-defacing brain extraction, '
             'provide a Frac value.',
        nargs=1
    )
    parser.add_argument(
        '--skip_bids_validation', default=False,
        help='Assume the input dataset is BIDS compliant and skip the '
             'validation (default: False).',
        action="store_true"
    )
    
    # New revert mode arguments
    parser.add_argument(
        '--revert', action='store_true', default=False,
        help='Revert BIDSonym anonymization by restoring original files '
             'from sourcedata. This will replace all defaced/de-identified '
             'files with the original versions.'
    )
    parser.add_argument(
        '--revert_confirm_off', action='store_true', default=False,
        help='Skip confirmation prompt when using --revert mode. '
             'Use with caution as this will immediately restore original '
             'files.'
    )
    
    parser.add_argument(
        '-v', '--version', action='version',
        version='BIDS-App version {}'.format(__version__)
    )

    return parser


def process_subject_session(args, layout, subject_label, session=None,
                            log_print=print):
    """
    Process a single subject/session combination.
    
    Parameters
    ----------
    args : argparse.Namespace
        Command line arguments.
    layout : BIDSLayout
        BIDS layout object.
    subject_label : str
        Subject label to process.
    session : str, optional
        Session label to process.
    log_print : function, optional
        Logging function to use for output.
    """
    
    log_print(
        f"Processing subject {subject_label}"
        + (f", session {session}" if session else "")
    )
    
    # Get T1w images for this subject/session
    if session:
        list_t1w = layout.get(subject=subject_label, extension='nii.gz',
                              suffix='T1w', return_type='filename',
                              session=session)
    else:
        list_t1w = layout.get(subject=subject_label, extension='nii.gz',
                              suffix='T1w', return_type='filename')
    
    if not list_t1w:
        log_print(
            f"No T1w images found for subject {subject_label}"
            + (f", session {session}" if session else "")
        )
        return
    
    log_print(f"Found {len(list_t1w)} T1w images: {list_t1w}")
    
    # Process each T1w image
    for T1_file in list_t1w:
        # Create output directories
        check_outpath(args.bids_dir, subject_label)
        
        # Run brain extraction for quality control
        if args.brainextraction == 'bet':
            if args.bet_frac is None:
                raise Exception(
                    "If you want to use BET for pre-defacing brain "
                    "extraction, please provide a Frac value. For example: "
                    "--bet_frac 0.5"
                )
            run_brain_extraction_bet(T1_file, args.bet_frac[0], subject_label,
                                     args.bids_dir)
        elif args.brainextraction == 'nobrainer':
            run_brain_extraction_nb(T1_file, subject_label, args.bids_dir)
        
        # Check metadata for potentially identifying information
        check_meta_data(args.bids_dir, subject_label, args.check_meta)
        
        # Copy original files to sourcedata before defacing
        source_t1w = copy_no_deid(args.bids_dir, subject_label, T1_file,
                                  session=session)
        
        # Delete specified metadata fields if requested
        if args.del_meta:
            del_meta_data(args.bids_dir, subject_label, args.del_meta)
        
        # Run the specified defacing algorithm
        if args.deid == "pydeface":
            run_pydeface(source_t1w, T1_file)
        elif args.deid == "mri_deface":
            run_mri_deface(source_t1w, T1_file)
        elif args.deid == "quickshear":
            run_quickshear(source_t1w, T1_file)
        elif args.deid == "mridefacer":
            run_mridefacer(source_t1w, T1_file)
        elif args.deid == "deepdefacer":
            run_deepdefacer(source_t1w, subject_label, args.bids_dir)
    
    # Process T2w images if requested
    if args.deface_t2w:
        process_additional_modality(args, layout, subject_label, 'T2w',
                                    session, log_print)
    
    # Process FLAIR images if requested
    if args.deface_flair:
        process_additional_modality(args, layout, subject_label, 'FLAIR',
                                    session, log_print)


def process_additional_modality(args, layout, subject_label, modality,
                                session=None, log_print=print):
    """
    Process additional image modalities (T2w, FLAIR) using T1w defacing mask.
    
    Parameters
    ----------
    args : argparse.Namespace
        Command line arguments.
    layout : BIDSLayout
        BIDS layout object.
    subject_label : str
        Subject label to process.
    modality : str
        Image modality to process ('T2w' or 'FLAIR').
    session : str, optional
        Session label to process.
    log_print : function, optional
        Logging function to use for output.
    """
    
    log_print(
        f"Processing {modality} images for subject {subject_label}"
        + (f", session {session}" if session else "")
    )
    
    # Get images of this modality
    if session:
        modality_files = layout.get(subject=subject_label, extension='nii.gz',
                                    suffix=modality, return_type='filename',
                                    session=session)
    else:
        modality_files = layout.get(subject=subject_label, extension='nii.gz',
                                    suffix=modality, return_type='filename')
    
    if not modality_files:
        log_print(
            f"Warning: You requested {modality} defacing but no {modality} "
            f"images found for subject {subject_label}"
            + (f", session {session}" if session else "")
        )
        return
    
    log_print(
        f"Found {len(modality_files)} {modality} images: {modality_files}"
    )
    
    # Process each image of this modality
    for modality_file in modality_files:
        try:
            # Run brain extraction for quality control
            if args.brainextraction == 'bet':
                run_brain_extraction_bet(modality_file, args.bet_frac[0],
                                         subject_label, args.bids_dir)
            elif args.brainextraction == 'nobrainer':
                run_brain_extraction_nb(modality_file, subject_label,
                                        args.bids_dir)
            
            # Copy original file to sourcedata
            source_modality = copy_no_deid(args.bids_dir, subject_label,
                                           modality_file, session=session)
            
            # Find corresponding T1w file to use as defacing reference
            if session:
                t1w_files = layout.get(subject=subject_label,
                                       extension='nii.gz',
                                       suffix='T1w', return_type='filename',
                                       session=session)
            else:
                # Extract session from filename if present
                if 'ses-' in modality_file:
                    extracted_session = (modality_file[
                        modality_file.find('ses-') + 4:
                    ].split('_')[0])
                    t1w_files = layout.get(subject=subject_label,
                                           extension='nii.gz',
                                           suffix='T1w',
                                           return_type='filename',
                                           session=extracted_session)
                else:
                    t1w_files = layout.get(subject=subject_label,
                                           extension='nii.gz',
                                           suffix='T1w',
                                           return_type='filename')
            
            if not t1w_files:
                log_print(
                    f"Warning: No corresponding T1w file found for "
                    f"{modality} image {modality_file}"
                )
                continue
                
            T1_file = t1w_files[0]  # Use first T1w file as reference
            
            # Apply defacing using T1w mask
            run_image_deface(source_modality, T1_file, modality_file)
            
        except Exception as e:
            log_print(
                f"Error processing {modality} file {modality_file}: {e}"
            )
            continue


def run_revert_mode(args, layout):
    """
    Run BIDSonym revert mode to restore original files.
    
    Parameters
    ----------
    args : argparse.Namespace
        Command line arguments.
    layout : BIDSLayout
        BIDS layout object.
    """
    
    print("=" * 60)
    print("BIDSONYM REVERT MODE")
    print("=" * 60)
    print("This will restore original (non-defaced) images and metadata")
    print("by replacing current defaced/de-identified files with backups")
    print("from sourcedata/bidsonym/")
    print("=" * 60)
    
    # Determine subjects to revert
    if args.participant_label:
        subjects_to_revert = args.participant_label
    else:
        # Find all subjects that have BIDSonym sourcedata
        sourcedata_path = os.path.join(args.bids_dir, "sourcedata",
                                       "bidsonym")
        if os.path.exists(sourcedata_path):
            subjects_to_revert = [
                d.replace("sub-", "") for d in os.listdir(sourcedata_path)
                if (os.path.isdir(os.path.join(sourcedata_path, d))
                    and d.startswith("sub-"))
            ]
        else:
            print("No BIDSonym sourcedata found. No subjects to revert.")
            return
    
    if not subjects_to_revert:
        print("No subjects specified and no BIDSonym sourcedata found.")
        return
    
    print(f"Subjects to revert: {subjects_to_revert}")
    
    # Validate that specified participants have BIDSonym data
    sourcedata_path = os.path.join(args.bids_dir, "sourcedata", "bidsonym")
    subjects_with_data = []
    subjects_without_data = []
    
    for subject_label in subjects_to_revert:
        subject_sourcedata = os.path.join(sourcedata_path,
                                          f"sub-{subject_label}")
        if os.path.exists(subject_sourcedata):
            subjects_with_data.append(subject_label)
        else:
            subjects_without_data.append(subject_label)
    
    if subjects_without_data:
        print(
            f"Warning: No BIDSonym data found for subjects: "
            f"{subjects_without_data}"
        )
    
    if not subjects_with_data:
        print("No subjects with BIDSonym data to revert.")
        return
    
    print(
        f"Found BIDSonym data for {len(subjects_with_data)} subjects: "
        f"{subjects_with_data}"
    )
    
    # Set confirmation flag based on argument
    confirm = not args.revert_confirm_off
    
    # Process each subject
    failed_subjects = []
    successful_subjects = []
    
    for subject_label in subjects_with_data:
        print(f"\n{'-' * 40}")
        print(f"Reverting subject: {subject_label}")
        print(f"{'-' * 40}")
        
        # Handle session-specific reversion if sessions are specified
        if args.session:
            if "all" in args.session:
                # Revert all sessions
                available_sessions = layout.get(subject=subject_label,
                                                return_type='id',
                                                target='session')
                if available_sessions:
                    for session in available_sessions:
                        try:
                            success = revert_bidsonym(
                                args.bids_dir, subject_label,
                                session=session, confirm=confirm
                            )
                            if not success:
                                failed_subjects.append(
                                    f"{subject_label}_ses-{session}"
                                )
                            else:
                                successful_subjects.append(
                                    f"{subject_label}_ses-{session}"
                                )
                        except Exception as e:
                            print(
                                f"Error reverting subject {subject_label}, "
                                f"session {session}: {e}"
                            )
                            failed_subjects.append(
                                f"{subject_label}_ses-{session}"
                            )
                else:
                    # No sessions, revert entire subject
                    try:
                        success = revert_bidsonym(
                            args.bids_dir, subject_label, session=None,
                            confirm=confirm
                        )
                        if not success:
                            failed_subjects.append(subject_label)
                        else:
                            successful_subjects.append(subject_label)
                    except Exception as e:
                        print(f"Error reverting subject {subject_label}: {e}")
                        failed_subjects.append(subject_label)
            else:
                # Revert specific sessions
                for session in args.session:
                    try:
                        success = revert_bidsonym(
                            args.bids_dir, subject_label, session=session,
                            confirm=confirm
                        )
                        if not success:
                            failed_subjects.append(
                                f"{subject_label}_ses-{session}"
                            )
                        else:
                            successful_subjects.append(
                                f"{subject_label}_ses-{session}"
                            )
                    except Exception as e:
                        print(
                            f"Error reverting subject {subject_label}, "
                            f"session {session}: {e}"
                        )
                        failed_subjects.append(
                            f"{subject_label}_ses-{session}"
                        )
        else:
            # Revert entire subject (all sessions)
            try:
                success = revert_bidsonym(
                    args.bids_dir, subject_label, session=None,
                    confirm=confirm
                )
                if not success:
                    failed_subjects.append(subject_label)
                else:
                    successful_subjects.append(subject_label)
            except Exception as e:
                print(f"Error reverting subject {subject_label}: {e}")
                failed_subjects.append(subject_label)
    
    # Print final summary
    print(f"\n{'=' * 60}")
    print("REVERSION SUMMARY")
    print(f"{'=' * 60}")
    print(f"Successfully reverted: {len(successful_subjects)} "
          f"subjects/sessions")
    if successful_subjects:
        for subj in successful_subjects:
            print(f"  Success: {subj}")
    
    if failed_subjects:
        print(f"\nFailed to revert: {len(failed_subjects)} "
              f"subjects/sessions")
        for subj in failed_subjects:
            print(f"  Failed: {subj}")
    
    print(f"{'=' * 60}")


def run_deeid():
    """
    Main entry point for BIDSonym de-identification workflow.
    """
    
    args = get_parser().parse_args()
    
    # Initialize logging for normal processing (not for revert mode)
    log_print = print  # Default to regular print
    log_path = None
    
    if not args.revert:
        # Set up logging for normal BIDSonym processing
        # Use the first participant as the primary subject for logging
        primary_subject = (args.participant_label[0]
                           if args.participant_label else "all")
        log_print, log_path = setup_logging(
            args.bids_dir, primary_subject, session=None,
            operation="bidsonym"
        )
        
        log_print("BIDSonym De-identification Workflow")
        log_print("=" * 60)
        log_print(f"Command line arguments: {' '.join(sys.argv)}")
        log_print("=" * 60)
    
    # Determine execution environment
    if os.getenv('IS_DOCKER'):
        exec_env = 'singularity'
        cgroup = Path('/proc/1/cgroup')
        if cgroup.exists() and 'docker' in cgroup.read_text():
            exec_env = 'docker'
    else:
        exec_env = 'local'

    # Validate BIDS dataset if requested (always done for both modes)
    if args.skip_bids_validation:
        log_print("Input data will not be checked for BIDS compliance.")
    else:
        log_print(
            "Making sure the input data is BIDS compliant "
            "(warnings can be ignored in most cases)."
        )
        validate_input_dir(exec_env, args.bids_dir, args.participant_label)

    # Initialize BIDS layout
    layout = BIDSLayout(args.bids_dir)

    # Check if we're in revert mode
    if args.revert:
        print("Running in REVERT mode - will restore original files")
        run_revert_mode(args, layout)
        return  # Exit after reversion, don't run normal processing

    # Validate required arguments for normal processing mode
    if args.brainextraction is None:
        raise Exception(
            "For post defacing quality control it is required to run a form "
            "of brain extraction on the non-de-identified data. Please "
            "specify either --brainextraction bet or --brainextraction "
            "nobrainer."
        )

    # Determine subjects to analyze
    if args.analysis_level == "participant":
        if args.participant_label:
            subjects_to_analyze = args.participant_label
        else:
            raise Exception(
                "No participant label indicated for participant-level "
                "analysis. Please specify --participant_label."
            )
    else:
        subjects_to_analyze = layout.get(return_type='id', target='subject')

    # Validate that specified participants exist
    available_subjects = layout.get_subjects()
    invalid_subjects = [subj for subj in subjects_to_analyze
                        if subj not in available_subjects]
    if invalid_subjects:
        raise Exception(
            f"The following participant(s) are not present in the BIDS "
            f"dataset: {invalid_subjects}"
        )

    log_print(
        f"Processing {len(subjects_to_analyze)} subjects: "
        f"{subjects_to_analyze}"
    )

    # Process each subject
    for subject_label in subjects_to_analyze:
        log_print(f"\n{'=' * 60}")
        log_print(f"Processing subject: {subject_label}")
        log_print(f"{'=' * 60}")
        
        # Get available sessions for this subject
        available_sessions = layout.get(subject=subject_label,
                                        return_type='id',
                                        target='session')
        log_print(
            f"Available sessions for subject {subject_label}: "
            f"{available_sessions}"
        )
        
        # Determine which sessions to process
        if args.session:
            if "all" in args.session:
                sessions_to_process = available_sessions
            else:
                # Validate requested sessions exist
                invalid_sessions = [ses for ses in args.session
                                    if ses not in available_sessions]
                if invalid_sessions:
                    log_print(
                        f"Warning: The following sessions are not available "
                        f"for subject {subject_label}: {invalid_sessions}"
                    )
                sessions_to_process = [ses for ses in args.session
                                       if ses in available_sessions]
        else:
            sessions_to_process = available_sessions
        
        log_print(f"Processing sessions: {sessions_to_process}")
        
        # Process each session (or no-session data)
        if sessions_to_process:
            # Multi-session processing
            for session in sessions_to_process:
                process_subject_session(args, layout, subject_label,
                                        session, log_print)
        else:
            # Single-session or no-session processing
            process_subject_session(args, layout, subject_label,
                                    session=None, log_print=log_print)
        
        # Rename non-deidentified files with descriptive labels
        rename_non_deid(args.bids_dir, subject_label)
        
        # Generate quality control visualizations
        log_print(
            f"\nGenerating quality control visualizations for "
            f"subject {subject_label}"
        )
        
        # Determine which modalities to include in visualizations based
        # on processing flags. Always include T1w since it's always processed
        visualization_modalities = ['T1w']
        
        # Add T2w if it was processed
        if args.deface_t2w:
            visualization_modalities.append('T2w')
            
        # Add FLAIR if it was processed
        if args.deface_flair:
            visualization_modalities.append('FLAIR')
        
        log_print(
            f"Creating visualizations for modalities: "
            f"{visualization_modalities}"
        )
        
        # Generate visualizations for each session
        if sessions_to_process:
            for session in sessions_to_process:
                log_print(f"Creating visualizations for session {session}")
                create_graphics(
                    args.bids_dir, subject_label, session=session,
                    modalities=visualization_modalities
                )
                clean_up_files(args.bids_dir, subject_label, session=session)
        else:
            log_print("Creating visualizations for single-session data")
            create_graphics(args.bids_dir, subject_label, session=None,
                            modalities=visualization_modalities)
            clean_up_files(args.bids_dir, subject_label, session=None)
        
        log_print(f"Completed processing for subject {subject_label}")

    log_print(f"\n{'=' * 60}")
    log_print("BIDSonym de-identification workflow completed successfully!")
    if log_path:
        log_print(f"Complete log saved to: {log_path}")
    log_print(f"{'=' * 60}")


if __name__ == "__main__":
    run_deeid()