#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import pandas as pd
import numpy as np
import os
import sys
import shutil
from pathlib import Path
from datetime import datetime
import re


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
        plate_list.append(s.split('.')[0])
    
    # abort program if the plate name in output folder does not
    # match plate name parsed from sample name in smear analysis .csv file
    if folder_name not in set(plate_list):
        print (f'\nThere is a mismatch between FA plate ID and sample names for plate {folder_name}.  Aborting script\n')
        sys.exit()
    
    
    return

##########################
##########################
def findLatestAttempt():
    """
    Find the latest attempt directory in the E_pooling_and_rework directory.
    
    Scans the E_DIR (E_pooling_and_rework) for subdirectories with pattern 'Attempt_X'
    where X is a number, and returns the directory name with the highest attempt number.
    
    Returns:
        str: Name of the latest attempt directory (e.g., "Attempt_3")
        
    Raises:
        SystemExit: If no attempt directories are found or if directory parsing fails
    """
    
    # Scan the E_DIR (E_pooling_and_rework) for attempt directories
    rework_dir = REWORK_DIR
    
    if not rework_dir.exists():
        print(f'\n\nRework directory {rework_dir} does not exist. Aborting script\n')
        sys.exit()
    
    attempt_dirs = []
    attempt_pattern = re.compile(r'^Attempt_(\d+)$')
    
    # Scan for attempt directories
    for item in rework_dir.iterdir():
        if item.is_dir():
            match = attempt_pattern.match(item.name)
            if match:
                attempt_num = int(match.group(1))
                attempt_dirs.append((attempt_num, item.name))
    
    # Check if any attempt directories were found
    if not attempt_dirs:
        print(f'\nNo attempt directories found in {rework_dir}. Expected format: Attempt_X where X is a number. Aborting script\n')
        sys.exit()
    
    # Sort by attempt number and return the latest (highest number)
    attempt_dirs.sort(key=lambda x: x[0])
    latest_attempt = attempt_dirs[-1][1]
    
    print(f'\nFound {len(attempt_dirs)} attempt directories. Using latest: {latest_attempt}')
    
    return latest_attempt

##########################
##########################



##########################
##########################
def getFAfiles(crnt_dir):

    fa_files = []
    

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
                            os.rename(os.path.join(crnt_dir, file), os.path.join(crnt_dir, f'{folder_name}.csv'))
                            
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
# MAIN PROGRAM
##########################
# # get current working directory and its parent directory
# crnt_dir = os.getcwd()
# prnt_dir = os.path.dirname(crnt_dir)
# prjct_dir = os.path.dirname(prnt_dir)

PROJECT_DIR = Path.cwd()

ARCHIV_DIR = PROJECT_DIR / "archived_files"

POOL_DIR = PROJECT_DIR / "5_pooling"

REWORK_DIR = POOL_DIR / "E_pooling_and_rework"

# find the latest attempt directory in the E_pooling_and_rework directory
latest_attempt = findLatestAttempt()

ATTEMPT_DIR = REWORK_DIR / latest_attempt

crnt_dir = ATTEMPT_DIR


fa_files = getFAfiles(crnt_dir)

if len(fa_files) >1:
    print('\nMultiple FA12 output file found. There should be only one.  Aborting script.\n\n')
    sys.exit()

else:
    file = fa_files[0]


# # read FA12 smear analysis file into df
# fa_df = pd.read_csv(crnt_dir + f'/{file}')
fa_df = pd.read_csv(ATTEMPT_DIR / file)


# remove rows with "empty" or "ladder" in sample ID. search is case insensitive
fa_df = fa_df[fa_df["Sample ID"].str.contains(
    'empty', case=False) == False]

fa_df = fa_df[fa_df["Sample ID"].str.contains(
    'LibStd', case=False) == False]

fa_df = fa_df[fa_df["Sample ID"].str.contains(
    'ladder', case=False) == False]


#split into 400-800_df and 100-400_df based on column "Range"
small_df = fa_df[fa_df['Range']=='100 bp to 400 bp'].copy()

small_df = small_df[['Sample ID','% Total']]

small_df = small_df.rename(columns={'% Total': 'small % Total'})

fa_df = fa_df[fa_df['Range']=='400 bp to 800 bp']

if fa_df.shape[0] != small_df.shape[0]:
    print('\n\nThe smear analysis file could not be parsed based on Range column. Aborting. \n\n')
    sys.exit()


#merge columns based on Sample ID.
fa_df = fa_df.merge(small_df, how='outer',left_on=['Sample ID'], right_on=['Sample ID'])

if fa_df.shape[0] != small_df.shape[0]:
    print('\n\nThe smear analysis file could not be parsed based on Range column. Aborting. \n\n')
    sys.exit()



#use np.where to compare $ Total from 400-800 vs 100-400, and fail libs with too much DNA in 100-400
fa_df['pass_fail'] = np.where(((fa_df['% Total'] >= 70) & (fa_df['small % Total'] <= 15)),1,0)

# us np.where to apply a minimum concentration cutoff in addition the % lib in 400_800 size fracrtion
fa_df['pass_fail'] = np.where(((fa_df['nmole/L'] >=1.250) & (fa_df['pass_fail'] ==1)),1,0)

# Dest_Tube_Size_Selected


fa_df = fa_df[['Sample ID','pass_fail','nmole/L','Avg. Size']]

fa_df.rename(columns={'Sample ID':'Sample_ID'}, inplace=True)

# create three new columns by parsing Sample_ID string using "." as delimiter
fa_df[['FA_plate_barcode','Dest_Tube_Size_Selected','Well']] = fa_df.Sample_ID.str.split(".", expand=True)


# pool_df = pd.read_csv(prjct_dir + "/pool_summary.csv", header=0, usecols=['Pool_Name','Pool_Barcode','Pippin_Cassette','1st_Pippin_lane','2nd_Pippin_lane','Dest_Tube_Size_Selected','FA_plate_barcode','FA_well'])

pool_df = pd.read_csv(POOL_DIR / "pool_summary.csv", header=0)


# determine next increment number of FA plate barcode
FA_list = pool_df['FA_plate_barcode'].unique().tolist()

FA_list.sort()

last_FA = FA_list[-1]

# Validate that last_FA is not empty or None
if not last_FA or last_FA is None or str(last_FA).strip() == '':
    print('\n\nError: Could not identify the latest FA run. The FA plate barcode list appears to be empty or invalid. Aborting script.\n\n')
    sys.exit()

# next_FA_num = int(last_FA[-1])+1

# make last_df with only data from most recent pooling/size selection run, i.e.
# rows from the most recent FA plate based in FA plate increment number
last_df = pool_df.loc[pool_df['FA_plate_barcode']==last_FA].copy()

rest_df = pool_df.loc[pool_df['FA_plate_barcode']!=last_FA].copy()

last_df = last_df[['Pool_Name','Pool_Barcode','Pippin_Cassette','1st_Pippin_lane','2nd_Pippin_lane','Dest_Tube_Size_Selected','FA_plate_barcode','FA_well']]

last_df['old_index'] = last_df.index

update_df = pd.merge(last_df, fa_df, left_on=['FA_plate_barcode','Dest_Tube_Size_Selected','FA_well'], right_on=['FA_plate_barcode','Dest_Tube_Size_Selected','Well'])

# Check if update_df is empty after merge operation
if update_df.empty:
    print('\n\nError: No matching data found between FA results and pool_summary.csv. There was a problem matching data from FA results with data in pool_summary.csv. Aborting script.\n\n')
    sys.exit()


if "Passed_Pool" not in update_df.columns:
    update_df['Passed_Pool'] = ""

update_df['Passed_Pool'] = update_df['pass_fail'] 

update_df['New_pool'] = ""

update_df.drop(['Well','Sample_ID','pass_fail'], inplace=True, axis=1)

update_df.set_index('old_index',inplace=True)

final_df = pd.concat([rest_df,update_df])



# get current date and time, will add to archive database file name
date = datetime.now().strftime("%Y_%m_%d-Time%H-%M-%S")

# arive the current lib_info.csv
Path(POOL_DIR /
      "pool_summary.csv").rename(ARCHIV_DIR / f"archive_pool_summary_{date}.csv")
Path(ARCHIV_DIR / f"archive_pool_summary_{date}.csv").touch()
# create updated library info file
final_df.to_csv(POOL_DIR / 'pool_summary.csv', index=False)

# Create success marker file to indicate script completed successfully
import os
os.makedirs('.workflow_status', exist_ok=True)
with open('.workflow_status/pool.FA12.analysis.success', 'w') as f:
    f.write('Script completed successfully')

