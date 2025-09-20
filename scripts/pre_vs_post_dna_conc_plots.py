#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#!/usr/bin/env python3

# USAGE:   python calcSequinAddition.py


from pathlib import Path
import pandas as pd
import numpy as np
import sys
import os
from datetime import datetime
import matplotlib.pyplot as plt
from PyPDF2 import PdfFileMerger

# call exists() function named 'file_exists'
from os.path import exists as file_exists


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
def getMatchedPrePostFiles(dirname):
    # create empty list to hold names of files where DNA conc with prefix has matching
    # density and volume check files
    list_matched_files_pre = []

    list_matched_files_post = []

    # loop through all files in directory and find DNA conc files with pre and post versions
    for file in os.listdir(dirname):
        if file.startswith('pre'):

            # determine if there is matching post PEG DNA conc file
            post_dna_conc = file.replace("pre", "post")

            if (file_exists(post_dna_conc)):

                # extract plate id from file name from density file name and add to plate id list
                plateid = file.replace("pre", "")
                plateid = plateid.replace(".txt", "")

                # create volume check file name
                vol_file = dirname+"/"+plateid+".CSV"

                # create dna conc file name
                dens_file = dirname+"/"+plateid+".xlsx"

                # check if matching pre and post DNA conc files have corresponding density (.xlsx) and volume (.csv) files
                if (file_exists(dens_file)):
                    if (file_exists(vol_file)):
                        list_matched_files_pre.append(file)
                        list_matched_files_post.append(post_dna_conc)

                    else:
                        print(
                            f'\n\n Warning: File was not found\nVolume file {vol_file}\n\n')
                        continue
                else:
                    print(
                        f'\n\n Warning: File was not found\nDensity file {dens_file} \n\n')
                    continue

            else:
                print(
                    f'\n\n Warning: Did not find a matching "post" dna conc file that matches: {file} \n\n')
                continue

        else:
            continue

    # quit script if directory doesn't contain any matched sets of density, conc, volume files
    if len(list_matched_files_pre) == 0:
        print("\n\n Did not find any matched sets of PRE and POST dna conc files that also had coresponding volume and density files.  Aborting program\n\n")
        sys.exit()

    # double check the same number of pre and post dnca conc file are in lists
    elif len(list_matched_files_pre) != len(list_matched_files_post):
        print("\n\n Problem finding mathced pre and post dna conc files.  Aborting program\n\n")
        sys.exit()

    else:
        # return a list of mathcing "pre" and "post" dna conc file names that also have corresponding volume and density files
        return list_matched_files_pre, list_matched_files_post
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

    try:
        os.remove(tmp_conc_file)

    except:
        print(f'\nError deleting {tmp_conc_file}')

    return my_DNA_conc_df

##########################
##########################


##########################
##########################
def getMergedPlates(DNA_conc_df, volume_df, density_df, plateid, list_merged_plates, sample_dict, prefix):
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

    # add column to merged df indicating if dna conc values are pre or post
    d[plateid]['pre_or_post'] = prefix

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
            sample_dict[s] = list(set(sample_dict[s]))
        else:
            sample_dict[s] = [plateid]

    return d[plateid], list_merged_plates, sample_dict

    # return d[plateid], list_merged_plates
##########################
##########################


##########################
##########################
def updatePostVolume(post_all_plate_df, resuspend_vol=-1):

    if resuspend_vol == -1:

        resuspend_vol = float(
            input("Enter the resuspension volume following PEG precipitation (default 35): ") or 35)

        if (resuspend_vol <= 0):
            print('\n\nError.  Resuspension volume must be >0.  Aborting.\n\n')
            sys.exit()

    post_all_plate_df['Resuspension_vol_(uL)'] = resuspend_vol

    return post_all_plate_df
##########################
##########################

############################
############################


def updateAllPlate(my_result_df, my_project_df):

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
def addFractionMass(pre_all_plate_df, post_all_plate_df):

    pre_all_plate_df['pre_mass_(ng)'] = pre_all_plate_df['VOLAVG'] * \
        pre_all_plate_df['[Concentration]']

    post_all_plate_df['post_mass_(ng)'] = post_all_plate_df['Resuspension_vol_(uL)'] * \
        post_all_plate_df['[Concentration]']

    return pre_all_plate_df, post_all_plate_df
############################
############################

##########################
##########################


def comparePrePostDNAvsDensity(all_plate_df, sample_dict, total_fractions):

    # empty list to later hold names of pdfs for each group figure
    # this will be used ot merge multiple pdfs at end of script
    pdf_files = []

    for s in sample_dict.keys():

        for p in sample_dict[s]:

            f = plt.figure()

            xpre = all_plate_df[(all_plate_df['Sample barcode'] == s) & (all_plate_df['Plate barcode'] == p) & (
                all_plate_df['Fraction #'].between(1, total_fractions))]['Density']
            ypre = all_plate_df[(all_plate_df['Sample barcode']
                                 == s) & (all_plate_df['Plate barcode'] == p) & (all_plate_df['Fraction #'].between(1, total_fractions))]['pre_mass_(ng)']

            xpost = all_plate_df[(all_plate_df['Sample barcode'] == s) & (all_plate_df['Plate barcode'] == p) & (
                all_plate_df['Fraction #'].between(1, total_fractions))]['Density']
            ypost = all_plate_df[(all_plate_df['Sample barcode']
                                  == s) & (all_plate_df['Plate barcode'] == p) & (all_plate_df['Fraction #'].between(1, total_fractions))]['post_mass_(ng)']

            # # make new column the concats sample barcode with fraction_sample_name
            # all_plate_df['combo_name'] = all_plate_df['Sample barcode'] + '-' + p + \
            #     '-'+all_plate_df['Fraction_sample_name']

            # extract user provided sample name by removing the suffix "_fraction#" from fraction name
            name_list = all_plate_df[all_plate_df['Sample barcode'] ==
                                     s]['Fraction_sample_name'].unique().tolist()

            # remove "_fraction#' from sample name
            ch = '_'
            parts = name_list[0].split(ch)
            parts.pop()
            name = ch.join(parts)

            # add plot of current sample
            plt.plot(xpre, ypre, label='pre '+name, marker='o')
            plt.plot(xpost, ypost, label='post '+name, marker='o')

            plt.plot([1.67, 1.67], [0, 25], 'k-', lw=1, dashes=[2, 2])
            plt.plot([1.78, 1.78], [0, 25], 'k-', lw=1, dashes=[2, 2])

            plt.plot([1.66, 1.8], [50, 50], 'k-', lw=1, dashes=[2, 2])

            plt.text(1.66, 52, 'pre', fontsize=8)

            plt.plot([1.66, 1.8], [35, 35], 'k-', lw=1, dashes=[2, 2])

            plt.text(1.66, 37, 'post', fontsize=8)

            # add plot title, axes labels, and legend to group plot
            plt.xlabel("Density (g/mL)")
            plt.ylabel("DNA Mass (ng)")
            plt.title(f'pre vs post for Sample: {s} Plate: {p}')
            plt.legend(fontsize='x-small')

            # plt.show()
            f.savefig(f'DNAvsDensity_{s}_{p}.pdf',
                      format="pdf", bbox_inches="tight")

            # add name of group figure pdf
            pdf_files.append(f'DNAvsDensity_{s}_{p}.pdf')

            plt.close(f)

    # # Create and instance of PdfFileMerger() class
    # merger = PdfFileMerger()

    # # loop through group figure pdfs and merge them into one
    # for pdf in pdf_files:
    #     # Append PDF files
    #     merger.append(pdf)
    #     # # delete indidvidual group figure pdf
    #     # os.remove(pdf)

    # # total_samples = len(pdf_files)

    # # Write out the merged PDF
    # merger.write(
    #     PROJECT_DIR / f"Compare_{prefix}_sample_versions{date}.pdf")
    # merger.close()

    # for pdf in pdf_files:
    #     # delete indidvidual group figure pdf
    #     os.remove(pdf)

    return pdf_files
##########################
##########################


##########################
##########################
###    MAIN Program    ###
##########################
##########################

def main(total_fractions=-1, resuspend_vol=-1, date=-1):

    if date == -1:
        # get current date and time, will add some file names
        date = datetime.now().strftime("%Y_%m_%d-Time%H-%M-%S")

    # set currign working directory and create a 'sequins' folder if it doesn't exist already
    BASE_DIR = Path.cwd()

    PROJECT_DIR = BASE_DIR.parent

    # get current directory
    dirname = os.getcwd()

    if total_fractions == -1:
        # ask user for number for fractions collected per sample
        total_fractions = getFractionNumber()

    # get list of matched sets of density, volume, and Pre+Post dna conc files
    pre_dna_files, post_dna_files = getMatchedPrePostFiles(dirname)

    # create empty list to hold all plate ids found
    list_merged_plates = []

    # create empty dict where key will be sample_id and values will be plate_ids
    sample_dict = {}

    # create empty df to hold results for all plates
    pre_all_plate_df = pd.DataFrame()
    post_all_plate_df = pd.DataFrame()

    # loop through all dna conc plates and merge with density and volume files
    # and calculate amount of sequins to add to each fraction
    for pre_dna in pre_dna_files:

        prefix = "pre"

        # generate df of DNA conc values
        DNA_conc_df = getConc(dirname, pre_dna)

        # get plate name by removing DNA conc file prefix
        plateid = pre_dna.replace(prefix, "")
        plateid = plateid.replace(".txt", "")

        # creat df's from density and volume files
        volume_df = getVolumes(dirname, plateid)
        density_df, density_emptyrow_df = getDensity(dirname, plateid)

        # merge dna conc, density, and volume df's
        merged_df, list_merged_plates, sample_dict = getMergedPlates(
            DNA_conc_df, volume_df, density_df, plateid, list_merged_plates, sample_dict, prefix)

        # concat merged_df from current dna plate with master df of all dna plates
        pre_all_plate_df = pd.concat([pre_all_plate_df, merged_df],
                                     axis=0, ignore_index=True)

    # loop through all dna conc plates and merge with density and volume files
    # and calculate amount of sequins to add to each fraction
    for post_dna in post_dna_files:

        prefix = "post"

        # generate df of DNA conc values
        DNA_conc_df = getConc(dirname, post_dna)

        # get plate name by removing DNA conc file prefix
        plateid = post_dna.replace(prefix, "")
        plateid = plateid.replace(".txt", "")

        # creat df's from density and volume files
        volume_df = getVolumes(dirname, plateid)
        density_df, density_emptyrow_df = getDensity(dirname, plateid)

        # merge dna conc, density, and volume df's
        merged_df, list_merged_plates, sample_dict = getMergedPlates(
            DNA_conc_df, volume_df, density_df, plateid, list_merged_plates, sample_dict, prefix)

        # concat merged_df from current dna plate with master df of all dna plates
        post_all_plate_df = pd.concat([post_all_plate_df, merged_df],
                                      axis=0, ignore_index=True)

    # add resuspension volume following PEG precipitation
    post_all_plate_df = updatePostVolume(post_all_plate_df, resuspend_vol)

    # calculate mass per fraction in pre and post df
    pre_all_plate_df, post_all_plate_df = addFractionMass(
        pre_all_plate_df, post_all_plate_df)

    # all_plate_df = pd.merge(pre_all_plate_df, post_all_plate_df, on=[
    #                         'Sample barcode', 'Fraction #', 'Density'])

    all_plate_df = pd.merge(pre_all_plate_df, post_all_plate_df[['Sample barcode', 'Plate barcode', 'Fraction #', 'Density', 'post_mass_(ng)']], on=[
                            'Sample barcode', 'Plate barcode', 'Fraction #', 'Density'], how='left')

    # read project_database.csv into  a dataframe
    project_df = pd.read_csv(PROJECT_DIR / 'project_database.csv', header=0, usecols=['Sample_Name', 'Replicate_Group', 'ITS_sample_id'], converters={
        'ITS_sample_id': str})

    # add user sample name and replicate group to all_plate_df
    all_plate_df = updateAllPlate(all_plate_df, project_df)

    pdf_files = comparePrePostDNAvsDensity(
        all_plate_df, sample_dict, total_fractions)

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
        PROJECT_DIR / f"Compare_pre_vs_post_{date}.pdf")
    merger.close()

    for pdf in pdf_files:
        # delete indidvidual group figure pdf
        os.remove(pdf)
    # # make pdf plots of density vs DNA conc comparing different versions of sampe initial sample
    # if any(len(plates) > 1 for plates in sample_dict.values()):
    #     compareDNAvsDensityVersions(
    #         all_plate_df, sample_dict, total_fractions)


##########################
##########################


if __name__ == "__main__":
    main(-1, -1)
