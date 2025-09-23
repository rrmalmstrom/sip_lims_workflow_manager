#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import sys
import os
import xlrd
from xlutils.copy import copy
import xlwt
from datetime import datetime
from pathlib import Path
from sqlalchemy import create_engine
import shutil


##########################
##########################
def readSQLdb():

    # path to sqlite db lib_info_submitted_to_clarity.db
    sql_db_path = PROJECT_DIR / 'lib_info_submitted_to_clarity.db'

    # create sqlalchemy engine
    engine = create_engine(f'sqlite:///{sql_db_path}') 

    # define sql query
    query = "SELECT * FROM lib_info_submitted_to_clarity"
    
    # import sql db into pandas df
    summary_df = pd.read_sql(query, engine)
    
    summary_df['Sample Barcode'] = summary_df['Sample Barcode'].astype('str')
    
    summary_df['Fraction #'] = summary_df['Fraction #'].astype('int')
    
    # select subset of columns with data only specific libraries going into sequencing
    lib_df = summary_df[['Pool_source_plate', 'Pool_source_well', 'Pool_Illumina_index_set', 'Pool_Illumina_index', 'Pool_DNA_conc_ng/uL', 'Pool_nmole/L', 'Pool_Avg. Size']]
    
    engine.dispose()

    return summary_df, lib_df
##########################
##########################


#########################
#########################
def updateSQLdb(lb_info_df):
    
    # make copy of current version so lib_info.db to be archived
    # the copy will be moved to archive folder at a later step
    shutil.copy(PROJECT_DIR /'lib_info.db', PROJECT_DIR / 'archive_lib_info.db')

    sql_db_path = PROJECT_DIR /'lib_info.db'

    engine = create_engine(f'sqlite:///{sql_db_path}') 


    # Specify the table name and database engine
    table_name = 'lib_info'
    
    # Export the DataFrame to the SQLite database
    lb_info_df.to_sql(table_name, engine, if_exists='replace', index=False) 
    
    engine.dispose()


    return
#########################
#########################



##########################
##########################
def getCalrityFiles(my_dirname, my_ext):
    # create empty list to hold FA output files
    my_list_matched_files = []

# loop through all files in directory, find files that end with .xls and adde them to a list
    for file in os.listdir(my_dirname):
        if file.startswith('autofilled'):
            continue

        elif file.endswith(my_ext):

            my_list_matched_files.append(file)

        else:
            continue

    # quit script if directory doesn't contain FA .csv files
    if len(my_list_matched_files) == 0:
        print(
            "\n\n Did not find any .xls clarity lib creation files.  Aborting program\n\n")
        sys.exit()

    else:

        return my_list_matched_files
##########################
##########################


#####################
#####################
def mergeLibDataFiles(my_lib_df, my_clarity_df, my_lib_plate, my_clarity_lib_plate_id):

    # make slice of lib_df with only data matching library plate on current worksheet
    tmp_lib_df = my_lib_df[lib_df['Pool_source_plate'] == my_lib_plate].copy()

    # add make new column with original index from lib_df
    # this can be used to update dataframe later
    tmp_lib_df['original_index'] = tmp_lib_df.index

    # tmp_lib_df['original_index'] = tmp_lib_df['original_index'].astype(str)

    # add column wiht fake library volume
    tmp_lib_df['Library Volume (ul)'] = 35

    # make slice of clarity_df with well and lib name
    tmp_clarity_df = my_clarity_df[['Well', 'Library Name']].dropna().copy()

    # abort script if current library plate id wasn't found in database
    if tmp_lib_df.shape[0] < 1:
        print(
            f"\n\n Could not find {my_lib_plate} in database file. Aborting process\n\n")
        sys.exit()

    # aborts script if there's a mismatch in number of libraries in clarity_df and lib_df
    elif tmp_lib_df.shape[0] != tmp_clarity_df.shape[0]:
        print(
            f"\n\n Mismatch in plate {my_lib_plate} between number of libs in creation sheet and database. Aborting processn\n")
        sys.exit()

    # confirm tmp_clarity_df and tmp_lib_df can be merged without any mismatches
    # if there's a mismatch, i.e. and extra row because of outer  join created row with Nan
    # then abort process
    else:
        tmp_merge_df = pd.merge(tmp_clarity_df, tmp_lib_df, how='outer', left_on=[
            'Well'], right_on=['Pool_source_well'])

        if tmp_merge_df.shape[0] != tmp_clarity_df.shape[0]:
            print(
                f"\n\n Mismatch in plate {my_lib_plate} between number of libs in creation sheet and database. Aborting processn\n")
            sys.exit()

    # merge tmp_lib_df with info on libs with the clarity_df based on Well position
    my_clarity_info_df = pd.merge(my_clarity_df, tmp_lib_df,  how='outer', left_on=[
        'Well'], right_on=['Pool_source_well'])

    my_merged_df = my_clarity_info_df.copy()

    my_merged_df.drop(['Pool_source_plate', 'Pool_source_well',
                       'Pool_Illumina_index_set', 'original_index'], inplace=True, axis=1)

    # rearrange column order to match expect excel file format
    my_merged_df = my_merged_df.reindex(
        columns=['Well', 'Library LIMS ID', 'Library Name', 'Pool_Illumina_index', 'Aliquot Mass (ng)', 'Pool_DNA_conc_ng/uL', 'Pool_Avg. Size', 'Library Volume (ul)', 'Pool_nmole/L'])

    my_merged_df['Aliquot Mass (ng)'] = np.where(
        my_merged_df['Library Name'].notnull(), 1.0, my_merged_df['Aliquot Mass (ng)'])

    # Convert all columns to object dtype to allow string values, then fill NaN
    my_merged_df = my_merged_df.astype(object)
    my_merged_df.fillna('', inplace=True)

    my_clarity_info_df['Aliquot Mass (ng)'] = np.where(
        my_clarity_info_df['Library Name'].notnull(), 1.0, my_clarity_info_df['Aliquot Mass (ng)'])

    my_clarity_info_df.dropna(inplace=True)

    my_clarity_info_df['Clarity_Lib_Plate_ID'] = my_clarity_lib_plate_id

    my_clarity_info_df.drop(['Well', 'Pool_Illumina_index_set', 'Pool_Illumina_index', 'Aliquot Mass (ng)', 'Pool_DNA_conc_ng/uL',
                            'Pool_Avg. Size', 'Library Volume (ul)', 'Pool_nmole/L'], inplace=True, axis=1)

    my_clarity_info_df.rename(columns={'Pool_source_plate': 'tmp_pool_source_plate',
                              'Pool_source_well': 'tmp_pool_source_well'}, inplace=True)

    my_clarity_info_df = my_clarity_info_df.set_index('original_index')

    my_clarity_info_df.index = my_clarity_info_df.index.rename('Index')

    return my_merged_df, my_clarity_info_df


#####################
#####################


#####################
#####################
def updateLibCreationFile(my_sheet, my_merged_df, my_lib_plate):

    # define the index set to be entered in lib creation file
    illumina_index_set = 'Custom'

    # add fake values about DNA aliquots that are necessary for clarity upload
    target_aliquot_mass = 1

    target_aliquot_vol = 5

    pcr_cycle = int(input(
        f"\nEnter number of PCR cycles used in library creation for {my_lib_plate} (default = 12):") or 12)

    # overwrite all cell values from row 26-500 and col 1-21 to create blank slate in lib info area of .xls file
    for r in range(26, 500, 1):
        for c in range(0, 20, 1):
            my_sheet.write(r, c, '')

    # loop through merged df and write info into .xls file
    for row_num, row in my_merged_df.iterrows():
        for col_num, col in enumerate(row):
            my_sheet.write(26+row_num, col_num, col)

    # update necessary cells in .xls file
    my_sheet.write(14, 1, 'Pass')

    my_sheet.write(16, 1, pcr_cycle)

    my_sheet.write(17, 1, illumina_index_set)

    my_sheet.write(10, 1, target_aliquot_mass)

    my_sheet.write(11, 1, target_aliquot_vol)

    return my_sheet

#####################
#####################


##########################
##########################
def processXLSfiles(my_xls_files, my_lib_df):
    # make empty list to hold names of lib plates that successfully filled .xls lib creation file
    my_completed_plates = []

    # create empty df to eventually hold lib summary info plus clairty lib name, sample ID, and plate IDs
    my_lib_name_df = pd.DataFrame()

    for x in my_xls_files:

        lib_creation_file = CLARITY_DIR / x

        # import library creation .xls file downloaded from clarity queue
        clarity_df = pd.read_excel(
            lib_creation_file, header=25, engine=("xlrd"), usecols=['Well', 'Library LIMS ID', 'Library Name', 'Aliquot Mass (ng)'])

        # # provide dummy aliquot mass info if missing from .xls downloaded from clarity
        # clarity_df['Aliquot Mass (ng)'].fillna(1.0, inplace=True)

        # read in library creation file
        book = xlrd.open_workbook(lib_creation_file)

        # make copy of workbook with xlwt module so that it can be editted
        wb = copy(book)

        # loop through all sheets in workbook
        for sheet in book.sheets():

            # # skip over hidden sheets in library creation file
            # if (sheet.name == 'hidden') or (sheet.name == 'Excel Configuration'):
            #     continue

            # else:

            # skip over hidden sheets in library creation file
            if (sheet.name == 'Results'):

                # get the name of the library plates from lib creation file
                lib_plate = sheet.cell_value(rowx=4, colx=1)

                clarity_lib_plate_id = sheet.cell_value(rowx=3, colx=1)

                # call funtion to merge data from lib summary file and lib creation file
                merged_df, clarity_info_df = mergeLibDataFiles(
                    my_lib_df, clarity_df, lib_plate, clarity_lib_plate_id)

                # append clarity lib name, lib id, and plate id to
                if my_lib_name_df.empty:
                    my_lib_name_df = clarity_info_df.copy()

                else:
                    # my_lib_name_df = pd.concat(
                    #     [my_lib_name_df, clarity_info_df], axis=0, ignore_index=True)

                    my_lib_name_df = pd.concat(
                        [my_lib_name_df, clarity_info_df], axis=0)

                # select current worksheet in wlwt from wb copy of workbook
                s = wb.get_sheet(sheet.name)

                # update worksheet with library summary stats and metadata
                s = updateLibCreationFile(s, merged_df, lib_plate)

                my_completed_plates.append(lib_plate)

                # make new lib_creation.xls filled out with library metadata
                wb.save(CLARITY_DIR / f'autofilled_{x}')

    return my_completed_plates, my_lib_name_df
##########################
##########################


##########################
##########################
def removefiles(my_dirname, my_ext):
    for file in os.listdir(my_dirname):
        if file.endswith(my_ext) and file.startswith('autofilled'):
            os.remove(file)

        else:
            continue

    return
##########################
##########################


##########################
##########################
def findMissingPlateFiles(lib_df, completed_plates):

    total_lib_plates = sorted(lib_df['Pool_source_plate'].unique().tolist())

    missing_plates = sorted(set(set(total_lib_plates)-set(completed_plates)))

    if len(missing_plates) > 0:
        print(
            f'\n\nWARNING!!!   WARNING!!!   WARNING!!!\n\nThe library plates below were NOT processed in clarity lib creation files:\n\n{missing_plates}\n\n')

        keep_going = input(
            'Would you like to autofill clarity creation files for ONLY some the library plates? (Y/N)\n')

        if (keep_going == 'Y' or keep_going == 'y'):
            print(
                "Ok, we'll keep going, but do you have a plan for processing missing plates?\n\n")

        elif (keep_going == 'N' or keep_going == 'n'):
            print('Ok, aborting script\n\n')
            removefiles(crnt_dir, ext)
            sys.exit()
        else:
            print("Sorry, you must choose 'Y' or 'N' next time. \n\nAborting\n\n")
            removefiles(crnt_dir, ext)
            sys.exit()

##########################
##########################


##########################
##########################
def addClarityInfoToLibInfo(summary_df, lib_name_df):

    # check if lib_info_submitted_to_clarity.csv already has column 'Library Name' indicating
    # it was already partially upated with a subset lib plates
    # in this case just fill in empty (Nan) cells with new data from lib_name_df
    if 'Library Name' in summary_df.columns:
        message = """
        The lib_info_submitted_to_clarity.csv database already has some
        info about clarity Library names, Library LIMS ID, and Library Plates.
        Existing data will NOT be overwritten by continuing this process.
        Only library currenlty missing these clarity id's will be updated.
        """
        print(f'\n\n{message}\n\n')

        keep_going = input(
            'Would you like to autofill clarity creation files for ONLY some the library plates? (Y/N)\n')

        if (keep_going == 'Y' or keep_going == 'y'):
            print(
                "Ok, we'll keep going, but do you have a plan for processing missing plates?\n\n")

        elif (keep_going == 'N' or keep_going == 'n'):
            print('Ok, aborting script\n\n')
            removefiles(crnt_dir, ext)
            sys.exit()
        else:
            print("Sorry, you must choose 'Y' or 'N' next time. \n\nAborting\n\n")
            removefiles(crnt_dir, ext)
            sys.exit()

        lib_name_df.drop(
            ['tmp_pool_source_plate', 'tmp_pool_source_well'], inplace=True, axis=1)
        updated_df = summary_df.copy()
        updated_df = updated_df.fillna(lib_name_df)

    # if lib_info_submitted_to_clarity.csv doesn't have columen 'Library Name'
    # then merge with lib_name_df to add clarity lib name, lims id, and lib plate id
    else:
        updated_df = pd.merge(summary_df, lib_name_df, how='outer', left_on=[
                              'Pool_source_plate', 'Pool_source_well'], right_on=['tmp_pool_source_plate', 'tmp_pool_source_well'])

        updated_df.drop(
            ['tmp_pool_source_plate', 'tmp_pool_source_well'], inplace=True, axis=1)

        # updated_df = pd.concat([summary_df, lib_name_df], axis=1)

    if updated_df.shape[0] != summary_df.shape[0]:
        print('\n\nError in adding Clarity LIMS ID, Library Name, and Library Plate ID to library database.  Aborting process:')
        removefiles(crnt_dir, ext)
        sys.exit()

    return updated_df
##########################
##########################


##########################
##########################
def moveBlankLibCreationFiles(my_xls_files):

    for x in my_xls_files:
        # archive the blank .xls file
        Path(CLARITY_DIR /
             f"{x}").rename(OLD_DIR / f"{x}")
        Path(OLD_DIR / f"{x}").touch()

##########################
##########################


#########################
#########################
def createSQLdb(updated_df):
    

    sql_db_path = PROJECT_DIR /'lib_info_submitted_to_clarity.db'

    engine = create_engine(f'sqlite:///{sql_db_path}') 


    # Specify the table name and database engine
    table_name = 'lib_info_submitted_to_clarity'
    
    # Export the DataFrame to the SQLite database
    updated_df.to_sql(table_name, engine, if_exists='replace', index=False) 


    return
#########################
#########################




##########################
# MAIN PROGRAM
##########################

prjct_dir = os.getcwd()

dir_name = "5_pooling"

prnt_dir = os.path.join(prjct_dir, dir_name)

sub_dir_name = "B_fill_clarity_lib_creation_file"

crnt_dir = os.path.join(prnt_dir, sub_dir_name)


###########################
# set up folder organiztion
###########################
PROJECT_DIR = Path.cwd()

ARCHIV_DIR = PROJECT_DIR / "archived_files"

POOL_DIR = PROJECT_DIR / "5_pooling"

CLARITY_DIR = POOL_DIR / "B_fill_clarity_lib_creation_file"

PLOT_DIR = PROJECT_DIR / "DNA_vs_Density_plots"

OLD_DIR = CLARITY_DIR / "processed_blank_lib_creation_files"
OLD_DIR.mkdir(parents=True, exist_ok=True)


# get current date and time, will add to archive database file name
date = datetime.now().strftime("%Y_%m_%d-Time%H-%M-%S")

# file extension for FA output file
ext = ('.xls')

# get list of .xls clarity lib creation files
xls_files = getCalrityFiles(crnt_dir, ext)

# create two dfs from lib_info_submitted_to_clarity.db sqlite file
# lib_df has only columns starting with "Pool"
# summary_df has all columns in lib_submitted_to_clarity.db
summary_df, lib_df = readSQLdb()

# loop through all .xls files and fill in missing library metadata
# and return a df lib_name_df that can be used to update lib_info_submitted_to_clarity.csv
# with Clarity LIMS ID, library name, and lib plate ID
completed_plates, lib_name_df = processXLSfiles(xls_files, lib_df)

# make sure all library plates had a corresponding blank .xls file downloaded from clarity, and that
# all .xls file were filled out by python script
findMissingPlateFiles(lib_df, completed_plates)

# # make new df from lib_info_submitted_to_clarity.csv  so that clarity lib name, lims id, and lib plate id can be added to df
# summary_df = pd.read_csv(PROJECT_DIR / 'lib_info_submitted_to_clarity.csv',
#                          header=0, converters={'Sample Barcode': str})

# add clarity library lims id, library name, and library plate id to lib_info_submitted_to_clarity.csv database
updated_df = addClarityInfoToLibInfo(summary_df, lib_name_df)

# move blank .xls files that have been processed to subfolder for storage
moveBlankLibCreationFiles(xls_files)




# create sqlite database for updated lib_info_submitted_to_clarity.db
createSQLdb(updated_df)



# arive the current lib_info_submitted_to_clarity.csv
Path(PROJECT_DIR /
     "lib_info_submitted_to_clarity.csv").rename(ARCHIV_DIR / f"archive_lib_info_submitted_to_clarity_{date}.csv")
Path(ARCHIV_DIR / f"archive_lib_info_submitted_to_clarity_{date}.csv").touch()

# create updated lib_info_submitted_to_clarity.csv file
updated_df.to_csv(
    PROJECT_DIR / 'lib_info_submitted_to_clarity.csv', index=False)

# Create success marker file to indicate script completed successfully
import os
os.makedirs('.workflow_status', exist_ok=True)
with open('.workflow_status/fill.clarity.lib.creation.sheet.success', 'w') as f:
    f.write('Script completed successfully')
