import argparse
import os
from pathlib import Path
from glob import glob
from .defacing_algorithms import (run_pydeface, run_mri_deface, run_mridefacer,
                                  run_quickshear, run_deepdefacer)
from .utils import (check_outpath, copy_no_deid, check_meta_data, del_meta_data,
                    run_brain_extraction_nb, run_brain_extraction_bet, validate_input_dir)


def run_deeid():

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
    parser.add_argument('--del_nodeface',
                        help='Overwrite and delete original data or copy original data to sourcedata/.',
                        choices=['del', 'no_del'])
    parser.add_argument('--check_meta',
                        help='Indicate if and which information from the image and \
                        .json meta-data files should be check for potentially problematic information. \
                        If so, indicate strings that should be searched for. \
                        The results will be saved to sourcedata/',
                        nargs="+")
    parser.add_argument('--del_meta',
                        help='Indicate if and which information from the .json meta-data files should be deleted. \
                        If so, the original .josn files will be copied to sourcedata/',
                        nargs="+")
    parser.add_argument('--brainextraction',
                        help='What algorithm should be used for pre-defacing brain extraction \
                        (outputs will be used in quality control).',
                        choices=['bet', 'nobrainer'])
    parser.add_argument('--bet_frac',
                        help='In case BET is used for pre-defacing brain extraction, povide a Frac value.',
                        nargs=1)
    parser.add_argument('-v', '--version', action='version',
                        version='BIDS-App example version {}'.format(__version__))

    args = parser.parse_args()
    subjects_to_analyze = []

    # special variable set in the container
    if os.getenv('IS_DOCKER'):
        exec_env = 'singularity'
        cgroup = Path('/proc/1/cgroup')
        if cgroup.exists() and 'docker' in cgroup.read_text():
            exec_env = 'docker'

    print("Making sure the input data is BIDS compliant "
          "(warnings can be ignored in most cases).")
    validate_input_dir(exec_env, args.bids_dir, args.participant_label)

    if args.analysis_level == "participant":
        if args.participant_label:
            subjects_to_analyze = args.participant_label
        else:
            print("No participant label indicated. Please do so.")
    else:
        subject_dirs = glob(os.path.join(args.bids_dir, "sub-*"))
        subjects_to_analyze = [subject_dir.split("-")[-1] for subject_dir in subject_dirs]

    list_check_meta = args.check_meta

    list_field_del = args.del_meta

    for subject_label in subjects_to_analyze:
        for T1_file in glob(os.path.join(args.bids_dir, "sub-%s" % subject_label,
                                         "anat", "*_T1w.nii*")) + \
                                         glob(os.path.join(args.bids_dir, "sub-%s" % subject_label,
                                                           "ses-*", "anat", "*_T1w.nii*")):
            check_outpath(args.bids_dir, subject_label)
            if args.brainextraction == 'bet':
                if args.bet_frac is None:
                    raise Exception('If you want to use BET for pre-defacing brain extraction, \
                    please provide a Frac value. For example: --bet_frac 0.5')
                else:
                    run_brain_extraction_bet(T1_file, args.bet_frac[0], subject_label, args.bids_dir)
            elif args.brainextraction == 'nobrainer':
                run_brain_extraction_nb(T1_file, subject_label, args.bids_dir)
            if args.deid == "pydeface":
                if args.del_nodeface == "del":
                    run_pydeface(T1_file, T1_file)
                    if args.check_meta:
                        check_meta_data(args.bids_dir, subject_label, list_check_meta)
                    if args.del_meta:
                        del_meta_data(args.bids_dir, subject_label, list_field_del)
                else:
                    copy_no_deid(subject_label, args.bids_dir, T1_file)
                    run_pydeface(T1_file, T1_file)
                    if args.check_meta:
                        check_meta_data(args.bids_dir, subject_label, list_check_meta)
                    if args.del_meta:
                        del_meta_data(args.bids_dir, subject_label, list_field_del)
            if args.deid == "mri_deface":
                if args.del_nodeface == "del":
                    run_mri_deface(T1_file, T1_file)
                if args.check_meta:
                    check_meta_data(args.bids_dir, subject_label, list_check_meta)
                if args.del_meta:
                    del_meta_data(args.bids_dir, subject_label, list_field_del)
                else:
                    copy_no_deid(subject_label, args.bids_dir, T1_file)
                    run_mri_deface(T1_file, T1_file)
                    if args.check_meta:
                        check_meta_data(args.bids_dir, subject_label, list_check_meta)
                    if args.del_meta:
                        del_meta_data(args.bids_dir, subject_label, list_field_del)
            if args.deid == "quickshear":
                if args.del_nodeface == "del":
                    run_quickshear(T1_file, T1_file)
                if args.check_meta:
                    check_meta_data(args.bids_dir, subject_label, list_check_meta)
                if args.del_meta:
                    del_meta_data(args.bids_dir, subject_label, list_field_del)
                else:
                    copy_no_deid(subject_label, args.bids_dir, T1_file)
                    run_quickshear(T1_file, T1_file)
                    if args.check_meta:
                        check_meta_data(args.bids_dir, subject_label, list_check_meta)
                    if args.del_meta:
                        del_meta_data(args.bids_dir, subject_label, list_field_del)
            if args.deid == "mridefacer":
                if args.del_nodeface == "del":
                    run_mridefacer(T1_file, subject_label, args.bids_dir)
                if args.check_meta:
                    check_meta_data(args.bids_dir, subject_label, list_check_meta)
                if args.del_meta:
                    del_meta_data(args.bids_dir, subject_label, list_field_del)
                else:
                    copy_no_deid(subject_label, args.bids_dir, T1_file)
                    run_mridefacer(T1_file, subject_label, args.bids_dir)
                    if args.check_meta:
                        check_meta_data(args.bids_dir, subject_label, list_check_meta)
                    if args.del_meta:
                        del_meta_data(args.bids_dir, subject_label, list_field_del)
            if args.deid == "deepdefacer":
                if args.del_nodeface == "del":
                    run_deepdefacer(T1_file, subject_label, args.bids_dir)
                if args.check_meta:
                    check_meta_data(args.bids_dir, subject_label, list_check_meta)
                if args.del_meta:
                    del_meta_data(args.bids_dir, subject_label, list_field_del)
                else:
                    copy_no_deid(subject_label, args.bids_dir, T1_file)
                    run_deepdefacer(T1_file, subject_label, args.bids_dir)
                    if args.check_meta:
                        check_meta_data(args.bids_dir, subject_label, list_check_meta)
                    if args.del_meta:
                        del_meta_data(args.bids_dir, subject_label, list_field_del)


if __name__ == "__main__":

    run_deeid()
