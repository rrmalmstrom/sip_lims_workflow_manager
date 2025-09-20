#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import os
import sys
import os
from datetime import datetime
import matplotlib.pyplot as plt
from PyPDF2 import PdfFileMerger
import seaborn as sns


######################
######################
def updateDataFrames(orig_df, update_df):

    orig_df.sort_values(by=['Sample Barcode', 'Fraction #'], inplace=True)

    orig_df.reset_index(drop=True, inplace=True)

    orig_df = orig_df.round({'Redo_ng/uL': 3})

    orig_df = orig_df.round({'Redo_nmole/L': 3})

    update_df.sort_values(by=['Sample Barcode', 'Fraction #'], inplace=True)

    update_df.reset_index(drop=True, inplace=True)

    update_df = update_df.round({'Redo_ng/uL': 3})

    update_df = update_df.round({'Redo_nmole/L': 3})

    return orig_df, update_df

######################
######################


######################
######################
def compareDataframes(orig_df, update_df):
    # make df of just differences between original and update final_lib_summary.csv versions
    diff_df = orig_df.compare(update_df)

    # get list of column headers in diff_df
    diff_headers = set(list(diff_df.columns))

    # load set of expected column headers in diff_df
    expected_headers = {('Passed_library', 'other'), ('Redo_Passed_library', 'self'), ('Total_passed_attempts',
                                                                                       'other'), ('Passed_library', 'self'), ('Redo_Passed_library', 'other'), ('Total_passed_attempts', 'self')}

    if diff_headers != expected_headers:
        print('\n\nThere are unexpected columns than Passed_Library, Redo_Passed_library, and Total_passed_attempts\n\n')
        print('Aborting script\n\n')
        sys.exit()

    changed_df = update_df[update_df.index.isin(
        diff_df.index.values.tolist())].copy()

    # # create updated library info file
    # changed_df.to_csv('manually_modified_libraries.csv', index=False)

    print(
        f'\n\nA total of {diff_df.shape[0]} libraries were manually modified as either pass/fail\n\n')

    return changed_df
######################
######################

######################
######################


def getTMPdf(df, s):
    # make a temporary df that only includese info of current sample
    tmp_df = df[df['Sample Barcode'] == s].copy()

    # make new column the concats sample barcode with fraction_sample_name
    tmp_df['combo_name'] = tmp_df['Sample Barcode'].astype(str) + \
        '-'+tmp_df['Fraction_sample_name']

    # extract user provided sample name by removing the suffix "_fraction#" from fraction name
    name_list = tmp_df[tmp_df['Sample Barcode'] ==
                       s]['combo_name'].unique().tolist()

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

    color_dict = {'original': 'b', 'updated': 'r'}

    color = list(color_dict[version])

    # indicate marker style for plot of passed vs failed libs
    marker_form = {"Pass": "o", "Fail": "X"}

    # make temporary df that only has fraction where sample barcode ==s
    # and return name of sample provided by user
    tmp_df, name = getTMPdf(df, s)

    # creation matliplot object
    f = plt.figure()

    # make line plot of sample DNA concentration, NOT the library concentration
    sns.lineplot(data=tmp_df, x="Density (g/mL)",
                 y="DNA Concentration (ng/uL)", hue="Sample Barcode", palette=color, legend=False).set(title=f'{version} {g}: {name}')

    # make scatter plot where marker style indicates if library was successfully created (pass)
    sns.scatterplot(data=tmp_df, x="Density (g/mL)",
                    y="DNA Concentration (ng/uL)", style="Lib Pass/Fail",  hue="Sample Barcode", palette=color, markers=marker_form, s=100)

    # save plot to a pdf
    plt.savefig(f'tmp_{s}_{version}.pdf', format="pdf", dpi=300)

    # add name of group figure pdf
    all_pdf_files.append(f'tmp_{s}_{version}.pdf')

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

    if version == 'all':
        # Write out the merged PDF
        merger.write(f"original_vs_updated_PASS-FAIL_plots_{date}.pdf")
        merger.close()

    elif version == 'updated':
        # Write out the merged PDF
        merger.write(f"DNAvsDensity_PASS-FAIL_plots_{date}.pdf")
        merger.close()

    # # second loop to separately delete individual files is necessary
    # # to make script work on PC... for some reason.
    # for pdf in all_pdf_files:
    #     # delete indidvidual group figure pdf
    #     os.remove(pdf)

######################
######################


# get current date and time, will add some file names
date = datetime.now().strftime("%Y_%m_%d-Time%H-%M-%S")

orig_df = pd.read_csv('final_lib_summary.csv', header=0, skip_blank_lines=True)

update_df = pd.read_csv('updated_final_lib_summary.csv',
                        header=0, skip_blank_lines=True)


orig_df, update_df = updateDataFrames(orig_df, update_df)


# compare original and updated dataframes to find differences in pass/fail assignments
# also look for differences in any other columns.  Only columsn with info on pass/fail
# should be different
changed_df = compareDataframes(orig_df, update_df)


# create updated library info file
changed_df.to_csv('manually_modified_libraries.csv', index=False)


# add new column if at least 1 library passed, otherwise fail
orig_df['Lib Pass/Fail'] = np.where(
    orig_df['Total_passed_attempts'] > 0, "Pass", "Fail")

# add new column if at least 1 library passed, otherwise fail
update_df['Lib Pass/Fail'] = np.where(
    update_df['Total_passed_attempts'] > 0, "Pass", "Fail")


# get list of unique group names in project
groups = sorted(orig_df['Replicate_Group'].unique().tolist())


# empty list to later hold names of pdfs for each group figure
# this will be used ot merge multiple pdfs at end of script
all_pdf_files = []

# loop through list of groups
for g in groups:

    # get list of samples in group
    samples = sorted(orig_df[orig_df['Replicate_Group'] == g]
                     ['Sample Barcode'].unique().tolist())

    # loop through samples and add line to plt.plot
    for s in samples:

        plotDensVsConc(s, orig_df, 'original', all_pdf_files)

        plotDensVsConc(s, update_df, 'updated', all_pdf_files)


# merged plots from each individual sample into one
# pdf with all plots
mergePDFs(all_pdf_files, 'all')


# get list of pdf graphs only from updated df
list_updated_pdfs = list(filter(lambda a: 'update' in a, all_pdf_files))

# merged plots from each individual sample into one
# pdf with all plots
mergePDFs(list_updated_pdfs, 'updated')

# second loop to separately delete individual files is necessary
# to make script work on PC... for some reason.
for pdf in all_pdf_files:
    # delete indidvidual group figure pdf
    os.remove(pdf)
