import argparse
import os
from subprocess import check_call
import json

from glob import glob
import pandas as pd
import nibabel as nib
import nipype.pipeline.engine as pe
from nipype.interfaces import utility as niu
from nipype.interfaces.quickshear import Quickshear
from nipype.interfaces.fsl import BET
from shutil import copy, move

__version__ = open(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                '_version.py')).read()

# define function for pydeface
def run_pydeface(image, outfile):
    #pydeface $image --outfile $outfile
    cmd = ["pydeface", image,
           "--out", outfile,
           "--force",
           ]
    check_call(cmd)
    return

# define function for mri_deface
def run_mri_deface(image, brain_template, face_template, outfile):
    #mri_deface $image $brain_template $face_template $outfile
    cmd = ["mri_deface", image,
                         brain_template,
                         face_template,
                         outfile,
           ]
    check_call(cmd)
    return

# define function for quickshear
# based on the nipype docs quickshear example
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

# define function for mridefacer
def run_mridefacer(image, subject_label):
    cmd = ["mridefacer/mridefacer", "--apply",
                         image]
    check_call(cmd)
    path = os.path.join(args.bids_dir, "sourcedata/bidsonym/sub-%s"%subject_label)
    facemask = os.path.join(args.bids_dir, "sub-%s"%subject_label, "anat/sub-%s_T1w_defacemask.nii.gz"%subject_label)
    if os.path.isdir(path) == True:
        move(facemask, os.path.join(path))
    else:
        os.makedirs(path)
        move(facemask, os.path.join(path))
    return

# define function to copy non deidentified images to sourcedata/,
# overwriting images in the bids root folder
def copy_no_deid(subject_label):
    # images
    path = os.path.join(args.bids_dir, "sourcedata/bidsonym/sub-%s"%subject_label)
    outfile = T1_file[T1_file.rfind('/')+1:T1_file.rfind('.nii')]+'_no_deid.nii.gz'
    if os.path.isdir(path) == True:
        copy(T1_file, os.path.join(path, outfile))
    else:
        os.makedirs(path)
        copy(T1_file, os.path.join(path, outfile))
    # meta-data
    path_task_meta = os.path.join(args.bids_dir, "sourcedata/bidsonym/")
    path_sub_meta = os.path.join(args.bids_dir, "sourcedata/bidsonym/sub-%s" % subject_label)
    list_task_meta_files = glob(os.path.join(args.bids_dir, '*json'))
    list_sub_meta_files = glob(os.path.join(args.bids_dir, subject_label, '*', '*.json'))
    for task_meta_data_file in list_task_meta_files:
        task_out = task_meta_data_file[task_meta_data_file.rfind('/') + 1:task_meta_data_file.rfind('.json')] + '_no_deid.json'
        copy(task_meta_data_file, os.path.join(path_task_meta, task_out))
    for sub_meta_data_file in list_sub_meta_files:
        sub_out = sub_meta_data_file[sub_meta_data_file.rfind('/') + 1:sub_meta_data_file.rfind('.json')] + '_no_deid.json'
        copy(sub_meta_data_file, os.path.join(path_sub_meta, sub_out))


def check_meta_data(bids_path, subject_label, prob_fields):
    # gather all image files
    list_subject_image_files = glob(os.path.join(bids_path, 'sub-' + subject_label, '*', '*nii.gz'))
    # gather all meta data files
    list_task_meta_files = glob(os.path.join(bids_path, '*json'))
    list_sub_meta_files = glob(os.path.join(bids_path, 'sub-' + subject_label, '*', '*.json'))
    list_meta_files = list_task_meta_files + list_sub_meta_files
    # define potentially problematic fields
    prob_fields = prob_fields
    # check image files, output .csv dataframe with found header information and if it might be problematic
    for subject_image_file in list_subject_image_files:
        #load image header
        header = nib.load(subject_image_file).header
        #create df with header information
        keys = []
        dat = []
        for key, data in zip(header.keys(), header.values()):
            keys.append(key)
            dat.append(data)
        header_df = pd.DataFrame({'meta_data_field': keys, 'data': dat, 'problematic': 'no'})
        #loop over df, checking if information might be problematic
        for index, row in header_df.iterrows():
            if any(i.lower() in row['meta_data_field'] for i in prob_fields):
                row['problematic'] = 'maybe'
            else:
                row['problematic'] = 'no'
        #save image specific df to sourcedata
        header_df.to_csv(os.path.join(bids_path, 'sourcedata/bidsonym', 'sub-%s' % subject_label, subject_image_file[subject_image_file.rfind('/') + 1:subject_image_file.rfind('.nii.gz')] + '_header_info.csv'), index=False)

    # check meta data files, output .csv dataframe with found information and if it might be problematic
    for meta_file in list_meta_files:
        #open meta data files and create df that contains the respective information
        with open(meta_file, 'r') as json_file:
            meta_data = json.load(json_file)
            keys = []
            info = []
            for key, inf in zip(meta_data.keys(), meta_data.values()):
                keys.append(key)
                info.append(inf)
            json_df = pd.DataFrame({'meta_data_field': keys, 'information': info, 'problematic': 'no'})
            #loop over df, checking if information might be problematic
            for index, row in json_df.iterrows():
                if any(i in row['meta_data_field'] for i in prob_fields):
                    row['problematic'] = 'maybe'
                else:
                    row['problematic'] = 'no'
            #save json specifci df to sourcedata
            json_df.to_csv(os.path.join(bids_path, 'sourcedata/bidsonym', 'sub-%s' % subject_label, meta_file[meta_file.rfind('/') + 1:meta_file.rfind('.json')] + '_json_info.csv'), index=False)


# define function to remove certain fields from the meta-data files
# after copying the original ones to sourcedata/
def del_meta_data(bids_path, subject_label, fields_del):

    #get all .json files for tasks and subjects, combine both lists
    list_task_meta_files = glob(os.path.join(bids_path, '*json'))
    list_sub_meta_files = glob(os.path.join(bids_path, 'sub-'+subject_label, '*', '*.json'))
    list_meta_files = list_task_meta_files + list_sub_meta_files

    #declare fields that should be deleted from the .json files
    fields_del = fields_del

    #provide information on workflow
    print('working on %s'%subject_label)
    print('found the following meta-data files:')
    print(*list_meta_files, sep='\n')
    print('the following fields will be deleted:')
    print(*list_field_del, sep='\n')

    #loop over meta data files and delete indicated fields, copying original file to sourcedata
    for meta_file in list_meta_files:
        with open(meta_file, 'r') as json_file:
            meta_data = json.load(json_file)
            for field in fields_del:
                meta_data[field] = 'deleted_by_bidsonym'
        with open(meta_file, 'w') as json_output_file:
                    json.dump(meta_data, json_output_file, indent=4)



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
                    choices=['pydeface', 'mri_deface', 'quickshear', 'mridefacer'])
parser.add_argument('--del_nodeface', help='Overwrite and delete original data or copy original data to sourcedata/.',
                    choices=['del', 'no_del'])
parser.add_argument('--check_meta',
                    help='Indicate if and which information from the image and .json meta-data files should be check for potentially problematic information. If so, indicate strings that should be searched for. The results will be saved to sourcedata/',
                    nargs="+")
parser.add_argument('--del_meta',
                    help='Indicate if and which information from the .json meta-data files should be deleted. If so, the original .josn files will be copied to sourcedata/',
                    nargs="+")
parser.add_argument('-v', '--version', action='version',
                    version='BIDS-App example version {}'.format(__version__))


args = parser.parse_args()

subjects_to_analyze = []

# only for a subset of subjects
if args.participant_label:
    subjects_to_analyze = args.participant_label
# for all subjects
else:
    subject_dirs = glob(os.path.join(args.bids_dir, "sub-*"))
    subjects_to_analyze = [subject_dir.split("-")[-1] for subject_dir in subject_dirs]

list_check_meta = args.check_meta

list_field_del = args.del_meta

# running participant level
if args.analysis_level == "participant":

    # find all T1s and de-identify them
    for subject_label in subjects_to_analyze:
         for T1_file in glob(os.path.join(args.bids_dir, "sub-%s"%subject_label,
                                         "anat", "*_T1w.nii*")) + glob(os.path.join(args.bids_dir,"sub-%s"%subject_label,"ses-*","anat", "*_T1w.nii*")):
            if args.deid == "pydeface":
                if args.del_nodeface == "del":
                    run_pydeface(T1_file, T1_file)
                    if args.check_meta:
                        check_meta_data(args.bids_dir, subject_label, list_check_meta)
                    if args.del_meta:
                        del_meta_data(args.bids_dir, subject_label, list_field_del)
                else:
                    copy_no_deid(subject_label)
                    run_pydeface(T1_file, T1_file)
                    if args.check_meta:
                        check_meta_data(args.bids_dir, subject_label, list_check_meta)
                    if args.del_meta:
                        del_meta_data(args.bids_dir, subject_label, list_field_del)
            if args.deid == "mri_deface":
                if args.del_nodeface == "del":
                    run_mri_deface(T1_file, '/home/fs_data/talairach_mixed_with_skull.gca', '/home/fs_data/face.gca', T1_file)
                    if args.check_meta:
                        check_meta_data(args.bids_dir, subject_label, list_check_meta)
                    if args.del_meta:
                        del_meta_data(args.bids_dir, subject_label, list_field_del)
                else:
                    copy_no_deid(subject_label)
                    run_mri_deface(T1_file, '/home/fs_data/talairach_mixed_with_skull.gca', '/home/fs_data/face.gca', T1_file)
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
                    copy_no_deid(subject_label)
                    run_quickshear(T1_file, T1_file)
                    if args.check_meta:
                        check_meta_data(args.bids_dir, subject_label, list_check_meta)
                    if args.del_meta:
                        del_meta_data(args.bids_dir, subject_label, list_field_del)
            if args.deid == "mridefacer":
                if args.del_nodeface == "del":
                    run_mridefacer(T1_file, subject_label)
                    if args.check_meta:
                        check_meta_data(args.bids_dir, subject_label, list_check_meta)
                    if args.del_meta:
                        del_meta_data(args.bids_dir, subject_label, list_field_del)
                else:
                    copy_no_deid(subject_label)
                    run_mridefacer(T1_file, subject_label)
                    if args.check_meta:
                        check_meta_data(args.bids_dir, subject_label, list_check_meta)
                    if args.del_meta:
                        del_meta_data(args.bids_dir, subject_label, list_field_del)
else:

    # find all T1s and de-identify them
    for subject_label in subjects_to_analyze:
        for T1_file in glob(os.path.join(args.bids_dir, "sub-%s"%subject_label,
                                         "anat", "*_T1w.nii*")) + glob(os.path.join(args.bids_dir,"sub-%s"%subject_label,"ses-*","anat", "*_T1w.nii*")):
            if args.deid == "pydeface":
                if args.del_nodeface == "del":
                    run_pydeface(T1_file, T1_file)
                else:
                    copy_no_deid(subject_label)
                    run_pydeface(T1_file, T1_file)
                    del_meta_data(args.bids_dir, subject_label, list_field_del)
    if args.deid == "mri_deface":
                if args.del_nodeface == "del":
                    run_mri_deface(T1_file, '/home/fs_data/talairach_mixed_with_skull.gca', '/home/fs_data/face.gca', T1_file)
                else:
                    copy_no_deid(subject_label)
                    run_mri_deface(T1_file, '/home/fs_data/talairach_mixed_with_skull.gca', '/home/fs_data/face.gca', T1_file)
                    del_meta_data(args.bids_dir, subject_label, list_field_del)
    if args.deid == "quickshear":
                if args.del_nodeface == "del":
                    run_quickshear(T1_file, T1_file)
                else:
                    copy_no_deid(subject_label)
                    run_quickshear(T1_file, T1_file)
                    del_meta_data(args.bids_dir, subject_label, list_field_del)
    if args.deid == "mridefacer":
                if args.del_nodeface == "del":
                    run_mridefacer(T1_file)
                else:
                    copy_no_deid(subject_label)
                    run_mridefacer(T1_file)
                    del_meta_data(args.bids_dir, subject_label, list_field_del)
