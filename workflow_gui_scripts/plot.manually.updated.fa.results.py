#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# USAGE:   python plot.updated.analysis.summary.py



import pandas as pd
import numpy as np
import sys
from pathlib import Path
from os.path import exists as file_exists
import os
import matplotlib.pyplot as plt
from PyPDF2 import PdfFileMerger
import seaborn as sns
from datetime import datetime



##########################
##########################
def confirmFileProvided(current_dir):

    if (current_dir == 'D_second_attempt_fa_result') and (file_exists('updated_2nd_fa_analysis_summary.txt') == 1) and (file_exists('reduced_2nd_fa_analysis_summary.txt') == 1):
        
        # create df 
        updated_df = pd.read_csv('updated_2nd_fa_analysis_summary.txt', sep='\t',
                                 header=0, converters={'Sample Barcode': str, 'Fraction #': int})
        
        # create df 
        reduced_df = pd.read_csv('reduced_2nd_fa_analysis_summary.txt', sep='\t',
                                 header=0, converters={'Sample Barcode': str, 'Fraction #': int})


        
    elif (current_dir == 'F_third_attempt_fa_result') and (file_exists('updated_3rd_fa_analysis_summary.txt') == 1) and (file_exists('reduced_3rd_fa_analysis_summary.txt') == 1):
        
        # create df 
        updated_df = pd.read_csv('updated_3rd_fa_analysis_summary.txt', sep='\t',
                                 header=0, converters={'Sample Barcode': str, 'Fraction #': int})
        
        # create df 
        reduced_df = pd.read_csv('reduced_3rd_fa_analysis_summary.txt', sep='\t',
                                 header=0, converters={'Sample Barcode': str, 'Fraction #': int})
                                                                                                                   
    else:    
        print('\n\nAborting. Cannot fine input files: "updated_*_fa_analysis_summary.txt"  or "reduced_*_fa_analysis_summary.txt"\n\n')
        sys.exit()
        
    return updated_df, reduced_df
##########################
##########################


##########################
##########################
def compareUpdateVsReduced(updated_df, reduced_df):
    
    # if updated_df and reduced_df are not identical, find manually modified pass/fail libs
    if not updated_df['Total_passed_attempts'].equals(reduced_df['Total_passed_attempts']):
            
        # merge updated_df and reduced_df based on matching sample barcodes and fraction #'s
        merge_df = pd.merge(reduced_df, updated_df, on=['Sample Barcode','Fraction #'],suffixes=('_y', '')) 
        
        # sort df based on sample and fraction number in case user manually
        # changed sorting when generated updated_fa_analysis_summary.txt
        merge_df.sort_values(by=['Sample Barcode', 'Fraction #'], inplace=True)


        # identify libs with manually modified pass/fail status
        merge_df['manual_mod'] = np.where(merge_df['Total_passed_attempts'] != merge_df['Total_passed_attempts_y'],1,0)
        
        # if passed lib has different pass/fail values in reduced vs updated dfs, mark as modified
        merge_df['manual_mod'] = np.where(merge_df['Passed_library'] != merge_df['Passed_library_y'],1,merge_df['manual_mod'])
        
        # if redo passed lib is not null and redo passed libs is different in reduced vs updated version, mark as modified
        merge_df['manual_mod'] = np.where((merge_df['Redo_Passed_library'].isnull() == 0) & (merge_df['Redo_Passed_library'] != merge_df['Redo_Passed_library_y']),1,merge_df['manual_mod'])
        
        
        ## if using updated_3rd file, then check the manual modification status of third attempt
        if file_exists('updated_3rd_fa_analysis_summary.txt'):
            
            # if redo passed lib is not null and redo passed libs is different in reduced vs updated version, mark as modified
            merge_df['manual_mod'] = np.where((merge_df['Third_Passed_library'].isnull() == 0) & (merge_df['Third_Passed_library'] != merge_df['Third_Passed_library_y']),1,merge_df['manual_mod'])
           
        
        
        
        # remove redundant columns after merging leaving updated_df plus new column indicating libs that were manually modified
        merge_df.drop(merge_df.filter(regex='_y$').columns, axis=1, inplace=True)
        
        # version to plot is first if no rework was attempted
        merge_df['plot_version'] = np.where(merge_df['Redo_Passed_library'].isnull(),'first','second')
        
        # version to plot is first if rework was done, but first attempt was passed and second attempt failed
        merge_df['plot_version'] = np.where((merge_df['Passed_library']==1) & (merge_df['Redo_Passed_library']==0),'first',merge_df['plot_version'])
        
        
        ## if using updated_3rd file, then add 'third' status if 3rd_passed_library ==1
        if file_exists('updated_3rd_fa_analysis_summary.txt'):
            
            # set plot version to 'third' if any libs have pass or fail results in 'Third_Passed_library' column
            merge_df['plot_version'] = np.where(merge_df['Third_Passed_library'].isin([0,1]) ,'third',merge_df['plot_version'])
           
        
        else:
        
            # indicate if sample is scheduled for emergency third attempt at lib creation
            merge_df['plot_version'] = np.where(merge_df['Emergency_third_attempt'] == 1,'third_scheduled',merge_df['plot_version'])
      
        
        return merge_df
    
    # if total pass/fail results are identical beteween, then set values to be used in column 'plot_version'
    else:
        
        # version to plot is first if no rework was attempted
        updated_df['plot_version'] = np.where(updated_df['Redo_Passed_library'].isnull(),'first','second')
        
        # version to plot is first if rework was done, but first attempt was passed and second attempt failed
        updated_df['plot_version'] = np.where((updated_df['Passed_library']==1) & (updated_df['Redo_Passed_library']==0),'first',updated_df['plot_version'])
        
        ## if using updated_3rd file, then add 'third' status if 3rd_passed_library ==1
        if file_exists('updated_3rd_fa_analysis_summary.txt'):
            
            updated_df['plot_version'] = np.where(updated_df['Third_Passed_library'].isin([0,1]) ,'third',updated_df['plot_version'])
           
        
        else:
        
            # indicate if sample is scheduled for emergency third attempt at lib creation
            updated_df['plot_version'] = np.where(updated_df['Emergency_third_attempt'] == 1,'third_scheduled',updated_df['plot_version'])
        
        return updated_df
##########################
##########################


##########################
##########################
def updateLibInfo(updated_df):

    #  make df of lib_df.  Remember, lib_df does not include results of 2nd fa analysis yet
    lib_df = pd.read_csv(PROJECT_DIR / "lib_info.csv",
                         header=0, converters={'Sample Barcode': str, 'Fraction #': int})

    
    if 'Total_passed_attempts' in lib_df.columns:
    
        # remove older version to Total_attempts_passed so it can be replaced  during merge step below
        lib_df.drop(['Total_passed_attempts'], inplace=True, axis=1)


    lib_df = lib_df.merge(updated_df, how='outer', left_on=[
                          'Sample Barcode', 'Fraction #'], right_on=['Sample Barcode', 'Fraction #'], suffixes=('', '_y'))

    # remove redundant columns after merging
    lib_df.drop(lib_df.filter(regex='_y$').columns, axis=1, inplace=True)

    
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

    else:

        return lib_df
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
    
    
    if ('manual_mod' in tmp_df) and (tmp_df['manual_mod'].any()):
        tmp_df['Lib Pass/Fail'] = np.where(tmp_df['manual_mod']
                                           == 1, 'Manual_mod', tmp_df['Lib Pass/Fail'])


    # tmp_df['attempt_status'] = np.where(tmp_df['Redo_Passed_library'].isnull(),'first','second')
    
    # tmp_df['attempt_status'] = np.where(tmp_df['Emergency_third_attempt'] == 1,'third_scheduled',tmp_df['attempt_status'])
    
    
    

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
    color_dict = {'first': 'b', 'second': 'r', 'third_scheduled' : 'g', 'third' : 'g'}

    # indicate marker style for plot of passed vs failed libs
    marker_form = {"Pass": "o", "Fail": "X", "Manual_mod" : "v"}

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
                    y="DNA Concentration (ng/uL)", style="Lib Pass/Fail",  hue="plot_version", palette=color_dict, markers=marker_form, s=100)

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
    # Create and instance of PdfFileMerger() class
    merger = PdfFileMerger()

    # loop through group figure pdfs and merge them into one
    for pdf in pdf_files:
        # Append PDF files
        merger.append(pdf)

    merger.write(f"UPDATED_DNAvsDensity_PASS-FAIL_plots_{version}_{date}.pdf")

    merger.close()

    # # second loop to separately delete individual files is necessary
    # # to make script work on PC... for some reason.
    # for pdf in all_pdf_files:
    #     # delete indidvidual group figure pdf
    #     os.remove(pdf)

######################
######################








###########################
# set up folder organiztion
###########################



SECOND_FA_DIR = Path.cwd()

LIB_DIR = SECOND_FA_DIR.parent

PROJECT_DIR = LIB_DIR.parent


# get current date and time, will add to archive database file name
date = datetime.now().strftime("%Y_%m_%d-Time%H-%M-%S")

# current working direcotry
current_dir = os.path.basename(os.getcwd())

# confirm user provided needed input file in correct directory
# and generate df from updated and reduced versions of fa analysis summary .txt files
updated_df, reduced_df = confirmFileProvided(current_dir)


# identify libs whose pass/fail status were manually changed in updated_2nd_fa_analysis_summary.txt
updated_df = compareUpdateVsReduced(updated_df, reduced_df)


# add library pass/fail results from reduced_2nd_fa_analysis.txt to info stored in lib_info.csv, but don't update lib_info.csv
# pass/fail results may have been manually modified from
# automatic outpt generated by script second.FA.output.analysis.py
lib_df = updateLibInfo(updated_df)



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

