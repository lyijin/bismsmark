# Install HOWTO #

README assumes that this repo will be cloned to `./bismsmark`, and assumes that `conda`/`miniconda` has been installed.

## 0. Create folders ##

`git clone https://github.com/lyijin/bismsmark`

`cd bismsmark`

## 1. Use conda to install prerequisites ##

`conda create -c conda-forge -n bismsmark mamba`

`conda activate bismsmark`

`mamba install -c bioconda -c conda-forge snakemake bismark trim-galore`

(skip next three commands if running locally. if running on cluster, with `slurm` as scheduler, run these commands)

`mkdir -p ~/.config/snakemake/slurm`

`nano ./config/slurm/config.yaml` and add your email, so that `slurm` can email you if things fail. Remove the last two flags if you don't want to be bothered / just want to test things out quickly.

`cp ./config/slurm/config.yaml ~/.config/snakemake/slurm`

## 2. run tests to check installation ##

`cd workflow`

(use this command if running locally.)\
`snakemake --cores 8`

(use this command if running on `slurm`)\
`snakemake --profile slurm`

## 3. read `Snakefile` to understand how to plug your own data in ##

`cat Snakefile | head -40`

Use the test files to guide naming choices.

## Extras: `scripts` folder ##

To be run AFTER the snakemake pipeline completes successfully.

The Python script `compile_bismark_logs.py` scrapes some stats from `bismark` logs e.g. mapping rates, deduplication rates, ...

Run this script from `workflow/`, i.e. `python3 scripts/compile_bismark_logs.py`. No additional arguments needed, as the script hardcodes the folder names containing log files.

## Additional customisation ##

The resources (RAM/cores) requested in `Snakefile` is optimised to work on the human genome (hg38/GRch38), and on my local `slurm` cluster. Remember that larger genomes will need more RAM, larger sequence files will need more time to be processed.

To check resources consumed by jobs, use `sacct` with the `-S mmdd` flag, where `mmdd` == month, date e.g. `-S 0801`.

# Why is this called `bismsmark`? #

Erm, it's because I'm trying to embed `snakemake` ("sm") into `bismark` to make a reproducible pipeline.
