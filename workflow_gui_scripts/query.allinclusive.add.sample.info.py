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
def updateLibInfo(my_lib_info, merged_project_df):

    # make group_dict dictionary where key is ITS sample ID and value is replicate group
    group_dict = dict(zip(merged_project_df.ITS_sample_id,
                      merged_project_df.Replicate_Group))

    # make group_dict dictionary where key is ITS sample ID and value is replicate group
    name_dict = dict(zip(merged_project_df.ITS_sample_id,
                     merged_project_df.Sample_Name))

    # read current lib_info.csv file into df
    my_lib_info_df = pd.read_csv(my_lib_info)

    # check of project_database.csv already has
    if ('Fraction_sample_name' in my_lib_info_df.columns) or ('Replicate_Group' in my_lib_info_df.columns):
        print('\n\nThe lib_info.csv / lib_info_submitted...csv file already have columns with Fraction_sample_name and/or Replicate_Group.  Do you want to overwrite?')

        val = input()

        if (val == 'Y' or val == 'y'):
            print("Ok, we'll keep going\n\n")

            # remove existing names and replicate groups
            my_lib_info_df.drop(
                columns={'Fraction_sample_name', 'Replicate_Group'}, inplace=True)

        elif (val == 'N' or val == 'n'):
            print('Ok, aborting script\n\n')
            sys.exit()
        else:
            print("Sorry, you must choose 'Y' or 'N' next time. \n\nAborting\n\n")
            sys.exit()

    # add column using group_dict
    my_lib_info_df['Replicate_Group'] = my_lib_info_df['Sample Barcode'].map(
        group_dict)

    # add column of fraction sample name by concat parent sample name with the fraction #
    my_lib_info_df['Fraction_sample_name'] = my_lib_info_df['Sample Barcode'].map(
        name_dict) + "_" + my_lib_info_df['Fraction #'].astype(str)

    # get a list of columns
    cols = list(my_lib_info_df)
    # move the column to head of list using index, pop and insert
    cols.insert(0, cols.pop(cols.index('Replicate_Group')))

    # move the column to head of list using index, pop and insert
    cols.insert(0, cols.pop(cols.index('Fraction_sample_name')))

    # use ix to reorder
    my_lib_info_df = my_lib_info_df.loc[:, cols]

    return my_lib_info_df
############################
############################


############################
############################
def makeUpdatedFiles(merged_project_df, updated_lib_info_df):
    # update project database and archive older version of project database
    date = datetime.now().strftime("%Y_%m_%d-Time%H-%M-%S")

    Path(PROJECT_DIR /
         "project_database.csv").rename(ARCHIV_DIR / f"archive_project_database_{date}.csv")
    Path(ARCHIV_DIR / f"archive_project_database_{date}.csv").touch()

    merged_project_df.to_csv(PROJECT_DIR / 'project_database.csv', index=False)

    # update lib_info.csv and archive older version
    Path(PROJECT_DIR /
         "lib_info.csv").rename(ARCHIV_DIR / f"archive_lib_info_{date}.csv")
    Path(ARCHIV_DIR / f"archive_lib_info_{date}.csv").touch()

    updated_lib_info_df.to_csv(PROJECT_DIR / 'lib_info.csv', index=False)

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

lib_info = 'lib_info.csv'

submit_info = 'lib_info_submitted_to_clarity.csv'


# make list of input files... intentionally did not include submit_info
# in case want to run this script on projects before final fractions
# were selected for sequencing
files = [current_project, parent_all_inclusive, lib_info]

# stop program if input files do not exist
for f in files:
    if (file_exists(f) == 0):
        print(f'\n\nCould not find file {f} \nAborting\n\n')
        sys.exit()


# add Project ID, PI name, Sample Name, and Sample Replicate Group to project_database.csv
merged_project_df = updateProjectDatabase(
    current_project, parent_all_inclusive)


# add Fraction Sample Name and replicate group to lib_info.csv
updated_lib_info_df = updateLibInfo(lib_info, merged_project_df)

# update project_database.csv and lib_info.csv
makeUpdatedFiles(merged_project_df, updated_lib_info_df)

# updated file 'lib_info_submitted_to_clarity.csv' if it exists
if (file_exists(submit_info) == 1):
    # add Fraction Sample Name and replicate group to lib_info.csv
    updated_submit_df = updateLibInfo(submit_info, merged_project_df)

    # update project database and archive older version of project database
    date = datetime.now().strftime("%Y_%m_%d-Time%H-%M-%S")

    Path(PROJECT_DIR /
         "lib_info_submitted_to_clarity.csv").rename(ARCHIV_DIR / f"archive_lib_info_submitted_to_clarity_{date}.csv")
    Path(ARCHIV_DIR /
         f"archive_lib_info_submitted_to_clarity_{date}.csv").touch()

    updated_submit_df.to_csv(
        PROJECT_DIR / 'lib_info_submitted_to_clarity.csv', index=False)
