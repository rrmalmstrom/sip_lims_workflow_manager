#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pandas as pd
import sys
import os
import math
from pathlib import Path
import shutil
from datetime import datetime

# call exists() function named 'file_exists'
from os.path import exists as file_exists




###################
###################
def makeQPCRfile (final_df):

    qpcr_df = final_df.copy()    

    qpcr_cols = ['Date','Library creator','Library/ Pool Name','Plate LIMS ID','Plate Name','blank','Library Type gDNA, cDNA','Library Amplified or Unamp','BioA or FA Conc  in pM','Library Length (Fragment + Adaptors) (bp)','Instructions']

    
    qpcr_df['BioA or FA Conc  in pM'] = qpcr_df['nmole/L'] * 1000
    
    qpcr_df['BioA or FA Conc  in pM'] = qpcr_df['BioA or FA Conc  in pM'].astype(int)
    
    # create three new columns by parsing Sample_ID string using "." as delimiter
    qpcr_df[['Date','Library/ Pool Name']] = qpcr_df.Source_Barcode.str.split("_", expand=True)
    
    qpcr_df['Plate Name'] = ""
    
    qpcr_df['Date'] = datetime.now().strftime("%m/%d/%Y")
    
    qpcr_df['Library creator'] = "Rex Malmstrom"
    
    qpcr_df['Library Type gDNA, cDNA'] = "gDNA"
    
    qpcr_df['Library Amplified or Unamp'] = "Amp"
    
    qpcr_df['Instructions'] = "Pool from Microscale App requiring qPCR"
    
    qpcr_df['blank'] = ""
    
    qpcr_df.rename(columns={'Avg. Size':'Library Length (Fragment + Adaptors) (bp)','Destination_Tube_Barcode':'Plate LIMS ID'}, inplace=True)
    
    qpcr_df = qpcr_df[qpcr_cols]

    return qpcr_df
###################
###################


###################
###################
def makeFinalPoolTransfer(pool_df):
    
    # copy rows of pool_df with passed pools
    final_df = pool_df.loc[pool_df['Passed_Pool'] == 1].copy()
    
    # # select barcodes needs for final pooling
    # final_df = final_df[['Dest_Tube_Size_Selected', 'Pool_Barcode']]
    
    # df[['V','allele']] = df['V'].str.split('-',expand=True)
    
    final_df['copy_Dest_tube'] = final_df['Dest_Tube_Size_Selected']
    
    final_df[['number','pool']] = final_df['copy_Dest_tube'].str.split('_',expand=True)
    
    tmp_df= final_df[final_df['pool'].duplicated() ==True]
    
    if tmp_df.shape[0]>0:
        dup_list =tmp_df['pool'].tolist()
        duplicate = input((f"\n\nThere are pools with duplicate siz-selected tubes,i.e. {dup_list}. Do you with to continue (y/n)?  ") or 'n')
        
        if duplicate != 'y' and duplicate != 'Y':
            print ('\n\nOk. Please fix pool_summary.csv.  Aborting script\n\n')
            sys.exit()
    
    
    
    # this is a bit confusing, but the Dest_Tube_Size_Selected barcoded tube
    # is not the source tube for the final pooling step.  Thus, it is renamed
    # the Pool_Barcode is the Clarity container ID, e.g. 27-XXXXX
    # the containter ID has not been used yet, and the label hasn't been printed yet
    final_df = final_df.rename(
        columns={'Dest_Tube_Size_Selected': 'Source_Name', 'Pool_Barcode': 'Destination_Tube_Name'})

    # add additional columns expected by the Hamilton method
    final_df['Source_Barcode'] = final_df['Source_Name']

    final_df['Destination_Tube_Barcode'] = final_df['Destination_Tube_Name']
    
    transfer_vol = float(input("\nWhat is transfer volume for loading final LIMS tubes? default is 49:   ")  or 49)

    if transfer_vol <= 0:
        print ('\nTransfer volumes must by > 0uL.  Aborting script\n')
        sys.exit()
    
  
    final_df['Transfer_Volume'] = transfer_vol

    final_col_list = ['Source_Name', 'Source_Barcode', 'Transfer_Volume',
                      'Destination_Tube_Name', 'Destination_Tube_Barcode','nmole/L','Avg. Size']
    
    # final_df.rename(columns={'Avg. Size':'Avg_size_(bp)'})
    
    # put columns in order expected by Hamilton method
    final_df = final_df.reindex(columns=final_col_list)
    
    qpcr_df = makeQPCRfile (final_df)


    return final_df, qpcr_df

###################
###################


###################
###################
def makeFinalTubeLabels(final_df):
    
    # make dict where key is pool name and value is dest tube size id
    final_dict = dict(zip(final_df.Source_Barcode,
                      final_df.Destination_Tube_Name))
  
    # add info to start of barcode print file indicating the template and printer to use
    x = '%BTW% /AF="\\\\bartender\shared\\templates\JGI_Label_BCode5_Rex.btw" /D="%Trigger File Name%" /PRN="bcode5" /R=3 /P /DD\r\n%END%\r\n\r\n\r\n'


    bc_file = open(FINISH_DIR / "Clarity_containter_labels_for_size-selected_pools.txt", "w")

    bc_file.writelines(x)

    # add barcodes of library destination plates, dna source plates, and buffer plate
    for p in final_dict.keys():
        tube_name = p.split('_')
        pool_num = tube_name[0].split('-')
        bc_file.writelines(f'{final_dict[p]},{pool_num[0]},{tube_name[1]}\r\n')

    bc_file.close()
    
    return
###################
###################


###################
###################
def incrementPoolLetterInName(redo_pool_list):

    # new_pool_list=[]
    pool_dict = {}

    # increment letter, e.g. 1A_NUSPU to 1B_NUSPU
    for i, r in enumerate(redo_pool_list):
        x = chr(ord(r[1])+1)

        s = r[:1] + x + r[2:]
        
        # new_pool_list.append(s)

        pool_dict[redo_pool_list[i]] = s    

    return pool_dict
    # return new_pool_list
###################
###################


###################
###################
def incrementPoolNumberInName(redo_dest_tube_list,new_dest_list):

    # empty dict where  key is old dest tube id and value
    # is new dest tube id, e.g. 1-1_XXXX : 1-2_XXXX
    redo_dict = {}

    # increment number, e.g. 1-1_NUSPU to 1-2_NUSPU
    for i, r in enumerate(redo_dest_tube_list):
        # x = chr(ord(r[1])+1)
        
        y = int(r[2])+1

        s = r[:2] + str(y) + r[3:]
        
        # double check if doing a 3rd attenpt at size selection without
        # requesting a whole new pool. There shouldn't be enough of the 
        # first pool remainin for 3 attempts
        if y == 3 and r not in new_dest_list:
            x = input((f"\n\n{r} will be on 3rd attempt at size selction, but a whole new pool has not been requested.  Do you wish to proceed (y/n)?  ")or'n')
        
            if x in ['y','yes','Y']:
                redo_dict[redo_dest_tube_list[i]] = s  
                
            else:
                print ('\n\nOk. Please update the pool_summary.csv file.  Aborting script\n\n')
                sys.exit()


        # double check if doing a > 4thrd attenpt at size selection 
        #There shouldn't be enough of the pooled material remaining for 5+ attempts
        elif y >4:
            x = input((f"\n\n{r} will be on >4th attempt at size selction, but the pool should be exhausted.  Do you with to proceed (y/n)?  ")or'n')
        
            if x in ['y','yes','Y']:
                redo_dict[redo_dest_tube_list[i]] = s  
                
            else:
                print ('\n\nOk. Please update the pool_summary.csv file.  Aborting script\n\n')
                sys.exit()


        else:
            redo_dict[redo_dest_tube_list[i]] = s    

    return redo_dict
###################
###################



###################
###################
def getPippinCassetteBarcode(my_pool_df):
    # parse first row entry for "Pippin_Cassette" to get base ID without "-#"
    base_bc = pool_df['Pippin_Cassette'].iloc[0].split("-")[0]

    # get next number for pippin cassette barcode
    next_bc = 1 + len(pool_df['Pippin_Cassette'].unique().tolist())

    
    return base_bc, next_bc
###################
###################

###################
###################
def addLaneAndPippinCassetteForReSize(rework_df, redo_pool_list,pip_bc_base, pip_next_bc):
    
    # create empty dicts for linkin pool# with lane# and cassette#
    lane_dict = {}

    cassette_dict = {}

    # create tuple of tuples indicating pairs of pippin lanes
    # tuple (1,3) indicates a pool should be loaded into lanes 1 and 3
    lane_pairs = ((1,3),(5,7),(9,11),(2,4),(6,8))
    
    
    # list through all pool# and create two dicts where key is pool# and
    # value is either the pippin lane# (lane_dict) or pippin cassette barcode
    # (cassette_dict) using modulo 10 instead of 12 because lanes 11 and 12 are used
    # for library standard positive controls and ladder
    for i, p in enumerate(redo_pool_list):
        if (i+1) % 5 == 0:
            lane_dict[p] = lane_pairs[4]
        else:
            pair_position = ((i+1) % 5) - 1
            lane_dict[p] = lane_pairs[pair_position]

        cassette_dict[p] = pip_bc_base + "-" + str((math.floor((i)/5))+pip_next_bc)

    # add column with Pippin lane # to df, but lane is a tuple because
    # pool is split into 2 lanes indicated in lane_pairs
    rework_df['Pippin_Lane'] = rework_df['Pool_Name'].map(lane_dict)
    
    # df[['b1', 'b2']] = pd.DataFrame(df['b'].tolist(), index=df.index)
    rework_df[['1st_Pippin_lane','2nd_Pippin_lane']] = pd.DataFrame(rework_df['Pippin_Lane'].tolist(),index=rework_df.index)
    
    # drop column containing lane tuple
    rework_df.drop(['Pippin_Lane'], axis=1, inplace=True)


    # add column with Pippin cassette barcode to df
    rework_df['Pippin_Cassette'] = rework_df['Pool_Name'].map(cassette_dict)

    return rework_df
###################
###################


###################
###################
def getFAbarcode(rework_df):
    # parse first row entry for "FA_plate_barcode" to get base ID without "-FA*"
    base_fa = rework_df['FA_plate_barcode'].iloc[0].split("-FA")[0]

    # get next number for FA barcode
    num_fa = 1 + int(rework_df['FA_plate_barcode'].iloc[0].split("-FA")[1])
    
    # join variables to make updated FA plate barcode
    next_fa = base_fa +"-FA"+str(num_fa)
    
    # replace old FA plate barcode with updated barcode
    rework_df['FA_plate_barcode'] = next_fa

    return rework_df
###################
###################

##########################
##########################
def FAplatePoolQC(my_pippin_list):

    # list will be refernced to convert row number into row letter
    row_list = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']

    # create empty dict where key will be pool name and value
    # will be FA well position
    well_dict = {}

    # loop through list of pool names
    for i, p in enumerate(my_pippin_list):

        # set row number as floor after dividing by 10
        r = math.floor((i)/10)
    

        # set column number as modulo of 10
        # use modulo 10 so that no pool is assigned
        # to columns 11 or 12. They ar reserved for
        # control and ladder in the FA plate
        c = ((i+1) % 10)

        if c == 0:
            c = 10

        well_dict[p] = row_list[r]+str(c)

    return well_dict
##########################
##########################


##########################
##########################
def makeTubeBarcodeFiles(rework_df, new_pool_dict):
    
    # make dict where key is pool name and value is dest tube size id
    pool_to_dest_tube_dict = dict(zip(rework_df.Pool_Name,
                      rework_df.Dest_Tube_Size_Selected))

    
    # this was older format for bartender templates.  The newer version below changes "/" to "\"
    # in the path to the template files  AF="*"
    # x = '%BTW% /AF="//bartender/shared/templates/JGI_Label_BCode5_Rex.btw" /D="%Trigger File Name%" /PRN="bcode5" /R=3 /P /DD\r\n%END%\r\n\r\n\r\n'

    # add info to start of barcode print file indicating the template and printer to use
    x = '%BTW% /AF="\\\\bartender\shared\\templates\JGI_Label_BCode5_Rex.btw" /D="%Trigger File Name%" /PRN="bcode5" /R=3 /P /DD\r\n%END%\r\n\r\n\r\n'


    bc_file = open(new_attempt_dir / "pooling_TUBES_barcode_labels.txt", "w")

    bc_file.writelines(x)

    # add tube labeles for pools that need full re-pooling
    for p in new_pool_dict.keys():
        tube_name = new_pool_dict[p].split('_')

        # make multiple copies of barcode labels
        for z in range(3):
            # bc_file.writelines(f'{p},{p}\n')
            bc_file.writelines(
                f'{new_pool_dict[p]},{tube_name[0]},{tube_name[1]}\r\n')

        # # add barcode with LIMS containter ID
        # bc_file.writelines(
        #     f'{pool_dict[p]},{tube_name[0]},{tube_name[1]}\n')


        size_tubename = pool_to_dest_tube_dict[new_pool_dict[p]].split('_')
        
        bc_file.writelines(
            f'{pool_to_dest_tube_dict[new_pool_dict[p]]},{size_tubename[0]},{size_tubename[1]}\r\n')


        # # create special label for tube that will collect
        # # size selected DNA recoverd from pippin
        # # add an number to name that can be iterated if rework
        # # is needed.  E.g. 1a_XXXXX becomes 1-1_XXXXX
        # bc_file.writelines(
        #     f'{tube_name[0]}1_{tube_name[1]},{tube_name[0]}1,{tube_name[1]}\n')
        
        # add a row of blank labels
        bc_file.writelines(',,\r\n')
        
        # remove this pool from dict of all pools to rework
        # because pools that need full re-pooling have different
        # tube label printing requirements than pools that
        # just need a second attempt at resizing
        pool_to_dest_tube_dict.pop(new_pool_dict[p])
        
    
    # add tube labels for pools that just need resizing
    for r in pool_to_dest_tube_dict.keys():
        
        if r not in new_pool_dict.keys():
            
            size_tubename = pool_to_dest_tube_dict[r].split('_')
            
            bc_file.writelines(
                f'{pool_to_dest_tube_dict[r]},{size_tubename[0]},{size_tubename[1]}\r\n')
            
            # add a row of blank labels
            bc_file.writelines(',,\r\n')

    
    bc_file.close()

    return
##########################
##########################



##########################
##########################
def makePippinBarcodeFile(rework_df):

    # get list of all pool numbers
    pippin_list = rework_df['Pippin_Cassette'].unique().tolist()

    fa_list = rework_df['FA_plate_barcode'].unique().tolist()

    # this was older format for bartender templates.  The newer version below changes "/" to "\"
    # in the path to the template files  AF="*"
    # x = '%BTW% /AF="//BARTENDER/shared/templates/ECHO_BCode8.btw" /D="%Trigger File Name%" /PRN="bcode8" /R=3 /P /DD\r\n\r\n%END%\r\n\r\n\r\n'


    # add info to start of barcode print file indicating the template and printer to use
    x = '%BTW% /AF="\\\BARTENDER\shared\\templates\ECHO_BCode8.btw" /D="%Trigger File Name%" /PRN="bcode8" /R=3 /P /DD\r\n\r\n%END%\r\n\r\n\r\n'


    bc_file = open(new_attempt_dir / "PIPPIN_CASSETTE_FA_PLATE_barcode_labels.txt", "w")

    bc_file.writelines(x)

    for p in pippin_list:

        bc_file.writelines(f'{p},pip.casset {p}\r\n')

    for fa in fa_list:

        bc_file.writelines(f'{fa},FA.plate {fa}\r\n')

    bc_file.close()

    return
##########################
##########################

##########################
##########################
# this verseion fo function assuming pool will be split into 1 pippin lane
def getWellList(FA_df):

    # list will be refernced to convert row number into row letter
    row_list = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']

    well_list = []

    num_fa_wells = len(FA_df['Dest_Tube_Size_Selected'].unique().tolist())

    num_rows = math.ceil(num_fa_wells/10)

    for i in range(1, (12*num_rows)+1):

        # set row number as floor after dividing by 12
        r = math.floor((i-1)/12)

        # set column number as modulo of 12
        c = ((i) % 12)

        if c == 0:
            well_list.append(row_list[r]+'12')

        else:
            well_list.append(row_list[r]+str(c))

    return well_list, num_rows
##########################
##########################


##########################
##########################
def makeFAinputFiles(rework_df):

    # list will be refernced to convert row number into row letter
    row_list = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']

    FA_df = rework_df[['Dest_Tube_Size_Selected',
                          'FA_plate_barcode', 'FA_well']].copy()

    FA_df['FA_plate_barcode'] = FA_df['FA_plate_barcode'].astype(str)

    FA_df['Dest_Tube_Size_Selected'] = FA_df['Dest_Tube_Size_Selected'].astype(str)

    FA_df['FA_well'] = FA_df['FA_well'].astype(str)

    FA_df['name'] = FA_df[['FA_plate_barcode', 'Dest_Tube_Size_Selected', 'FA_well']].agg(
        '.'.join, axis=1)

    my_well_list, my_num_rows = getWellList(FA_df)

    # drop unecessary columns so only have df with 'Destination_Well', 'Destination_ID', and 'name'
    FA_df.drop(['Dest_Tube_Size_Selected'], inplace=True, axis=1)

    tmp_fa_df = pd.DataFrame(my_well_list)

    tmp_fa_df.columns = ["Well"]

    tmp_fa_df = tmp_fa_df.merge(FA_df, how='outer', left_on=[
                                'Well'], right_on=['FA_well'])

    tmp_fa_df.index = range(1, tmp_fa_df.shape[0]+1)

    fabc = tmp_fa_df['FA_plate_barcode'].iloc[0]

    tmp_fa_df.drop(['FA_plate_barcode', 'FA_well'], inplace=True, axis=1)

    tmp_fa_df['name'] = tmp_fa_df['name'].fillna('empty_well')

    start = 0
    stop = 12

    for i in range(1, my_num_rows+1):

        print_df = tmp_fa_df.iloc[start:stop].copy()

        print_df.index = range(1, print_df.shape[0]+1)

        # df.loc[df.index[#], 'NAME']

        print_df.loc[print_df.index[10], 'name'] = 'LibStd'

        print_df.loc[print_df.index[11], 'name'] = 'ladder'

        print_df.to_csv(new_attempt_dir / f'FA_upload_{fabc}_row{row_list[i-1]}.csv', index=True, header=False)

        start = start + 12

        stop = stop + 12


##########################
##########################


##########################
##########################
def makePippinTransferFiles(rework_df):
    
    rework_df['Sample_volume_(uL)'] = 44

    rework_df['Marker_volume_(uL)'] = 11

    rework_df['Load_volume_(uL)'] = 25

    rework_df['Recover_volume_(uL)'] = 30

    rework_df['FA_transfer_vol_(uL)'] = 2.4
    
    # list with columns in the order expected by the Hamilton script
    col_list = ['Pool_Name'	,'Pool_Barcode'	,'Pippin_Cassette'	,'1st_Pippin_lane'	,'2nd_Pippin_lane'	,'Dest_Tube_Size_Selected'	,'Sample_volume_(uL)'	,'Marker_volume_(uL)'	,'Load_volume_(uL)',	'Recover_volume_(uL)'	,'FA_plate_barcode',	'FA_well'	,'FA_transfer_vol_(uL)']

    # rearrange columns
    rework_df = rework_df[col_list]


    # create pippin transfer file
    rework_df.to_csv(new_attempt_dir / 'PIPPIN_load_unload_transfer_file.csv', index=False, header=True)


    return
##########################
##########################



###################
###################
def reSizeModule(pool_df, rework_df):
    
    # make list of pools that need whole new pools
    new_dest_list = rework_df[rework_df['New_pool']
                              == 1]['Dest_Tube_Size_Selected'].unique().tolist()
    
    # make list of destination tubes  that need updating
    redo_dest_tube_list = rework_df['Dest_Tube_Size_Selected'].unique().tolist()
    
    # make dict that will be used to update destination tube id
    # the key is the old dest tube id and the value is the new tube id
    redo_dict= incrementPoolNumberInName(redo_dest_tube_list,new_dest_list)

    # add new dest tube name
    rework_df['Dest_Tube_Size_Selected'] = rework_df['Dest_Tube_Size_Selected'].map(redo_dict)

    # make list of pools that need whole new pools
    new_pool_list = rework_df[rework_df['New_pool']
                              == 1]['Pool_Name'].unique().tolist()

    # create dict where key is old pool name (e.g. 1A_NUSPU) and
    # value is new pool name (e.g. 1B_NUSPU).  The letter in the 
    # prefix is incremented from A to B, etc
    new_pool_dict= incrementPoolLetterInName(new_pool_list)
        
    # add new pool name to df by replacing old pool name
    # only sample that need a new round of pooling will
    # get an updated name... the fillna part keeps current pool name
    # if replacement not found in new_pool_dict
    rework_df['Pool_Name'] = rework_df['Pool_Name'].map(new_pool_dict).fillna(rework_df['Pool_Name'])
    

    # # generate new barcode for pippin cassette    
    pip_bc_base, pip_next_bc = getPippinCassetteBarcode(rework_df)

    redo_pool_list = rework_df['Pool_Name'].unique().tolist()
    
    redo_pool_list.sort()
    
    # add new pippin lanes and pippin cassette numbers to resize_df
    rework_df = addLaneAndPippinCassetteForReSize(rework_df, redo_pool_list,pip_bc_base, pip_next_bc ) 
    
    # generate new FA plate ID and FA well positions
    
    rework_df = getFAbarcode(rework_df)

    well_dict = FAplatePoolQC(redo_pool_list)
    
    # add new FA12 well position for each pool receiving rework
    rework_df['FA_well'] = rework_df['Pool_Name'].map(well_dict)
    
    # rework_df.drop(['Passed_Pool','New_pool'], inplace=True, axis=1)
    
    # reset FA results in rework_df to ''
    rework_df[['nmole/L', 'Avg. Size','Passed_Pool','New_pool']] = ''
    
    pool_df = pd.concat([pool_df,rework_df], ignore_index=True)
    
    
    
    # copy pool transfer files for pools that need new round of pooling
    for p in new_pool_list:
        pnum = p[0]
        
        transfer_file = first_attempt_dir / f"Pool_{pnum}_transfer_file.csv"
        
        
        if (file_exists(transfer_file)):
            shutil.copy(transfer_file,new_attempt_dir)
            
        else:
            print(f'\n\nCannot find transfer file for pool number {pnum}.  Aborting script\n\n')
            sys.exit()
    
    # update pool transfer files with new tube ids
    for p in new_pool_list:
        pnum = p[0]
        
        transfer_df = pd.read_csv(new_attempt_dir / f'Pool_{pnum}_transfer_file.csv',header=0)
        
        transfer_df['Destination_Tube_Name'] = transfer_df['Destination_Tube_Name'].map(new_pool_dict) 
    
        transfer_df['Destination_Tube_Barcode'] = transfer_df['Destination_Tube_Barcode'].map(new_pool_dict)
    
        # delete copy of original transfer file
        os.remove(new_attempt_dir / f'Pool_{pnum}_transfer_file.csv')
        
        # make new transfer file with updated tube ids
        transfer_df.to_csv(new_attempt_dir / f'Pool_{pnum}_transfer_file.csv', index=False, header=True)
    
    # make file for printing tube barcode labels with updated pool and  tube id's
    makeTubeBarcodeFiles(rework_df,new_pool_dict)
    
    # make file for printing pippin cassette and FA plate labels
    makePippinBarcodeFile(rework_df)
    
    # make FA input files
    makeFAinputFiles(rework_df)
    
    makePippinTransferFiles(rework_df)
    
    
    
    
    Path(POOL_DIR /
          "pool_summary.csv").rename(ARCHIV_DIR / f"archive_pool_summary_{date}.csv")
    Path(ARCHIV_DIR / f"archive_pool_summary_{date}.csv").touch()

    # create updated library info file
    pool_df.to_csv(POOL_DIR / 'pool_summary.csv', index=False, header=True)

###################
###################






###################
### MAIN PRORGRAM
###################

# get current date and time, will add to archive database file name
date = datetime.now().strftime("%Y_%m_%d-Time%H-%M-%S")

PROJECT_DIR = Path.cwd()

POOL_DIR = PROJECT_DIR / "5_pooling"

REWORK_DIR = POOL_DIR / "E_pooling_and_rework"

ATTEMPT_DIR = REWORK_DIR / "Attempt_1"

ARCHIV_DIR = PROJECT_DIR / "archived_files"

FINISH_DIR = POOL_DIR / "F_final_pooling_files"
FINISH_DIR.mkdir(parents=True, exist_ok=True)




# create df from pool summary
pool_df = pd.read_csv(POOL_DIR / 'pool_summary.csv', header=0)

# determine next increment number of FA plate barcode
FA_list = pool_df['FA_plate_barcode'].unique().tolist()

FA_list.sort()

last_FA = FA_list[-1]

next_FA_num = int(last_FA[-1])+1

# make last_df with only data from most recent pooling/size selection run, i.e.
# rows from the most recent FA plate based in FA plate increment number
last_df = pool_df.loc[pool_df['FA_plate_barcode']==last_FA].copy()

# confirm all pools have pass/fail value of 0 or 1
if last_df[~last_df['Passed_Pool'].isin([0,1])].shape[0]>0:
    print('\nSome pass/fail value is not 0 or 1. Aborting\n\n')
    sys.exit()

# copy rows of pool_df with failed pools
rework_df = last_df.loc[last_df['Passed_Pool'] == 0].copy()


rework_df = rework_df.sort_values(by=['Pool_Name'], ascending=True)

rework_df.reset_index(drop=True, inplace=True)

if rework_df.shape[0] == 0:
    all_done = (input("\nNo pools need rework. Is that correct (y/n)?   ")  or 'n')

    if all_done.lower() == 'y':
        
        # generate final_df to be used to make Hamilton transfer file
        final_df, qpcr_df = makeFinalPoolTransfer(pool_df)
        
        # make the Hamilton transfer file
        final_df.to_csv(FINISH_DIR / 'Size_selected_pools_transfer_file.csv',
                      index=False, header=True)
        
        qpcr_df.to_csv(FINISH_DIR / 'qPCR_pooling_form.csv', index=False, header=True)
        
        makeFinalTubeLabels(final_df)


        print("\n✅ SUCCESS: All pools meet quality criteria. Final files generated.")
        print("🎉 WORKFLOW COMPLETE: No further iterations needed.")

    else:    
        print('\nOk, please fix the pool_summary.csv file.  Aborting.\n\n')
        sys.exit()

else:

    # make new folder to hold output of this script
    # crnt_attempt_dir = os.getcwd()
    
    # rework_dir = str(Path(crnt_attempt_dir).parents[0])
    
    # first_attempt_dir = rework_dir+"/Attempt_1/"
    
    # new_attempt_dir = rework_dir+f"/Attempt_{next_FA_num}/"



    first_attempt_dir = ATTEMPT_DIR

    new_attempt_dir = REWORK_DIR / f"Attempt_{next_FA_num}/"    

    os.makedirs(new_attempt_dir)
    
    reSizeModule(pool_df, rework_df)

    print("\n⚠️ REWORK NEEDED: Some pools require additional size selection.")
    print("📋 NEXT STEPS: Perform size selection, then re-run Step 18 to analyze updated pools.")
    print("🔄 ITERATION: You can repeat Steps 18-19 as many times as needed.")

# Create success marker file to indicate script completed successfully
import os
os.makedirs('.workflow_status', exist_ok=True)
with open('.workflow_status/rework.pooling.steps.success', 'w') as f:
    f.write('Script completed successfully')


