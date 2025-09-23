#!/usr/bin/env python3

# USAGE:   update.ultracentrifuge.transfer.py <ultracentrifuge.csv>

# sys.argv[1] = .csv file with list of ITS sample IDs to go in ultracentrifuge

import pandas as pd
import numpy as np
import sys
import os
import shutil
from datetime import datetime
from os.path import exists as file_exists
from pathlib import Path
import math
from sqlalchemy import create_engine



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

###########################
###########################
def getTubesForUltra(tube_file):

    # read in list of tube sample ids from .csv file
    with open(tube_file, encoding='utf-8-sig', newline='') as file:
        lines = file.readlines()
        tubes = [line.rstrip() for line in lines]

    # example tubes IDs used for testing script
    #tubes = ['282375','282376','282377','282378','282379','282380','282381','282382']

    # determine if there are any tubes in list
    if (len(tubes) == 0):
        print("\n\nThere were no sample tube IDs in list.\n\n Aborting process\n\n")
        sys.exit()

    # determine if user really wants to process >16 tubes at once
    if (len(tubes) > 16):
        print(tubes)
        print("\n\nThere are >16 tubes in list, which is more than rotor holds\n\n Do you wish to continue (Y/N)\n\n")

        val = input()

        if (val == 'Y' or val == 'y'):
            print("Ok, we'll keep going\n\n")

        elif (val == 'N' or val == 'n'):
            print('Ok, aborting script\n\n')
            sys.exit()
        else:
            print("Sorry, you must choose 'Y' or 'N' next time. \n\nAborting\n\n")
            sys.exit()

    # determine if number of tubes is odd
    if (len(tubes) % 2 != 0):
        print(tubes)
        print("\n\nThere are an odd number of tubes in list.\n\n Do you wish to continue (Y/N)\n\n")

        val = input()

        if (val == 'Y' or val == 'y'):
            print("Ok, we'll keep going\n\n")

        elif (val == 'N' or val == 'n'):
            print('Ok, aborting script\n\n')
            sys.exit()
        else:
            print("Sorry, you must choose 'Y' or 'N' next time. \n\nAborting\n\n")
            sys.exit()

    return tubes
###########################
###########################


###########################
###########################
def checkTubesInDatabase(my_tubes, all_samples_df):

    # reduce size of dataframe to list of targetted tubes
    my_centrifuge_df = all_samples_df[all_samples_df['ITS_sample_id'].isin(
        tubes)].copy()

    # reduced size fo datafram to all samples EXCEPT those in uploaded list of tubes
    my_unused_tubes_df = all_samples_df[~all_samples_df['ITS_sample_id'].isin(
        tubes)].copy()

    if len(my_tubes) != my_centrifuge_df.shape[0]:
        print('\n')
        print('At least one of the sample IDs was not found in the project summary database.  Aborting process\n\n')
        sys.exit()

    return my_centrifuge_df, my_unused_tubes_df

###########################
###########################


###########################
###########################
def checkIfEnoughMassorVolume(centrifuge_df):
    # make sure the tubes have some amount of Available volume
    if (any(centrifuge_df['Available_vol_(ul)'] <= 0)):
        # print(centrifuge_df[centrifuge_df['Available_vol_(ul)'] <= 0])
        print("\nAt least one sample doesn't have any remaining volume\n\n See table above\n\n Do you wish to continue (Y/N)\n\n")

        val = input()

        if (val == 'Y' or val == 'y'):
            print("Ok, we'll keep going\n\n")

        elif (val == 'N' or val == 'n'):
            print('Ok, aborting script. \n\n')
            sys.exit()
        else:
            print("Sorry, you must choose 'Y' or 'N' next time. \n\nAborting\n\n")
            sys.exit()

    # # ask User to input transfer mass, default value is 1,000 ng's
    centrifug_mass = float(
        input("Enter the mass of DNA needed for ULTRACENTRIFUGE in ng's (default 1,000): ") or 1000)

    # abort if not enough sample mass for ultracentrifuge transfer
    if (any(centrifuge_df['Available_mass_(ng)'] < centrifug_mass)):
        # print(
        #     centrifuge_df[centrifuge_df['Available_mass_(ng)'] < centrifug_mass])
        print("\nAt least one sample doesn't have enough DNA mass\n\n See table above\n\n Do you wish to continue (Y/N)\n\n")

        val = input()

        if (val == 'Y' or val == 'y'):
            print("Ok, we'll keep going\n\n")

        elif (val == 'N' or val == 'n'):
            print('Ok, aborting script.  Try reducing transfer mass value\n\n')
            sys.exit()
        else:
            print("Sorry, you must choose 'Y' or 'N' next time. \n\nAborting\n\n")
            sys.exit()

    return centrifug_mass
###########################
###########################


###########################
###########################
def makeLiquidHandlerTransferFile(centrifuge_df, centrifug_mass, dead_volume):
    # set mass to transfer to  ultracentrifuge to value entered by user or to total
    # available DNA mass if user requesting >= all DNA mass
    centrifuge_df['Ultracentrifuge_mass_(ng)'] = np.where(
        (centrifug_mass >= centrifuge_df['Available_mass_(ng)']), centrifuge_df['Available_mass_(ng)'], centrifug_mass)

    # add transfer volume based on transfer mass and sample conc.
    centrifuge_df['Ultracentrifuge_vol_(ul)'] = (centrifuge_df["Ultracentrifuge_mass_(ng)"] /
                                                 centrifuge_df['Updated_conc_(ng/ul)']).round(decimals=1)

    # indicate if volume necessary to reach target mass requires use of dead volume
    centrifuge_df['Use_dead_vol'] = np.where(
        (centrifuge_df['Ultracentrifuge_vol_(ul)'] > centrifuge_df['Available_vol_(ul)'] - dead_volume), 1, 0)

    centrifuge_df['Ultracentrifuge_vol_(ul)'] = np.where(
        centrifuge_df['Use_dead_vol'] == 1, (centrifuge_df['Available_vol_(ul)'] - dead_volume), centrifuge_df['Ultracentrifuge_vol_(ul)'])

    # create dataframe for printing output file for hamilton transfer to ultracentrifuge tubes
    output_df = centrifuge_df

    output_df = output_df.drop(['Isotope_plate_barcode',
                                'Isotope_well', 'Ultracentrifuge_attempts_(#)', 'Merged_files', 'Made_Library'], axis=1)

    # determine max and min sample ID
    # use for naming ultracentrifuge and tubewriter files so that
    # we know which subset of samples are bing processed
    min_tube = min(tubes)
    max_tube = max(tubes)

    # # print out csv file for transfering from matrix to ultraceentrifuge tubes
    # output_df.to_csv(
    #     f'Ultracentrifuge_transfer_{min_tube}_to_{max_tube}.csv', index=False)

    return output_df, min_tube, max_tube
###########################
###########################


###########################
###########################
def updateProjectDatabase(centrifuge_df, unused_tubes_df, dead_volume):

    # calculate remaining volume and remaining mass.  Set to 0 if using all remaining sample
    centrifuge_df['Remain_vol_(ul)'] = (centrifuge_df['Available_vol_(ul)'] -
                                        centrifuge_df["Ultracentrifuge_vol_(ul)"]).round(1)
    centrifuge_df['Remain_vol_(ul)'] = np.where(
        centrifuge_df['Remain_vol_(ul)'] <= (dead_volume+1), 0, centrifuge_df['Remain_vol_(ul)'])

    centrifuge_df['Available_vol_(ul)'] = centrifuge_df['Remain_vol_(ul)']

    centrifuge_df['Remain_mass_(ng)'] = (centrifuge_df['Available_mass_(ng)'] -
                                         centrifuge_df['Ultracentrifuge_mass_(ng)']).astype(int)

    # set remaining mass to 0 if estimated <0 mass remaining or if avaialble volume is set to 0
    centrifuge_df['Remain_mass_(ng)'] = np.where((
        (centrifuge_df['Remain_mass_(ng)'] < 0) | (centrifuge_df['Available_vol_(ul)'] == 0)), 0, centrifuge_df['Remain_mass_(ng)'])

    centrifuge_df['Available_mass_(ng)'] = centrifuge_df['Remain_mass_(ng)']

    # get rid of some columns not needed for updating database file
    centrifuge_df = centrifuge_df.drop(
        ['Ultracentrifuge_mass_(ng)', 'Ultracentrifuge_vol_(ul)', 'Use_dead_vol',
         'Remain_mass_(ng)', 'Remain_vol_(ul)'], axis=1)

    # increment the number of attempt to transfers from matrix tubes to ultracentrifuge tubes
    centrifuge_df['Ultracentrifuge_attempts_(#)'] = centrifuge_df['Ultracentrifuge_attempts_(#)'] + 1

    # make updated dataframe for export as new database file
    project_df = pd.concat([unused_tubes_df, centrifuge_df])

    return project_df
###########################
###########################


# ###########################
# ###########################
# def makeTubewriterFile(tubes, min_tube, max_tube):

#     # creat df with two columns of the ITS sample IDs
#     ultratubes_df = pd.DataFrame(tubes)
#     ultratubes_df[1] = tubes

#     # update index to start at 1 instead of 0
#     ultratubes_df.index = range(1, ultratubes_df.shape[0] + 1)

#     ultratubes_df.to_excel(
#         f'Tubewriter_{min_tube}_to_{max_tube}.xlsx', index=True, header=False)

# ###########################
# ###########################


#########################
#########################
def makeBarcodeLabels(tubes, min_tube, max_tube):
    
    # sort tube numbers from largest to smallest so they eventually
    # print out smallest to largest
    rev_tubes = tubes
    
    rev_tubes.sort(reverse=True)

    # add info to start of barcode print file indicating the template and printer to use
    x = '%BTW% /AF="\\\BARTENDER\shared\\templates\ECHO_BCode8.btw" /D="%Trigger File Name%" /PRN="bcode8" /R=3 /P /DD\r\n\r\n%END%\r\n\r\n\r\n'


    bc_file = open(BARTEND_DIR / f"BARTENDER_ultracentrifuge_tube_labels_{min_tube}_to_{max_tube}.txt", "w")

    bc_file.writelines(x)  

    # add barcodes labels for each ultracentrifuge sample
    for t in rev_tubes:
        bc_file.writelines(f'{t},"ultracentrifuge {t}"\r\n')
        

    bc_file.close()
#########################
#########################




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

###########################
# MAIN PROGRAM
###########################
# check if path  was provided, otherwise use current directory
if len(sys.argv) < 2:
    print('\nDid not provide all required input files. Aborting. \n')
    sys.exit()
else:

    # loop through all provided input files and confirm they exist
    for s in sys.argv[1:]:  # Skip script name (sys.argv[0])
        if (file_exists(s) == 0):
            print(f'\nCould not find file {s} \nAborting\n')
            sys.exit()


# get current working directory and its parent directory
#BASE_DIR = Path.cwd()

#PROJECT_DIR = BASE_DIR.parent

PROJECT_DIR = Path.cwd()

ULTRA_DIR = PROJECT_DIR / "2_load_ultracentrifuge"

BARTEND_DIR = ULTRA_DIR / "BARTENDER_files"
BARTEND_DIR.mkdir(parents=True, exist_ok=True)

TRASNFER_DIR = ULTRA_DIR / "Hamilton_transfer_files"
TRASNFER_DIR.mkdir(parents=True, exist_ok=True)

OLD_DIR = ULTRA_DIR / "previously_processed_sample_lists"
OLD_DIR.mkdir(parents=True, exist_ok=True)  

ARCHIV_DIR = PROJECT_DIR / "archived_files"

# Handle both full paths and relative filenames
input_file_arg = sys.argv[1]
if Path(input_file_arg).is_absolute():
    # GUI passed full path, use it directly
    tube_file = Path(input_file_arg)
else:
    # Check if the path already includes the directory
    if input_file_arg.startswith("2_load_ultracentrifuge/"):
        # GUI passed relative path with directory, use from project root
        tube_file = PROJECT_DIR / input_file_arg
    else:
        # Script called with just filename, construct path
        tube_file = ULTRA_DIR / input_file_arg


# make list of tubes to be ultracentrifuged
#tubes = getTubesForUltra(sys.argv[1])
tubes = getTubesForUltra(tube_file)

# # create df from project_database.csv file
# all_samples_df = pd.read_csv(PROJECT_DIR / "project_database.csv",
#                              header=0, converters={'ITS_sample_id': str})

# create pandas df from sqlite db of project_database.db
all_samples_df = readSQLdb()


centrifuge_df, unused_tubes_df = checkTubesInDatabase(tubes, all_samples_df)

# # reduce size of dataframe to list of targetted tubes
# centrifuge_df = all_samples_df[all_samples_df['ITS_sample_id'].isin(
#     tubes)].copy()


# # reduced size fo datafram to all samples EXCEPT those in uploaded list of tubes
# unused_tubes_df = all_samples_df[~all_samples_df['ITS_sample_id'].isin(
#     tubes)].copy()

# determine if there's enough DNA mass or volume to meet input target
# centrifug_mass is input target provided by user
centrifug_mass = checkIfEnoughMassorVolume(centrifuge_df)

# set dead volume in uL's for Hamilton transfer from matrix tubes
dead_volume = 10

# make df for generating Hamilton liquid handler transfer file
output_df, min_tube, max_tube = makeLiquidHandlerTransferFile(
    centrifuge_df, centrifug_mass, dead_volume)

# make df for updating project database, indicating which samples have be ultracentrifuged
project_df = updateProjectDatabase(centrifuge_df, unused_tubes_df, dead_volume)

# # make file for printing barcodes on ultracentrifuge tubes
# makeTubewriterFile(tubes, min_tube, max_tube)

# make file for printing BARTENDER barcodes for ultracentrifuge tubes
makeBarcodeLabels(tubes,min_tube, max_tube)

# print out csv file for transfering from matrix to ultraceentrifuge tubes
output_df.to_csv(TRASNFER_DIR /
    f'Ultracentrifuge_transfer_{min_tube}_to_{max_tube}.csv', index=False)

# update project database and archive older version of project database
date = datetime.now().strftime("%Y_%m_%d-Time%H-%M-%S")

# Move the tube_file to OLD_DIR for archival
try:
    tube_file_name = tube_file.name
    destination = OLD_DIR / tube_file_name
    shutil.move(str(tube_file), str(destination))
    # print(f"Moved input file {tube_file_name} to {OLD_DIR}")
except Exception as e:
    print(f"\nWarning: Could not move {tube_file} to {OLD_DIR}: {e}")

Path(PROJECT_DIR /
     "project_database.csv").rename(ARCHIV_DIR / f"archive_project_database_{date}.csv")
Path(ARCHIV_DIR / f"archive_project_database_{date}.csv").touch()

project_df.to_csv(PROJECT_DIR / 'project_database.csv', index=False)

# create updated project_database.db
createSQLdb(project_df)

# SUCCESS MARKER: Create success marker file to indicate script completed successfully
script_name = Path(__file__).stem  # Use just the filename without extension
status_dir = Path(".workflow_status")
status_dir.mkdir(exist_ok=True)

# Remove any existing success file (for re-runs)
success_file = status_dir / f"{script_name}.success"
if success_file.exists():
    success_file.unlink()

# Create success marker file
try:
    with open(success_file, "w") as f:
        f.write(f"SUCCESS: {script_name} completed at {datetime.now()}")
    #print(f"✓ Step {script_name} completed successfully")
except Exception as e:
    print(f"✗ Failed to create success marker: {e}")
    sys.exit(1)
