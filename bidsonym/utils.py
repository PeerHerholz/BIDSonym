import os
import json

from glob import glob
import pandas as pd
import nibabel as nib
from shutil import copy


def copy_no_deid(subject_label, bids_dir, T1_file):

    path = os.path.join(bids_dir, "sourcedata/bidsonym/sub-%s" % subject_label)
    outfile = T1_file[T1_file.rfind('/') + 1:T1_file.rfind('.nii')] + '_no_deid.nii.gz'
    if os.path.isdir(path) is True:
        copy(T1_file, os.path.join(path, outfile))
    else:
        os.makedirs(path)
        copy(T1_file, os.path.join(path, outfile))

    path_task_meta = os.path.join(bids_dir, "sourcedata/bidsonym/")
    path_sub_meta = os.path.join(bids_dir, "sourcedata/bidsonym/sub-%s" % subject_label)
    list_task_meta_files = glob(os.path.join(bids_dir, '*json'))
    list_sub_meta_files = glob(os.path.join(bids_dir, subject_label, '*', '*.json'))
    for task_meta_data_file in list_task_meta_files:
        task_out = task_meta_data_file[task_meta_data_file.rfind('/') +
                                       1:task_meta_data_file.rfind('.json')] \
                                       + '_no_deid.json'
        copy(task_meta_data_file, os.path.join(path_task_meta, task_out))
    for sub_meta_data_file in list_sub_meta_files:
        sub_out = sub_meta_data_file[sub_meta_data_file.rfind('/') +
                                     1:sub_meta_data_file.rfind('.json')] +\
                                     '_no_deid.json'
        copy(sub_meta_data_file, os.path.join(path_sub_meta, sub_out))


def check_meta_data(bids_path, subject_label, prob_fields):

    list_subject_image_files = glob(os.path.join(bids_path, 'sub-' + subject_label, '*', '*nii.gz'))
    list_task_meta_files = glob(os.path.join(bids_path, '*json'))
    list_sub_meta_files = glob(os.path.join(bids_path, 'sub-' + subject_label, '*', '*.json'))
    list_meta_files = list_task_meta_files + list_sub_meta_files
    prob_fields = prob_fields

    for subject_image_file in list_subject_image_files:

        header = nib.load(subject_image_file).header
        keys = []
        dat = []

        for key, data in zip(header.keys(), header.values()):
            keys.append(key)
            dat.append(data)
        header_df = pd.DataFrame({'meta_data_field': keys, 'data': dat, 'problematic': 'no'})

        for index, row in header_df.iterrows():
            if any(i.lower() in row['meta_data_field'] for i in prob_fields):
                row['problematic'] = 'maybe'
            else:
                row['problematic'] = 'no'

        header_df.to_csv(os.path.join(bids_path, 'sourcedata/bidsonym',
                                      'sub-%s' % subject_label,
                                      subject_image_file[subject_image_file.rfind('/') +
                                                         1:subject_image_file.rfind('.nii.gz')] +
                                      '_header_info.csv'),
                         index=False)

    for meta_file in list_meta_files:

        with open(meta_file, 'r') as json_file:
            meta_data = json.load(json_file)
            keys = []
            info = []
            for key, inf in zip(meta_data.keys(), meta_data.values()):
                keys.append(key)
                info.append(inf)
            json_df = pd.DataFrame({'meta_data_field': keys, 'information': info, 'problematic': 'no'})

            for index, row in json_df.iterrows():
                if any(i in row['meta_data_field'] for i in prob_fields):
                    row['problematic'] = 'maybe'
                else:
                    row['problematic'] = 'no'

            json_df.to_csv(os.path.join(bids_path, 'sourcedata/bidsonym', 'sub-%s' % subject_label,
                                        meta_file[meta_file.rfind('/') +
                                                  1:meta_file.rfind('.json')] +
                                        '_json_info.csv'),
                           index=False)


def del_meta_data(bids_path, subject_label, fields_del):

    list_task_meta_files = glob(os.path.join(bids_path, '*json'))
    list_sub_meta_files = glob(os.path.join(bids_path, 'sub-' + subject_label, '*', '*.json'))
    list_meta_files = list_task_meta_files + list_sub_meta_files

    fields_del = fields_del

    print('working on %s' % subject_label)
    print('found the following meta-data files:')
    print(*list_meta_files, sep='\n')
    print('the following fields will be deleted:')
    print(*fields_del, sep='\n')

    for meta_file in list_meta_files:
        with open(meta_file, 'r') as json_file:
            meta_data = json.load(json_file)
            for field in fields_del:
                meta_data[field] = 'deleted_by_bidsonym'
        with open(meta_file, 'w') as json_output_file:
            json.dump(meta_data, json_output_file, indent=4)
