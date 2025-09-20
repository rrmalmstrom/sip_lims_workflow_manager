#!/usr/bin/env python3

# USAGE:   python calcSequinAddition.py


from pathlib import Path
import pandas as pd
import numpy as np
import sys
import os
# from openpyxl import load_workbook
from datetime import datetime
import matplotlib.pyplot as plt
from PyPDF2 import PdfFileMerger

# call exists() function named 'file_exists'
from os.path import exists as file_exists

import pre_vs_post_dna_conc_plots


##########################
##########################
def getPrefix():
    # ask user for total number of fractions collected
    prefix = input(
        "Comparing 'pre' or 'post' PEG additions?\n\nNote, prefix must be lower case and must match case used in file names:  ")

    if (prefix != 'pre') and (prefix != 'post'):
        print(
            "\n\nError.  Must select either 'pre' or 'post' in lower case.  Aborting.\n\n")
        sys.exit()

    return prefix
##########################
##########################


##########################
##########################
def getFractionNumber():
    # ask user for total number of fractions collected
    total_fractions = float(
        input("Enter the total # fractions collected (default 24): ") or 24)

    if (total_fractions <= 0):
        print('\n\nError.  Fractions must be >0.  Aborting.\n\n')
        sys.exit()

    return total_fractions
##########################
##########################


##########################
##########################


def getMatchedFiles(dirname, prefix):
    # create empty list to hold names of files where DNA conc with prefix has matching
    # density and volume check files
    list_matched_files = []

    # loop through all files in directory and find DNA conc files with prefix
    for file in os.listdir(dirname):
        if file.startswith(prefix):

            # extract plate id from file name from density file name and add to plate id list
            plateid = file.replace(prefix, "")
            plateid = plateid.replace(".txt", "")

            # create volume check file name
            vol_file = dirname+"/"+plateid+".CSV"

            # create dna conc file name
            dens_file = dirname+"/"+plateid+".xlsx"

            # check if DNA conc file with prefix has corresponding density (.xlsx) and volume (.csv) files
            if (file_exists(dens_file)):
                if (file_exists(vol_file)):
                    list_matched_files.append(file)
                else:
                    print(
                        f'\n\n Warning: File was not found\nVolume file {vol_file}\n\n')
                    continue
            else:
                print(
                    f'\n\n Warning: File was not found\nDensity file {dens_file} \n\n')
                continue

        else:
            continue

    # quit script if directory doesn't contain any matched sets of density, conc, volume files
    if len(list_matched_files) == 0:
        print(
            f"\n\n Did not find any matche sets of desnity and volume info corresponding with DNA conc files that have {prefix} in name.  Aborting program\n\n")
        sys.exit()

    return list_matched_files
##########################
##########################

##########################
##########################


def getVolumes(my_dirname, my_plateid):
    vol_path = my_dirname+"/" + my_plateid+".CSV"

    # import corrsponding volume check file
    my_volume_df = pd.read_csv(vol_path, header=0, usecols=['RACKID', 'TUBE', 'VOLAVG'], converters={
        'TUBE': str, 'RACKID': str}, skip_blank_lines=True)
    # volume_df = pd.read_csv(plateid+".CSV", header=0, usecols=['RACKID', 'TUBE', 'VOLAVG'], converters={
    #     'TUBE': str, 'RACKID': str})

    # replace missing values with 0 ONLY for well A01.  This seems to be a glitch
    # in instrument used to measure well volumes
    my_volume_df['VOLAVG'] = np.where(
        ((my_volume_df['TUBE'] == 'A01') & (my_volume_df['VOLAVG'].isnull())), 0, my_volume_df['VOLAVG'])

    if my_volume_df['VOLAVG'].isnull().values.any():
        print(
            f"\n\nERROR\n\nThe volume plate for {my_plateid} is missing data.  Aborting script\n\n")
        sys.exit()

    my_volume_df['VOLAVG'] = my_volume_df['VOLAVG'].astype(int)

    # loop to reformat well positions, e.g. A01 --> A1, B01 --> B1
    new_pos_list = []
    for index, row in my_volume_df.iterrows():
        # print(row['TUBE'])
        well = row['TUBE']
        if well[1] == '0':
            well = well.replace('0', '')

        new_pos_list.append(well)

    # replace old well format with new format
    my_volume_df["TUBE"] = new_pos_list

    return my_volume_df

##########################
##########################

##########################
##########################


def getDensity(my_dirname, my_plateid):
    # Read in density file
    dens_path = my_dirname+"/"+my_plateid+".xlsx"

    # # solves a problem that arose where formulas in density.xlsx files would no longer import values
    # # for some reason, problem is solved by opening, saving, and closing the files before reading into pandas
    # # the 4 lines below automaticaly open, save, and close the density files
    # app = xl.App(visible=False)
    # book = app.books.open(dens_path)
    # book.save()
    # app.kill()

    my_density_df = pd.read_excel(dens_path, header=0, engine=("openpyxl"), usecols=['Plate barcode', 'Sample barcode', 'Well Pos', 'Fraction #', 'Density', 'Spike-in Mass (pg)'],
                                  converters={'Plate barcode': str, 'Sample barcode': str, 'Fraction #': int})

    # # check if desnity .xlsx file already hase values ented in Spike-in Mass (pg) column
    # if not(my_density_df['Spike-in Mass (pg)'].isnull().all()):

    #     keep_going = str(
    #         input(f'Density file {my_plateid}.xlsx already has values in column Spike-in Mass (pg)\n\nDo you want to overwrite these data?  (y/n)') or 'n')

    #     if (keep_going == 'Y' or keep_going == 'y'):
    #         print("Ok, we'll keep going and overwrite existing sequin mass data\n\n")

    #     elif (keep_going == 'N' or keep_going == 'n'):
    #         print(
    #             'Ok, aborting script.\n\n')
    #         sys.exit()
    #     else:
    #         print("Sorry, you must choose 'Y' or 'N' next time. \n\nAborting\n\n")
    #         sys.exit()

    # get rid of spike-in mass column
    my_density_df.drop(columns=['Spike-in Mass (pg)'], inplace=True)

    # make a copy of df that include the empty row between the two samples in density plates
    my_density_emptyrow_df = my_density_df.copy()

    my_density_df = my_density_df[my_density_df['Density'].notna()]

    my_density_df['Density'] = my_density_df['Density'].astype(float)

    my_density_df = my_density_df.round({'Density': 4})

    return my_density_df, my_density_emptyrow_df

##########################
##########################

##########################
##########################


def getConc(my_dirname, my_dna):

    conc_path = my_dirname+"/" + my_dna

    tmp_conc_file = 'tmp_conc.txt'

    with open(tmp_conc_file, 'w') as outfile:
        with open(conc_path, 'r') as file:
            for line in file:
                if not line.isspace():
                    outfile.write(line)

    my_DNA_conc_df = pd.read_csv(tmp_conc_file, sep='\t', header=1, usecols=['Well ID', 'Well', '[Concentration]'],
                                 converters={'[Concentration]': str}, skip_blank_lines=True)

    # remove empty lines with NaN
    my_DNA_conc_df.dropna(inplace=True)

    # remove blanks and standards from dataframe and keep only rows with "SPL" in well ID
    my_DNA_conc_df = my_DNA_conc_df.loc[my_DNA_conc_df['Well ID'].str.contains(
        'SPL')]

    my_DNA_conc_df.drop('Well ID', inplace=True, axis=1)

    # remove "<" character from dna conc for samples below detection limit
    my_DNA_conc_df["[Concentration]"] = my_DNA_conc_df["[Concentration]"].str.replace(
        '<', '')

    # replace dna conc values <= 0.001 with 0.001 ng/ul.  Clarity/ITS won't accept a conc <= 0
    my_DNA_conc_df["[Concentration]"] = np.where(my_DNA_conc_df["[Concentration]"].astype(
        float) <= 0.001, 0.001, my_DNA_conc_df["[Concentration]"].astype(float))

    # round DNA concentration
    my_DNA_conc_df = my_DNA_conc_df.round({'[Concentration]': 3})

    # append my_DNA_conc_df to larger DF of all files

    try:
        os.remove(tmp_conc_file)

    except:
        print(f'\nError deleting {tmp_conc_file}')

    return my_DNA_conc_df

##########################
##########################


##########################
##########################
def getMergedPlates(DNA_conc_df, volume_df, density_df, plateid, list_merged_plates, sample_dict):
    # create dictionarly to hold merged df for each plateid
    # the plate id is the key, and the merged df is the value
    d = {}

    # merge denisty and volume dataframes
    d[plateid] = density_df.merge(volume_df, how='outer', left_on=['Well Pos', 'Plate barcode'],
                                  right_on=['TUBE', 'RACKID'])

    # generate error if there is a mismatch in wells or plate id between density and volume files
    if (d[plateid]["TUBE"].isnull().values.any()):
        print("\n\n")
        print(d[plateid])
        print(
            '\n\n Wells and plated id do not match. Aborting. Check error file. \n\n')
        d[plateid].to_csv('error.desnity.volume.merge.csv', index=False)

        sys.exit()

    # merge dnc conc dataframe with density and volume df
    d[plateid] = d[plateid].merge(DNA_conc_df, how='inner', left_on='Well Pos',
                                  right_on='Well')

    # generate error if there is a mismatch in wells or plate id between dna conc file and merged density+volume df
    if (d[plateid]["TUBE"].isnull().values.any()):
        print("\n\n")
        print(d[plateid])
        print(
            '\n\n Wells and plated id do not match. Aborting. Check error file. \n\n')
        d[plateid].to_csv('error.desnity.volume.merge.csv', index=False)

        sys.exit()

    # create list of successfully merged plate IDs
    list_merged_plates.append(plateid)

    # get list of sample ids in a SIP plate
    samples_in_plate = sorted(density_df['Sample barcode'].unique().tolist())

    # update dict with sample_id as key and values are plates where sample are found
    # the same sample id can be in >1 plate if the sample was re-run/re-frationated
    for s in samples_in_plate:
        if s in sample_dict.keys():
            sample_dict[s].append(plateid)
        else:
            sample_dict[s] = [plateid]

    return d[plateid], list_merged_plates, sample_dict
##########################
##########################


############################
############################
def addRepGroupandSampleName(my_result_df, my_project_df):

    # make group_dict dictionary where key is ITS sample ID and value is replicate group
    group_dict = dict(zip(my_project_df.ITS_sample_id,
                      my_project_df.Replicate_Group))

    # make group_dict dictionary where key is ITS sample ID and value is sample name
    name_dict = dict(zip(my_project_df.ITS_sample_id,
                     my_project_df.Sample_Name))

    # add column using group_dict
    my_result_df['Replicate_Group'] = my_result_df['Sample barcode'].map(
        group_dict)

    # add column of fraction sample name by concat parent sample name with the fraction #
    my_result_df['Fraction_sample_name'] = my_result_df['Sample barcode'].map(
        name_dict) + "_" + my_result_df['Fraction #'].astype(str)

    # make sure replicate group and fraction sample ids were assigned to all fractions
    if (my_result_df['Replicate_Group'].isnull().values.any()):
        print("\n\n")
        print(
            '\n\n Could not assign Replciate_Group to at least one sample. Aborting. Check error file. \n\n')

        my_result_df.to_csv('error.desnity.volume.merge.csv', index=False)
        sys.exit()

    elif (my_result_df['Fraction_sample_name'].isnull().values.any()):
        print("\n\n")
        print(
            '\n\n Could not assign Fraction_sample_name to at least one sample. Aborting. Check error file. \n\n')
        my_result_df.to_csv('error.desnity.volume.merge.csv', index=False)
        sys.exit()

    # get a list of columns
    cols = list(my_result_df)
    # move the column to head of list using index, pop and insert
    cols.insert(0, cols.pop(cols.index('Replicate_Group')))

    # move the column to head of list using index, pop and insert
    cols.insert(0, cols.pop(cols.index('Fraction_sample_name')))

    # use ix to reorder
    my_result_df = my_result_df.loc[:, cols]

    return my_result_df
############################
############################


############################
############################
def addDnaMassPerFraction(all_plate_df, prefix, total_fractions):

    if prefix == 'pre':

        all_plate_df['pre_PEG_total_DNA_mass_(pg)'] = all_plate_df['VOLAVG'] * \
            all_plate_df['[Concentration]']

        tmp_df = all_plate_df[all_plate_df['Fraction #'].between(
            3, (total_fractions-2))]

        # calculate the total ng's recovered in pre PEG fractions
        total_ng_df = tmp_df.groupby(['Sample barcode', 'Plate barcode'], as_index=False)[
            'pre_PEG_total_DNA_mass_(pg)'].sum().round(0)

        # not applicable when analyzing pre PEG dnc conc
        resuspend_vol = 'NA'

    elif prefix == 'post':
        # get post PEG resuspension volume from user
        resuspend_vol = float(
            input("\n\nEnter the resuspension volume following PEG precipitation (default 35): ") or 35)

        if (resuspend_vol <= 0):
            print('\n\nError.  Resuspension volume must be >0.  Aborting.\n\n')
            sys.exit()

        # add columen with resuspension volume and use to calculate DNA mass in each fraction
        all_plate_df['Resuspension_vol_(uL)'] = resuspend_vol

        all_plate_df['post_PEG_total_DNA_mass_(ng)'] = all_plate_df['Resuspension_vol_(uL)'] * \
            all_plate_df['[Concentration]']

        # excluding first 2 and last 2 fractions from each sample for later calculation
        tmp_df = all_plate_df[all_plate_df['Fraction #'].between(
            3, (total_fractions-2))]

        # calculate the total ng's recovered in pre PEG fractions
        total_ng_df = tmp_df.groupby(['Sample barcode', 'Plate barcode'], as_index=False)[
            'post_PEG_total_DNA_mass_(ng)'].sum().round(0)

    total_ng_df.columns.values[2] = "Total_DNA"

    return all_plate_df, total_ng_df, resuspend_vol
############################
############################


##########################
##########################


def makeDNAvsDensityPlots(all_plate_df, sample_dict, total_fractions, prefix):

    # get list of unique group names in project
    groups = sorted(all_plate_df['Replicate_Group'].unique().tolist())

    # empty list to later hold names of pdfs for each group figure
    # this will be used ot merge multiple pdfs at end of script
    pdf_files = []

    # loop through list of groups
    for g in groups:

        # get list of samples in group
        samples = sorted(all_plate_df[all_plate_df['Replicate_Group'] == g]
                         ['Sample barcode'].unique().tolist())

        # creation matliplot object
        f = plt.figure()

        # loop through samples and add line to plt.plot
        for s in samples:
            for p in sample_dict[s]:
                x = all_plate_df[(all_plate_df['Sample barcode'] == s) & (all_plate_df['Plate barcode'] == p) & (
                    all_plate_df['Fraction #'].between(1, total_fractions))]['Density']
                y = all_plate_df[(all_plate_df['Sample barcode']
                                  == s) & (all_plate_df['Plate barcode'] == p) & (all_plate_df['Fraction #'].between(1, total_fractions))]['[Concentration]']

                # x = lib_df[(lib_df['Sample barcode'] == s) & (
                #     lib_df['Density (g/mL)'].between(1.669, 1.781))]['Density (g/mL)']
                # y = lib_df[(lib_df['Sample barcode']
                #            == s) & (lib_df['Density (g/mL)'].between(1.669, 1.781))]['DNA Concentration (ng/uL)']

                # x = all_plate_df[(all_plate_df['Sample barcode'] == s) & (
                #     all_plate_df['Make_Lib'] == 1)]['Density (g/mL)']
                # y = all_plate_df[(all_plate_df['Sample barcode']
                #                   == s) & (all_plate_df['Make_Lib'] == 1)]['DNA Concentration (ng/uL)']

                # make new column the concats sample barcode with fraction_sample_name
                all_plate_df['combo_name'] = all_plate_df['Sample barcode'] + '-' + p + \
                    '-'+all_plate_df['Fraction_sample_name']

                # extract user provided sample name by removing the suffix "_fraction#" from fraction name
                name_list = all_plate_df[all_plate_df['Sample barcode'] ==
                                         s]['combo_name'].unique().tolist()

                # remove "_fraction#' from sample name
                ch = '_'
                parts = name_list[0].split(ch)
                parts.pop()
                name = ch.join(parts)

                # add plot of current sample
                plt.plot(x, y, label=name, marker='o')

        # add reference lines to plot for density range
        # the range of density from 1.67 to 1.78 is where we theoretically expect to recover DNA
        # though shoud be at or below detection limit closer we are to range termini
        plt.plot([1.67, 1.67], [0, 0.3], 'k-', lw=1, dashes=[2, 2])
        plt.plot([1.78, 1.78], [0, 0.3], 'k-', lw=1, dashes=[2, 2])

        # add reference line to plot for DNA concentration
        # pre dna conc of 0.25ng/ul equates to 50ng/fraction
        # post dna con of 1ng/ul equates to 35ng/fraction
        if prefix == 'pre':
            plt.plot([1.66, 1.8], [0.25, 0.25], 'k-', lw=1, dashes=[2, 2])

        elif prefix == 'post':
            plt.plot([1.66, 1.8], [1, 1], 'k-', lw=1, dashes=[2, 2])

        # add plot title, axes labels, and legend to group plot
        plt.xlabel("Density (g/mL)")
        plt.ylabel("DNA Concentration (ng/uL)")
        plt.title(f'{prefix} PEG DNA conc for Replicate Group: {g}')
        plt.legend(fontsize='x-small')
        # plt.show()
        f.savefig(f'DNAvsDensity_{g}.pdf',
                  format="pdf", bbox_inches="tight")

        # add name of group figure pdf
        pdf_files.append(f'DNAvsDensity_{g}.pdf')

        plt.close(f)

    # Create and instance of PdfFileMerger() class
    merger = PdfFileMerger()

    # loop through group figure pdfs and merge them into one
    for pdf in pdf_files:
        # Append PDF files
        merger.append(pdf)
        # # delete indidvidual group figure pdf
        # os.remove(pdf)

    # total_samples = len(pdf_files)

    # Write out the merged PDF
    merger.write(
        PROJECT_DIR / f"{prefix}_PEG_DNAvsDensity_plots_by_replicategroup_{date}.pdf")
    merger.close()

    for pdf in pdf_files:
        # delete indidvidual group figure pdf
        os.remove(pdf)

    return total_fractions
##########################
##########################


##########################
##########################
def compareDNAvsDensityVersions(all_plate_df, sample_dict, total_fractions, prefix):

    # empty list to later hold names of pdfs for each group figure
    # this will be used ot merge multiple pdfs at end of script
    pdf_files = []

    for s in sample_dict.keys():
        if len(sample_dict[s]) > 1:
            f = plt.figure()

            for p in sample_dict[s]:

                # for s in samples:
                #     for p in sample_dict[s]:
                x = all_plate_df[(all_plate_df['Sample barcode'] == s) & (all_plate_df['Plate barcode'] == p) & (
                    all_plate_df['Fraction #'].between(1, total_fractions))]['Density']
                y = all_plate_df[(all_plate_df['Sample barcode']
                                  == s) & (all_plate_df['Plate barcode'] == p) & (all_plate_df['Fraction #'].between(1, total_fractions))]['[Concentration]']

                # make new column the concats sample barcode with fraction_sample_name
                all_plate_df['combo_name'] = all_plate_df['Sample barcode'] + '-' + p + \
                    '-'+all_plate_df['Fraction_sample_name']

                # extract user provided sample name by removing the suffix "_fraction#" from fraction name
                name_list = all_plate_df[all_plate_df['Sample barcode'] ==
                                         s]['combo_name'].unique().tolist()

                # remove "_fraction#' from sample name
                ch = '_'
                parts = name_list[0].split(ch)
                parts.pop()
                name = ch.join(parts)

                # add plot of current sample
                plt.plot(x, y, label=name, marker='o')

            # add reference line to plot for DNA concentration
            # pre dna conc of 0.25ng/ul equates to 50ng/fraction
            # post dna con of 1ng/ul equates to 35ng/fraction
            if prefix == 'pre':

                plt.plot([1.67, 1.67], [0, 0.3], 'k-', lw=1, dashes=[2, 2])
                plt.plot([1.78, 1.78], [0, 0.3], 'k-', lw=1, dashes=[2, 2])

                plt.plot([1.66, 1.8], [0.25, 0.25], 'k-', lw=1, dashes=[2, 2])

            elif prefix == 'post':

                plt.plot([1.67, 1.67], [0, 1.3], 'k-', lw=1, dashes=[2, 2])
                plt.plot([1.78, 1.78], [0, 1.3], 'k-', lw=1, dashes=[2, 2])

                plt.plot([1.66, 1.8], [1, 1], 'k-', lw=1, dashes=[2, 2])

            # add plot title, axes labels, and legend to group plot
            plt.xlabel("Density (g/mL)")
            plt.ylabel("DNA Concentration (ng/uL)")
            plt.title(f'{prefix} PEG DNA conc for versions of sample: {s}')
            plt.legend(fontsize='x-small')
            # plt.show()
            f.savefig(f'DNAvsDensity_{s}.pdf',
                      format="pdf", bbox_inches="tight")

            # add name of group figure pdf
            pdf_files.append(f'DNAvsDensity_{s}.pdf')

            plt.close(f)

    # Create and instance of PdfFileMerger() class
    merger = PdfFileMerger()

    # loop through group figure pdfs and merge them into one
    for pdf in pdf_files:
        # Append PDF files
        merger.append(pdf)
        # # delete indidvidual group figure pdf
        # os.remove(pdf)

    # total_samples = len(pdf_files)

    # Write out the merged PDF
    merger.write(
        PROJECT_DIR / f"Compare_{prefix}_by_sample_{date}.pdf")
    merger.close()

    for pdf in pdf_files:
        # delete indidvidual group figure pdf
        os.remove(pdf)

    return
##########################
##########################


##########################
##########################
def individualDNAvsDensityPlots(all_plate_df, sample_dict, total_fractions, prefix, total_ng_df):

    # empty list to later hold names of pdfs for each group figure
    # this will be used ot merge multiple pdfs at end of script
    pdf_files = []

    # get list of samples in group
    samples = sorted(all_plate_df['Sample barcode'].unique().tolist())

    # loop through samples and add line to plt.plot
    for s in samples:
        # creation matliplot object
        # f = plt.figure()

        for p in sample_dict[s]:
            f = plt.figure()
            x = all_plate_df[(all_plate_df['Sample barcode'] == s) & (all_plate_df['Plate barcode'] == p) & (
                all_plate_df['Fraction #'].between(1, total_fractions))]['Density']
            y = all_plate_df[(all_plate_df['Sample barcode']
                              == s) & (all_plate_df['Plate barcode'] == p) & (all_plate_df['Fraction #'].between(1, total_fractions))]['[Concentration]']

            # find total DNA mass for specific sample to add to figure
            tmp_df = total_ng_df.set_index(
                ['Sample barcode', 'Plate barcode']).copy()

            mass = int(tmp_df.loc[(s, p), 'Total_DNA'])

            # make new column the concats sample barcode with fraction_sample_name
            all_plate_df['combo_name'] = all_plate_df['Sample barcode'] + '-' + p + \
                '-'+all_plate_df['Fraction_sample_name']

            # extract user provided sample name by removing the suffix "_fraction#" from fraction name
            name_list = all_plate_df[all_plate_df['Sample barcode'] ==
                                     s]['combo_name'].unique().tolist()

            # remove "_fraction#' from sample name
            ch = '_'
            parts = name_list[0].split(ch)
            parts.pop()
            name = ch.join(parts)

            # add plot of current sample
            plt.plot(x, y, label=name, marker='o')

            # # add reference lines to plot for density range
            # # the range of density from 1.67 to 1.78 is where we theoretically expect to recover DNA
            # # though shoud be at or below detection limit closer we are to range termini
            # plt.plot([1.67, 1.67], [0, 0.3], 'k-', lw=1, dashes=[2, 2])
            # plt.plot([1.78, 1.78], [0, 0.3], 'k-', lw=1, dashes=[2, 2])

            # add reference line to plot for DNA concentration
            # pre dna conc of 0.25ng/ul equates to 50ng/fraction
            # post dna con of 1ng/ul equates to 35ng/fraction
            if prefix == 'pre':

                plt.plot([1.67, 1.67], [0, 0.3], 'k-', lw=1, dashes=[2, 2])
                plt.plot([1.78, 1.78], [0, 0.3], 'k-', lw=1, dashes=[2, 2])

                plt.plot([1.66, 1.8], [0.25, 0.25], 'k-', lw=1, dashes=[2, 2])

                plt.text(1.66, 0.35, 'total DNA: {}ng'.format(mass), fontsize=8)

            elif prefix == 'post':

                plt.plot([1.67, 1.67], [0, 1.3], 'k-', lw=1, dashes=[2, 2])
                plt.plot([1.78, 1.78], [0, 1.3], 'k-', lw=1, dashes=[2, 2])

                plt.plot([1.66, 1.8], [1, 1], 'k-', lw=1, dashes=[2, 2])

                plt.text(1.66, 1.5, 'total DNA: {}ng'.format(mass), fontsize=8)

            # add plot title, axes labels, and legend to group plot
            plt.xlabel("Density (g/mL)")
            plt.ylabel("DNA Concentration (ng/uL)")
            plt.title(f'{prefix} PEG DNA conc for sample: {s}-{p}')
            # plt.legend(fontsize='x-small')

            # plt.show()

            f.savefig(f'DNAvsDensity_{s}_{p}.pdf',
                      format="pdf", bbox_inches="tight")

            # add name of group figure pdf
            pdf_files.append(f'DNAvsDensity_{s}_{p}.pdf')

            plt.close(f)

    # Create and instance of PdfFileMerger() class
    merger = PdfFileMerger()

    # loop through group figure pdfs and merge them into one
    for pdf in pdf_files:
        # Append PDF files
        merger.append(pdf)
        # # delete indidvidual group figure pdf
        # os.remove(pdf)

    # total_samples = len(pdf_files)

    # Write out the merged PDF
    merger.write(
        PROJECT_DIR / f"{prefix}_PEG_DNAvsDensity_plots_INDIVIDUAL_samples_{date}.pdf")
    merger.close()

    for pdf in pdf_files:
        # delete indidvidual group figure pdf
        os.remove(pdf)

    return total_fractions
##########################
##########################


##########################
##########################
###    MAIN Program    ###
##########################
##########################
# get current date and time, will add some file names
date = datetime.now().strftime("%Y_%m_%d-Time%H-%M-%S")


# set currign working directory and create a 'sequins' folder if it doesn't exist already
BASE_DIR = Path.cwd()

PROJECT_DIR = BASE_DIR.parent

# get current directory
dirname = os.getcwd()


# ask user for number for fractions collected per sample
total_fractions = getFractionNumber()

# ask user if plotting pre or post peg DNAvsDensity
prefix = getPrefix()


# get list of matched sets of density, dna conc, and volume files
dna_files = getMatchedFiles(dirname, prefix)

# create empty list to hold all plate ids found
list_merged_plates = []

# create empty dict where key will be sample_id and values will be plate_ids
sample_dict = {}

# create empty df to hold results for all plates
all_plate_df = pd.DataFrame()

# loop through all dna conc plates and merge with density and volume files
# and calculate amount of sequins to add to each fraction
for dna in dna_files:

    # generate df of DNA conc values
    DNA_conc_df = getConc(dirname, dna)

    # get plate name by removing DNA conc file prefix
    plateid = dna.replace(prefix, "")
    plateid = plateid.replace(".txt", "")

    # creat df's from density and volume files
    volume_df = getVolumes(dirname, plateid)
    density_df, density_emptyrow_df = getDensity(dirname, plateid)

    # merge dna conc, density, and volume df's
    merged_df, list_merged_plates, sample_dict = getMergedPlates(
        DNA_conc_df, volume_df, density_df, plateid, list_merged_plates, sample_dict)

    # concat merged_df from current dna plate with master df of all dna plates
    all_plate_df = pd.concat([all_plate_df, merged_df],
                             axis=0, ignore_index=True)
# read project_database.csv into  a dataframe
project_df = pd.read_csv(PROJECT_DIR / 'project_database.csv', header=0, usecols=['Sample_Name', 'Replicate_Group', 'ITS_sample_id'], converters={
    'ITS_sample_id': str})

# add user sample name and replicate group to all_plate_df
all_plate_df = addRepGroupandSampleName(all_plate_df, project_df)

# add user sample name and replicate group to all_plate_df
all_plate_df, total_ng_df, resuspend_vol = addDnaMassPerFraction(
    all_plate_df, prefix, total_fractions)

# make pdf plots of density vs DNA conc organized by replicate group
makeDNAvsDensityPlots(all_plate_df, sample_dict, total_fractions, prefix)

# make pdf plots of density vs DNA conc for each individual sample
individualDNAvsDensityPlots(
    all_plate_df, sample_dict, total_fractions, prefix, total_ng_df)

# make pdf plots of density vs DNA conc comparing different versions of sampe initial sample
if any(len(plates) > 1 for plates in sample_dict.values()):
    compareDNAvsDensityVersions(
        all_plate_df, sample_dict, total_fractions, prefix)

# call main function in another .py file that will plot pre vs post dna conc
if prefix == 'post':
    pre_vs_post_dna_conc_plots.main(total_fractions, resuspend_vol, date)

# drop columns and rename others in order to create summary file for all plates
all_plate_df.drop(columns=['TUBE', 'Well', 'RACKID',
                  'combo_name'], inplace=True)

all_plate_df.rename(columns={'VOLAVG': 'Fraction_vol_(ul)',
                    '[Concentration]': f'{prefix}_DNA_conc_(ng/uL)', 'Density': 'Density_(g/mL)'}, inplace=True)

#  remove empty fractions from summary all_plate_df
all_plate_df = all_plate_df[all_plate_df['Fraction #'] <= total_fractions]

all_plate_df.to_csv(
    f'summary_{prefix}_Density_DNA_Volume_{date}.csv', index=False)

# Create success marker to indicate script completed successfully
from pathlib import Path
status_dir = Path.cwd() / ".workflow_status"
status_dir.mkdir(exist_ok=True)
success_file = status_dir / "plot_DNAconc_vs_Density.success"
success_file.touch()
