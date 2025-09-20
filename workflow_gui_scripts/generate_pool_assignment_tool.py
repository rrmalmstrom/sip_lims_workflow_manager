#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# USAGE:

import pandas as pd
import numpy as np
import sys
from datetime import datetime
from pathlib import Path
import openpyxl
import shutil
import os
from sqlalchemy import create_engine



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
    sql_df = pd.read_sql(query, engine)
    
    sql_df['Sample Barcode'] = sql_df['Sample Barcode'].astype('str')
    
    sql_df['Fraction #'] = sql_df['Fraction #'].astype('int')
     
    engine.dispose()

    return sql_df
##########################
##########################


##########################
##########################
def getConstants():
    print('\n')

    # user provides min conc threshold for successful lib creation.
    target_pool_mass = float(
        input("Enter the target pool MASS needed (default 2.75 pmol): ") or 2.75)

    max_conc_vol = float(
        input("Enter the max CONCENTRATED volume used for individual libraries.  Should be <= half lib volume (default = 20uL): ") or 20)

    max_dilut_vol = float(
        input("Enter the max DILUTED volume used for individual libraries.  Should be <= half lib volume (default = 45uL): ") or 45)

    min_tran_vol = float(
        input("Enter the MINIMUM accurate pipet volume of instrument (efault = 2.4uL): ") or 2.4)

    return target_pool_mass, max_conc_vol, max_dilut_vol, min_tran_vol
##########################
##########################


##########################
##########################
def fillPoolingSheet(my_passed_df, target_pool_mass, max_conc_vol, max_dilut_vol, min_tran_vol):
    
    file_path = ASSIGN_DIR / "tmp_BLANK.xlsx"
    
    # workbook = openpyxl.load_workbook(filename="tmp_BLANK.xlsx")
    workbook = openpyxl.load_workbook(filename=file_path)


    poolsheet = workbook['Pooling_tool']

    # make small df of plate id, illumina index set, and number of libs in plate
    x_df = my_passed_df.groupby(['Pool_source_plate', 'Pool_Illumina_index_set'])[
        'Pool_Illumina_index'].agg('count').reset_index()

    x_df.rename(columns={'Pool_Illumina_index': '#_of_libs'}, inplace=True)

    # make each column of x_df into own df, then loop through
    # each row and write to corresponding column in .xslx file
    plate_df = x_df[['Pool_source_plate']].copy()

    for index, row in plate_df.iterrows():
        cell = 'A%d' % (index + 3)
        poolsheet[cell] = row['Pool_source_plate']

    index_df = x_df[['Pool_Illumina_index_set']].copy()

    for index, row in index_df.iterrows():
        cell = 'C%d' % (index + 3)
        poolsheet[cell] = row['Pool_Illumina_index_set']

    count_df = x_df[['#_of_libs']].copy()

    for index, row in count_df.iterrows():
        cell = 'D%d' % (index + 3)
        poolsheet[cell] = row['#_of_libs']

    # add info about individuals to different tab in .xlsx file
    poolsheet['Q2'] = min_tran_vol

    poolsheet['Q4'] = max_conc_vol

    poolsheet['Q6'] = max_dilut_vol

    poolsheet['Q8'] = target_pool_mass


    # save as new .xlsx file for users to manually assign pool numbers
    output_file_path = ASSIGN_DIR / "assign_pool_number_sheet.xlsx"
    workbook.save(filename=output_file_path)
    
    writer = pd.ExcelWriter(output_file_path, engine="openpyxl", mode="a", if_sheet_exists="overlay")
    
    y_df = my_passed_df[['Pool_source_plate', 'Pool_source_well',
                         'Pool_Illumina_index_set', 'Pool_nmole/L', 'Pool_dilution_factor']].copy()

    y_df.to_excel(writer, sheet_name='individual_lib_info',
                  header=True, index=False)

    writer.close()

    return
##########################
##########################


##########################
# MAIN PROGRAM
##########################
PROJECT_DIR = Path.cwd()

ARCHIV_DIR = PROJECT_DIR / "archived_files"

POOL_DIR = PROJECT_DIR / "5_pooling"

ASSIGN_DIR = POOL_DIR / "C_assign_libs_to_pools"

PLOT_DIR = PROJECT_DIR / "DNA_vs_Density_plots"



# make temporary copy of blank pooling tool, and use temp copy for modifications
# this script corrupts the blank .xlsx  file used in functions above
# so I make a copy of original, use temp copy for modification, then delete temp copy
shutil.copy(ASSIGN_DIR / 'BLANK_POOLING_TOOL.xlsx', ASSIGN_DIR / 'tmp_BLANK.xlsx')  # new metatags


# create df from lib_info_submitted_to_clarity.db sqliute file
passed_df = readSQLdb()

# get library and pipetting specs from user
target_pool_mass, max_conc_vol, max_dilut_vol, min_tran_vol = getConstants()


# fill a blank pooling tool .xlsx file with plate, illumina index, and # of libs in each plate
fillPoolingSheet(passed_df, target_pool_mass,
                 max_conc_vol, max_dilut_vol, min_tran_vol)

# delete temporary copy of blank pooling tool .xlsx
os.remove(ASSIGN_DIR / 'tmp_BLANK.xlsx')

# Create success marker file to indicate script completed successfully
import os
os.makedirs('.workflow_status', exist_ok=True)
with open('.workflow_status/generate_pool_assignment_tool.success', 'w') as f:
    f.write('Script completed successfully')
