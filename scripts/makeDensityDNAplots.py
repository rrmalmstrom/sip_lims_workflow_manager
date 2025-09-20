#!/usr/bin/env python3

import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
from PyPDF2 import PdfFileMerger
import os


PROJECT_DIR = Path.cwd()


# import csv with sample data
lib_df = pd.read_csv('lib_info.csv', header=0,
                     converters={'Sample Barcode': str})

# get list of unique group names in project
groups = sorted(lib_df['Replicate_Group'].unique().tolist())

# empty list to later hold names of pdfs for each group figure
# this will be used ot merge multiple pdfs at end of script
pdf_files = []

# loop through list of groups
for g in groups:

    # get list of samples in group
    samples = sorted(lib_df[lib_df['Replicate_Group'] == g]
                     ['Sample Barcode'].unique().tolist())

    # creation matliplot object
    f = plt.figure()

    # loop through samples and add line to plt.plot
    for s in samples:
        x = lib_df[lib_df['Sample Barcode'] == s]['Density (g/mL)']
        y = lib_df[lib_df['Sample Barcode'] == s]['DNA Concentration (ng/uL)']

        # extract user provided sample name by removign the suffix "_fraction#" from fraction name
        name_list = lib_df[lib_df['Sample Barcode'] ==
                           s]['Fraction_sample_name'].unique().tolist()

        # remove "_fraction#' from sample name
        ch = '_'
        parts = name_list[0].split(ch)

        parts.pop()

        name = ch.join(parts)

        # add plot of current sample
        plt.plot(x, y, label=name, marker='o')

    # add plot title, axes labels, and legend to group plot
    plt.xlabel("Density (g/mL)")
    plt.ylabel("DNA Concentration (ng/uL)")
    plt.title(f'{g}')
    plt.legend()
    # plt.show()
    f.savefig(f'UserName_DNAvsDensity_{g}.pdf',
              format="pdf", bbox_inches="tight")

    # add name of group figure pdf
    pdf_files.append(f'UserName_DNAvsDensity_{g}.pdf')


# Create and instance of PdfFileMerger() class
merger = PdfFileMerger()

# loop through group figure pdfs and merge them into one
for pdf in pdf_files:
    # Append PDF files
    merger.append(pdf)
    # delete indidvidual group figure pdf
    os.remove(pdf)
# Write out the merged PDF
merger.write(PROJECT_DIR / "merged_DNAvsDensity_plots.pdf")
merger.close()
