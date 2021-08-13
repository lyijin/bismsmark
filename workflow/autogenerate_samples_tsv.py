#!/usr/bin/env python3

SUPPORTED_LIBRARY_TYPES = ['bsseq', 'emseq', 'swift']
doc = f"""
> autogenerate_samples_tsv.py <

Creating the "samples.tsv" file needed to run bismsmark is tedious. It's a
necessary evil though, as that file is the basis for snakemake to generate
a list of expected output files; if the output file is missing, then 
snakemake knows what commands to execute to produce that output file.

This script aims to simplify the generation of "samples.tsv". Please remember
to visually inspect the generated file and change stuff to suit your project.
The price of not checking is heaps of wasted time on workstations/clusters
when the output files do not fit your expectations.

This script has no mandatory arguments (--verbose and --library_type optional), 
make sure the files/directories asterisked below are present before running
the script.

Supported library types are {SUPPORTED_LIBRARY_TYPES}.

Asterisks denote which files are mandatory for autogeneration to work.
Curly brackets == replaceable/optional strings.

workflow/
|-- Snakefile
|
|-- 00_raw_reads/                  (*)
|   |-- *_R1.fastq.gz              (*)
|   +-- *_R2.fastq.gz              (*)
|
+-- data/                          (*)
    |-- {{genome1}}/                 (*)
    |   +-- {{genome1}}.fa
    |-- {{genome2}}/
    |   +-- {{genome2}}.fa
    |-- {{genomeN}}/
        +-- {{genomeN}}.fa
""".strip()

import argparse
from pathlib import Path
import sys
import time

def benchmark_print(message):
    """
    Prints a timestamped message to stderr, to aid visual assessment of
    chokepoints in code.
    """
    print (f'[{time.asctime()}] {message}', file=sys.stderr)

parser = argparse.ArgumentParser(description=doc, 
                                 formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('-l', '--library_type', type=str, default=SUPPORTED_LIBRARY_TYPES[0],
                    help=f'pre-fill "library_type" column (default="{SUPPORTED_LIBRARY_TYPES[0]}").')
parser.add_argument('-v', '--verbose', action='store_true',
                    help='prints diagnostic stuff to stderr.')

args = parser.parse_args()

# check library type string is supported
assert args.library_type in SUPPORTED_LIBRARY_TYPES, \
    f'provided library type "{args.library_type}" is not in {SUPPORTED_LIBRARY_TYPES}'

# check "00_raw_reads/" folder
assert Path('./00_raw_reads').is_dir(), \
    'the "00_raw_reads/" folder (contains raw FASTQ reads) is not present!'

# check that there are reads in "00_raw_reads/"
R1_files = list(Path('./00_raw_reads').glob('*_R1.fastq.gz'))
assert R1_files, \
    'there are no files with pattern *_R1.fastq.gz in "00_raw_reads/"!'
R2_files = list(Path('./00_raw_reads').glob('*_R2.fastq.gz'))
assert R2_files, \
    'there are no files with pattern *_R2.fastq.gz in "00_raw_reads/"!'

assert len(R1_files) == len(R2_files), \
    f'number of R1 files ({R1_files}) != R2 files ({R2_files})!'

R1_files = sorted(R1_files, key=lambda x: x.name.replace("_R1.fastq.gz", ""))
R2_files = sorted(R2_files, key=lambda x: x.name.replace("_R2.fastq.gz", ""))

if args.verbose:
    benchmark_print(f'R1 files: {R1_files}')
    benchmark_print(f'R2 files: {R2_files}')

# check whether reads are properly paired
R1_names = [x.name for x in R1_files]
R2_names = [x.name.replace('_R2.fastq.gz', '_R1.fastq.gz') for x in R2_files]
assert R1_names == R2_names, 'files are not properly paired!'

# check "data/" folder
assert Path('./data').is_dir(), \
    'the "data/" folder (contains genome data) is not present!'

# check subfolders exist in "data/"
genome_folders = list(Path('./data').glob('*/'))
assert genome_folders, \
    'there are no subfolders in "00_raw_reads/" (at least one required)!'
genome_folders = sorted(genome_folders)

if args.verbose:
    benchmark_print(f'Subfolders in "data/": {genome_folders}')

# check that there's an uncompressed FASTA in each subfolder
for genome in genome_folders:
    genome_fasta = list(genome.glob('*.fa'))
    
    assert genome_fasta, \
        'there must be at least a single uncompressed FASTA (*.fa) file in ' + \
        'genome subfolders!'
    
    assert len(genome_fasta) == 1, \
        'there must be exactly a single uncompressed FASTA (*.fa) file in ' + \
        'genome subfolders!'

# all checks passed! define a few constants
header = f"""
## sample_id: do not alter from autodetected defaults; will contain everything
##            up to _R1/_R2
## short_id: user-editable, default rule is sample_id.split('_')[:-1]. 
##           used in the final rule to create symbolic links in "05_renamed_covs/"
## library_type: one of {SUPPORTED_LIBRARY_TYPES}
## R1_file: do not alter from autodetected defaults
## R2_file: do not alter from autodetected defaults
## mapped_genome: by default, prefills all folders in "data/"; reduce to taste
## score_min: `bismark` default is "--score_min L,0,-0.2". autogenerator tries
##            to guess best value from genome name, but change to taste.
##            each genome can only have ONE score_min
##
#sample_id	short_id	library_type	R1_file	R2_file	mapped_genome	score_min
""".strip()

def get_score_min(genome_name):
    """
    For some genomes, the optimal "--score_min" parameter is L,0,-0.6. Check
    the name of the genome subfolder for specific strings, and return "-0.6"
    if the string exists; else the default ("-0.2") is returned.
    """
    oh_point_six_genomes = ['45s', 'spis', 'pdae', 'aiptasia']
    for opsg in oh_point_six_genomes:
        if opsg in genome_name:
            return '-0.6'
    
    return '-0.2'

# time to generate "samples.tsv" file
with open('../config/samples.tsv', 'w') as outf:
    print (header, file=outf)
    for R1 in R1_files:
        for genome in genome_folders:
            sample_id = R1.name.replace('_R1.fastq.gz', '')
            short_id = sample_id if '_' not in sample_id else '_'.join(sample_id.split('_')[:-1])
            print (sample_id,
                   short_id,
                   args.library_type,
                   R1.name,
                   R1.name.replace('_R1.fastq.gz', '_R2.fastq.gz'),
                   genome.name,
                   get_score_min(genome.name),
                   sep='\t', file=outf)

if args.verbose:
    benchmark_print(f'"samples.tsv" file generated.')
