import argparse
import os
from pathlib import Path
from bidsonym.defacing_algorithms import (run_pydeface, run_mri_deface, run_mridefacer,
                                          run_quickshear, run_deepdefacer, run_t2w_deface)
from bidsonym.utils import (check_outpath, copy_no_deid, check_meta_data, del_meta_data,
                            run_brain_extraction_nb, run_brain_extraction_bet, validate_input_dir,
                            rename_non_deid, clean_up_files)
from bidsonym.reports import create_graphics
from bids import BIDSLayout


def get_parser():

    __version__ = open(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                    '_version.py')).read()

    parser = argparse.ArgumentParser(description='a BIDS app for de-identification of neuroimaging data')
    parser.add_argument('bids_dir', action='store', type=Path, help='The directory with the input dataset '
                        'formatted according to the BIDS standard.')
    parser.add_argument('analysis_level', help='Level of the analysis that will be performed. '
                        'Multiple participant level analyses can be run independently '
                        '(in parallel) using the same output_dir.',
                        choices=['participant', 'group'])
    parser.add_argument('--participant_label',
                        help='The label(s) of the participant(s) that should be analyzed. '
                        'The label corresponds to sub-<participant_label> from the BIDS spec '
                        '(so it does not include "sub-"). If this parameter is not '
                        'provided all subjects should be analyzed. Multiple '
                        'participants can be specified with a space separated list.',
                        nargs="+")
    parser.add_argument('--deid', help='Approach to use for de-identifictation.',
                        choices=['pydeface', 'mri_deface', 'quickshear', 'mridefacer',
                                 'deepdefacer'])
    parser.add_argument('--deface_t2w',  action="store_true", default=False,
                        help='Deface T2w images by using defaced T1w image as deface-mask.')
    parser.add_argument('--check_meta',
                        help='Indicate which information from the image and \
                        .json meta-data files should be check for potentially problematic information. \
                        Indicate strings that should be searched for. \
                        The results will be saved to sourcedata/',
                        nargs="+")
    parser.add_argument('--del_meta',
                        help='Indicate if and which information from the .json meta-data files should be deleted. \
                        If so, the original .json files will be copied to sourcedata/',
                        nargs="+")
    parser.add_argument('--brainextraction',
                        help='What algorithm should be used for pre-defacing brain extraction \
                        (outputs will be used in quality control).',
                        choices=['bet', 'nobrainer'])
    parser.add_argument('--bet_frac',
                        help='In case BET is used for pre-defacing brain extraction, provide a Frac value.',
                        nargs=1)
    parser.add_argument('--skip_bids_validation', default=False,
                        help='Assume the input dataset is BIDS compliant and skip the validation \
                             (default: False).',
                        action="store_true")
    parser.add_argument('-v', '--version', action='version',
                        version='BIDS-App version {}'.format(__version__))

    return parser


def run_deeid():

    args = get_parser().parse_args()
    subjects_to_analyze = []

    # special variable set in the container
    if os.getenv('IS_DOCKER'):
        exec_env = 'singularity'
        cgroup = Path('/proc/1/cgroup')
        if cgroup.exists() and 'docker' in cgroup.read_text():
            exec_env = 'docker'

    if args.brainextraction is None:
        raise Exception("For post defacing quality it is required to run a form of brainextraction"
                        "on the non-deindentified data. Thus please either indicate bet"
                        "(--brainextration bet) or nobrainer (--brainextraction nobrainer).")

    if args.skip_bids_validation:
        print("Input data will not be checked for BIDS compliance.")
    else:
        print("Making sure the input data is BIDS compliant "
              "(warnings can be ignored in most cases).")
        validate_input_dir(exec_env, args.bids_dir, args.participant_label)

    layout = BIDSLayout(args.bids_dir)

    if args.analysis_level == "participant":
        if args.participant_label:
            subjects_to_analyze = args.participant_label
        else:
            print("No participant label indicated. Please do so.")
    else:
        subjects_to_analyze = layout.get(return_type='id', target='subject')

    list_part_prob = []
    for part in subjects_to_analyze:
        if part not in layout.get_subjects():
            list_part_prob.append(part)
    if len(list_part_prob) >= 1:
        raise Exception("The participant(s) you indicated are present in the BIDS dataset, please check again."
                        "This refers to:")
        print(list_part_prob)

    sessions_to_analyze = layout.get(return_type='id', target='session')

    if not sessions_to_analyze:
        print('Processing data from one session.')
    else:
        print('Processing data from %s sessions:' % str(len(sessions_to_analyze)))
        print(sessions_to_analyze)

    list_check_meta = args.check_meta

    list_field_del = args.del_meta

    for subject_label in subjects_to_analyze:
        if not sessions_to_analyze:
            list_t1w = layout.get(subject=subject_label, extension='nii.gz', suffix='T1w',
                                  return_type='filename')
        else:
            list_t1w = layout.get(subject=subject_label, extension='nii.gz', suffix='T1w',
                                  return_type='filename', session=sessions_to_analyze)
        for T1_file in list_t1w:
            check_outpath(args.bids_dir, subject_label)
            if args.brainextraction == 'bet':
                if args.bet_frac is None:
                    raise Exception("If you want to use BET for pre-defacing brain extraction,"
                                    "please provide a Frac value. For example: --bet_frac 0.5")
                else:
                    run_brain_extraction_bet(T1_file, args.bet_frac[0], subject_label, args.bids_dir)
            elif args.brainextraction == 'nobrainer':
                run_brain_extraction_nb(T1_file, subject_label, args.bids_dir)

            check_meta_data(args.bids_dir, subject_label, list_check_meta)
            source_t1w = copy_no_deid(subject_label, args.bids_dir, T1_file)

            if args.del_meta:
                del_meta_data(args.bids_dir, subject_label, list_field_del)
            if args.deid == "pydeface":
                run_pydeface(source_t1w, T1_file)
            elif args.deid == "mri_deface":
                run_mri_deface(source_t1w, T1_file)
            elif args.deid == "quickshear":
                run_quickshear(source_t1w, T1_file)
            elif args.deid == "mridefacer":
                run_mridefacer(source_t1w, subject_label, args.bids_dir)
            elif args.deid == "deepdefacer":
                run_deepdefacer(source_t1w, subject_label, args.bids_dir)

        if args.deface_t2w:
            if not sessions_to_analyze:
                list_t2w = layout.get(subject=subject_label, extension='nii.gz', suffix='T2w',
                                      return_type='filename')
            else:
                list_t2w = layout.get(subject=subject_label, extension='nii.gz', suffix='T2w',
                                      return_type='filename', session=sessions_to_analyze)
            if list_t2w == []:
                raise Exception("You indicated that a T2w image should be defaced as well."
                                "However, no T2w image exists for subject %s."
                                "Please check again." % subject_label)

            for T2_file in list_t2w:
                if args.brainextraction == 'bet':
                    run_brain_extraction_bet(T2_file, args.bet_frac[0], subject_label, args.bids_dir)
                elif args.brainextraction == 'nobrainer':
                    run_brain_extraction_nb(T2_file, subject_label, args.bids_dir)

                source_t2w = copy_no_deid(subject_label, args.bids_dir, T2_file)
                run_t2w_deface(source_t2w, T1_file, T2_file)

        rename_non_deid(args.bids_dir, subject_label)

        if sessions_to_analyze is None and args.deface_t2w is None:
            create_graphics(args.bids_dir, subject_label, session=None, t2w=None)
        elif sessions_to_analyze and args.deface_t2w is None:
            for session in sessions_to_analyze:
                create_graphics(args.bids_dir, subject_label, session=session, t2w=None)
        elif sessions_to_analyze is None and args.deface_t2w:
            create_graphics(args.bids_dir, subject_label, session=None, t2w=True)
        elif sessions_to_analyze and args.deface_t2w:
            for session in sessions_to_analyze:
                create_graphics(args.bids_dir, subject_label, session=session, t2w=True)

        if not sessions_to_analyze:
            clean_up_files(args.bids_dir, subject_label)
        else:
            for session in sessions_to_analyze:
                clean_up_files(args.bids_dir, subject_label, session=session)


if __name__ == "__main__":

    run_deeid()
