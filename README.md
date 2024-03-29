This set of tools will query, store and track metadata through NMR data acquisition, conversion and analysis to facilitate later deposition to the BMRB.
It was developed by Heyi Zhang & Hugo van Ingen, Utrecht University, as part of the iNEXT-Discovery program WP5 Data Management project.

# Files
- setupTitration
> Bruker Topspin AU program to create dataset for titration experiment and query for sample metada        
- setupDataset
> Bruker Topspin AU program to create dataset and query for sample metadata
- setlev
> Bruker Tosppin AU program to calculate contour levels, using 1.2 factor and 20 levels
- xfbla
> Bruker Topspin macro to process 2D data, including setting of contours and baseline correction
- it
> Bruker Topspin macro to increment the experiment and query for new ligand concentration
- createSparkyProject.py
> Python3/Tkinter script to convert a complete Bruker NMR dataset into a ready-to-use SPARKY project and extract and store the associated metadata 
- bpar_bdat_scripts.tar.gz
> command line scripts (bpar, printbpar and bdat) to extract (meta)data from Bruker dataset and expno directories

# How to install
Use of these tools assumes you use a Bruker spectrometer with Topspin and do the analysis using NMRFAM-SPARKY.
This workflow has been tested w/ Topspin3.2 and Topspin4.1.3, and on Mac OS 10.14 with python3.9 (Anaconda3 distribution)

## On the spectrometer
- copy the AU programs "setupTitration", "setupDataset" and "setlev" in, e.g.:
> /opt/topspin3.2/exp/stan/nmr/au/src/user  
> /opt/topspin4.1.3/exp/stan/nmr/au/src/user
- adapt the loading of default parameter sets in "setupTitration", "setupDataset" according to your setup and needs
- copy the macros "xfbla" and "it" in, e.g.:
> /opt/topspin3.2/exp/stan/nmr/lists/mac/user  
> /opt/topspin4.1.3/exp/stan/nmr/lists/mac/user

## On your computer
- make sure you have python3.x with the tkinter module and NMRFAM-SPARKY installed
- store the createSparkyProject.py script in a convenient location, for instance in ~/bin
- locate the line below in the script and adapt to match the location of the bruk2ucsf and ucsfdata tools on your computer 
> sparky_bin_dir = '/Applications/nmrfam-sparky-mac/NMRFAM-SPARKY.app/Contents/Resources/bin/'
- we recommend to create an alias (substitute your python version!):
> tcsh: alias createSparkyProj 'python3.9 ~/bin/createSparkyProject.py'  (.tcshrc or .cshrc)  
> bash: alias createSparkyProj="python3.9 ~/bin/createSparkyProject.py"  (.bash_aliases or .profile)
- unzip and untar the bpar_bdat_scripts.tar.gz file in a location that is in your $PATH, e.g. ~/bin, or create an alias as above:
> tar -zxvf bpar_bdat_scripts.tar.gz 

# How to use

## On the spectrometer
- create your datase using the command        
> setupTitration            
- this will create a standardized dataset name and will query the user for the sample metadata (protein + ligand name, concentration, buffer etc)
- the metadata is stored in the title of the experiment
- to update the title for a new step in the titration, use the command
> it
- to process the data to a spectrum, use the command
 > xfbla
- this will set and store the contour levels appropiately and is required to be executed once to make sure the createSparkyProject.py will set the contour level properly

## On the local computer
To use the createSparkyProject.py:
- navigate to the NMR dataset folder in the Terminal and descend into the dataset folder (you should see the expno directories)
- if you have created the alias, execute on the command line
> createSparkyProj
- otherwise do (be sure to use the correct path to the createSparkyProject.py script):
> python3 ~/bin/createSparkyProject.py, 
- a GUI opens, the status line in the bottom of the window tells you what do.
- if you have executed the last command in the directory containing the various NMR experiments in the dataset,
  then it suffices to click "Update". 
- Otherwise, click "Select" to select the Bruker NMR folder (containing 1/ 2/ 3/ ...) and then click "Update"
- this will extract all metadata and show a list of all 2D and 3D experiments.
- you can manually edit metadata if desired, the labeling scheme and reference molecule can be set via the dropdown menu to values used by the BMRB 
- by default all the spectra in the spectra list are selected for conversion to SPARKY, you can manually unselect one or more spectra by mouse click while holding ctrl key 
- by default the SPARKY folder that will generated will be created in the folder that contains the Bruker NMR dataset, this can be changed using the "Select" button
- the name for the sparky project is generated based on the protein and ligand names, but can be changed manually
- click "Convert to sparky" to generate a Sparky folder with selected spectra.
- spectrum names will start with the corresponding expno of the NMR dataset; contouring and spectrum colors are automatically chosen
- a file metadata.txt is generated in the Sparky folder and the NMR dataset folder recording all metadata
- open the SPARKY project and enjoy!

To use bdat:
- make sure the scripts is stored in a location known in $PATH, or are aliased
- navigate to the NMR dataset folder in the Terminal and descend into the dataset folder (you should see the expno directories)
- to extract dataset, sample and expno information for all expnos, type on the command line:
> bdat
- the extracted data is shown on the screen and recorded in a file README
- CAUTION: expnos without a FID (ser or fid) will be automatically deleted
- CAUTION: a pre-existing README will be overwritten

To use the bpar, printbar:
- make sure the scripts are stored in a location known in $PATH, or are aliased
- navigate to the NMR dataset folder in the Terminal and descend into the dataset folder (you should see the expno directories)
- to extract all data from Bruker Topspin eda and ased windows, type on the command line:
> printbpar
- to extract a certain parameter, e.g. the number of scans, type on the command line:
> bpar ns
- if you are not exactly sure of the parameter name add "xx", e.g. to show all parameters with a "d" so all delays:
> bpar dxx






 
