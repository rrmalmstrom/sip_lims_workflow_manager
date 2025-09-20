#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# USAGE:   python emergency.third.attempt.rework.py 

import pandas as pd
import numpy as np
import sys
import os
import math
import string
from datetime import datetime
from pathlib import Path
from os.path import exists as file_exists
from sqlalchemy import create_engine
import shutil

# Opt-in to future pandas behavior to suppress downcasting warnings
pd.set_option('future.no_silent_downcasting', True)

# define list of destination well positions for a 96-well
well_list_96w = ['A1', 'B1', 'C1', 'D1', 'E1', 'F1', 'G1', 'H1', 'A2', 'B2', 'C2', 'D2', 'E2', 'F2', 'G2', 'H2', 'A3', 'B3', 'C3',
                 'D3', 'E3', 'F3', 'G3', 'H3', 'A4', 'B4', 'C4', 'D4', 'E4', 'F4', 'G4', 'H4', 'A5', 'B5', 'C5', 'D5', 'E5', 'F5', 'G5',
                 'H5', 'A6', 'B6', 'C6', 'D6', 'E6', 'F6', 'G6', 'H6', 'A7', 'B7', 'C7', 'D7', 'E7', 'F7', 'G7', 'H7', 'A8', 'B8', 'C8',
                 'D8', 'E8', 'F8', 'G8', 'H8', 'A9', 'B9', 'C9', 'D9', 'E9', 'F9', 'G9', 'H9', 'A10', 'B10', 'C10', 'D10', 'E10', 'F10', 'G10',
                 'H10', 'A11', 'B11', 'C11', 'D11', 'E11', 'F11', 'G11', 'H11', 'A12', 'B12', 'C12', 'D12', 'E12', 'F12', 'G12', 'H12']

# define list of destination well positions for a 96-well plate with empty corners
well_list_96w_emptycorner = ['B1', 'C1', 'D1', 'E1', 'F1', 'G1', 'A2', 'B2', 'C2', 'D2', 'E2', 'F2', 'G2', 'H2', 'A3', 'B3', 'C3',
                             'D3', 'E3', 'F3', 'G3', 'H3', 'A4', 'B4', 'C4', 'D4', 'E4', 'F4', 'G4', 'H4', 'A5', 'B5', 'C5', 'D5', 'E5', 'F5', 'G5',
                             'H5', 'A6', 'B6', 'C6', 'D6', 'E6', 'F6', 'G6', 'H6', 'A7', 'B7', 'C7', 'D7', 'E7', 'F7', 'G7', 'H7', 'A8', 'B8', 'C8',
                             'D8', 'E8', 'F8', 'G8', 'H8', 'A9', 'B9', 'C9', 'D9', 'E9', 'F9', 'G9', 'H9', 'A10', 'B10', 'C10', 'D10', 'E10', 'F10', 'G10',
                             'H10', 'A11', 'B11', 'C11', 'D11', 'E11', 'F11', 'G11', 'H11', 'B12', 'C12', 'D12', 'E12', 'F12', 'G12']



##########################
##########################
def readSQLdb():

    # # path to sqlite db lib_info.db
    # sql_db_path = f'{my_prjct_dir}/lib_info.db'
    
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
def readSQLProjectdb():
    
    # path to sqlite db lib_info.db
    sql_db_path = PROJECT_DIR /'project_database.db'

    # create sqlalchemy engine
    engine = create_engine(f'sqlite:///{sql_db_path}') 

    # define sql query
    query = "SELECT * FROM project_database"
    
    # import sql db into pandas df
    project_df = pd.read_sql(query, engine)
    
    project_df['ITS_sample_id'] = project_df['ITS_sample_id'].astype('str')
    
    engine.dispose()

    return project_df
##########################
##########################


##########################
##########################
def updateLibInfo(updated_file_name):
    # # create df from fa_analysis_summary.txt file
    # reduced_df = pd.read_csv(sys.argv[1], sep='\t',
    #                          header=0, converters={'Sample Barcode': str, 'Fraction #': int})
    
    # create df from fa_analysis_summary.txt file
    reduced_df = pd.read_csv(updated_file_name, sep='\t',
                             header=0, converters={'Sample Barcode': str, 'Fraction #': int})
    

    # reduced_df['Third_whole_plate'] = reduced_df['Third_whole_plate'].fillna('')

    # lib_df = pd.read_csv(PROJECT_DIR / "lib_info.csv",
    #                      header=0, converters={'Sample Barcode': str, 'Fraction #': int})
    
    # create df from lib_info.db sqliute file
    lib_df = readSQLdb()

    lib_df = lib_df.merge(reduced_df, how='outer', left_on=[
                          'Sample Barcode', 'Fraction #'], right_on=['Sample Barcode', 'Fraction #'], suffixes=('', '_y'))
    
    # update Passed_Library and Redo_Passed_library with manually modified results from updated_*_fa_analysis_summary.txt
    lib_df['Passed_library'] = lib_df['Passed_library_y']
    
    # update the fa dilution factor using value from threshold.txt
    lib_df['Redo_FA_dilution_factor'] = lib_df['Redo_FA_dilution_factor_y']
    

    # remove redundant columns after merging
    lib_df.drop(lib_df.filter(regex='_y$').columns, axis=1, inplace=True)

    # # remove unnecessary columne 'FA_Well'
    # lib_df.drop(['FA_Well'], inplace=True, axis=1)

    # sort df based on sample and fraction number in case user manually
    # changed sorting when generated updated_fa_analysis_summary.txt
    lib_df.sort_values(by=['Sample Barcode', 'Fraction #'], inplace=True)
    
    
    # confirm all samples and fraction numbers in reduced_df
    # matched up with all samples and fraction numbrs in lib_df
    if lib_df['Total_passed_attempts'].isnull().values.any():

        print('\nProblem updating lib_info.csv with pass/fail results from updated_2nd_fa_analysis_summary.txt. Aborting script\n\n')
        sys.exit()
        
        
    elif updated_file_name == FA_DIR / 'updated_2nd_fa_analysis_summary.txt':
        
        lib_df['check_total_pass'] =  lib_df['Total_passed_attempts'] - lib_df.fillna(0)['Passed_library'] - lib_df.fillna(0)['Redo_Passed_library']
        
        # abort script if the total passed attempts count does not match  the  sum of individual pass/fail results for each fraction
        if (lib_df['check_total_pass'] != 0).any():
            
            print('\nTotal_passed_attempts does not equal sum of pass/fail results. Aborting script\n\n')
            sys.exit()
            

    # drop column 'check_total_pass' since it's no longer needed
    lib_df.drop(['check_total_pass'], inplace=True, axis=1)        


    return lib_df
##########################
##########################

##########################
##########################


def addDestplate(my_Third_df, my_plate_num):
    # determine number of lib plates need  by dividing total libs by 92 for empty corner
    # and rounding up to next integer
    num_libplates = math.ceil(my_Third_df.shape[0]/92)

    # reduce my_plate_num by 1 so that incrementing sequence works
    my_plate_num = my_plate_num - 1

    # parse first row entry for "Destination_ID" to get base ID without "-#"
    my_destbc = my_Third_df['Destination_ID'].iloc[0].split("-")[0]

    if num_libplates > 1:
        # loop through number of lib plates (except last plate)
        # assign destination plate and destination wells for set of rows

        for i in range(1, num_libplates):
            if ((i == (num_libplates-1)) & (my_Third_df.shape[0] % 92 < 24)):
                start = (i*92)-92
                stop = start + \
                    divmod((92+(my_Third_df.shape[0] % 92)),  2)[0] - 1
            else:
                start = (i*92)-92
                stop = (i*92)-1

            # add destination plate and well position to last rows of dataframe
            my_Third_df.loc[start:stop,
                           "Destination_ID"] = my_destbc + "-" + str(i+my_plate_num)
            my_Third_df.loc[start:stop, "Destination_Well"] = np.array(
                well_list_96w_emptycorner[0:(stop-start+1)])

        # add destination plate and well position to last rows of dataframe
        start = stop + 1
        my_Third_df.loc[start:my_Third_df.shape[0],
                       "Destination_ID"] = my_destbc + "-" + str(num_libplates+my_plate_num)
        my_Third_df.loc[start:my_Third_df.shape[0], "Destination_Well"] = np.array(
            well_list_96w_emptycorner[0:my_Third_df.shape[0]-start])

    elif num_libplates == 1:
        my_Third_df.loc[0:my_Third_df.shape[0],
                       "Destination_ID"] = my_destbc + "-" + str(num_libplates+my_plate_num)
        my_Third_df.loc[0:my_Third_df.shape[0], "Destination_Well"] = np.array(
            well_list_96w_emptycorner[0:my_Third_df.shape[0]])

    else:
        print('\n\nError.  Problem with number of plates.  Aborting.\n\n')
        sys.exit()

    # parse destination well position into row and col, and convert row to a number
    my_Third_df['Destination_row'] = my_Third_df['Destination_Well'].astype(
        str).str[0]
    my_Third_df['Destination_col'] = my_Third_df['Destination_Well'].astype(
        str).str[1:]

    my_Third_df['Destination_row'] = my_Third_df['Destination_row'].apply(
        lambda x: 1 + string.ascii_uppercase.index(x))

    return my_Third_df

##########################
##########################


##########################
##########################
def getReworkFiles(my_lib_df, my_next_plate_num):

    # ask user for relative size of nextera lib creation reaction
    rxn_size = float(
        input("\n\nEnter the fraction of full nextera reaction (default 0.4): ") or 0.4)

    if ((rxn_size <= 0) | (rxn_size > 1)):
        print('\n\nError.  Fraction must be between 0-1.  Aborting.\n\n')
        sys.exit()

    # this is temporary limitation until I can make different dilution modules for
    # for different reaction sizes
    if rxn_size != 0.4:
        print("\n\nReaction size must be 0.4.  ABORTING script\n\n")
        sys.exit()

    lib_plate_list = my_lib_df['Redo_Destination_ID'].unique().tolist()
    
    lib_plate_list = [x for x in lib_plate_list if str(x) != 'nan']
    
    lib_plate_list = [x for x in lib_plate_list if x is not None]

    # whole_plate_redo = my_lib_df[my_lib_df['Third_whole_plate']
    #                              == True]['Destination_ID'].unique().tolist()

    # # whole_plate_redo = []

    # # for val, cnt in my_lib_df[my_lib_df['Passed_library'] == 0]['Destination_ID'].value_counts().iteritems():
    # #     # for val, cnt in Third_df.Destination_ID.value_counts().iteritems():
    # #     if cnt >= 36:
    # #         whole_plate_redo.append(val)

    # #     else:
    # #         for plate, conc_avg in my_lib_df.groupby(['Destination_ID']).apply(lambda x: x[x['Passed_library'] == 1]["nmole/L"].mean()).iteritems():
    # #             if ((plate == val) and (conc_avg <= 4)):
    # #                 whole_plate_redo.append(plate)

    # # sort the list of whole plates that neede to be reworked
    # whole_plate_redo = sorted(whole_plate_redo)

    # parse first row entry for "Destination_ID" to get base ID without "-#"
    # this get based destination barcode ID
    my_destbc = my_lib_df['Destination_ID'].iloc[0].split("-")[0]

    # # make new df composed only of whole plates that need rework
    # # wp_Third_df = my_lib_df.copy()

    # # wp_Third_df = wp_Third_df[wp_Third_df['Destination_ID'].isin(
    # #     whole_plate_redo)]

    # wp_Third_df = my_lib_df[my_lib_df['Destination_ID'].isin(
    #     whole_plate_redo)].copy()

    # # create empty column
    # wp_Third_df['Third_Destination_ID'] = ""

    # # add new destination plate ID for reworked plates
    # for wp in whole_plate_redo:
    #     wp_Third_df['Third_Destination_ID'].loc[wp_Third_df['Destination_ID']
    #                                           == wp] = my_destbc + "-" + str(my_next_plate_num)
    #     my_next_plate_num = my_next_plate_num + 1

    # wp_Third_df = wp_Third_df[['Plate Barcode', 'Source_row', 'Source_col',
    #                          'Third_Destination_ID', 'Destination_Well', 'Destination_row', 'Destination_col', 'DNA_transfer_vol_(nl)', 'Buffer_transfer_vol_(nl)']]

    # wp_Third_df = wp_Third_df.rename(
    #     columns={"Third_Destination_ID": "Destination_ID"})

    # # get list of plates with libs to redo, but not redoing whole plate
    # part_plate_redo = sorted(set(lib_plate_list) - set(whole_plate_redo))

    # # ## set up new df composed of libs that need rework by cherry picking, i.e. not redoing whole plate
    # pt_Third_df = my_lib_df[(my_lib_df['Destination_ID'].isin(
    #     part_plate_redo)) & (my_lib_df['Redo_Passed_library'] == 0)].copy()
    
    # Only remove whitespace if column contains string values
    if my_lib_df['Emergency_third_attempt'].dtype == 'object' and my_lib_df['Emergency_third_attempt'].astype(str).str.contains(r'\s', na=False).any():
        my_lib_df['Emergency_third_attempt'] = my_lib_df['Emergency_third_attempt'].str.replace(r'\s+', '', regex=True)
    
    my_lib_df = my_lib_df.replace('', np.nan).fillna(0)
    
    my_lib_df['Emergency_third_attempt'] = my_lib_df['Emergency_third_attempt'].fillna(0)
    

    
    my_lib_df['Emergency_third_attempt'] = my_lib_df['Emergency_third_attempt'].astype(int)
    
    # ## set up new df composed of libs that need rework by cherry picking, i.e. not redoing whole plate
    pt_Third_df = my_lib_df[(my_lib_df['Redo_Destination_ID'].isin(
        lib_plate_list)) & (my_lib_df['Emergency_third_attempt'] == 1)].copy()


    # make new column with original indexs.  This will be used later to merge back with the whole lib_df
    pt_Third_df['original_index'] = pt_Third_df.index

    # reset the index of df, this is necessary to add destination id's and well positions
    pt_Third_df = pt_Third_df.reset_index()

    # reduce number of column in df
    pt_Third_df = pt_Third_df[['original_index', 'Plate Barcode', 'Source_row', 'Source_col',
                             'Destination_ID', 'DNA_transfer_vol_(nl)', 'Buffer_transfer_vol_(nl)']]

    # call subroutine to add destination plate ID and desitination well/row/col
    pt_Third_df = addDestplate(pt_Third_df, my_next_plate_num)

    # go back to original index so that this df can be merged with whole lib_df using index
    pt_Third_df.set_index('original_index', inplace=True)

    pt_Third_df = pt_Third_df[['Plate Barcode', 'Source_row', 'Source_col',
                             'Destination_ID', 'Destination_Well', 'Destination_row', 'Destination_col', 'DNA_transfer_vol_(nl)', 'Buffer_transfer_vol_(nl)']]

    # combo_Third_df = pd.concat([wp_Third_df, pt_Third_df])
    
    combo_Third_df = pt_Third_df.copy()
    
    # add reaction size to dataframe
    combo_Third_df['Third_Lib_rxn_size(X)'] = rxn_size

    # set DNA transfer to max volume
    combo_Third_df['DNA_transfer_vol_(nl)'] = 5000 * rxn_size

    # set Buffer transfer to 0
    combo_Third_df['Buffer_transfer_vol_(nl)'] = 0

    return combo_Third_df, rxn_size

##########################
##########################


#########################
#########################
def addIlluminaIndex(my_import_df, lib_df):

    # adapt_set_5 = ['5A01i7-7A01i5',	'5B01i7-7B01i5',	'5C01i7-7C01i5',	'5D01i7-7D01i5',	'5E01i7-7E01i5',	'5F01i7-7F01i5',	'5G01i7-7G01i5',	'5H01i7-7H01i5',	'5A02i7-7A02i5',	'5B02i7-7B02i5',	'5C02i7-7C02i5',	'5D02i7-7D02i5',	'5E02i7-7E02i5',	'5F02i7-7F02i5',	'5G02i7-7G02i5',	'5H02i7-7H02i5',	'5A03i7-7A03i5',	'5B03i7-7B03i5',	'5C03i7-7C03i5',	'5D03i7-7D03i5',	'5E03i7-7E03i5',	'5F03i7-7F03i5',	'5G03i7-7G03i5',	'5H03i7-7H03i5',	'5A04i7-7A04i5',	'5B04i7-7B04i5',	'5C04i7-7C04i5',	'5D04i7-7D04i5',	'5E04i7-7E04i5',	'5F04i7-7F04i5',	'5G04i7-7G04i5',	'5H04i7-7H04i5',	'5A05i7-7A05i5',	'5B05i7-7B05i5',	'5C05i7-7C05i5',	'5D05i7-7D05i5',	'5E05i7-7E05i5',	'5F05i7-7F05i5',	'5G05i7-7G05i5',	'5H05i7-7H05i5',	'5A06i7-7A06i5',	'5B06i7-7B06i5',	'5C06i7-7C06i5',	'5D06i7-7D06i5',	'5E06i7-7E06i5',	'5F06i7-7F06i5',	'5G06i7-7G06i5',	'5H06i7-7H06i5',
    #                '5A07i7-7A07i5',	'5B07i7-7B07i5',	'5C07i7-7C07i5',	'5D07i7-7D07i5',	'5E07i7-7E07i5',	'5F07i7-7F07i5',	'5G07i7-7G07i5',	'5H07i7-7H07i5',	'5A08i7-7A08i5',	'5B08i7-7B08i5',	'5C08i7-7C08i5',	'5D08i7-7D08i5',	'5E08i7-7E08i5',	'5F08i7-7F08i5',	'5G08i7-7G08i5',	'5H08i7-7H08i5',	'5A09i7-7A09i5',	'5B09i7-7B09i5',	'5C09i7-7C09i5',	'5D09i7-7D09i5',	'5E09i7-7E09i5',	'5F09i7-7F09i5',	'5G09i7-7G09i5',	'5H09i7-7H09i5',	'5A10i7-7A10i5',	'5B10i7-7B10i5',	'5C10i7-7C10i5',	'5D10i7-7D10i5',	'5E10i7-7E10i5',	'5F10i7-7F10i5',	'5G10i7-7G10i5',	'5H10i7-7H10i5',	'5A11i7-7A11i5',	'5B11i7-7B11i5',	'5C11i7-7C11i5',	'5D11i7-7D11i5',	'5E11i7-7E11i5',	'5F11i7-7F11i5',	'5G11i7-7G11i5',	'5H11i7-7H11i5',	'5A12i7-7A12i5',	'5B12i7-7B12i5',	'5C12i7-7C12i5',	'5D12i7-7D12i5',	'5E12i7-7E12i5',	'5F12i7-7F12i5',	'5G12i7-7G12i5',	'5H12i7-7H12i5']

    # adapt_set_6 = ['6A01i7-8A01i5',	'6B01i7-8B01i5',	'6C01i7-8C01i5',	'6D01i7-8D01i5',	'6E01i7-8E01i5',	'6F01i7-8F01i5',	'6G01i7-8G01i5',	'6H01i7-8H01i5',	'6A02i7-8A02i5',	'6B02i7-8B02i5',	'6C02i7-8C02i5',	'6D02i7-8D02i5',	'6E02i7-8E02i5',	'6F02i7-8F02i5',	'6G02i7-8G02i5',	'6H02i7-8H02i5',	'6A03i7-8A03i5',	'6B03i7-8B03i5',	'6C03i7-8C03i5',	'6D03i7-8D03i5',	'6E03i7-8E03i5',	'6F03i7-8F03i5',	'6G03i7-8G03i5',	'6H03i7-8H03i5',	'6A04i7-8A04i5',	'6B04i7-8B04i5',	'6C04i7-8C04i5',	'6D04i7-8D04i5',	'6E04i7-8E04i5',	'6F04i7-8F04i5',	'6G04i7-8G04i5',	'6H04i7-8H04i5',	'6A05i7-8A05i5',	'6B05i7-8B05i5',	'6C05i7-8C05i5',	'6D05i7-8D05i5',	'6E05i7-8E05i5',	'6F05i7-8F05i5',	'6G05i7-8G05i5',	'6H05i7-8H05i5',	'6A06i7-8A06i5',	'6B06i7-8B06i5',	'6C06i7-8C06i5',	'6D06i7-8D06i5',	'6E06i7-8E06i5',	'6F06i7-8F06i5',	'6G06i7-8G06i5',	'6H06i7-8H06i5',
    #                '6A07i7-8A07i5',	'6B07i7-8B07i5',	'6C07i7-8C07i5',	'6D07i7-8D07i5',	'6E07i7-8E07i5',	'6F07i7-8F07i5',	'6G07i7-8G07i5',	'6H07i7-8H07i5',	'6A08i7-8A08i5',	'6B08i7-8B08i5',	'6C08i7-8C08i5',	'6D08i7-8D08i5',	'6E08i7-8E08i5',	'6F08i7-8F08i5',	'6G08i7-8G08i5',	'6H08i7-8H08i5',	'6A09i7-8A09i5',	'6B09i7-8B09i5',	'6C09i7-8C09i5',	'6D09i7-8D09i5',	'6E09i7-8E09i5',	'6F09i7-8F09i5',	'6G09i7-8G09i5',	'6H09i7-8H09i5',	'6A10i7-8A10i5',	'6B10i7-8B10i5',	'6C10i7-8C10i5',	'6D10i7-8D10i5',	'6E10i7-8E10i5',	'6F10i7-8F10i5',	'6G10i7-8G10i5',	'6H10i7-8H10i5',	'6A11i7-8A11i5',	'6B11i7-8B11i5',	'6C11i7-8C11i5',	'6D11i7-8D11i5',	'6E11i7-8E11i5',	'6F11i7-8F11i5',	'6G11i7-8G11i5',	'6H11i7-8H11i5',	'6A12i7-8A12i5',	'6B12i7-8B12i5',	'6C12i7-8C12i5',	'6D12i7-8D12i5',	'6E12i7-8E12i5',	'6F12i7-8F12i5',	'6G12i7-8G12i5',	'6H12i7-8H12i5']

    # adapt_set_7 = ['7A01i7-5A01i5',	'7B01i7-5B01i5',	'7C01i7-5C01i5',	'7D01i7-5D01i5',	'7E01i7-5E01i5',	'7F01i7-5F01i5',	'7G01i7-5G01i5',	'7H01i7-5H01i5',	'7A02i7-5A02i5',	'7B02i7-5B02i5',	'7C02i7-5C02i5',	'7D02i7-5D02i5',	'7E02i7-5E02i5',	'7F02i7-5F02i5',	'7G02i7-5G02i5',	'7H02i7-5H02i5',	'7A03i7-5A03i5',	'7B03i7-5B03i5',	'7C03i7-5C03i5',	'7D03i7-5D03i5',	'7E03i7-5E03i5',	'7F03i7-5F03i5',	'7G03i7-5G03i5',	'7H03i7-5H03i5',	'7A04i7-5A04i5',	'7B04i7-5B04i5',	'7C04i7-5C04i5',	'7D04i7-5D04i5',	'7E04i7-5E04i5',	'7F04i7-5F04i5',	'7G04i7-5G04i5',	'7H04i7-5H04i5',	'7A05i7-5A05i5',	'7B05i7-5B05i5',	'7C05i7-5C05i5',	'7D05i7-5D05i5',	'7E05i7-5E05i5',	'7F05i7-5F05i5',	'7G05i7-5G05i5',	'7H05i7-5H05i5',	'7A06i7-5A06i5',	'7B06i7-5B06i5',	'7C06i7-5C06i5',	'7D06i7-5D06i5',	'7E06i7-5E06i5',	'7F06i7-5F06i5',	'7G06i7-5G06i5',	'7H06i7-5H06i5',
    #                '7A07i7-5A07i5',	'7B07i7-5B07i5',	'7C07i7-5C07i5',	'7D07i7-5D07i5',	'7E07i7-5E07i5',	'7F07i7-5F07i5',	'7G07i7-5G07i5',	'7H07i7-5H07i5',	'7A08i7-5A08i5',	'7B08i7-5B08i5',	'7C08i7-5C08i5',	'7D08i7-5D08i5',	'7E08i7-5E08i5',	'7F08i7-5F08i5',	'7G08i7-5G08i5',	'7H08i7-5H08i5',	'7A09i7-5A09i5',	'7B09i7-5B09i5',	'7C09i7-5C09i5',	'7D09i7-5D09i5',	'7E09i7-5E09i5',	'7F09i7-5F09i5',	'7G09i7-5G09i5',	'7H09i7-5H09i5',	'7A10i7-5A10i5',	'7B10i7-5B10i5',	'7C10i7-5C10i5',	'7D10i7-5D10i5',	'7E10i7-5E10i5',	'7F10i7-5F10i5',	'7G10i7-5G10i5',	'7H10i7-5H10i5',	'7A11i7-5A11i5',	'7B11i7-5B11i5',	'7C11i7-5C11i5',	'7D11i7-5D11i5',	'7E11i7-5E11i5',	'7F11i7-5F11i5',	'7G11i7-5G11i5',	'7H11i7-5H11i5',	'7A12i7-5A12i5',	'7B12i7-5B12i5',	'7C12i7-5C12i5',	'7D12i7-5D12i5',	'7E12i7-5E12i5',	'7F12i7-5F12i5',	'7G12i7-5G12i5',	'7H12i7-5H12i5']

    # adapt_set_8 = ['8A01i7-6A01i5',	'8B01i7-6B01i5',	'8C01i7-6C01i5',	'8D01i7-6D01i5',	'8E01i7-6E01i5',	'8F01i7-6F01i5',	'8G01i7-6G01i5',	'8H01i7-6H01i5',	'8A02i7-6A02i5',	'8B02i7-6B02i5',	'8C02i7-6C02i5',	'8D02i7-6D02i5',	'8E02i7-6E02i5',	'8F02i7-6F02i5',	'8G02i7-6G02i5',	'8H02i7-6H02i5',	'8A03i7-6A03i5',	'8B03i7-6B03i5',	'8C03i7-6C03i5',	'8D03i7-6D03i5',	'8E03i7-6E03i5',	'8F03i7-6F03i5',	'8G03i7-6G03i5',	'8H03i7-6H03i5',	'8A04i7-6A04i5',	'8B04i7-6B04i5',	'8C04i7-6C04i5',	'8D04i7-6D04i5',	'8E04i7-6E04i5',	'8F04i7-6F04i5',	'8G04i7-6G04i5',	'8H04i7-6H04i5',	'8A05i7-6A05i5',	'8B05i7-6B05i5',	'8C05i7-6C05i5',	'8D05i7-6D05i5',	'8E05i7-6E05i5',	'8F05i7-6F05i5',	'8G05i7-6G05i5',	'8H05i7-6H05i5',	'8A06i7-6A06i5',	'8B06i7-6B06i5',	'8C06i7-6C06i5',	'8D06i7-6D06i5',	'8E06i7-6E06i5',	'8F06i7-6F06i5',	'8G06i7-6G06i5',	'8H06i7-6H06i5',
    #                '8A07i7-6A07i5',	'8B07i7-6B07i5',	'8C07i7-6C07i5',	'8D07i7-6D07i5',	'8E07i7-6E07i5',	'8F07i7-6F07i5',	'8G07i7-6G07i5',	'8H07i7-6H07i5',	'8A08i7-6A08i5',	'8B08i7-6B08i5',	'8C08i7-6C08i5',	'8D08i7-6D08i5',	'8E08i7-6E08i5',	'8F08i7-6F08i5',	'8G08i7-6G08i5',	'8H08i7-6H08i5',	'8A09i7-6A09i5',	'8B09i7-6B09i5',	'8C09i7-6C09i5',	'8D09i7-6D09i5',	'8E09i7-6E09i5',	'8F09i7-6F09i5',	'8G09i7-6G09i5',	'8H09i7-6H09i5',	'8A10i7-6A10i5',	'8B10i7-6B10i5',	'8C10i7-6C10i5',	'8D10i7-6D10i5',	'8E10i7-6E10i5',	'8F10i7-6F10i5',	'8G10i7-6G10i5',	'8H10i7-6H10i5',	'8A11i7-6A11i5',	'8B11i7-6B11i5',	'8C11i7-6C11i5',	'8D11i7-6D11i5',	'8E11i7-6E11i5',	'8F11i7-6F11i5',	'8G11i7-6G11i5',	'8H11i7-6H11i5',	'8A12i7-6A12i5',	'8B12i7-6B12i5',	'8C12i7-6C12i5',	'8D12i7-6D12i5',	'8E12i7-6E12i5',	'8F12i7-6F12i5',	'8G12i7-6G12i5',	'8H12i7-6H12i5']


    adapt_set_PE17 = ['PE17_A01','PE17_B01','PE17_C01','PE17_D01','PE17_E01','PE17_F01','PE17_G01','PE17_H01','PE17_A02','PE17_B02','PE17_C02','PE17_D02','PE17_E02','PE17_F02','PE17_G02','PE17_H02','PE17_A03','PE17_B03','PE17_C03','PE17_D03','PE17_E03','PE17_F03','PE17_G03','PE17_H03','PE17_A04','PE17_B04','PE17_C04','PE17_D04','PE17_E04','PE17_F04','PE17_G04','PE17_H04','PE17_A05','PE17_B05','PE17_C05','PE17_D05','PE17_E05','PE17_F05','PE17_G05','PE17_H05','PE17_A06','PE17_B06','PE17_C06','PE17_D06','PE17_E06','PE17_F06','PE17_G06','PE17_H06','PE17_A07','PE17_B07','PE17_C07','PE17_D07','PE17_E07','PE17_F07','PE17_G07','PE17_H07','PE17_A08','PE17_B08','PE17_C08','PE17_D08','PE17_E08','PE17_F08','PE17_G08','PE17_H08','PE17_A09','PE17_B09','PE17_C09','PE17_D09','PE17_E09','PE17_F09','PE17_G09','PE17_H09','PE17_A10','PE17_B10','PE17_C10','PE17_D10','PE17_E10','PE17_F10','PE17_G10','PE17_H10','PE17_A11','PE17_B11','PE17_C11','PE17_D11','PE17_E11','PE17_F11','PE17_G11','PE17_H11','PE17_A12','PE17_B12','PE17_C12','PE17_D12','PE17_E12','PE17_F12','PE17_G12','PE17_H12']

    adapt_set_PE18 = ['PE18_A01','PE18_B01','PE18_C01','PE18_D01','PE18_E01','PE18_F01','PE18_G01','PE18_H01','PE18_A02','PE18_B02','PE18_C02','PE18_D02','PE18_E02','PE18_F02','PE18_G02','PE18_H02','PE18_A03','PE18_B03','PE18_C03','PE18_D03','PE18_E03','PE18_F03','PE18_G03','PE18_H03','PE18_A04','PE18_B04','PE18_C04','PE18_D04','PE18_E04','PE18_F04','PE18_G04','PE18_H04','PE18_A05','PE18_B05','PE18_C05','PE18_D05','PE18_E05','PE18_F05','PE18_G05','PE18_H05','PE18_A06','PE18_B06','PE18_C06','PE18_D06','PE18_E06','PE18_F06','PE18_G06','PE18_H06','PE18_A07','PE18_B07','PE18_C07','PE18_D07','PE18_E07','PE18_F07','PE18_G07','PE18_H07','PE18_A08','PE18_B08','PE18_C08','PE18_D08','PE18_E08','PE18_F08','PE18_G08','PE18_H08','PE18_A09','PE18_B09','PE18_C09','PE18_D09','PE18_E09','PE18_F09','PE18_G09','PE18_H09','PE18_A10','PE18_B10','PE18_C10','PE18_D10','PE18_E10','PE18_F10','PE18_G10','PE18_H10','PE18_A11','PE18_B11','PE18_C11','PE18_D11','PE18_E11','PE18_F11','PE18_G11','PE18_H11','PE18_A12','PE18_B12','PE18_C12','PE18_D12','PE18_E12','PE18_F12','PE18_G12','PE18_H12']
    
    adapt_set_PE19 = ['PE19_A01','PE19_B01','PE19_C01','PE19_D01','PE19_E01','PE19_F01','PE19_G01','PE19_H01','PE19_A02','PE19_B02','PE19_C02','PE19_D02','PE19_E02','PE19_F02','PE19_G02','PE19_H02','PE19_A03','PE19_B03','PE19_C03','PE19_D03','PE19_E03','PE19_F03','PE19_G03','PE19_H03','PE19_A04','PE19_B04','PE19_C04','PE19_D04','PE19_E04','PE19_F04','PE19_G04','PE19_H04','PE19_A05','PE19_B05','PE19_C05','PE19_D05','PE19_E05','PE19_F05','PE19_G05','PE19_H05','PE19_A06','PE19_B06','PE19_C06','PE19_D06','PE19_E06','PE19_F06','PE19_G06','PE19_H06','PE19_A07','PE19_B07','PE19_C07','PE19_D07','PE19_E07','PE19_F07','PE19_G07','PE19_H07','PE19_A08','PE19_B08','PE19_C08','PE19_D08','PE19_E08','PE19_F08','PE19_G08','PE19_H08','PE19_A09','PE19_B09','PE19_C09','PE19_D09','PE19_E09','PE19_F09','PE19_G09','PE19_H09','PE19_A10','PE19_B10','PE19_C10','PE19_D10','PE19_E10','PE19_F10','PE19_G10','PE19_H10','PE19_A11','PE19_B11','PE19_C11','PE19_D11','PE19_E11','PE19_F11','PE19_G11','PE19_H11','PE19_A12','PE19_B12','PE19_C12','PE19_D12','PE19_E12','PE19_F12','PE19_G12','PE19_H12']
    
    adapt_set_PE20 = ['PE20_A01','PE20_B01','PE20_C01','PE20_D01','PE20_E01','PE20_F01','PE20_G01','PE20_H01','PE20_A02','PE20_B02','PE20_C02','PE20_D02','PE20_E02','PE20_F02','PE20_G02','PE20_H02','PE20_A03','PE20_B03','PE20_C03','PE20_D03','PE20_E03','PE20_F03','PE20_G03','PE20_H03','PE20_A04','PE20_B04','PE20_C04','PE20_D04','PE20_E04','PE20_F04','PE20_G04','PE20_H04','PE20_A05','PE20_B05','PE20_C05','PE20_D05','PE20_E05','PE20_F05','PE20_G05','PE20_H05','PE20_A06','PE20_B06','PE20_C06','PE20_D06','PE20_E06','PE20_F06','PE20_G06','PE20_H06','PE20_A07','PE20_B07','PE20_C07','PE20_D07','PE20_E07','PE20_F07','PE20_G07','PE20_H07','PE20_A08','PE20_B08','PE20_C08','PE20_D08','PE20_E08','PE20_F08','PE20_G08','PE20_H08','PE20_A09','PE20_B09','PE20_C09','PE20_D09','PE20_E09','PE20_F09','PE20_G09','PE20_H09','PE20_A10','PE20_B10','PE20_C10','PE20_D10','PE20_E10','PE20_F10','PE20_G10','PE20_H10','PE20_A11','PE20_B11','PE20_C11','PE20_D11','PE20_E11','PE20_F11','PE20_G11','PE20_H11','PE20_A12','PE20_B12','PE20_C12','PE20_D12','PE20_E12','PE20_F12','PE20_G12','PE20_H12']
    
    

    # # creat dict where key is index set# + well postion, and values is illumin index ID
    # dict_index = dict(zip(['5' + w for w in well_list_96w], adapt_set_5)
    #                   ) | dict(zip(['6' + w for w in well_list_96w], adapt_set_6)) | dict(zip(['7' + w for w in well_list_96w], adapt_set_7)) | dict(zip(['8' + w for w in well_list_96w], adapt_set_8))

    # creat dict where key is index set# + well postion, and values is illumin index ID
    dict_index = dict(zip(['PE17' + w for w in well_list_96w], adapt_set_PE17)
                        ) | dict(zip(['PE18' + w for w in well_list_96w], adapt_set_PE18)) | dict(zip(['PE19' + w for w in well_list_96w], adapt_set_PE19)) | dict(zip(['PE20' + w for w in well_list_96w], adapt_set_PE20))


    # # create list of illumin index set numbers
    # ill_sets = ['6', '7', '8','5']
    
    # create list of illumin index set numbers
    ill_sets = ['PE17', 'PE18', 'PE19','PE20']

    # create empty dict that will eventually hold destination plate as key
    # and illumina index set as value
    dest_id_dict = {}

    # get list of new unique destination plate IDs for rework
    tmp_list = sorted(my_import_df['Destination_ID'].unique().tolist())
    
    # create dict where key is destination plate name from the second round of lib creation
    # and value is Illumina index set used
    dest_set_dict = dict(zip(lib_df['Redo_Destination_ID'],lib_df['Redo_Illumina_index_set']))
    
    # find the index set used in the last destination plate from the second round of lib creation
    # that is, the value in the last key of the dest_set_dict
    last_set = dest_set_dict[list(dest_set_dict)[-1]]
    
    # determine the next set of illumina indexes to use on the first rework plate
    # by finding the element position in ill_set of last set and adding 1 to element position
    next_set_num = 1 + ill_sets.index(last_set)
    
    # ## create dict were keys are destination plate IDs and values are illumin index set#
    # # the modulo is used because the number of destination plates might exceed the number
    # # of index sets, so the module wraps around ill_set list
    # # also use cnt+next_plate_num-1 so that the first illumina index used fo rework
    # # is the next in the list after last index used in first attempt at lib creation
    # for cnt, dp in enumerate(tmp_list):
    #     id_set = str(ill_sets[(cnt+next_plate_num-1) % len(ill_sets)])
    #     dest_id_dict[dp] = id_set
    
    ## create dict were keys are destination plate IDs and values are illumin index set#
    # the modulo is used because the number of destination plates might exceed the number
    # of index sets, so the module wraps around ill_set list
    # also use next_set_num so that the first illumina index used fo rework
    # is the next in the list after last index used in first attempt at lib creation
    for cnt, dp in enumerate(tmp_list):
        id_set = str(ill_sets[(cnt+next_set_num) % len(ill_sets)])
        dest_id_dict[dp] = id_set
        
        
    # add new column with illumina set # based on Destination ID by looking up in dict
    my_import_df['Illumina_index_set'] = my_import_df['Destination_ID'].replace(
        dest_id_dict)

    # add new row that's a concat of the illumina index set and well postion
    my_import_df['Illumina_index'] = my_import_df['Illumina_index_set'] + \
        my_import_df['Destination_Well']

    # replace index set and well poistion wiht JGI illumina index ID using dict
    my_import_df['Illumina_index'] = my_import_df['Illumina_index'].replace(
        dict_index)

    # # add new row that's a concat of the illumina index set and well postion
    # my_import_df['Illumina_index_set'] = 'Nextera_Index-' + \
    #     my_import_df['Illumina_index_set']
    

    return my_import_df

#########################
#########################


##########################
##########################


def makeEchoFiles(my_rework_df):

    # create two copies of subsets of import_df
    dna_df = my_rework_df[['Plate Barcode', 'Source_row', 'Source_col',
                           'Destination_ID', 'Destination_row', 'Destination_col', 'DNA_transfer_vol_(nl)']].copy()
    buffer_df = my_rework_df[['Plate Barcode', 'Source_row', 'Source_col',
                              'Destination_ID', 'Destination_row', 'Destination_col', 'Buffer_transfer_vol_(nl)']].copy()

    # rename transfer volume headers
    dna_df = dna_df.rename(columns={"Plate Barcode": "Source_ID",
                                    "DNA_transfer_vol_(nl)": "Transfer_vol_(nl)"})
    buffer_df = buffer_df.rename(
        columns={"Plate Barcode": "Source_ID", "Buffer_transfer_vol_(nl)": "Transfer_vol_(nl)"})

    # add "buffer" as source plate id
    buffer_df['Source_ID'] = 'Buffer'

    # add "e" to source plate ID because echo plates have "e" as prefix  to plate ID
    dna_df['Source_ID'] = 'e' + dna_df['Source_ID']

    # combine two dna_ and buffer_df into new df
    echo_df = pd.concat([dna_df, buffer_df], ignore_index=True)

    # add new column to help sorting rows so that buffer rows are always
    # the first rows in the df and echo transfer file
    echo_df['sorter'] = np.where(
        (echo_df['Source_ID'] == 'Buffer'), 1, 2)

    # convert row and column values to integers to aid in df sorting
    echo_df['Destination_col'] = echo_df['Destination_col'].astype(int)
    echo_df['Destination_row'] = echo_df['Destination_row'].astype(int)

    # # sort dataframe
    # echo_df.sort_values(by=['Destination_ID', 'sorter', 'Source_ID',
    #                           'Destination_col', 'Destination_row'], inplace=True)

    # sort dataframe
    echo_df.sort_values(by=['Destination_ID', 'sorter',
                            'Destination_col', 'Destination_row'], inplace=True)

    # rename columns to match echo software expected format
    echo_df = echo_df.rename(
        columns={"Source_ID": "Source Plate Name",
                 "Source_row": "Source Row",
                 "Source_col": "Source Column",
                 "Destination_ID": "Destination Plate Name",
                 "Destination_row": "Destination Row",
                 "Destination_col": "Destination Column",
                 "Transfer_vol_(nl)": "Transfer Volume"})

    # add column with plate barcodes, which is same as plate name, to meet echo expectations
    echo_df['Source Plate Barcode'] = echo_df['Source Plate Name']
    echo_df['Destination Plate Barcode'] = echo_df['Destination Plate Name']

    # rearrange columns into final order
    echo_df = echo_df[['Source Plate Name',	'Source Plate Barcode',	'Source Row',	'Source Column',
                       'Destination Plate Name',	'Destination Plate Barcode',	'Destination Row',	'Destination Column',	'Transfer Volume']]

    dest_list = echo_df['Destination Plate Barcode'].unique().tolist()

    # create echo transfer files
    for d in dest_list:
        tmp_df = echo_df.loc[echo_df['Destination Plate Barcode'] == d].copy()

        # create echo transfer file
        tmp_df.to_csv(ECHO_DIR /
                      f'Third_echo_transfer_{d}.csv', index=False)

    return echo_df, dest_list
##########################
##########################


##########################
##########################
def makeBarcodeFils(my_dest_list):
    
    my_dest_list.sort(reverse=True)
    
    # this was older format for bartender templates.  The newer version below changes "/" to "\"
    # in the path to the template files  AF="*"
    # x = '%BTW% /AF="//BARTENDER/shared/templates/ECHO_BCode8.btw" /D="%Trigger File Name%" /PRN="bcode8" /R=3 /P /DD\r\n\r\n%END%\r\n\r\n\r\n'

    # add info to start of barcode print file indicating the template and printer to use
    x = '%BTW% /AF="\\\BARTENDER\shared\\templates\ECHO_BCode8.btw" /D="%Trigger File Name%" /PRN="bcode8" /R=3 /P /DD\r\n\r\n%END%\r\n\r\n\r\n'


    bc_file = open(THIRD_ATMPT_DIR / "echo_barcode.txt", "w")

    bc_file.writelines(x)

    # add barcodes of library destination plates, dna source plates, and buffer plate

    for p in my_dest_list:
        bc_file.writelines(f'{p}F,"third.FA.run {p}F"\r\n')

    for p in my_dest_list:
        bc_file.writelines(f'{p}D,"third.FA.dilute {p}D"\r\n')

    for p in my_dest_list:      
        bc_file.writelines(f'h{p},"    h{p}"\r\n')
        bc_file.writelines(f'{p},"third.SIP.lib {p}"\r\n')


    bc_file.writelines('Buffer,"Buffer.plate"\r\n')

    bc_file.close()

    return
##########################
##########################


#########################
#########################
def createIllumDataframe(rework_df, rxn_size):

    illum_df = rework_df[['Destination_ID',
                          'Destination_Well', 'Illumina_index_set']].copy()

    # adjuste volume of primer addition based on tagementation reactions size
    illum_df['Primer_volume_(uL)'] = 10*rxn_size

    illum_df['Illumina_source_well'] = illum_df['Destination_Well']

    illum_df = illum_df.rename(
        columns={'Destination_Well': 'Lib_plate_well', 'Destination_ID': 'Lib_plate_ID'})

    # rearrange column order
    illum_column_list = ['Illumina_index_set',
                         'Illumina_source_well', 'Lib_plate_ID', 'Lib_plate_well', 'Primer_volume_(uL)']

    illum_df = illum_df.reindex(columns=illum_column_list)

    return illum_df
#########################
#########################


#########################
#########################
def makeDilution(rework_df):
    dilution_df = rework_df[['Destination_ID',
                             'Destination_Well', 'Third_Lib_rxn_size(X)']].copy()

    dilution_df['Library_Plate_Barcode'] = dilution_df['Destination_ID']
    dilution_df['Dilution_Plate_Barcode'] = dilution_df['Destination_ID']+"D"
    dilution_df['FA_Plate_Barcode'] = dilution_df['Destination_ID']+"F"
    dilution_df['Library_Well'] = dilution_df['Destination_Well']

    dilution_df['Nextera_Vol_Add'] = np.where(
        dilution_df['Third_Lib_rxn_size(X)'] == 0.4, 30, np.nan)
    dilution_df['Dilution_Vol'] = np.where(
        dilution_df['Third_Lib_rxn_size(X)'] == 0.4, 5, np.nan)
    dilution_df['FA_Vol_Add'] = np.where(
        dilution_df['Third_Lib_rxn_size(X)'] == 0.4, 2.4, np.nan)
    dilution_df['Dilution_Plate_Preload'] = np.where(
        dilution_df['Third_Lib_rxn_size(X)'] == 0.4, 125, np.nan)

    # drop unecessary columns
    dilution_df.drop(['Destination_ID',
                      'Destination_Well', 'Third_Lib_rxn_size(X)'], inplace=True, axis=1)

    # Library_Plate_Barcode,Dilution_Plate_Barcode,FA_Plate_Barcode,Library_Well, Nextera_Vol_Add, Dilution_Vol_Add, FA_Vol_Add, Dilution_Plate_Preload

    # calculate the dilution factor used to make the FA plate
    rework_df['Third_FA_dilution_factor'] = (dilution_df['Dilution_Plate_Preload'] +
                                            dilution_df['Dilution_Vol']-dilution_df['Nextera_Vol_Add'])/dilution_df['Dilution_Vol']

    return dilution_df, rework_df
#########################
#########################


#########################
#########################
def makeIlluminaFiles(illum_df, dest_list):
    # create illumin index transfer files
    for d in dest_list:
        tmp_illum_df = illum_df.loc[illum_df['Lib_plate_ID'] == d].copy()

        # add "h" prefix to lib plate ID because barcode label on plate side read by
        # hamilton scanner has "h" prefix
        tmp_illum_df['Lib_plate_ID'] = "h" + \
            tmp_illum_df['Lib_plate_ID'].astype(str)

        # create echo transfer file
        tmp_illum_df.to_csv(ILLUMINA_DIR /
                            f'Illumina_index_transfer_{d}.csv', index=False)

#########################
#########################


#########################
#########################
def makeDilutionFile(dilution_df, dest_list):
    # create echo transfer files
    for d in dest_list:
        tmp_df = dilution_df.loc[dilution_df['Library_Plate_Barcode'] == d].copy(
        )

        # had "h" prefix to library plate for reading barcode on Hamilton Star
        tmp_df['Library_Plate_Barcode'] = 'h'+tmp_df['Library_Plate_Barcode']

        # create echo transfer file
        tmp_df.to_csv(DILUTE_DIR /
                      f'dilution_plate_transfer_{d}.csv', index=False)

    return
#########################
#########################


#########################
#########################
def makeThreshold(rework_df):

    # make df with only unique destination ids and the ave dilution factor per plate
    thresh_df = rework_df.groupby(['Destination_ID'], as_index=False)[
        'Third_FA_dilution_factor'].mean().round(0)

    thresh_df = thresh_df.rename(columns={
                                 'Destination_ID': 'Destination_plate', 'Third_FA_dilution_factor': 'dilution_factor'})

    # add blan column
    thresh_df['DNA_conc_threshold_(nmol/L)'] = ""

    # add minimum library size to be used in FA analysis thresholds later
    thresh_df['Size_theshold_(bp)'] = 530

    # make list of column  headers to rearrange by column
    thresh_col_list = ['Destination_plate',
                       'DNA_conc_threshold_(nmol/L)', 'Size_theshold_(bp)', 'dilution_factor']

    thresh_df = thresh_df.reindex(columns=thresh_col_list)

    # create thresholds.txt file for use in later FA analysis
    thresh_df.to_csv(THIRD_FA_DIR / 'thresholds.txt', index=False, sep='\t')

    return
#########################
#########################


##########################
##########################

def makeFAinputFiles(my_update_lib_df, my_dest_list, my_well_list):
    FA_df = my_update_lib_df[['Third_Destination_Well',
                              'Third_Destination_ID', 'Sample Barcode', 'Fraction #']].copy()

    FA_df['Third_Destination_ID'] = FA_df['Third_Destination_ID'].astype(str)

    FA_df['Fraction #'] = FA_df['Fraction #'].astype(str)

    FA_df['Sample Barcode'] = FA_df['Sample Barcode'].astype(str)

    FA_df['name'] = FA_df[['Third_Destination_ID', 'Sample Barcode', 'Fraction #']].agg(
        '_'.join, axis=1)

    # drop unecessary columns so only have df with 'Destination_Well', 'Destination_ID', and 'name'
    FA_df.drop(['Sample Barcode', 'Fraction #'], inplace=True, axis=1)

    # create FA upload files
    for d in my_dest_list:
        # tmp_fa_df = FA_df.loc[FA_df['Destination_ID'] == d].copy()

        # # find unused wells, e.g. corner wells, in FA plate
        # empty_wells = set(well_list) - set(tmp_fa_df['Destination_Well'].tolist())

        #     for e in empty_wells:

        tmp_fa_df = pd.DataFrame(my_well_list)

        tmp_fa_df.columns = ["Well"]

        tmp_fa_df = tmp_fa_df.merge(FA_df.loc[FA_df['Third_Destination_ID'] == d], how='outer', left_on=['Well'],
                                    right_on=['Third_Destination_Well'])

        tmp_fa_df.index = range(1, tmp_fa_df.shape[0]+1)

        tmp_fa_df.drop(['Third_Destination_ID', 'Third_Destination_Well'],
                       inplace=True, axis=1)

        tmp_fa_df['name'] = tmp_fa_df['name'].fillna('empty_well')

        tmp_fa_df.loc[tmp_fa_df.Well == 'H12', 'name'] = "ladder_1"

        tmp_fa_df.loc[tmp_fa_df.Well == 'A1', 'name'] = "LibStd_A1"

        tmp_fa_df.loc[tmp_fa_df.Well == 'A12', 'name'] = "LibStd_A12"

        tmp_fa_df.loc[tmp_fa_df.Well == 'H1', 'name'] = "LibStd_H1"

        tmp_fa_df.to_csv(FAUPLOAD_DIR /
                         f'FA_upload_{d}.csv', index=True, header=False)

        # # using .txt extension, but still comma separated data, because FA instrument
        # # looks for .txt files as input
        # tmp_fa_df.to_csv(THIRD_ATMPT_DIR /
        #                  f'FA_upload_{d}.txt', index=True, header=False)

    return FA_df

##########################
##########################


##########################
##########################
# update project database with samples the went into Library creation
def updateProjectDatabase(my_update_lib_df):

    # make small df of plate id, illumina index set, and number of libs in plate
    Third_df = my_update_lib_df.groupby(['Third_Destination_ID', 'Sample Barcode'])[
        'Third_Illumina_index'].agg('count').reset_index()

    # find unique list of sample IDs in merged results_df at end of merging script
    made_list = Third_df['Sample Barcode'].unique().tolist()

    # # import project_database.csv into database
    # project_df = pd.read_csv(PROJECT_DIR / 'project_database.csv',
    #                          header=0, converters={'ITS_sample_id': str})

    # import project_database.db into dataframe
    project_df = readSQLProjectdb()

    return project_df
#########################
#########################


#########################
#########################
def updateSqlDb(project_df):

    sql_db_path = PROJECT_DIR /'project_database.db'

    engine = create_engine(f'sqlite:///{sql_db_path}') 


    # Specify the table name and database engine
    table_name = 'project_database'
    
    if (file_exists(PROJECT_DIR / "project_database.db")):
        
        # archive the current sql .db
        Path(PROJECT_DIR /
              "project_database.db").rename(ARCHIV_DIR / f"archive_project_database_{date}.db")
        Path(ARCHIV_DIR / f"archive_project_database_{date}.db").touch()

    
    # Export the DataFrame to the SQLite database
    project_df.to_sql(table_name, engine, if_exists='replace', index=False) 

    engine.dispose()

        # arive the current project_database.csv
    Path(PROJECT_DIR /
         "project_database.csv").rename(ARCHIV_DIR / f"archive_project_database_{date}.csv")
    Path(ARCHIV_DIR / f"archive_project_database_{date}.csv").touch()

    # create updated project database file
    project_df.to_csv(PROJECT_DIR / 'project_database.csv', index=False)

    return
#########################
#########################


#########################
#########################
def createSQLdb(update_lib_df):
    
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
    update_lib_df.to_sql(table_name, engine, if_exists='replace', index=False) 
    
    engine.dispose()

    # archive the current lib_info.csv
    Path(PROJECT_DIR /
        "lib_info.csv").rename(ARCHIV_DIR / f"archive_lib_info_{date}.csv")
    Path(ARCHIV_DIR / f"archive_lib_info_{date}.csv").touch()

    # create updated library info file
    update_lib_df.to_csv(PROJECT_DIR / 'lib_info.csv', index=False)

    return
#########################
#########################



##########################
# MAIN PROGRAM
##########################

PROJECT_DIR = Path.cwd()

LIB_DIR = PROJECT_DIR / "4_make_library_analyze_fa"

FA_DIR = LIB_DIR / "D_second_attempt_fa_result"

THIRD_ATMPT_DIR = LIB_DIR / "E_third_attempt_make_lib"
THIRD_ATMPT_DIR.mkdir(parents=True, exist_ok=True)

THIRD_FA_DIR = LIB_DIR / "F_third_attempt_fa_result"
THIRD_FA_DIR.mkdir(parents=True, exist_ok=True)

DILUTE_DIR = THIRD_ATMPT_DIR / "Dultion_plate_transfer_files"
DILUTE_DIR.mkdir(parents=True, exist_ok=True)

ECHO_DIR = THIRD_ATMPT_DIR / "Echo_transfer_files"
ECHO_DIR.mkdir(parents=True, exist_ok=True)

FAUPLOAD_DIR = THIRD_ATMPT_DIR / "FA_upload_files"
FAUPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ILLUMINA_DIR = THIRD_ATMPT_DIR / "Illumina_index_transfer_files"
ILLUMINA_DIR.mkdir(parents=True, exist_ok=True)

ARCHIV_DIR = PROJECT_DIR / "archived_files"

PLOT_DIR = PROJECT_DIR / "DNA_vs_Density_plots"

################

# get current date and time, will add to archive database file name
date = datetime.now().strftime("%Y_%m_%d-Time%H-%M-%S")

# define name of file that has updated FA analysis results
updated_file_name = FA_DIR / "updated_2nd_fa_analysis_summary.txt"

# add library pass/fail results from reduced_fa_analysis file
# to the lib_info file
lib_df = updateLibInfo(updated_file_name)


# find the number of original FA plates + redo plates and increment by 1
next_plate_num = len(lib_df.Destination_ID.value_counts().index) + \
    len(lib_df.Redo_Destination_ID.value_counts().index) + 1


# generate files for reworking libs
rework_df, rxn_size = getReworkFiles(lib_df, next_plate_num)

# add Illumina indexes to rework df
rework_df = addIlluminaIndex(rework_df, lib_df)


# make df that will be used ot create echo transfer files, then creat echo transfer files
echo_df, dest_list = makeEchoFiles(rework_df)

# make file for printing barcodes for lib plates and FA plates
makeBarcodeFils(dest_list)

# create df just for making Illumin index transfer files for loading indexes after tagmentation reaction
illum_df = createIllumDataframe(rework_df, rxn_size)

# create df just for making a liquid transfer file for the dilution plates
dilution_df, rework_df = makeDilution(rework_df)


# make Illumina Index transfer files
makeIlluminaFiles(illum_df, dest_list)


# make Dilution plate liquid transfer files
makeDilutionFile(dilution_df, dest_list)

# make threshold.txt file for FA output analysis in next step of SIP wetlab process
makeThreshold(rework_df)


# select subset of columns in rework_df, change column headers, and merge with lib_df
rework_df = rework_df[['Destination_ID', 'Destination_Well',
                       'Destination_row', 'Destination_col', 'Third_Lib_rxn_size(X)', 'DNA_transfer_vol_(nl)', 'Illumina_index_set', 'Illumina_index','Third_FA_dilution_factor']]
rework_df = rework_df.rename(
    columns={'Destination_ID': 'Third_Destination_ID', 'DNA_transfer_vol_(nl)': 'Third_DNA_transfer_vol_(nl)', 'Destination_Well': 'Third_Destination_Well', 'Destination_row': 'Third_Destination_row', 'Destination_col': 'Third_Destination_col', 'Illumina_index_set': 'Third_Illumina_index_set', 'Illumina_index': 'Third_Illumina_index'})

update_lib_df = pd.concat([lib_df, rework_df], axis=1)

# remove column 'Emergency_third_attempt'
update_lib_df.drop(['Emergency_third_attempt'], inplace=True, axis=1)

# make input files for Fragment Analysis for reworked libs
FA_input_df = makeFAinputFiles(
    update_lib_df, dest_list, well_list_96w)

# update the 'made lib' columen of overall project summary file
project_df = updateProjectDatabase(update_lib_df)

# update the sql project_database.db
updateSqlDb(project_df)

# create sqlite database file
createSQLdb(update_lib_df)


# Create success marker file to indicate script completed successfully
import os
os.makedirs('.workflow_status', exist_ok=True)
with open('.workflow_status/emergency.third.attempt.rework.success', 'w') as f:
    f.write('Script completed successfully')
