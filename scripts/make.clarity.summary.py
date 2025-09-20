#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# USAGE:   python make_clarity_summary.py <final_lib_summary.csv>

# sys.argv[1] = manually updated version of final_lib_summary.csv generated from second_FA.output.analysis.py

import pandas as pd
import numpy as np
import sys
from datetime import datetime
from pathlib import Path
import openpyxl
import shutil
from sqlalchemy import create_engine
import os


##########################
##########################
def readSQLdb():

    # path to sqlite db lib_info.db
    sql_db_path = PROJECT_DIR / 'lib_info.db'

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


#########################
#########################
def updateSQLdb(lb_info_df):

    # archive the older version of sql lib_info.db
    Path(PROJECT_DIR /
            "lib_info.db").rename(ARCHIV_DIR / f"archive_lib_info_{date}.db")
    Path(ARCHIV_DIR / f"archive_lib_info_{date}.db").touch()

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
def compareFinalVSlibinfo(lib_df, lb_info_df):
    # check for manual updates to final_lib_summary.csv
    # and update lib_info.csv if manual updates found
    if not lib_df.equals(lb_info_df):
        keep_going = str(input(
            """\n\nThe final_lib_summary.csv database is different from lib_info.csv.  Would you like to replace lib_info.csv with final_lib_summary.csv?  (y/n)\n\n""") or "n")

        if (keep_going.lower() == 'y'):
            print("Ok, we'll keep going\n\n")

        elif (keep_going.lower == 'n'):
            print('Ok, aborting script\n\n')
            sys.exit()
        else:
            print("Sorry, you must choose 'Y' or 'N' next time. \n\nAborting\n\n")
            sys.exit()

        # arive the current lib_info.csv
        Path(PROJECT_DIR /
             "lib_info.csv").rename(ARCHIV_DIR / f"archive_lib_info_{date}.csv")
        Path(ARCHIV_DIR / f"archive_lib_info_{date}.csv").touch()

        # create updated library info file
        lib_df.to_csv(PROJECT_DIR / 'lib_info.csv', index=False)
        
        # update lib_info.db sqlite database file
        updateSQLdb(lb_info_df)       

    return

##########################
##########################


##########################
##########################
def selectPlateForPooling(my_lib_df):

    # select samples that passed >=1 attempt at lib cration
    my_passed_df = my_lib_df[my_lib_df['Total_passed_attempts'] >= 1].copy()

    # create empty columns for pooling source plate and wells
    my_passed_df['Pool_source_plate'] = ""

    my_passed_df['Pool_source_well'] = ""

    # add pool info in special condition when emergency 3 attempt at lib creation is used
    if 'Third_Passed_library' in my_passed_df.columns:
    
        # select redo plate over intial plate if lib passed in both attempts
        my_passed_df['Pool_source_plate'] = np.where(
            my_passed_df['Third_Passed_library'] == 1, my_passed_df['Third_Destination_ID'], (np.where(my_passed_df['Redo_Passed_library'] == 1, my_passed_df['Redo_Destination_ID'], my_passed_df['Destination_ID'])))
    
        my_passed_df['Pool_source_well'] = np.where(
            my_passed_df['Third_Passed_library'] == 1, my_passed_df['Third_Destination_Well'], (np.where(my_passed_df['Redo_Passed_library'] == 1, my_passed_df['Redo_Destination_Well'], my_passed_df['Destination_Well'])))
    
        my_passed_df['Pool_Illumina_index_set'] = np.where(
            my_passed_df['Third_Passed_library'] == 1, my_passed_df['Third_Illumina_index_set'], (np.where(my_passed_df['Redo_Passed_library'] == 1, my_passed_df['Redo_Illumina_index_set'], my_passed_df['Illumina_index_set'])))
    
        my_passed_df['Pool_Illumina_index'] = np.where(
            my_passed_df['Third_Passed_library'] == 1, my_passed_df['Third_Illumina_index'], (np.where(my_passed_df['Redo_Passed_library'] == 1, my_passed_df['Redo_Illumina_index'], my_passed_df['Illumina_index'])))
    
        my_passed_df['Pool_DNA_conc_ng/uL'] = np.where(
            my_passed_df['Third_Passed_library'] == 1, my_passed_df['Third_ng/uL'], (np.where(my_passed_df['Redo_Passed_library'] == 1, my_passed_df['Redo_ng/uL'], my_passed_df['ng/uL'])))
    
        my_passed_df['Pool_nmole/L'] = np.where(
            my_passed_df['Third_Passed_library'] == 1, my_passed_df['Third_nmole/L'], (np.where(my_passed_df['Redo_Passed_library'] == 1, my_passed_df['Redo_nmole/L'], my_passed_df['nmole/L'])))
    
        my_passed_df['Pool_Avg. Size'] = np.where(
            my_passed_df['Third_Passed_library'] == 1, my_passed_df['Third_Avg. Size'], (np.where(my_passed_df['Redo_Passed_library'] == 1, my_passed_df['Redo_Avg. Size'], my_passed_df['Avg. Size'])))
    
        my_passed_df['Pool_dilution_factor'] = np.where(
            my_passed_df['Third_Passed_library'] == 1, my_passed_df['Third_FA_dilution_factor'], (np.where(my_passed_df['Redo_Passed_library'] == 1, my_passed_df['Redo_FA_dilution_factor'], my_passed_df['FA_dilution_factor'])))
    
        ###############

   # add pool info in normal circumstances when only 2 attempts at pooling were made
    else:
        # select redo plate over intial plate if lib passed in both attempts
        my_passed_df['Pool_source_plate'] = np.where(
            my_passed_df['Total_passed_attempts'] == 2, my_passed_df['Redo_Destination_ID'], (np.where(my_passed_df['Redo_Passed_library'] == 1, my_passed_df['Redo_Destination_ID'], my_passed_df['Destination_ID'])))

        my_passed_df['Pool_source_well'] = np.where(
            my_passed_df['Total_passed_attempts'] == 2, my_passed_df['Redo_Destination_Well'], (np.where(my_passed_df['Redo_Passed_library'] == 1, my_passed_df['Redo_Destination_Well'], my_passed_df['Destination_Well'])))

        my_passed_df['Pool_Illumina_index_set'] = np.where(
            my_passed_df['Total_passed_attempts'] == 2, my_passed_df['Redo_Illumina_index_set'], (np.where(my_passed_df['Redo_Passed_library'] == 1, my_passed_df['Redo_Illumina_index_set'], my_passed_df['Illumina_index_set'])))

        my_passed_df['Pool_Illumina_index'] = np.where(
            my_passed_df['Total_passed_attempts'] == 2, my_passed_df['Redo_Illumina_index'], (np.where(my_passed_df['Redo_Passed_library'] == 1, my_passed_df['Redo_Illumina_index'], my_passed_df['Illumina_index'])))

        my_passed_df['Pool_DNA_conc_ng/uL'] = np.where(
            my_passed_df['Total_passed_attempts'] == 2, my_passed_df['Redo_ng/uL'], (np.where(my_passed_df['Redo_Passed_library'] == 1, my_passed_df['Redo_ng/uL'], my_passed_df['ng/uL'])))

        my_passed_df['Pool_nmole/L'] = np.where(
            my_passed_df['Total_passed_attempts'] == 2, my_passed_df['Redo_nmole/L'], (np.where(my_passed_df['Redo_Passed_library'] == 1, my_passed_df['Redo_nmole/L'], my_passed_df['nmole/L'])))

        my_passed_df['Pool_Avg. Size'] = np.where(
            my_passed_df['Total_passed_attempts'] == 2, my_passed_df['Redo_Avg. Size'], (np.where(my_passed_df['Redo_Passed_library'] == 1, my_passed_df['Redo_Avg. Size'], my_passed_df['Avg. Size'])))

        my_passed_df['Pool_dilution_factor'] = np.where(
            my_passed_df['Total_passed_attempts'] == 2, my_passed_df['Redo_FA_dilution_factor'], (np.where(my_passed_df['Redo_Passed_library'] == 1, my_passed_df['Redo_FA_dilution_factor'], my_passed_df['FA_dilution_factor'])))

    print('\n\nHere are the number of passed fractions for each sample:\n\n')

    print(my_passed_df.groupby(['Sample Barcode'])[
          'Fraction #'].agg('count').reset_index())

    return my_passed_df

##########################
##########################


##########################
##########################
# Create summary file for direct upload to Clarity
####################
def makeClaritySummary(my_lib_df):
    # creat new dataframe for export into clarity_summary file
    its_df = my_lib_df[['Plate Barcode', 'Sample Barcode', 'Well Pos', 'Fraction #',
                        'Density (g/mL)', 'DNA Concentration (ng/uL)', 'Fraction Volume (uL)', 'Sequin Mix', 'Sequin Mass (pg)', 'DNA_transfer_vol_(nl)', 'Pool_source_plate', 'Pool_source_well']]

    # rename columns to match Clarity/ITS expectations
    its_df = its_df.rename(columns={'DNA_transfer_vol_(nl)': 'Transferred Volume (uL)',
                                    'Pool_source_plate': 'Destination Barcode',	'Pool_source_well': 'Destination Well Pos'})

    its_df['Sample Barcode'] = its_df['Sample Barcode'].astype(int)

    # user inputs # uL of DNA remaining before library construction
    fraction_vol = float(
        input("Enter the resuspension volume for DNA pellet (default 35uL): ") or 35)

    # this is usually the resuspension volume transfered into the echo plate for later lib creation
    its_df['Transferred Volume (uL)'] = fraction_vol

    its_df.to_excel(CLARITY_DIR / 'clarity_summary.xlsx', index=False, header=True)

    return

##########################
##########################


#########################
#########################
def createSQLdb(passed_df):

    sql_db_path = PROJECT_DIR /'lib_info_submitted_to_clarity.db'

    engine = create_engine(f'sqlite:///{sql_db_path}') 

    # Specify the table name and database engine
    table_name = 'lib_info_submitted_to_clarity'

    # Export the DataFrame to the SQLite database
    passed_df.to_sql(table_name, engine, if_exists='replace', index=False)

    # create updated library info file
    passed_df.to_csv(PROJECT_DIR / 'lib_info_submitted_to_clarity.csv', index=False)

    return
#########################
#########################

##########################
# MAIN PROGRAM
##########################
PROJECT_DIR = Path.cwd()

ARCHIV_DIR = PROJECT_DIR / "archived_files"

POOL_DIR = PROJECT_DIR / "5_pooling"

CLARITY_DIR = POOL_DIR / "A_make_clarity_aliquot_upload_file"

PLOT_DIR = PROJECT_DIR / "DNA_vs_Density_plots"

# get current date and time, will add to archive database file name
date = datetime.now().strftime("%Y_%m_%d-Time%H-%M-%S")


# create df from updated_redo_fa_analysis_summary.csv file
lib_df = pd.read_csv(CLARITY_DIR / 'final_lib_summary.csv',
                     header=0, converters={'Sample Barcode': str, 'Fraction #': int})

# create df from lib_info.db sqliute file
lb_info_df = readSQLdb()


compareFinalVSlibinfo(lib_df, lb_info_df)


# update df with final plate selection for each lib
passed_df = selectPlateForPooling(lib_df)


# make .xls summary file for upload to Clarity.  This will create good fractions in the Sample Aliquot Queue
makeClaritySummary(passed_df)

# create sqlite database file
createSQLdb(passed_df)



# Create success marker file to indicate script completed successfully
import os
os.makedirs('.workflow_status', exist_ok=True)
with open('.workflow_status/make.clarity.summary.success', 'w') as f:
    f.write('Script completed successfully')
