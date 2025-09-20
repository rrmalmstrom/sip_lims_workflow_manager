#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import sys
import os
from pathlib import Path
import matplotlib.pyplot as plt
from PyPDF2 import PdfMerger
import seaborn as sns
from datetime import datetime
import shutil
from sqlalchemy import create_engine


# define list of destination well positions for a 96-well plate
well_list_96w_emptycorner = ['B1', 'C1', 'D1', 'E1', 'F1', 'G1', 'A2', 'B2', 'C2', 'D2', 'E2', 'F2', 'G2', 'H2', 'A3', 'B3', 'C3',
                             'D3', 'E3', 'F3', 'G3', 'H3', 'A4', 'B4', 'C4', 'D4', 'E4', 'F4', 'G4', 'H4', 'A5', 'B5', 'C5', 'D5', 'E5', 'F5', 'G5',
                             'H5', 'A6', 'B6', 'C6', 'D6', 'E6', 'F6', 'G6', 'H6', 'A7', 'B7', 'C7', 'D7', 'E7', 'F7', 'G7', 'H7', 'A8', 'B8', 'C8',
                             'D8', 'E8', 'F8', 'G8', 'H8', 'A9', 'B9', 'C9', 'D9', 'E9', 'F9', 'G9', 'H9', 'A10', 'B10', 'C10', 'D10', 'E10', 'F10', 'G10',
                             'H10', 'A11', 'B11', 'C11', 'D11', 'E11', 'F11', 'G11', 'H11', 'B12', 'C12', 'D12', 'E12', 'F12', 'G12']


##########################
##########################
def compareFolderFileNames(folder_path, file, folder_name):
    
    # make df from FA smear analysis output .csv file
    fa_df = pd.read_csv(folder_path + f'/{file}', usecols=['Sample ID'] )
    
    # make list of all sample names
    sample_list = fa_df['Sample ID'].unique().tolist()
    
    plate_list = []
    
    # make new plate list after spliting sample names at '_'
    # add 'F' to paresed plate name to matche expected plate barcode in
    # FA output folder name
    for s in sample_list:
        plate_list.append(s.split('_')[0]+'F')
    
    # abort program if the plate name in output folder does not
    # match plate name parsed from sample name in smear analysis .csv file
    if folder_name not in set(plate_list):
        print (f'\n\nThere is a mismatch between FA plate ID and sample names for plate {folder_name}.  Aborting script\n')
        sys.exit()
    
    
    return

##########################
##########################




##########################
##########################
def getFAfiles(crnt_dir):

    fa_files = []
    
    # # scan current directory and find subdirectories
    for direct in os.scandir(crnt_dir):
        if direct.is_dir():
            nxt_dir = os.path.abspath(direct)
            
            # scan current directory and find subdirectories
            for fa in os.scandir(nxt_dir): 
                if fa.is_dir():
                    
                    # find full path to subdirectories
                    folder_path = os.path.abspath(fa)
                    
                    # extract name of FA plate by parsing the subdirectory name
                    folder_name = os.path.basename(fa)
                    folder_name = folder_name.split(' ')[0]
                    
                    # search for smear analysis files in each subdirectory
                    for file in os.listdir(fa):
                        if file.endswith('Smear Analysis Result.csv'):
                            # confirm folder name matches plate name parsed from
                            # smear analysis .csv sample names.  Error out if mismatch
                            compareFolderFileNames(folder_path, file, folder_name)
                            
                            # copy and rename smear analysis to main directory if good match
                            shutil.copy(folder_path +f'/{file}',crnt_dir)
                            
                            os.rename(crnt_dir + "/" + file, crnt_dir + f'/{folder_name}.csv')
                            
                            # add folder name (aka FA plate name) to list
                            fa_files.append(f'{folder_name}.csv')

    # quit script if directory doesn't contain FA .csv files
    if len(fa_files) == 0:
        print("\n\n Did not find any FA output files.  Aborting program\n\n")
        sys.exit()

    else:

        # return a list of FA plate names
        return fa_files
##########################
##########################


##########################
##########################
def processFAfiles(my_fa_files):

    # # ask user input dilution factor used in setting  up FA plate
    # dilute_factor = float(
    #     input("Enter the FA plate dilution factor (default 40): ") or 40)

    # if dilute_factor <= 1:
    #     print('\n Dilution factor must be >=1.  Aborting script\n\n')
    #     sys.exit()

    # create dict where  keys are FA file names and value are df's from those files
    fa_dict = {}

    # loop through all FA files and create df's stored in dict
    for f in my_fa_files:
        # fa_dict[f] = pd.read_csv(f, usecols=[
        #     'Well', 'Sample ID', 'nmole/L', 'Avg. Size'], converters={'nmole/L': float, 'Avg. Size': float})

        fa_dict[f] = pd.read_csv(FA_DIR / f, usecols=[
            'Well', 'Sample ID', 'ng/uL', 'nmole/L', 'Avg. Size'])

        fa_dict[f] = fa_dict[f].rename(
            columns={"Sample ID": "Redo_FA_Sample_ID", "Well": "Redo_FA_Well", "ng/uL": "Redo_ng/uL", "nmole/L": "Redo_nmole/L", "Avg. Size": "Redo_Avg. Size"})

        fa_dict[f]['Redo_FA_Well'] = fa_dict[f]['Redo_FA_Well'].str.replace(
            ':', '')

        # remove rows with "empty" or "ladder" in sample ID. seach is case insensitive
        fa_dict[f] = fa_dict[f][fa_dict[f]["Redo_FA_Sample_ID"].str.contains(
            'empty', case=False) == False]

        fa_dict[f] = fa_dict[f][fa_dict[f]["Redo_FA_Sample_ID"].str.contains(
            'ladder', case=False) == False]

        fa_dict[f] = fa_dict[f][fa_dict[f]["Redo_FA_Sample_ID"].str.contains(
            'LibStd', case=False) == False]

        # create three new columns by parsing Sample_ID string using "_" as delimiter
        fa_dict[f][['Redo_FA_Destination_plate', 'Redo_FA_Sample', 'Redo_FA_Fraction']
                   ] = fa_dict[f].Redo_FA_Sample_ID.str.split("_", expand=True)

        fa_dict[f]['Redo_ng/uL'] = fa_dict[f]['Redo_ng/uL'].fillna(0)

        fa_dict[f]['Redo_nmole/L'] = fa_dict[f]['Redo_nmole/L'].fillna(0)

        fa_dict[f]['Redo_Avg. Size'] = fa_dict[f]['Redo_Avg. Size'].fillna(0)

        fa_dict[f]['Redo_FA_Fraction'] = fa_dict[f]['Redo_FA_Fraction'].astype(
            int)

        fa_dict[f]['Redo_FA_Sample'] = fa_dict[f]['Redo_FA_Sample'].astype(str)

        fa_dict[f]['Redo_ng/uL'] = fa_dict[f]['Redo_ng/uL'].astype(float)

        fa_dict[f]['Redo_nmole/L'] = fa_dict[f]['Redo_nmole/L'].astype(float)

        fa_dict[f]['Redo_Avg. Size'] = fa_dict[f]['Redo_Avg. Size'].astype(
            float)

        # fa_dict[f]['Redo_ng/uL'] = fa_dict[f]['Redo_ng/uL'] * dilute_factor

        # fa_dict[f]['Redo_nmole/L'] = fa_dict[f]['Redo_nmole/L'] * dilute_factor

        # fa_dict[f]['Redo_dilution_factor'] = dilute_factor

    # quit script if were not able to process FA input files
    if len(fa_dict.keys()) == 0:
        print("\n\n Did not sucessfully extract FA files\n\n")
        sys.exit()

    # print out list of successfully processed FA files
    print("\n\n\nList of processed FA output files:\n\n\n")

    for k in fa_dict.keys():
        print(f'{k}\n')

    # add some blank lines after displaying list of processed FA files
    print('\n\n\n')

    return fa_dict
##########################
##########################


##########################
##########################
def findPassFailLibs(my_fa_df):

    # import df with dna conc and size thresholds for each FA plate
    thresh_df = pd.read_csv(FA_DIR / "thresholds.txt", sep="\t", header=0)

    # abort script if thresholds.txt has empty/null values
    if thresh_df.isnull().values.any():
        print("\n\n")
        print('\n\n Thresholds.txt is missing data or has empty values. Aborting. \n\n')
        sys.exit()

    thresh_df = thresh_df.rename(
        columns={'dilution_factor': 'Redo_dilution_factor'})

    # add thresholds of my_lib_df
    my_fa_df = my_fa_df.merge(thresh_df, how='outer', left_on=[
        'Redo_FA_Destination_plate'], right_on=['Destination_plate'])

    # # # identify libs that passed or failed based on conc and size thresholds
    # my_fa_df['Redo_Passed_library'] = np.where(((
    #     my_fa_df['Redo_nmole/L'] > min_lib_conc) & (my_fa_df['Redo_Avg. Size'] > min_lib_size)), 1, 0)

    # assign pass or fail to each lib based on dna conc and size thresholds
    my_fa_df['Redo_Passed_library'] = np.where(((my_fa_df['Redo_nmole/L'] > my_fa_df['DNA_conc_threshold_(nmol/L)']) & (
        my_fa_df['Redo_Avg. Size'] > my_fa_df['Size_theshold_(bp)'])), 1, 0)

    # update lib conc info based on the dilution factor.  This is conc in original library plate
    my_fa_df['Redo_ng/uL'] = my_fa_df['Redo_ng/uL'] * \
        my_fa_df['Redo_dilution_factor']

    my_fa_df = my_fa_df.round({'Redo_ng/uL': 3})

    my_fa_df['Redo_nmole/L'] = my_fa_df['Redo_nmole/L'] * \
        my_fa_df['Redo_dilution_factor']

    my_fa_df = my_fa_df.round({'Redo_nmole/L': 3})

    # remove columns no longer needed
    my_fa_df.drop(['Destination_plate', 'DNA_conc_threshold_(nmol/L)',
                   'Size_theshold_(bp)'], inplace=True, axis=1)
    
    # rename dilution factor column
    my_fa_df = my_fa_df.rename(
        columns={'Redo_dilution_factor':'Redo_FA_dilution_factor'})
    
    return my_fa_df

##########################
##########################


##########################
##########################
def readSQLdb(my_prjct_dir):

    # path to sqlite db lib_info.db
    sql_db_path = f'{my_prjct_dir}/lib_info.db'

    # create sqlalchemy engine
    engine = create_engine(f'sqlite:///{sql_db_path}') 

    # define sql query
    query = "SELECT * FROM lib_info"
    
    # import sql db into pandas df
    sql_df = pd.read_sql(query, engine)
    
    sql_df['Sample Barcode'] = sql_df['Sample Barcode'].astype('str')
    
    sql_df['Fraction #'] = sql_df['Fraction #'].astype('int')

    return sql_df
##########################
##########################


##########################
##########################
def addFAresults(my_prjct_dir, my_fa_df):

    # merging df from lib_info.csv, which as all samples, with df's from FA output

    # # create df from lib_info.csv file
    # my_lib_df = pd.read_csv(my_prjct_dir + "/lib_info.csv",
    #                         header=0, converters={'Sample Barcode': str, 'Fraction #': int})
    
    # create df from lib_info.db sqliute file
    my_lib_df = readSQLdb(my_prjct_dir)

    # record number of rows in my_lib_df. want to make sure doesn't change when merged with fa_df
    num_rows = my_lib_df.shape[0]

    # merge lib df with fa_df
    my_lib_df = my_lib_df.merge(my_fa_df, how='outer', left_on=['Redo_Destination_ID', 'Redo_Destination_Well',
                                                                'Sample Barcode', 'Fraction #'], right_on=['Redo_FA_Destination_plate', 'Redo_FA_Well', 'Redo_FA_Sample', 'Redo_FA_Fraction'], suffixes=('', '_y'))
    # confirm that merging did not change the row number
    if my_lib_df.shape[0] != num_rows:
        print(
            '\n\n problem merging lib_info.csv with FA files. Check out error.csv file just generated\n\n')
        print(my_lib_df.loc[my_lib_df['Destination_ID'].isnull()])

        my_lib_df.to_csv('error.txt', sep='\t', index=False)
        sys.exit()

    # get rid of unnecessary columns
    my_lib_df.drop(['Redo_FA_Destination_plate', 'Redo_FA_Sample',
                    'Redo_FA_Fraction'], inplace=True, axis=1)

    # find samples that failed both attempts at library creation
    # by adding Passed and Redo_Passed columns.  Treat NaN as 0 for summing
    my_lib_df['Total_passed_attempts'] = my_lib_df['Passed_library'].fillna(0) + \
        my_lib_df['Redo_Passed_library'].fillna(0)

    # make a summary file containing only libs  that failed both attempts
    my_double_fail_df = my_lib_df.loc[my_lib_df['Total_passed_attempts'] == 0].copy(
    )

    # double_fail_df.to_csv('double_failed_libraries.txt', sep='\t', index=False)

    return my_lib_df, my_double_fail_df

##########################
##########################


######################
######################
def getTMPdf(df, s):
    # make a temporary df that only includese info of current sample
    tmp_df = df[df['Sample Barcode'] == s].copy()

    # make new column the concats sample barcode with fraction_sample_name
    tmp_df['combo_name'] = tmp_df['Sample Barcode'].astype(str) + \
        '-'+tmp_df['Fraction_sample_name']

    # make list of unique combo names
    name_list = tmp_df[tmp_df['Sample Barcode'] ==
                       s]['combo_name'].unique().tolist()

    # make new column with 'pass' or 'fail' based on total attempts value
    tmp_df['Lib Pass/Fail'] = np.where(tmp_df['Total_passed_attempts']
                                       >= 1, "Pass", "Fail")


    tmp_df['first_or_second'] = np.where(tmp_df['Redo_Passed_library'].isnull(),'first','second')
    

    # remove "_fraction#' from sample name
    ch = '_'
    parts = name_list[0].split(ch)
    parts.pop()
    name = ch.join(parts)
    return tmp_df, name
######################
######################


######################
######################
def plotDensVsConc(s, df, version, all_pdf_files):

    # make dict where marker showng lib pass/fail results are colored by result of first or second attempt 
    color_dict = {'first': 'b', 'second': 'r'}

    # indicate marker style for plot of passed vs failed libs
    marker_form = {"Pass": "o", "Fail": "X"}

    # make temporary df that only has fraction where sample barcode ==s
    # and return name of sample provided by user
    tmp_df, name = getTMPdf(df, s)

    # creation matliplot object
    f = plt.figure()


    # make line plot of sample DNA concentration, NOT the library concentration
    sns.lineplot(data=tmp_df, x="Density (g/mL)",
                 y="DNA Concentration (ng/uL)", color='black', legend=False).set(title=f'{version} {g}: {name}')


    # make scatter plot where marker style indicates if library was successfully created (pass)
    sns.scatterplot(data=tmp_df, x="Density (g/mL)",
                    y="DNA Concentration (ng/uL)", style="Lib Pass/Fail",  hue="first_or_second", palette=color_dict, markers=marker_form, s=100)

    # save plot to a pdf
    plt.savefig(f'tmp_{s}_{version}.pdf', format="pdf", dpi=300)

    # add name of group figure pdf
    all_pdf_files.append(f'tmp_{s}_{version}.pdf')
    
    # show plot in different screen
    # plt.show()

    plt.close(f)

    return all_pdf_files

######################
######################


######################
######################
def mergePDFs(pdf_files, version):
    # Create and instance of PdfMerger() class
    merger = PdfMerger()

    # loop through group figure pdfs and merge them into one
    for pdf in pdf_files:
        # Append PDF files
        merger.append(pdf)

    merger.write(PLOT_DIR / f"DNAvsDensity_PASS-FAIL_plots_{version}_{date}.pdf")

    merger.close()
######################
######################


##########################
# MAIN PROGRAM
##########################
# # get current working directory and its parent directory
# crnt_dir = os.getcwd()
# prnt_dir = os.path.dirname(crnt_dir)
# prjct_dir = os.path.dirname(prnt_dir)

prjct_dir = os.getcwd()

lib_name = "4_make_library_analyze_fa"

# create path to subdirectory where FA results are located
prnt_dir = os.path.join(prjct_dir, lib_name)

fa_dir_name = "D_second_attempt_fa_result"

crnt_dir = os.path.join(prnt_dir, fa_dir_name)


###########################
# set up folder organiztion
###########################

PROJECT_DIR = Path.cwd()

ARCHIV_DIR = PROJECT_DIR / "archived_files"
# ARCHIV_DIR.mkdir(parents=True, exist_ok=True)

LIB_DIR = PROJECT_DIR / "4_make_library_analyze_fa"
# LIB_DIR.mkdir(parents=True, exist_ok=True)

FA_DIR = LIB_DIR / "D_second_attempt_fa_result"

PLOT_DIR = PROJECT_DIR / "DNA_vs_Density_plots"

POOL_DIR = PROJECT_DIR / "5_pooling"

CLARITY_DIR = POOL_DIR / "A_make_clarity_aliquot_upload_file"


# get current date and time, will add to archive database file name
date = datetime.now().strftime("%Y_%m_%d-Time%H-%M-%S")


# get list of FA output files
fa_files = getFAfiles(crnt_dir)


# get dictionary where keys are FA file names and values are df's created from FA files
fa_lib_dict = processFAfiles(fa_files)

# create new dataframe combining all entries in dictionary fa_lib_dict
fa_df = pd.concat(fa_lib_dict.values(), ignore_index=True)


fa_df = findPassFailLibs(fa_df)

# add FA results to df from lib_info.csv
lib_df, double_fail_df = addFAresults(prjct_dir, fa_df)


# # make smaller version of FA summary with only a subset of columns
# reduced_fa_df = lib_df[['Sample Barcode', 'Fraction #', 'Density (g/mL)', 'DNA Concentration (ng/uL)',
#                         'Destination_ID','FA_Well' ,'ng/uL', 'nmole/L', 'Avg. Size', 'Passed_library', 'Redo_whole_plate', 'Redo_Destination_ID',	'Redo_FA_Well',	'Redo_ng/uL',	'Redo_nmole/L',	'Redo_Avg. Size',	'Redo_Passed_library',	'Total_passed_attempts']].copy()

# make smaller version of FA summary with only a subset of columns, including the dilution factor extracted from threshold.txt
reduced_fa_df = lib_df[['Sample Barcode', 'Fraction #', 'Density (g/mL)', 'DNA Concentration (ng/uL)',
                        'Destination_ID','FA_Well' , 'ng/uL', 'nmole/L', 'Avg. Size', 'Passed_library', 'Redo_whole_plate', 'Redo_Destination_ID',	'Redo_FA_Well',	'Redo_FA_dilution_factor_y','Redo_ng/uL',	'Redo_nmole/L',	'Redo_Avg. Size',	'Redo_Passed_library',	'Total_passed_attempts']].copy()

# change name of dilution factor column with value extracted from the threshold.txt
reduced_fa_df = reduced_fa_df.rename(columns={'Redo_FA_dilution_factor_y':'Redo_FA_dilution_factor'})

# add empty column for emergency third attempt at library creation
reduced_fa_df['Emergency_third_attempt'] = ''

# sort reduced df by barcode and fraction#
reduced_fa_df.sort_values(
    by=['Sample Barcode', 'Fraction #'], inplace=True)

# get list of unique group names in project
groups = sorted(lib_df['Replicate_Group'].unique().tolist())


# empty list to later hold names of pdfs for each group figure
# this will be used ot merge multiple pdfs at end of script
all_pdf_files = []

# loop through list of groups
for g in groups:

    # get list of samples in group
    samples = sorted(lib_df[lib_df['Replicate_Group'] == g]
                     ['Sample Barcode'].unique().tolist())

    # loop through samples and add line to plt.plot
    for s in samples:

        plotDensVsConc(s, lib_df, 'updated', all_pdf_files)


# merged plots from each individual sample into one
# pdf with all plots
mergePDFs(all_pdf_files, 'second_attempt')

# second loop to separately delete individual files is necessary
# to make script work on PC... for some reason.
for pdf in all_pdf_files:
    # delete indidvidual group figure pdf
    os.remove(pdf)


# create small file with updated pass/fail info
# use this file for manual overides to automatic pass/fail results
reduced_fa_df.to_csv(FA_DIR / 'reduced_2nd_fa_analysis_summary.txt',
                      sep='\t', index=False)


# create new df of samples that failed both attempts at library creation
double_fail_df.to_csv(FA_DIR / 'double_failed_libraries.txt', sep='\t', index=False)



# Create success marker file to indicate script completed successfully
import os
os.makedirs('.workflow_status', exist_ok=True)
with open('.workflow_status/second.FA.output.analysis.success', 'w') as f:
    f.write('Script completed successfully')
