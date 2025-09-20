#!/usr/bin/env python3

# USAGE:   python merge.SIP.fraction.files.loop.py


from pathlib import Path
import pandas as pd
import numpy as np
import sys
import os
from datetime import datetime
from sqlalchemy import create_engine
import matplotlib.pyplot as plt
from PyPDF2 import PdfMerger

# call exists() function named 'file_exists'
from os.path import exists as file_exists


##########################
##########################
def readSQLdb():

    # # path to sqlite db for condensed fraction info
    # sql_db_path = f'{dirname}/fraction_selection_file.csv.db'

    # path to sqlite db for condensed fraction info
    sql_db_path = PROJECT_DIR / 'project_database.db'

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



# ##########################
# ##########################
# def usePREandPOST():
#     pre_post = input('Do DNA conc files have "post" prefix? (Y/N):   ')

#     if (pre_post == 'Y') or (pre_post == 'y'):
#         pre_post = True

#     elif (pre_post == 'N') or (pre_post == 'n'):
#         pre_post = False
#     else:
#         print("Sorry, you must choose Y or N. \n\nAborting\n\n")
#         sys.exit()

#     return pre_post

# ##########################
# ##########################

##########################
##########################


def getMatchedFiles(dirname, ext, pre_post):
    # create empty list to hold matching file sets
    list_matched_files = []

# loop through all files in directory, find sets of corresponding density, dna conc, and volume files
    for file in os.listdir(dirname):
        # if file.endswith(ext):
        if file.endswith(ext) and not file.startswith('~$'):

            # extract plate id from file name from density file name and add to plate id list
            plateid = file.replace(".xlsx", "")

            # create volume check file name
            vol_file = dirname+"/"+plateid+".CSV"

            # check for DNA conc with prefix 'post' if DNA conc was measured
            # before CsCl purification and after pellet resuspension
            if pre_post == True:
                # create dna conc file name
                conc_file = dirname+"/post"+plateid+"post.txt"

            else:
                # create dna conc file name
                conc_file = dirname+"/"+plateid+".txt"

            # check if .xlsx file has corresponding conce (.txt) and volume (.csv) files
            if (file_exists(conc_file)):
                if (file_exists(vol_file)):
                    list_matched_files.append(plateid)
                else:
                    print(
                        f'\n\n Warning: File was not found\nVolume file{vol_file}\n\n')
                    continue
            else:
                print(
                    f'\n\n Warning: File was not found\nDNA concentration file {conc_file} \n\n')
                continue

        else:
            continue

    # quit script if directory doesn't contain any matched sets of density, conc, volume files
    if len(list_matched_files) == 0:
        print("\n\n Did not find any matched sets of files.  Aborting program\n\n")
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

    my_density_df = pd.read_excel(dens_path, header=0, engine=("openpyxl"), usecols=['Plate barcode', 'Sample barcode', 'Well Pos', 'Fraction #', 'Density', 'Spike-in Set', 'Spike-in Mass (pg)'],
                                  converters={'Plate barcode': str, 'Sample barcode': str, 'Fraction #': int, 'Spike-in Mass (pg)': float})
    # add 'SIP' to plate barcode column to match actual barcode
    # my_density_df['Plate barcode'] = 'SIP' + my_density_df['Plate barcode']

    # my_density_df = my_density_df.dropna()

    my_density_df = my_density_df[my_density_df['Density'].notna()]

    my_density_df['Density'] = my_density_df['Density'].astype(float)

    my_density_df = my_density_df.round({'Density': 4})

    my_density_df['Spike-in Mass (pg)'] = my_density_df['Spike-in Mass (pg)'].astype(float)

    return my_density_df

##########################
##########################

##########################
##########################


def getConc(my_dirname, my_plateid, pre_post):

    # check for DNA conc with prefix 'post' if DNA conc was measured
    # before CsCl purification and after pellet resuspension
    if pre_post == True:
        # create dna conc file name
        conc_path = my_dirname+"/post"+my_plateid+"post.txt"

    else:
        # create dna conc file name
        conc_path = my_dirname+"/"+my_plateid+".txt"

    # conc_path = my_dirname+"/"+my_plateid+".txt"

    tmp_conc_file = 'tmp_conc.txt'

    with open(tmp_conc_file, 'w') as outfile:
        with open(conc_path, 'r') as file:
            for line in file:
                if not line.isspace():
                    outfile.write(line)

    # # read in DNA conc file
    # conc_path = my_dirname+"/"+my_plateid+".txt"

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

    # replace dna conc values <= 0 with 0.001 ng/ul.  Clarity/ITS won't accept a conc <= 0
    my_DNA_conc_df["[Concentration]"] = np.where(my_DNA_conc_df["[Concentration]"].astype(
        float) <= 0, 0.001, my_DNA_conc_df["[Concentration]"].astype(float))

    # round DNA concentration
    my_DNA_conc_df = my_DNA_conc_df.round({'Concentration]': 3})

    try:
        os.remove(tmp_conc_file)

    except:
        print(f'\nError deleting {tmp_conc_file}')

    return my_DNA_conc_df

##########################
##########################


##########################
##########################
def mergeIndividualPlates(dirname, matched, pre_post):

    # create dictionarly to hold merged df for each plateid
    # the plate id is the key, and the merged df is the value
    d = {}

    # create empty list to hold all plate ids found
    list_merged_plates = []

    # merge density, dna con, volume files for each fraction plate
    # and fill dict d{} described above
    for plateid in matched:
        volume_df = getVolumes(dirname, plateid)
        density_df = getDensity(dirname, plateid)
        DNA_conc_df = getConc(dirname, plateid, pre_post)

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
        # create list of successfully merged plate IDs
        list_merged_plates.append(plateid)

    # quit script if were not able to successfully merge any density, conc, volume files
    if len(list_merged_plates) == 0:
        print("\n\n Did not sucessfully merge sets of files\n\n")
        sys.exit()

    else:  # sort list of sucessfully merged fraction plates
        list_merged_plates.sort()
        print("\nList of merged sample plates:\n\n", list_merged_plates)

    return list_merged_plates, d

##########################
##########################


##########################
##########################
def setPassFailFractions (result_df):
    
    # get list of unique group names in project
    groups = sorted(result_df['Replicate_Group'].unique().tolist())
    
    # set Make_Lib to 1 for all libs as default
    result_df['Make_Lib'] = 1
    
    complete_isotope_set = {'O18','C13','N15','Unlabeled'}

    # loop through groups
    for g in groups:
        
        # get list of isotopes used in group.E.g. ["O18", "Unlabled"]
        isotopes = result_df[result_df['Replicate_Group']==g]['isotope_label'].unique().tolist()
        
        # check for isotope values that are not in the complete expected list of isotope values
        if not set(isotopes).issubset(complete_isotope_set):
            print (f"\n\nUnexpeced isotope value in group {g}\n\nAborting script\n")
            sys.exit()

        
        # set density range used for making libraries
        elif "O18" in isotopes:
            
            # add column idenitfying possible samples of lib creation based on density range
            result_df['Make_Lib'] = np.where(
                ((result_df['Replicate_Group'] == g) & ((result_df['Density (g/mL)'] > 1.78) | (result_df['Density (g/mL)'] < 1.68))), 0, result_df['Make_Lib'])
            
        elif "C13" in isotopes:
            
            # add column idenitfying possible samples of lib creation based on density range
            result_df['Make_Lib'] = np.where(
                ((result_df['Replicate_Group'] == g) & ((result_df['Density (g/mL)'] > 1.768) | (result_df['Density (g/mL)'] < 1.68))), 0, result_df['Make_Lib'])
            
        elif "N15" in isotopes:
            
            # add column idenitfying possible samples of lib creation based on density range
            result_df['Make_Lib'] = np.where(
                ((result_df['Replicate_Group'] == g) & ((result_df['Density (g/mL)'] > 1.76) | (result_df['Density (g/mL)'] < 1.68))), 0, result_df['Make_Lib'])
            
        # else:
        #     print (f"\n\nCould not determine isotopes used in group {g}\n\nAborting script\n")
        #     sys.exit()


    
    # always set Make_Lib to 0 for first fraction collected
    result_df['Make_Lib'] = np.where(
         result_df['Fraction #'] == 1, 0, result_df['Make_Lib'])

    return result_df
##########################
##########################

##########################
##########################
def mergeAllPlates(merged_dict):

    # create new dataframe combining all entries in dictionary d[plateid]
    result_df = pd.concat(merged_dict.values(), ignore_index=True)

    # # add column idenitfying possible samples of lib creation based on density range
    # result_df['Make_Lib'] = np.where(
    #     ((result_df['Density'] > 1.78) | (result_df['Density'] < 1.67)), 0, 1)
    
    

    # result_df['Make_Lib'] = np.where(
    #     result_df['Fraction #'] == 1, 0, result_df['Make_Lib'])

    #### THIS SECTION ALLOWS USER TO INCLUDE/EXCLUDE FRACTIONS WITHOUT SEQUIN ADDITION ####
    # miss_sequins = str(input(
    #     """\n\nDo you wish to INCLUDE fractions lacking sequins(Y/N)? Default == 'N' """) or "N")

    # if (miss_sequins == 'Y' or miss_sequins == 'y'):
    #     print("Ok, libraries might be made from fractions that do not have sequins\n\n")

    # elif (miss_sequins == 'N' or miss_sequins == 'n'):
    #     # exclude fractions that lack sequin addition
    #     result_df = result_df[result_df['Spike-in Mass (pg)'].notna()]

    # else:
    #     print("Sorry, you must choose 'Y' or 'N' next time. \n\nAborting\n\n")
    #     sys.exit()
    ############### END OF SECTION ALLOWING USER TO INCLUDE/EXCLUDE FRACTIONS WITHOUT SEQUIN ADDITION ##############



    # result_df = result_df[result_df['Make_Lib'] == 1]

    # low_density_fractions = [2, 3, 4]

    # result_df['Make_Lib'] = np.where(
    #     result_df['Fraction #'].isin(low_density_fractions), 1, 0)

    # # add column idenitfying possible samples of lib creation based on density range
    # result_df['Make_Lib'] = np.where(
    #     ((result_df['Fraction #'] > 20) | (result_df['Fraction #'] < 5)), 0, 1)

    # rename some columns
    result_df = result_df.rename(columns={'Plate barcode': 'Plate Barcode', 'Sample barcode': 'Sample Barcode', "[Concentration]": "DNA Concentration (ng/uL)", "Density": "Density (g/mL)",
                                          "VOLAVG": "Fraction Volume (uL)", "Spike-in Set": "Sequin Mix", "Spike-in Mass (pg)": "Sequin Mass (pg)"})

    # drop extraneous columns
    result_df.drop(['RACKID', 'TUBE', 'Well'], inplace=True, axis=1)

    result_df.sort_values(by=['Sample Barcode', 'Plate Barcode', 'Fraction #'],
                          inplace=True, ignore_index=True)

    return result_df
##########################
##########################


##########################
##########################
def removeEmptyFractions(result_df):

    # ask user for total number of fractions collected
    total_fractions = float(
        input("\n\nEnter the total # fractions collected (default 24): ") or 24)

    if (total_fractions <= 0):
        print('\n\nError.  Fractions must be >0.  Aborting.\n\n')
        sys.exit()

    result_df = result_df[result_df['Fraction #'] <= total_fractions]

    return result_df, total_fractions
##########################
##########################

##########################
##########################


def resolveDuplicates(result_df, dups_df2, dup_list):

    # end script if deplication file cannot be found
    if not (file_exists(MERGE_DIR / 'deduplication.csv')):
        print("Could not find 'deduplication.csv'.   Aborting script\n\n")
        sys.exit()

    else:
        # create empty dict of storying sample id (key) and plate id (value)
        # from info in deduplication.csv file provided by user
        d = {}
        with open(MERGE_DIR / "deduplication.csv") as f:
            for line in f:
                (key, val) = line.split(",")
                d[key] = val.rstrip('\n')

    # loop through list of all duplicate samples
    for s in dup_list:
        # find plate id from deduplication.csv that user wants to keep
        # abort script if a duplicate sample is not listed in deduplication.csv
        try:
            keep_p = d[s]
        except KeyError:
            print(
                f'There are duplicates of sample {s}, but sample {s} is not in deduplication.csv\n\nAborting\n')
            sys.exit()

        # confirm that df has rows that match the sample_id AND the plate_id listed
        # in deduplication.csv.  If not, then quit program.
        if result_df[(result_df['Sample Barcode'] == s) & (
                result_df['Plate Barcode'] == keep_p)].shape[0] == 0:

            print(
                f'\nCould not find sample {s} in plate {keep_p}. Check deduplication.csv for errors\n\n')
            sys.exit()

        # drop rows that match sample s and do NOT match plate_id you wish to keep (keep_p)
        # note the ~ for NOT in the filter for plate barcode matching
        result_df = result_df.drop(result_df[(result_df['Sample Barcode'] == s) & ~(
            result_df['Plate Barcode'] == keep_p)].index)

    return result_df
##########################
##########################

##########################
##########################


def findDuplicateSamples(result_df):

    find_dups_df = result_df.groupby(['Sample Barcode', 'Plate Barcode'])[
        'Fraction #'].agg('count').reset_index()

    find_dups_df = find_dups_df.rename(
        columns={'Fraction #': 'Number of fractions'})

    dups_df2 = find_dups_df[find_dups_df['Sample Barcode'].duplicated()]

    dup_list = list(dups_df2['Sample Barcode'].unique())

    if len(dup_list) > 0:
        # print(df2[(df2['Courses'].isin(y))].copy())
        print('\n\n Duplicate samples were found on multiple SIP fraction plates. See below and open duplicate_samples.csv to see problem:\n\n')
        print(find_dups_df[find_dups_df['Sample Barcode'].isin(dup_list)])
        find_dups_df[find_dups_df['Sample Barcode'].isin(dup_list)].to_csv(
            'summary_duplicate_samples.csv', index=False)

        keep_going = str(input("""
        There are three options for the next step. 
        Do you wish to deduplicate, keep duplicates, or quit? 
        options: (dedup/keep/quit):  """) or "quit")

        if (keep_going == 'dedup'):
            print("\n\nOk, proceeding with deduplication\n\n")

            # call function to determine which sample version to
            # use in library creation
            result_df = resolveDuplicates(result_df, dups_df2, dup_list)

        elif (keep_going == 'keep'):
            print("""
                  \n
                  \n
                  Ok, we'll keep going with duplicate samples
                  This means we'll make libraries from >1 version
                  of the same sample, which could be confusing
                  """)

        elif (keep_going == 'quit'):
            print('\nOk, aborting script\n\n')
            sys.exit()
        else:
            print(
                "\nSorry, you must choose 'dedup' or 'keep' or 'quit' next time. \n\nAborting\n\n")
            sys.exit()

    return result_df
##########################
##########################


############################
############################
def updateLibInfo(my_result_df, my_project_df):

    # make group_dict dictionary where key is ITS sample ID and value is replicate group
    group_dict = dict(zip(my_project_df.ITS_sample_id,
                      my_project_df.Replicate_Group))

    # make group_dict dictionary where key is ITS sample ID and value is sample name
    name_dict = dict(zip(my_project_df.ITS_sample_id,
                     my_project_df.Sample_Name))
    
    
    # make group_dict dictionary where key is ITS sample ID and value is isotope
    iso_dict = dict(zip(my_project_df.ITS_sample_id,
                     my_project_df.isotope_label))

    # add column using group_dict
    my_result_df['Replicate_Group'] = my_result_df['Sample Barcode'].map(
        group_dict)

    # add column of fraction sample name by concat parent sample name with the fraction #
    my_result_df['Fraction_sample_name'] = my_result_df['Sample Barcode'].map(
        name_dict) + "_" + my_result_df['Fraction #'].astype(str)
    
    # add column using group_dict
    my_result_df['isotope_label'] = my_result_df['Sample Barcode'].map(
        iso_dict)

    # make sure replicate group and fraction sample ids were assigned to all fractions
    if (my_result_df['Replicate_Group'].isnull().values.any()):
        print("\n\n")
        print(
            '\n\n Could not assign Replciate_Group to at least one sample. Aborting. Check error file. \n\n')

        my_result_df.to_csv(PROJECT_DIR / 'error.desnity.volume.merge.csv', index=False)
        sys.exit()

    elif (my_result_df['Fraction_sample_name'].isnull().values.any()):
        print("\n\n")
        print(
            '\n\n Could not assign Fraction_sample_name to at least one sample. Aborting. Check error file. \n\n')
        my_result_df.to_csv(PROJECT_DIR / 'error.desnity.volume.merge.csv', index=False)
        sys.exit()
        
    elif (my_result_df['isotope_label'].isnull().values.any()):
        print("\n\n")
        print(
            '\n\n Could not find isotope label to at least one sample. Aborting. Check error file. \n\n')
        my_result_df.to_csv(PROJECT_DIR / 'error.desnity.volume.merge.csv', index=False)
        sys.exit()    

    # get a list of columns
    cols = list(my_result_df)
    
    # move the column to head of list using index, pop and insert
    cols.insert(0, cols.pop(cols.index('isotope_label')))
    
    # move the column to head of list using index, pop and insert
    cols.insert(0, cols.pop(cols.index('Replicate_Group')))

    # move the column to head of list using index, pop and insert
    cols.insert(0, cols.pop(cols.index('Fraction_sample_name')))

    # use ix to reorder
    my_result_df = my_result_df.loc[:, cols]

    return my_result_df
############################
############################


##########################
##########################
def makeDNAvsDensityPlots(my_lib_df):

    # get list of unique group names in project
    groups = sorted(my_lib_df['Replicate_Group'].unique().tolist())

    # empty list to later hold names of pdfs for each group figure
    # this will be used ot merge multiple pdfs at end of script
    pdf_files = []

    # loop through list of groups
    for g in groups:

        # get list of samples in group
        samples = sorted(my_lib_df[my_lib_df['Replicate_Group'] == g]
                         ['Sample Barcode'].unique().tolist())

        # creation matliplot object
        f = plt.figure()

        # loop through samples and add line to plt.plot
        for s in samples:
            # x = lib_df[(lib_df['Sample Barcode'] == s) & (
            #     lib_df['Fraction #'].between(1, 24))]['Density (g/mL)']
            # y = lib_df[(lib_df['Sample Barcode']
            #            == s) & (lib_df['Fraction #'].between(1, 24))]['DNA Concentration (ng/uL)']

            # x = lib_df[(lib_df['Sample Barcode'] == s) & (
            #     lib_df['Density (g/mL)'].between(1.669, 1.781))]['Density (g/mL)']
            # y = lib_df[(lib_df['Sample Barcode']
            #            == s) & (lib_df['Density (g/mL)'].between(1.669, 1.781))]['DNA Concentration (ng/uL)']

            x = my_lib_df[(my_lib_df['Sample Barcode'] == s) & (
                my_lib_df['Make_Lib'] == 1)]['Density (g/mL)']
            y = my_lib_df[(my_lib_df['Sample Barcode']
                           == s) & (my_lib_df['Make_Lib'] == 1)]['DNA Concentration (ng/uL)']

            # make new column that joins sample barcode with fraction_sample_name
            my_lib_df['combo_name'] = my_lib_df['Sample Barcode'] + \
                '-'+my_lib_df['Fraction_sample_name']

            # extract user provided sample name by removing the suffix "_fraction#" from fraction name
            name_list = my_lib_df[my_lib_df['Sample Barcode'] ==
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

        plt.plot([1.66, 1.8], [1, 1], 'k-', lw=1, dashes=[2, 2])

        # add plot title, axes labels, and legend to group plot
        plt.xlabel("Density (g/mL)")
        plt.ylabel("DNA Concentration (ng/uL)")
        plt.title(f'Replicate Group: {g}')
        plt.legend(fontsize='x-small')
        # plt.show()
        f.savefig(f'UserName_DNAvsDensity_{g}.pdf',
                  format="pdf", bbox_inches="tight")

        # add name of group figure pdf
        pdf_files.append(f'UserName_DNAvsDensity_{g}.pdf')

        plt.close(f)

    # Create and instance of PdfMerger() class
    merger = PdfMerger()

    # loop through group figure pdfs and merge them into one
    for pdf in pdf_files:
        # Append PDF files
        merger.append(pdf)
        # # delete indidvidual group figure pdf
        # os.remove(pdf)

    # Write out the merged PDF
    merger.write(PLOT_DIR / "merged_POST_DNAvsDensity_plots.pdf")
    merger.close()

    for pdf in pdf_files:
        # delete indidvidual group figure pdf
        os.remove(pdf)

    return
##########################
##########################


#########################
#########################
def createSQLdb(df):
    
    # get current date and time, will add to archive database file name
    date = datetime.now().strftime("%Y_%m_%d-Time%H-%M-%S")

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
    df.to_sql(table_name, engine, if_exists='replace', index=False) 

    engine.dispose()

    return
#########################
#########################


##########################
##########################
###    MAIN Program    ###
##########################
##########################


PROJECT_DIR = Path.cwd()

MERGE_DIR = PROJECT_DIR / "3_merge_density_vol_conc_files"

ARCHIV_DIR = PROJECT_DIR / "archived_files"
# ARCHIV_DIR.mkdir(parents=True, exist_ok=True)

LIB_DIR = PROJECT_DIR / "4_make_library_analyze_fa"
# LIB_DIR.mkdir(parents=True, exist_ok=True)

FIRST_DIR = LIB_DIR / "A_first_attempt_make_lib"
# FIRST_DIR.mkdir(parents=True, exist_ok=True)

PLOT_DIR = PROJECT_DIR / "DNA_vs_Density_plots"
PLOT_DIR.mkdir(parents=True, exist_ok=True)


# get current directory
current_directory = os.getcwd()

subdirectory_name = "3_merge_density_vol_conc_files"

# create path to subdirectory where density, volume, and dna conc files are located
dirname = os.path.join(current_directory, subdirectory_name)


# # determine if DNA conc was measured before CsCl purification
# # and if this was used to determine sequin addition
# # this was change in protocol and impacts whetheror not
# # there is a "post" prefix on the DNA conc file used in merging
# pre_post = usePREandPOST()

# for now, assume DNA conc files have "post" prefix
pre_post = True  # DNA conc files have "post" prefix


# file extension for desnity file
ext = ('.xlsx')

# # read project_database.csv into  a dataframe
# project_df = pd.read_csv(PROJECT_DIR / 'project_database.csv', header=0, converters={
#     'ITS_sample_id': str})

# read project_database.db into  a dataframe
project_df = readSQLdb()


# get list of matched sets of density, dna conc, and volume files
matched = getMatchedFiles(dirname, ext, pre_post)


# merge files density, dnaconc, and volume files for individual plates into individual dataframes
list_merged_plates, merged_dict = mergeIndividualPlates(
    dirname, matched, pre_post)

# combine all merged results in individual dataframes into one dataframe
# and select specific fraction to go into library creation
result_df = mergeAllPlates(merged_dict)

# remove empty fractions from result_df

result_df, total_fractions = removeEmptyFractions(result_df)

# search results_df for duplicate sampel entries, e.g. re-running a sample on another plate
result_df = findDuplicateSamples(result_df)

# add user sample names and replicate group info to results_df
result_df = updateLibInfo(result_df, project_df)


# call fuction to set Make_Lib to 1 or 0 based on density
result_df = setPassFailFractions (result_df)

# creat library selection file
result_df.to_csv(FIRST_DIR / 'library_selection_file.csv', index=False)

# make pdf plots of DNA vs Density
makeDNAvsDensityPlots(result_df)


################################
# update project database with samples successfully merged
################################


# find unique list of sample IDs in merged results_df at end of merging script
good_merged_list = result_df['Sample Barcode'].unique().tolist()

# # import project_database.csv into database
# update_project_df = pd.read_csv(PROJECT_DIR / 'project_database.csv',
#                                 header=0, converters={'ITS_sample_id': str})

# read project_database.db into database
update_project_df = readSQLdb()

# upldate values im 'Merged_files' column
update_project_df['Merged_files'] = np.where(
    (update_project_df['ITS_sample_id'].isin(good_merged_list)), update_project_df['Merged_files']+1, update_project_df['Merged_files'])


# get current date and time, will add to archive database file name
date = datetime.now().strftime("%Y_%m_%d-Time%H-%M-%S")

# # create archive of database file by renaming file and adding date and time to file name
# os.rename('project_database.csv', f'archive_project_database_{date}.csv')
Path(PROJECT_DIR /
     "project_database.csv").rename(ARCHIV_DIR / f"archive_project_database_{date}.csv")
Path(ARCHIV_DIR / f"archive_project_database_{date}.csv").touch()

# archive old project_database.db and replace with updated version
createSQLdb(update_project_df)

# make updated version of project_database.csv
update_project_df.to_csv(PROJECT_DIR / 'project_database.csv', index=False)



# Create success marker to indicate script completed successfully
from pathlib import Path
status_dir = Path.cwd() / ".workflow_status"
status_dir.mkdir(exist_ok=True)
success_file = status_dir / "merge.SIP.fraction.files.loop.success"
success_file.touch()
