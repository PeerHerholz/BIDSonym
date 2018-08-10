#!/usr/bin/env python3
import argparse
import os
from subprocess import check_call
import nibabel
import numpy
from glob import glob
import nipype.pipeline.engine as pe
from nipype.interfaces import utility as niu
from nipype.interfaces.quickshear import Quickshear
from nipype.interfaces.fsl import BET
from shutil import copy

__version__ = open(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                'version')).read()

def run_pydeface(image, outfile):
    #pydeface $image --outfile $outfile
    cmd = ["pydeface", image,
           "--out", outfile,
           "--force",
           ]
    check_call(cmd)
    return

def run_mri_deface(image, brain_template, face_template, outfile):
    #mri_deface $image $brain_template $face_template $outfile
    cmd = ["mri_deface", image,
                         brain_template,
                         face_template,
                         outfile,
           ]
    check_call(cmd)
    return

def run_quickshear(image, outfile):
    #quickshear anat_file mask_file defaced_file [buffer]
    deface_wf = pe.Workflow('deface_wf')
    inputnode = pe.Node(niu.IdentityInterface(['in_file']),
                     name='inputnode')
    outputnode = pe.Node(niu.IdentityInterface(['out_file']),
                      name='outputnode')
    bet = pe.Node(BET(mask=True, frac=0.5), name='bet')
    quickshear = pe.Node(Quickshear(buff=50), name='quickshear')
    deface_wf.connect([
        (inputnode, bet, [('in_file', 'in_file')]),
        (inputnode, quickshear, [('in_file', 'in_file')]),
        (bet, quickshear, [('mask_file', 'mask_file')]),
        ])
    inputnode.inputs.in_file = image
    quickshear.inputs.out_file = outfile
    res = deface_wf.run()

def copy_no_deid(subject_label):
    path = os.path.join(args.bids_dir, "derivatives/bidsonym/sub-%s"%subject_label)
    outfile = "sub-%s_T1w_no_deid.nii.gz"%subject_label
    if os.path.isdir(path) == True:
        copy(T1_file, os.path.join(path, outfile))
    else:
        os.makedirs(path)
        copy(T1_file, os.path.join(path, outfile))


parser = argparse.ArgumentParser(description='a BIDS app for de-identification of neuroimaging data')
parser.add_argument('bids_dir', help='The directory with the input dataset '
                    'formatted according to the BIDS standard.')
parser.add_argument('analysis_level', help='Level of the analysis that will be performed. '
                    'Multiple participant level analyses can be run independently '
                    '(in parallel) using the same output_dir.',
                    choices=['participant', 'group'])
parser.add_argument('--participant_label', help='The label(s) of the participant(s) that should be analyzed. The label '
                   'corresponds to sub-<participant_label> from the BIDS spec '
                   '(so it does not include "sub-"). If this parameter is not '
                   'provided all subjects should be analyzed. Multiple '
                   'participants can be specified with a space separated list.',
                   nargs="+")
parser.add_argument('--deid', help='Approach to use for de-identifictation.',
                    choices=['pydeface', 'mri_deface', 'quickshear'])
parser.add_argument('--del_nodeface', help='Overwrite and delete original data or copy original data to different folder.',
                    choices=['del', 'no_del'])
parser.add_argument('-v', '--version', action='version',
                    version='BIDS-App example version {}'.format(__version__))


args = parser.parse_args()

#if not args.skip_bids_validator:
#    run('bids-validator %s'%args.bids_dir)

subjects_to_analyze = []
# only for a subset of subjects
if args.participant_label:
    subjects_to_analyze = args.participant_label
# for all subjects
else:
    subject_dirs = glob(os.path.join(args.bids_dir, "sub-*"))
    subjects_to_analyze = [subject_dir.split("-")[-1] for subject_dir in subject_dirs]

# running participant level
if args.analysis_level == "participant":

    # find all T1s and de-identify them
    for subject_label in subjects_to_analyze:
        for T1_file in glob(os.path.join(args.bids_dir, "sub-%s"%subject_label,
                                         "anat", "*_T1w.nii*")) + glob(os.path.join(args.bids_dir,"sub-%s"%subject_label,"ses-*","anat", "*_T1w.nii*")):
            if args.deid == "pydeface":
                if args.del_nodeface == "no_del":
                    copy_no_deid(subject_label)
                    run_pydeface(T1_file, T1_file)
                else:
                    run_pydeface(T1_file, T1_file)
            if args.deid == "mri_deface":
                if args.del_nodeface == "no_del":
                    copy_no_deid(subject_label)
                    run_mri_deface(T1_file, '/home/fs_data/talairach_mixed_with_skull.gca', '/home/fs_data/face.gca', T1_file)
                else:
                    run_mri_deface(T1_file, '/home/fs_data/talairach_mixed_with_skull.gca', '/home/fs_data/face.gca', T1_file)
            if args.deid == "quickshear":
                if args.del_nodeface == "no_del":
                    copy_no_deid(subject_label)
                    run_quickshear(T1_file, T1_file)
                else:
                    copy_no_deid(subject_label)

else:

    # find all T1s and de-identify them
    for subject_label in subjects_to_analyze:
        for T1_file in glob(os.path.join(args.bids_dir, "sub-%s"%subject_label,
                                         "anat", "*_T1w.nii*")) + glob(os.path.join(args.bids_dir,"sub-%s"%subject_label,"ses-*","anat", "*_T1w.nii*")):
            if args.deid == "pydeface":
                if args.del_nodeface == "no_del":
                    copy_no_deid(subject_label)
                    run_pydeface(T1_file, T1_file)
                else:
                    run_pydeface(T1_file, T1_file)
            if args.deid == "mri_deface":
                if args.del_nodeface == "no_del":
                    copy_no_deid(subject_label)
                    run_mri_deface(T1_file, '/home/fs_data/talairach_mixed_with_skull.gca', '/home/fs_data/face.gca', T1_file)
                else:
                    run_mri_deface(T1_file, '/home/fs_data/talairach_mixed_with_skull.gca', '/home/fs_data/face.gca', T1_file)
            if args.deid == "quickshear":
                if args.del_nodeface == "no_del":
                    copy_no_deid(subject_label)
                    run_quickshear(T1_file, T1_file)
                else:
                    copy_no_deid(subject_label)
