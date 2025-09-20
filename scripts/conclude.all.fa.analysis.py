#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# USAGE:   python conclude.all.fa.analysis.py


import pandas as pd
import sys
from pathlib import Path
from os.path import exists as file_exists
from datetime import datetime
import os
from sqlalchemy import create_engine
import shutil


##########################
##########################
def findUpdateFAFile():
    # Check for missing critical files when directories exist
    if THIRD_FA_DIR.exists():
        third_fa_file = THIRD_FA_DIR / "updated_3rd_fa_analysis_summary.txt"
        if not third_fa_file.exists():
            print(f'\nERROR: Third attempt directory exists but critical file is missing!')
            print('Please generate the updated_3rd_fa_analysis_summary.txt file before running this script.\n')
            sys.exit(1)
        updated_file_name = third_fa_file

    elif SECOND_FA_DIR.exists():
        second_fa_file = SECOND_FA_DIR / "updated_2nd_fa_analysis_summary.txt"
        if not second_fa_file.exists():
            print(f'\nERROR: Second attempt directory exists but critical file is missing!')
            print('Please generate the updated_2nd_fa_analysis_summary.txt file before running this script.\n')
            sys.exit(1)
        updated_file_name = second_fa_file

    # elif FIRST_FA_DIR.exists():
    #     first_fa_file = FIRST_FA_DIR / "updated_fa_analysis_summary.txt"
    #     if not first_fa_file.exists():
    #         print(f'\nERROR: First attempt directory exists but critical file is missing!')
    #         print('Please generate the updated_fa_analysis_summary.txt file before running this script.\n')
    #         sys.exit(1)
    #     updated_file_name = first_fa_file

    else:
        print('\nERROR: No FA analysis directories found!')
        print('Expected one of the following directories to exist:')
        print('Please ensure at least one FA analysis has been completed.\n')
        sys.exit(1)

    return updated_file_name
##########################
##########################



##########################
##########################
def readSQLdb():
    
    # path to sqlite db lib_info.db
    sql_db_path = PROJECT_DIR /'lib_info.db'

    # create sqlalchemy engine
    engine = create_engine(f'sqlite:///{sql_db_path}') 

    # define sql query
    query = "SELECT * FROM lib_info"
    
    # import sql db into pandas df
    sql_df = pd.read_sql(query, engine)
    
    sql_df['Sample Barcode'] = sql_df['Sample Barcode'].astype('str')
    
    sql_df['Fraction #'] = sql_df['Fraction #'].astype('int')
    
    engine.dispose()

    return sql_df
##########################
##########################


##########################
##########################
def updateLibInfo(updated_file_name):

    # create df from fa_analysis_summary.txt file
    reduced_df = pd.read_csv(updated_file_name, sep='\t',
                             header=0, converters={'Sample Barcode': str, 'Fraction #': int})
    
    # create df from lib_info.db sqliute file
    lib_df = readSQLdb()

    
    if 'Total_passed_attempts' in lib_df.columns:
    
        # remove older version to Total_attempts_passed so it can be replaced  during merge step below
        lib_df.drop(['Total_passed_attempts'], inplace=True, axis=1)


    lib_df = lib_df.merge(reduced_df, how='outer', left_on=[
                          'Sample Barcode', 'Fraction #'], right_on=['Sample Barcode', 'Fraction #'], suffixes=('', '_y'))
    
    # update dilution factors and previous lib pass/fail decisions
    # this logic also distinguished between instances when a 3rd emergency attempt was made or not
    if 'Third_FA_dilution_factor' in lib_df.columns:
        # update the fa dilution factor using value from threshold.txt
        lib_df['Third_FA_dilution_factor'] = lib_df['Third_FA_dilution_factor_y']
        
        # update Passed_Library and Redo_Passed_library with manually modified results from updated_*_fa_analysis_summary.txt
        lib_df['Passed_library'] = lib_df['Passed_library_y']
        
        # updated  Redo_Passed_library, if necessary
        lib_df['Redo_Passed_library'] = lib_df['Redo_Passed_library_y']
        
    else: 
        # update the fa dilution factor using value from threshold.txt
        lib_df['Redo_FA_dilution_factor'] = lib_df['Redo_FA_dilution_factor_y']
        
        # update Passed_Library and Redo_Passed_library with manually modified results from updated_*_fa_analysis_summary.txt
        lib_df['Passed_library'] = lib_df['Passed_library_y']
        

    
    # remove redundant columns after merging
    lib_df.drop(lib_df.filter(regex='_y$').columns, axis=1, inplace=True)
    
    # remove redundante columns
    if 'Redo_FA_Well' in lib_df.columns:
        # remove unnecessary columne 'FA_Well'
        lib_df.drop(['Redo_FA_Well'], inplace=True, axis=1)
    
    
    if 'Third_FA_Well' in lib_df.columns:
        # remove unnecessary columne 'FA_Well'
        lib_df.drop(['Third_FA_Well'], inplace=True, axis=1)

    # sort df based on sample and fraction number in case user manually
    # changed sorting when generated updated_fa_analysis_summary.txt
    lib_df.sort_values(by=['Sample Barcode', 'Fraction #'], inplace=True)

    # confirm all samples and fraction numbers in reduced_df
    # matched up with all samples and fraction numbrs in lib_df
    if lib_df['Total_passed_attempts'].isnull().values.any():

        print('\nProblem updating lib_info.csv with pass/fail results from updated_2nd_fa_analysis_summary.txt. Aborting script\n\n')
        sys.exit()
        
        
    elif updated_file_name == SECOND_FA_DIR / 'updated_2nd_fa_analysis_summary.txt':
        
        lib_df['check_total_pass'] =  lib_df['Total_passed_attempts'] - lib_df.fillna(0)['Passed_library'] - lib_df.fillna(0)['Redo_Passed_library']
        
        # abort script if the total passed attempts count does not match  the  sum of individual pass/fail results for each fraction
        if (lib_df['check_total_pass'] != 0).any():
            
            print('\nTotal_passed_attempts does not equal sum of pass/fail results. Aborting script\n\n')
            sys.exit()
            
    elif updated_file_name == THIRD_FA_DIR / 'updated_3rd_fa_analysis_summary.txt':
    
        lib_df['check_total_pass'] =  lib_df['Total_passed_attempts'] - lib_df.fillna(0)['Passed_library'] - lib_df.fillna(0)['Redo_Passed_library'] - lib_df.fillna(0)['Third_Passed_library']
             
        # abort script if the total passed attempts count does not match  the  sum of individual pass/fail results for each fraction
        if (lib_df['check_total_pass'] != 0).any():
            
            print('\nTotal_passed_attempts does not equal sum of pass/fail results. Aborting script\n\n')
            sys.exit()


    # drop column 'check_total_pass' since it's no longer needed
    lib_df.drop(['check_total_pass'], inplace=True, axis=1)        

    return lib_df
##########################
##########################



#########################
#########################
def createSQLdb(lib_df):
    
    # # make copy of current version so lib_info.db to be archived
    # # the copy will be moved to archive folder at a later step
    # shutil.copy(PROJECT_DIR /'lib_info.db', PROJECT_DIR / 'archive_lib_info.db')
    
    # archive the older version of sql lib_info.db
    Path(PROJECT_DIR /
        "lib_info.db").rename(ARCHIV_DIR / f"archive_lib_info_{date}.db")
    Path(ARCHIV_DIR / f"archive_lib_info_{date}.db").touch()

    sql_db_path = PROJECT_DIR /'lib_info.db'

    engine = create_engine(f'sqlite:///{sql_db_path}') 


    # Specify the table name and database engine
    table_name = 'lib_info'
    
    # Export the DataFrame to the SQLite database
    lib_df.to_sql(table_name, engine, if_exists='replace', index=False) 

    engine.dispose()

    # archive the current lib_info.csv
    Path(PROJECT_DIR /
        "lib_info.csv").rename(ARCHIV_DIR / f"archive_lib_info_{date}.csv")
    Path(ARCHIV_DIR / f"archive_lib_info_{date}.csv").touch()

    # create updated library info file
    lib_df.to_csv(PROJECT_DIR / 'lib_info.csv', index=False)

    return 
#########################
#########################


###########################
# set up folder organiztion
###########################

# current_dir = os.path.basename(os.getcwd())

PROJECT_DIR = Path.cwd()

LIB_DIR = PROJECT_DIR / "4_make_library_analyze_fa"

FIRST_FA_DIR = LIB_DIR / "B_first_attempt_fa_result"

SECOND_FA_DIR = LIB_DIR / "D_second_attempt_fa_result"

THIRD_FA_DIR = LIB_DIR / "F_third_attempt_fa_result"

PLOT_DIR = PROJECT_DIR / "DNA_vs_Density_plots"

ARCHIV_DIR = PROJECT_DIR / "archived_files"

POOL_DIR = PROJECT_DIR / "5_pooling"

CLARITY_DIR = POOL_DIR / "A_make_clarity_aliquot_upload_file"


# get current date and time, will add to archive database file name
date = datetime.now().strftime("%Y_%m_%d-Time%H-%M-%S")


# determine if we should use 2nd or 3rd attempt fa results
# based on which folder exists and contains the appropriate
# updated_fa_analysis_summary.txt file
updated_file_name = findUpdateFAFile()

# add library pass/fail results from updated_X_fa_analysis.txt
# to the lib_info.csv file
# pass/fail results may have been manually modified
lib_df = updateLibInfo(updated_file_name)

# create updated version of library info file and place
# in pooling directory
# this file can be manually modified one last time before
# submitting the final version to clarity
lib_df.to_csv(CLARITY_DIR / 'final_lib_summary.csv', index=False)


# create sqlite database file
createSQLdb(lib_df)


# Create success marker file to indicate script completed successfully
import os
os.makedirs('.workflow_status', exist_ok=True)
with open('.workflow_status/conclude.all.fa.analysis.success', 'w') as f:
    f.write('Script completed successfully')
