#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import sys
from datetime import datetime
from os.path import exists as file_exists
from pathlib import Path


# parent_headers = ['Proposal ID', 'Principal Investigator ',
#                   'Sample Name', 'Sample Replicate Group', 'Sample ID', 'Barcode']

# fraction_headers = ['Final Deliverable Project ID', 'Sequencing Project ID',
#                     'Sample ID', 'Sample Name', 'Sample Replicate Group', 'Sample Tube/Plate Label', 'Plate Location']

# library_headers = ['Sample ID', 'Sample Tube/Plate Label',
#                    'Plate Location', 'Library Name', 'Pool Name', 'Pool of Pools Name']


# # read in specific columns of all_inclusive file into df
# all_df = pd.read_excel('all_inclusive.xlsx', usecols=parent_headers)


############################
############################
def updateProjectDatabase(current_project, parent_all_inclusive):
    # read in all columns of all_inclusive file into df
    all_df = pd.read_excel(parent_all_inclusive)

    # find and remove rows with 'abandoned' in any column
    mask = np.column_stack([all_df[col].astype(str).str.contains(
        '.*Abandoned.*', na=False, case=False) for col in all_df])

    # not the ~ to select rows that are not in mask
    all_df = all_df.loc[~mask.any(axis=1)]

    # split PI name based on first comma
    all_df[['PI_name', 'First_name']] = all_df['Principal Investigator '].str.split(
        ',', expand=True, n=1)

    # rearrange columns and keep only desired columns
    all_df = all_df[['Proposal ID', 'PI_name',
                     'Sample Name', 'Sample Replicate Group', 'Sample ID', 'Barcode']]

    # rename columns that will ultimately be kept by removing white spaces
    all_df.rename(columns={'Proposal ID': 'Proposal_ID', 'Sample Name': 'Sample_Name',
                  'Sample Replicate Group': 'Replicate_Group'}, inplace=True)

    # read existing project_database.csv file into df
    p_df = pd.read_csv(current_project)

    # check of project_database.csv already has
    if ('Sample_Name' in p_df.columns) or ('Replicate_Group' in p_df.columns):
        print('\n\nThe project_database.csv file already had columns with Sample Name and/or Replicate Group.  Do you want to overwrite?')

        val = input()

        if (val == 'Y' or val == 'y'):
            print("Ok, we'll keep going\n\n")

            # remove existing names and replicate groups
            p_df.drop(columns={'Sample_Name', 'Replicate_Group'}, inplace=True)

        elif (val == 'N' or val == 'n'):
            print('Ok, aborting script\n\n')
            sys.exit()
        else:
            print("Sorry, you must choose 'Y' or 'N' next time. \n\nAborting\n\n")
            sys.exit()

    # merege all inclused df with project database df based on sample id and tube barcodes
    my_merged_project_df = all_df.merge(p_df, how='outer', left_on=[
        'Sample ID', 'Barcode'], right_on=['ITS_sample_id', 'Matrix_barcode'])

    # confirm that all sample is and tube barcodes in all_inclusive.xlsx were found in project_database.csv and vice versa
    if my_merged_project_df.shape[0] != all_df.shape[0]:
        print('\n\nThere was a mismatch in sample id or tube barcode when merging all_inclusive.xlsx info with project_datavase.csv.  Aborting process:')
        sys.exit()

    # drop redundant columsn used during merge
    my_merged_project_df.drop(columns={'Sample ID', 'Barcode'}, inplace=True)

    return my_merged_project_df
############################
############################


############################
############################
def makeUpdatedFiles(merged_project_df):
    # update project database and archive older version of project database
    date = datetime.now().strftime("%Y_%m_%d-Time%H-%M-%S")

    Path(PROJECT_DIR /
         "project_database.csv").rename(ARCHIV_DIR / f"archive_project_database_{date}.csv")
    Path(ARCHIV_DIR / f"archive_project_database_{date}.csv").touch()

    merged_project_df.to_csv(PROJECT_DIR / 'project_database.csv', index=False)

    return
############################
############################


############################
# MAIN PROGRAM
############################
# get current working directory and its parent directory
PROJECT_DIR = Path.cwd()

ARCHIV_DIR = PROJECT_DIR / "archived_files"

# get input files
current_project = 'project_database.csv'

parent_all_inclusive = 'parent_all_inclusive.xlsx'


# add Project ID, PI name, Sample Name, and Sample Replicate Group to project_database.csv
merged_project_df = updateProjectDatabase(
    current_project, parent_all_inclusive)


# update project_database.csv and lib_info.csv
makeUpdatedFiles(merged_project_df)
