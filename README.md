This set of tools will query, story and track metadata thorugh NMR data acquisition, conversion and analysis to facilitate later deposition to the BMRB.
It was developed by Heyi Zhang & Hugo van Ingen, Utrecht University, as part of the iNEXT-Discovery program WP5 Data Management project.

# How to install
Use of these tools assumes you use a Bruker spectrometer with Topspin and do the analysis using NMRFAM-SPARKY.
This workflow has been tested w/ Topspin3.2 and Topspin4.1.3, and on Mac OS 10.14 with python3.9 (Anaconda3 distribution)

## Description of the files
- setupTitration	Bruker Topspin AU program to create dataset for titration experiment and query for sample metadata        
- setupDataset		Bruker Topspin AU program to create dataset and query for sample metadata
- setlev                Bruker Tosppin AU program to calculate contour levels, using 1.2 factor and 20 levels
- xfbla			Bruker Topspin macro to process 2D data, including setting of contours and baseline correction
- it			Bruker Topspin macro to increment the experiment and query for new ligand concentration
- createSparkyProject.py	Python3/Tkinter script to convert a complete Bruker NMR dataset into a ready-to-use SPARKY project and extract and store the associated metadata 


## On the spectrometer
copy the AU programs "setupTitration", "setupDataset" and "setlev" in, e.g.:
                    /opt/topspin3.2/exp/stan/nmr/au/src/user
                    /opt/topspin4.1.3/exp/stan/nmr/au/src/user
                    
copy the macros "xfbla" and "it" in, e.g.:
                    /opt/topspin3.2/exp/stan/nmr/lists/mac/user
                    /opt/topspin4.1.3/exp/stan/nmr/lists/mac/user

## On your computer

This script requires python3.x with the tkinter module and NMRFAM-SPARKY.
Store the script in a convenient location, for instance ~/bin
Adapt the line 
    sparky_bin_dir = '/Applications/nmrfam-sparky-mac/NMRFAM-SPARKY.app/Contents/Resources/bin/'
to match the location of the bruk2ucsf and ucsfdata tools on your computer

Then we recommend to create an alias (substitute your python version!):
  tcsh: alias createSparkyProj 'python3.9 ~/bin/createSparkyProject.py'  (.tcshrc or .cshrc)
  bash: alias createSparkyProj="python3.9 ~/bin/createSparkyProject.py"  (.bash_aliases or .profile)

# How to use

## On the spectrometer
- to create your dataset, use the command        
    setupTitration            
    this will create a standardized dataset name and will query the user for the sample metadata (protein + ligand name, concentration, buffer etc)
    the metadata is stored in the title of the experiment
- to update the title for a new step in the titration, use the command
        it
   this will query the user for the new ligand concentration and update the title field accordingly
- to process the data to a spectrum, use the command
        xfbla
  this will set and store the contour levels appropiately and is required to be executed once to make sure the createSparkyProject.py will set the contour level properly

## On the local computer
- navigate to the NMR dataset folder in the Terminal and descend into the dataset folder (you should see the expno directories)
- on the command line execute the command
        createSparkyProj
  if you have created the alias, or
         python3 ~/bin/createSparkyProject.py
  if you haven't, be sure to use the correct path to the createSparkyProject.py script
- a GUI opens, the status line in the bottom of the window tells you what do.
  If you have executed the last command in the directory containing the various NMR experiments in the dataset,
  then it suffices to click "Update". Otherwise, click "Select" to select the Bruker NMR folder (containing 1/ 2/ 3/ ...) and then click "Update"
- this will extract all metadata and show a list of all 2D and 3D experiments.
  You can manually edit metadata if desired.
  The labeling scheme and reference molecule can also be chosedn in the dropdown menu to make sure it corresponds to values used by the BMRB 
- by default all the spectra in the spectra list are selected for conversion to SPARKY
	You can manually unselect one or more spectra by mouse click while holding ctrl key 
- by default the SAPRKY folder that will generated will be created in the folder that contains the Bruker NMR dataset
	You can change this location using the "Select" button
- the name for the sparky project is generated based on the protein and ligand names, but can be changed manually
- click "Convert to sparky" to generate a Sparky folder with selected spectra.
- a file metadata.txt is generated in the Sparky folder and the NMR dataset folder recording all metadata




 
