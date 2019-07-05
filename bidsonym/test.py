import os
import nibabel as nib
from glob import glob
import pandas as pd
import json


def check_metda_data(bids_path, subject_label):

    #gather all image files
    list_subject_image_files = glob(os.path.join(bids_path, 'sub-' + subject_label, '*', '*nii.gz'))

    #gather all meta data files
    list_task_meta_files = glob(os.path.join(bids_path, '*json'))
    list_sub_meta_files = glob(os.path.join(bids_path, 'sub-' + subject_label, '*', '*.json'))
    list_meta_files = list_task_meta_files + list_sub_meta_files

    #define potentially problematic fields
    prob_fields = ['Name', 'Data', 'Patient', 'Institution']

    #check image files, output .csv dataframe with found header information and if it might be problematic
    for subject_image_file in list_subject_image_files:

        header = nib.load(subject_image_file).header

        keys=[]
        dat = []

        for key, data in zip(header.keys(), header.values()):
            keys.append(key)
            dat.append(data)

        header_df = pd.DataFrame({'meta_data_field':keys, 'data':dat, 'problematic':'no'})

        for index, row in header_df.iterrows():
            if any(i.lower() in row['meta_data_field'] for i in prob_fields):
                row['problematic'] = 'maybe'
            else:
                row['problematic'] = 'no'

        header_df.to_csv(os.path.join(bids_path, 'sourcedata/bidsonym', 'sub-%s'%subject_label, subject_image_file[subject_image_file.rfind('/') + 1:subject_image_file.rfind('.nii.gz')] + '_header_info.csv'), index=False)

    #check meta data files, output .csv dataframe with found information and if it might be problematic
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

            json_df.to_csv(os.path.join(bids_path, 'sourcedata/bidsonym', 'sub-%s'%subject_label, meta_file[meta_file.rfind('/') + 1:meta_file.rfind('.nii.gz')] + '_header_info.csv'), index=False)