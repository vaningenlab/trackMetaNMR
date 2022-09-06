# createSparkyProject.py
#
# 2021-2022 Heyi Zhang / Hugo van Ingen / Utrecht University
# funded by iNEXT-Discovery program WP5 Data Management project
#
# to run:   python3 createSparkyProject.py
#
# recommended use:
#   - save alias in your shell settings, e.g. "alias createSparkyProj 'python3.10 ~/bin/createSparkyProject.py'" for tcsh
#   - then simply execute script from within the Bruker dataset from command line
#   - click update in the GUI
#   - click convert to SPARKY if you're happy with the extracted data
#   - the SPARKY folder is created in same dir as the one that contains the NMR dataset
#   - it also contains "metadata.txt" which contains all extracted metadata
#   - note that the path of your NMR data should not contain spaces!!
#   - open the SPARKY project file and you're good to go!
#
# this script needs:
# 1, Python 3.9 or higher
# 2, Python module tkinter
# 3, NMRFAM-SPARKY.app w/ bruk2ucsf and ucsfdata  ==> ! ADAPT the sparky_bin_dir below for your computer !
sparky_bin_dir = '/Applications/nmrfam-sparky-mac/NMRFAM-SPARKY.app/Contents/Resources/bin/'

#
# to do:
#   - fix spaces issue
#   - auto find sparky bin dir
#   - proper synching of axes using nuclei names
#   - should run default from top folder containing dataset instead of within
#   - add optional pre-fix or suf-fix to outfiles
#   - check existing data; should add to currrent project
#   - add projections for 3Ds
#   - rigourous check intensity scaling

import os, subprocess, shutil
import re
import math as m
from tkinter import *
from tkinter import filedialog as fd
from tkinter import ttk

# find sparky tools
#ucsfdata = shutil.which('ucsfdata')
#bruk2ucsf = shutil.which('bruk2ucsf')

root = Tk()

#to remember spectra
intvar_dict={}
checkbutton_list=[]

# set window size
root.geometry("700x700")


# declaring string variable
# for storing nmr folder path
folder_path = StringVar(root, value= str(os.getcwd()))
#for storing selected SPARKY path
folder_path_select = StringVar()
#for storing selected NMR folder last two dir levels
#folder_path_display = StringVar(root, value='... ' + '/'.join(str(os.getcwd()).split('/')[-2:]) )
#for storing selected SPARKY folder last two dir levels
#sparky_folder_display = StringVar()
#tube type
tube = StringVar()
#sample volume
volume = StringVar()
# for storing protein name
protein_name = StringVar()
#for storing concentration
concentration = StringVar()
# for storing titration
info_line = StringVar()
#for storing buffer
buffer = StringVar()
#for storing temperature
temp = StringVar()
#for storing magetic field
field = StringVar()
#for storing pressure
press = StringVar()
press.set('1')
#for sparky project name
proj_name = StringVar()
#for sparky folder
sparky_folder = StringVar()
# for spectrometer info
spec_info = []
# for status text
statusvar = StringVar(root, value="Select the NMR data folder and click update ...")

#define the function to open NMR folder
def open_folder():
    global foldername
    global folder_path
    global current_dir
    current_dir = os.getcwd()
    foldername = fd.askdirectory(initialdir=current_dir)
    folder_path.set(foldername)
    #lastTwo = '... ' + '/'.join(foldername.split('/')[-2:])
    #folder_path_display.set(lastTwo)

#define the function to open SPARKY project folder
def select_folder():
    global foldername_select
    global folder_path_select
    current_dir = os.getcwd()
    foldername_select = fd.askdirectory(initialdir=current_dir)
    folder_path_select.set(foldername_select)

#define function to create a new folder
def creat_folder():
    global foldername_creat
    global folder_path_creat
    foldername_creat = entry10.get()
    if os.path.isdir(foldername_creat):
        popupBonusWindow = Tk()
        popupBonusWindow.wm_title("error")
        labelBonus = Label(popupBonusWindow, text="folder already exists, please enter new path")
        labelBonus.grid(row=0, column=0)
        B1 = Button(popupBonusWindow, text="Okay", command=popupBonusWindow.destroy)
        B1.grid(row=1, column=0)
    else:
        os.mkdir(os.path.expanduser(foldername_creat))

# define convert2sparky
def cvt2sparky():

    # make folders if not exist
    if not os.path.exists(entry10.get()):
        os.mkdir(entry10.get())
        statusvar.set("Created SPARKY folder " + entry10.get())
    sparky_spectra_path = os.path.join(entry10.get(),"Spectra")
    if not os.path.exists(sparky_spectra_path):
        os.mkdir(sparky_spectra_path)
        statusvar.set("Created SPARKY Spectra folder")
    sparky_list_path = os.path.join(entry10.get(), "Lists")
    if not os.path.exists(sparky_list_path):
        os.mkdir(sparky_list_path)
        statusvar.set("Created SPARKY Lists folder")
    sparky_save_path = os.path.join(entry10.get(), "Save")
    if not os.path.exists(sparky_save_path):
        os.mkdir(sparky_save_path)
        statusvar.set("Created SPARKY Save folder")
    sparky_proj_path = os.path.join(entry10.get(), "Projects")
    if not os.path.exists(sparky_proj_path):
        os.mkdir(sparky_proj_path)
        statusvar.set("Created SPARKY Projects folder")
    sparky_plot_path = os.path.join(entry10.get(), "Plots")
    if not os.path.exists(sparky_plot_path):
        os.mkdir(sparky_plot_path)
        statusvar.set("Created SPARKY Plots folder")

    # define color list
    colorPosList=("red", "orange", "gold", "magenta", "maroon", "royal blue", "coral", "dark orange", "lime green", "purple")
    colorNegList=("green", "cyan", "pink", "white", "tomato", "light green", "gray", "turquoise", "yellow", "light blue")

    # make sparky project file
    projectFile = sparky_proj_path + '/' + entry9.get() + '.proj'

    # start to write .proj file
    statusvar.set("Writing SPARKY project file ...")
    root.update_idletasks()
    f_proj = open(projectFile, 'w')
    f_proj.write('<sparky project file>' + '\n' +
                '<version 3.135>' + '\n' +
                '<savefiles>' +'\n')
    i_save = 0      #for color of each spectra

    # for selected spectrum
    spectrumList = []
    spectrumCnt  = 0

    for item in my_tree.selection():

        # get spectrum tree values: expno, experiment, remark
        expno = str(my_tree.item(item)["values"][0]).replace(' ','')
        expnam = str(my_tree.item(item)["values"][1]).replace(' ','')
        expinfo = str(my_tree.item(item)["values"][2]).replace(' ','')

        # derive UCSF name
        if titrationFlag == 1:
            ucsf_name = expno + '-' + expnam + '-' + expinfo
        else:
            ucsf_name = expno + '-' + expnam + '-' + protein_name.get()
        spectrumList.append(ucsf_name)
        spectrumCnt = spectrumCnt + 1

        # convert 2rr / 3rrr to UCSF
        itm_2rr = entry1.get() + '/' + expno + '/pdata/1/2rr'
        itm_3rrr = entry1.get() + '/' + expno + '/pdata/1/3rrr'
        if os.path.exists(itm_2rr):
            bruk_spectra = entry1.get() + '/' + expno + '/pdata/1/2rr'
        elif os.path.exists(itm_3rrr):
            bruk_spectra = entry1.get() + '/' + expno + '/pdata/1/3rrr'
        statusvar.set("Converting expno " + expno + ' to ' + ucsf_name + " ...")
        root.update_idletasks()
        sparky_spectra = sparky_spectra_path + '/' + ucsf_name + '.ucsf'
        # nc_proc 0 to not scale intensities; +n = divide by 2^n; -n is multiply by 2^n
        # bruk2ucsf still seems to scale intensity by factor 10^(int/1e-7), see below
        bash_command = sparky_bin_dir + 'bruk2ucsf ' + bruk_spectra + ' ' + sparky_spectra + ' 0 >& /dev/null'
        subprocess.call(bash_command, shell=True)

        # get dimensions and number of points
        os.chdir(sparky_spectra_path)
        #dim_command= sparky_bin_dir + 'ucsfdata ' + ucsf_name + ".ucsf | head -1 | awk '{print NF-1}'"
        dim_command= sparky_bin_dir + 'ucsfdata ' + ucsf_name + ".ucsf"
        #points_command= sparky_bin_dir + 'ucsfdata ' + ucsf_name + ".ucsf | head -3 | tail -1 | awk '{print $3, $4, $5}'"
        points_command= sparky_bin_dir + 'ucsfdata ' + ucsf_name + ".ucsf"
        dim = len(subprocess.check_output(dim_command, shell=True).decode('ascii').split('\n',1)[0].split())
        points = subprocess.check_output(points_command, shell=True).decode('ascii').splitlines()[2].split()[2:4]

        # get base level from processed bruker file
        # note that bruk2ucsf will scale levels? 
        clevel_path = entry1.get() + '/' + expno + '/pdata/1/clevels'
        clevel = open(clevel_path, 'r')
        for line in clevel:
            if line.startswith('##$POSBASE='):
                base_level_bruker = float(line.split()[1])
                # compensate for bruk2ucsf scaling (approximate)
                #factor = 10**round(m.log10(base_level_bruker/1e7))
                factor = base_level_bruker/1e7
                #factor = 10**m.floor(m.log10(base_level_bruker/1e7))
                #factor = 2**round(m.log(base_level_bruker/1e7))
                base_level = base_level_bruker/factor

        # write to project file 
        f_proj.write('../Save/' + ucsf_name + '.save' + '\n')

        # write .save file (minimal entries)
        statusvar.set("Writing SPARKY save files ...")
        root.update_idletasks()
        save_name = sparky_save_path + '/' + ucsf_name + '.save'
        f_save = open(save_name, 'w')
        f_save.write('<sparky save file>' + '\n' +
                    '<version 3.135>' + '\n' +
                    '<user>' + '\n' +
                    'set mode 10' + '\n' +
                    'set saveprompt 1' + '\n' +
                    'set saveinterval 0' + '\n' +
                    'set resizeViews 0' + '\n' +
                    'set keytimeout 3000' + '\n' +
                    'set cachesize 4' + '\n' +
                    'set contourgraying 1' + '\n' +
                    'default print command lpr' + '\n' +
                    'default print file ../Plots/' + ucsf_name + '.ps' + '\n' +
                    'default print options 2 27 1.000000 1.000000' + '\n' +
                    '<end user>' + '\n' +
                    '<spectrum>' + '\n' +
                    'molecule ' + entry2.get() + '\n' +
                    'condition ' + entry4.get() + '\n' +
                    'name ' + ucsf_name + '\n' +
                    'pathname ../Spectra/' + ucsf_name + '.ucsf' + '\n' +
                    'dimension ' + str(dim) + '\n' )
        if dim == 3:
            f_save.write('shift 0 0 0' + '\n')
        elif dim == 2:
            f_save.write('shift 0 0' + '\n')
        
        print(points)
        print(' '.join(points))
        f_save.write('points ' + str(' '.join(points)) + '\n')

        if dim == 3:
            f_save.write('extraPeakPlanes 0 0 0' + '\n' +
                        'extraContourPlanes false' + '\n' +
                        'assignFormat %a2' + '\n')
        elif dim == 2:
            f_save.write('assignFormat %a1' + '\n')

        f_save.write('<attached data>' + '\n' +
                    '<end attached data>' + '\n' +
                    '<view>' + '\n' +
                    'name ' + ucsf_name + '\n' +
                    'precision 0' + '\n' +
                    'precision_by_units 0 0 0' + '\n' +
                    'viewmode 0' + '\n' +
                    'show 1 label line peak grid peakgroup' + '\n' +
                    'axistype 2' + '\n')

        if dim == 3:
            f_save.write('flags crosshair crosshair2 curpos' + '\n')
        elif dim == 2:
            if spectrumCnt == 1:
                f_save.write('flags crosshair crosshair2' + '\n')
            else:
                f_save.write('flags hidden crosshair crosshair2' + '\n')

        
        # keep for now
        f_save.write('contour.pos 20 ' + str(base_level) + ' 1.200000 0.0000 ' + colorPosList[i_save] + '\n' +
                    'contour.neg 20 -' + str(base_level) + ' 1.200000 0.0000 ' + colorNegList[i_save] + '\n' +
                    '<params>' + '\n')
        # do not need to set contour explicitly; sparky will choose appropiate levels; BUT no control over colours!
        #f_save.write('<params>' + '\n')


        if dim == 3:
            # this may depend on pulse-sequence?
            f_save.write('orientation 1 2 0' + '\n')
        elif dim == 2:
            f_save.write('orientation 1 0' + '\n')

        # shift spectra on screen to have windows not fully overlapping
        f_save.write('location ' + str(300+20*(spectrumCnt-1)) + ' ' + str(200+20*(spectrumCnt-1)) + '\n' +
                    'size 500 400' + '\n')

        if dim == 3:
            # this needs to match with orientation and size of dim; go to center of spec on z-axis
            p1 = 0
            p2 = int(points[1])*0.5
            p3 = 0
            f_save.write('offset ' + str(p1) + ' ' + str(p2) + ' ' + str(p3) + '\n' +
                    'scale 1 1 1' + '\n')
        elif dim == 2:
            # this needs to match with orientation and size of dim
            p1 = 0
            p2 = 0
            f_save.write('offset ' + str(p1) + ' ' + str(p2) + '\n' +
                    'scale 1 1' + '\n')

        f_save.write('zoom 1' + '\n' +
                    'flags 0' + '\n' +
                    '<end params>' + '\n' +
                    '<end view>' + '\n' +
                    '<ornament>' + '\n' +
                    '<end ornament>' + '\n' +
                    '<end spectrum>' + '\n')

        f_save.close()
        i_save = i_save + 1
        if i_save == 10:
            i_save = 0

    f_proj.write('<end savefiles>' + '\n' +
                '<options>' + '\n' +
                '<end options>' + '\n' +
                '<syncaxes>' + '\n')
    #proj sync axes
    if titrationFlag == 1:
        # assume all have same axis which is not necessarily true
        ref_spec = spectrumList[0]
        for s in range(1,len(spectrumList)):
            f_proj.write(ref_spec + ' 0 ' + spectrumList[s] + ' 0' + '\n' + ref_spec + ' 1 ' + spectrumList[s] + ' 1' + '\n' )
    f_proj.write('<end syncaxes>' + '\n' +
                '<overlays>' + '\n')
    #proj overlays
    if titrationFlag == 1:
        for s in range(1,len(spectrumList)):
            f_proj.write('overlay ' + spectrumList[s] + ' ' + ref_spec + '\n')
    f_proj.write('<end overlays>' + '\n' +
                '<attached data>' + '\n' +
                '<end attached data>' + '\n' +
                '<molecule>' + '\n' +
                'name'  + '\n' +
                '<attached data>' + '\n' +
                '<end attached data>' + '\n' +
                '<condition>' + '\n' +
                'name'  + '\n' +
                '<resonances>' + '\n' +
                '<end resonances>' + '\n' +
                '<end condition>' + '\n' +
                '<end molecule>' + '\n' )
    f_proj.close()

    #write metadata file
    statusvar.set("Writing meta-data.txt file ...")
    root.update_idletasks()
    if len(entry10.get()) == 0:
        meta_data_path = entry1.get()
    else:
        meta_data_path = entry10.get()

    meta_dat = str(' '.join(spec_info[0].split()[0:2]))
    meta_usr = str(spec_info[0].split()[3])
    meta_sdf = str('/'.join(spec_info[1].split('/')[:-2]))
    meta_swr = str(spec_info[2].split()[1].split('/')[2])
    meta_exp = entry1.get()
    meta_prt = entry2.get()
    meta_con = entry2_1.get()
    if titrationFlag == 1:
        meta_ttr = entry11.get()
    else:
        meta_ttr = "n/a"
    meta_lab = labeling.get()
    meta_buf = entry4.get()
    meta_tmp = entry5.get()
    meta_pre = entry5_1.get()
    meta_fld = entry6.get()
    meta_ref = ref_mol.get()
    meta_sparky_proj = entry9.get()
    meta_sparky_folder = entry10.get()
    meta_tube = entry99.get()
    meta_volume = entry98.get()

    f_meta_name = os.path.join(meta_data_path+'/metadata.txt')
    f_meta = open(f_meta_name,'w')

    f_meta.write('### meta data file ###' + '\n' + '\n'
                + '----------------------------' + '\n'
                 + '## experiment ##' + '\n' + '\n'
                 + 'NMR data           : ' + meta_exp + '\n'
                 + 'SPARKY data        : ' + meta_sparky_folder + '\n'
                 + 'SPARKY project     : ' + meta_sparky_proj + '\n'
                 + '----------------------------' + '\n'
                 + '## sample condition ##' + '\n' + '\n'
                 + 'protein            : ' + meta_prt + '\n'
                 + 'labeling scheme    : ' + meta_lab + '\n'
                 + 'concentration      : ' + meta_con + '\n'
                 + 'buffer             : ' + meta_buf + '\n'
                 + 'tube type          : ' + meta_tube + '\n'
                 + 'sample volume      : ' + meta_volume + '\n' + '\n'
                 + 'temperature        : ' + meta_tmp + ' K\n'
                 + 'pressure           : ' + meta_pre + ' bar\n'
                 + 'reference molecule : ' + meta_ref + '\n' + '\n'
                 + 'titration          : ' + meta_ttr + '\n'
                 + '----------------------------' + '\n'
                 + '## spectrometer details ##' + '\n' + '\n'
                 + 'magnetic field     : ' + meta_fld + ' MHz\n'
                 + 'date               : ' + meta_dat + '\n'
                 + 'user/spectrometer  : ' + meta_usr + '\n'
                 + 'spectrometer data  : ' + meta_sdf + '\n'
                 + 'spectromer software: ' + meta_swr + '\n'
                 + '----------------------------' + '\n'
                 + '## SPARKY project contents ##' + '\n' + '\n')
    for row_id in my_tree.selection():
        row = str(my_tree.item(row_id)['values'])
        f_meta.write('  - ' + row + '\n')
    
    f_meta.write('----------------------------' + '\n' + '\n')
    f_meta.write('### end meta data file ###' + '\n')
    f_meta.close()

    # copy metafile also to original Bruker NMR folder
    shutil.copy2(meta_data_path + '/metadata.txt', meta_exp)

    statusvar.set("Done! You can close the program")
    print("\nDONE!\n")


# define the function to update fields
# with metadata in the bruker nmr folder
def update():
    global titrationFlag
    # list all 2D spectra
    n = 0
    titrationFlag = 0
    directory_contents = os.listdir(entry1.get())
    statusvar.set("Looking for NMR data ...")
    root.update_idletasks()
    for item in directory_contents:
        item_dir = os.path.join(entry1.get(),item)
        item_2rr = str(item_dir + '/pdata/1/2rr')
        item_3rrr = str(item_dir + '/pdata/1/3rrr')
        if os.path.exists(item_2rr) or os.path.exists(item_3rrr):
        #if os.path.exists(item_2rr):
            n = n +1
            if os.path.isdir(item_dir):
                if n == 1:
                    statusvar.set("Extracting meta data ...")
                    root.update_idletasks()
                    # get info from acqus file; first expno only
                    acqus_file = str(item_dir + '/acqus')
                    if os.path.isfile(acqus_file):
                        a = open(acqus_file,'r')
                        for line in a:
                            if line.startswith("##$TE= "):
                                tempature = "{:.2f}".format(float(line.split()[1].strip()))
                                temp.set(tempature)
                            elif line.startswith("##$SFO1="):
                                field_strength = "{:.2f}".format(float(line.split()[1].strip()))
                                field.set(field_strength)
                            elif line.startswith("$$"):
                                spec_info.append(' '.join(line.split()[1:]).strip())
                        a.close()
                    # get info from title file; first expno only
                    title_file = str(item_dir + '/pdata/1/title')
                    if os.path.isfile(title_file):
                        t = open(title_file, 'r')
                        for line in t:
                            if "protein" in line:
                                tname = (line.split(':')[1]).split('/')[0].strip()
                                tconc = line.split('/')[1].strip()
                                tlab  = line.split('/')[2].strip()
                                tvol  = line.split('/')[3].strip()
                                ttube = line.split('/')[4].strip()
                                labeling.set(tlab)
                                protein_name.set(tname)
                                concentration.set(tconc)
                                volume.set(tvol)
                                tube.set(ttube)
                            elif "buffer" in line:
                                buff = line.split(':')[1].strip()
                                buffer.set(buff)
                            elif "titration w/ ligand:" in line:
                                titrationFlag = 1
                                ligand = line.split()[3].strip()
                                info_line.set("titration w/ " + ligand)
                        t.close()

                # get pulprog name
                # fix Sep 6 2022 HvI
                pulse_program1 = str(item_dir + '/pulseprogram')
                pulse_program2 = str(item_dir + '/pulseprogram.precomp')
                if os.path.isfile(pulse_program1):
                    pulse_program = pulse_program1
                elif os.path.isfile(pulse_program2):
                    pulse_program = pulse_program2
                p = open(pulse_program, 'r')
                # difference between TS4 and TS3 in pulseprogram file!
                firstLine = p.readline()
                firstChar = firstLine.split()[0][0]
                if firstChar == '#':
                    # TS3: pulprog at end of path on line
                    pgWord = ((firstLine.split()[-1]).split('/')[-1]).replace("\"",'')
                elif firstChar == ';':
                    # TS4 pulprog as first word after removing ;
                    pgWord = (firstLine.replace(";",'')).split()[0]
                p.close()
                # derive root of sparky file by keeping only:
                # {HN}{NH}{HA}{HB}{CA}{CB}{CO}{HSQC}{TROSY}{NOESY}{TOCSY}{ME}
                pattern = 'hn|co|ca|cb||ha|hb|nh|hc|ch|cc|hsqc|hmqc|trosy|noesy|tocsy|cosy|me|ch3|ex|noe|t1|t2|dipsi'
                pg = ''.join(re.findall(pattern,pgWord.lower())).upper()
                if pg == '':
                    pg = pgWord
                # get remark from title file (only active for titration)
                title_file = str(item_dir + '/pdata/1/title')
                if os.path.isfile(title_file) and titrationFlag == 1:
                    t = open(title_file, 'r')
                    ligand_conc = ''
                    for line in t:
                        #if "ligand" in line:
                        if line.startswith("ligand"):
                            ligand_conc = ' '.join(line.split()[2:]).strip()
                    t.close()
                    remark = ligand_conc + ' ' + ligand
                else:
                    remark = pgWord
                # get data for tree view: expno; pulprog and remark (only for titration)
                my_tree.insert(parent='', index='end', text="", values=(item, pg, remark))

    #sort the spectra list based on experiment number
    l = [(my_tree.item(k)["values"][0], k) for k in my_tree.get_children('')]
    l.sort(key=lambda t: t[0])

    # rearrange items in sorted positions
    for index, (val, k) in enumerate(l):
        my_tree.move(k, '', index)

    #default select all spectra in the treeview
    children = my_tree.get_children()
    my_tree.selection_set(children)

    #by default set sparky folder one folder up from NMR folder
    topFolder = '/' + '/'.join(str(entry1.get()).split('/')[1:-1])
    sf_name = topFolder + '/SPARKY'
    sparky_folder.set(sf_name)
    #lastTwo = '... ' + '/'.join(sf_name.split('/')[-2:])
    #sparky_folder_display.set(lastTwo)

    #by default set project name
    if titrationFlag == 1:
        # easy: use titration and ligand name
        proj_name.set(tname + '_titration_' + ligand)
    else:
        # could be anything, but for sure use protein name
        proj_name.set(tname + '_CHANGE-THIS')

    statusvar.set("NMR data extracted. Select SPARKY folder and click convert to sparky ...")


#sort spectra by experiment number
def treeview_sort_column(my_tree, col, reverse):
    l = [(my_tree.set(k, col), k) for k in my_tree.get_children('')]
    l.sort(key=lambda columns: int(columns[0]), reverse=reverse)

    # rearrange items in sorted positions
    for index, (val, k) in enumerate(l):
        my_tree.move(k, '', index)

    # reverse sort next time
    my_tree.heading(col, command=lambda _col=col: treeview_sort_column(my_tree, _col, not reverse))






# create labels
myLabel1 = Label(root, text = "NMR folder")
myLabel5 = Label(root, text = "temperature (K)")
myLabel5_1 = Label(root, text = "pressure (bar)")
myLabel6 = Label(root, text = "magnetic field (MHz)")
myLabel99 = Label(root, text = "tube type")
myLabel98 = Label(root, text = "sample volume")

myLabel2 = Label(root, text = "protein")
myLabel2_1 = Label(root, text = "conc.")
myLabel3 = Label(root, text = "buffer")
myLabel4 = Label(root, text = "other")

myLabel11 = Label(root, text = "labeling")
myLabel7 = Label(root, text = "reference molecule")
myLabel8 = Label(root, text = "spectra")

myLabel10 = Label(root, text = "SPARKY folder")
myLabel9 = Label(root, text = "project name")



# position labels
myLabel1.grid(row=0, column=0)
myLabel5.grid(row=1, column=0)
myLabel5_1.grid(row=2, column=0)
myLabel6.grid(row=3, column=0)
myLabel99.grid(row=4, column=0)
myLabel98.grid(row=5, column=0)


myLabel2.grid(row=6, column=0)
myLabel2_1.grid(row=6, column=4, sticky="w")
myLabel3.grid(row=7, column=0)
myLabel4.grid(row=8, column=0)
myLabel11.grid(row=9, column=0)
myLabel7.grid(row=10, column=0)
myLabel8.grid(row=11, column=0)
myLabel10.grid(row=12, column=0)
myLabel9.grid(row=13, column=0)

# create input box
entry1 = Entry(root, textvariable=folder_path)
entry5 = Entry(root, width=10, textvariable=temp) #temperature
entry5_1 = Entry(root, width=10, textvariable=press) #Pressure
entry6 = Entry(root, width=10, textvariable=field) #magnetic field
entry99 = Entry(root, width=10, textvariable=tube) #tube size
entry98 = Entry(root, width=10, textvariable=volume) #sample volume

entry2 = Entry(root, width=20, textvariable=protein_name)
entry2_1 = Entry(root, width=10, textvariable=concentration)
entry4 = Entry(root, width=20, textvariable=buffer)

entry11 = Entry(root, width=20, textvariable=info_line)
entry10 = Entry(root, textvariable=sparky_folder) #sparky folder path
entry9 = Entry(root, textvariable=proj_name) #sparky project name


# position entry box
entry1.grid(row=0, column=1, columnspan=3)
entry5.grid(row=1, column=1)
entry5_1.grid(row=2, column=1)
entry6.grid(row=3, column=1)
entry99.grid(row=4, column=1)
entry98.grid(row=5, column=1)

entry2.grid(row=6, column=1, columnspan=3)
entry2_1.grid(row=6, column=5)
entry4.grid(row=7, column=1, columnspan=3)
entry11.grid(row=8, column=1, columnspan=3)
entry10.grid(row=12, column=1, columnspan=3)
entry9.grid(row=13, column=1, columnspan=3)


# create button
button1 = Button(root, text = "Open", command=open_folder)
button2 = Button(root, text = "Update", command=update)
button5 = Button(root, text = "Convert to SPARKY", command=cvt2sparky)
button6 = Button(root, text = "Select", command=select_folder)
button7 = Button(root, text = "Create",command=creat_folder)

# position button
button1.grid(row=0, column=4, sticky="sw")
button2.grid(row=0, column=5, sticky="sw")
button5.grid(row=13, column=4, sticky="sw", columnspan=2)
button6.grid(row=12, column=4, sticky="sw")
button7.grid(row=12, column=5, sticky="sw")

# dropdown menu for labeling scheme
labeling = StringVar(root)
labeling.set(" unknown") #default value
labeling_choice = OptionMenu(root, labeling,
                             " unknown",
                             " natural abundance",
                             "[U - 15N]",
                             "[U - 13C]",
                             "[U - 13C;U - 15N]",
                             "[U - 13C;U - 15N;U - 2H]",
                             "[U - 2H]",
                             "[U - 13C;U - 15N;U - 2H;99 % 1HD - Ile, Leu;99 % 1HG - Val]",
                             "[U-100% 15N]",
                             "[U - 99 % 15N]",
                             "[U - 98 % 15N]",
                             "[U - 95 % 15N]",
                             "[U - 90 % 15N]",
                             "[U - 100 % 13C]",
                             "[U - 95 % 13C]",
                             "[U - 10 % 13C]",
                             "[U - 100 % 13C;U - 100 % 15N]",
                             "[U - 99 % 13C;U - 99 % 15N]",
                             "[U - 98 % 13C;U - 98 % 15N]",
                             "[U - 95 % 13C;U - 95 % 15N]",
                             "[U - 95 % 13C;U - 90 % 15N]",
                             "[U - 10 % 13C;U - 100 % 15N]",
                             "[U - 10 % 13C;U - 99 % 15N]",
                             "[U - 100 % 13C;U - 100 % 15N;U - 80 % 2H]",
                             "[U - 100 % 2H]",
                             "[U - 99 % 2H]",
                             "[U - 13C;U - 15N]-Ade",
                             "[U - 13C;U - 15N]-Cyt",
                             "[U - 13C;U - 15N]-Gua",
                             "[U - 13C;U - 15N]-Ura",
                             "[U - 15N]-Leu",
                             "[95 % 13CA]-Trp")
labeling_choice.config(width=30, anchor='w')
labeling_choice.grid(row=9, column=1, columnspan=2)

# reference molecule dropdown menu
ref_mol = StringVar(root)
ref_mol.set("water") #default value
ref_mol_choice = OptionMenu(root, ref_mol,
                            "water", "DSS", "TSP", "TMS", "DMSO", "DMSO-d5", "DMSO-d6",
                            "methanol", "acetate", "dioxane",
                            "ammonium chloride","[15N] ammonium chloride",
                            "ammonium hydroxide", "ammonium nitrate",
                            "[15N] ammonium nitrate", "[15N, 15N] ammonium nitrate",
                            "ammonium nitrite", "ammonium sulfate",
                            "[15N] ammonium sulfate", "liquid anhydrous ammonia",
                            "formamide", "nitric acid", "[15N] nitric acid",
                            "nitromethane", "[15N] nitromethane", "urea",
                            "phosphoric acid", "phosphoric acid (85%)", "TMP",
                            "cadmium perchlorate", "adamantane", "DMPC","HFIP","TFA",
                            "TFE","TFE-d2","TMPS","TMSPA","TSP-d4","TSPA","borate",
                            "glucose","hexamethylbenzene","methyl iodide","p-dioxane",
                            "sodium acetate","sodium phosphate","suberic acid bis",
                            "trichlorofluoromethane", "na")
ref_mol_choice.config(width=30, anchor='w')
ref_mol_choice.grid(row=10, column=1, columnspan=2)

# tree_view frame, is necessary for the scroll bar
tree_frame = Frame(root)
tree_frame.grid(row=11, column=1, columnspan=3)

# create scroll bar
tree_scroll = Scrollbar(tree_frame)
tree_scroll.grid(row=11, column=7, sticky='ns')

#c reate treeview for spectra
columns = ("EXPNO","EXPERIMENT","REMARK")
my_tree = ttk.Treeview(tree_frame, show='headings', columns=columns, yscrollcommand=tree_scroll.set)
my_tree.grid(row=11, column=1, sticky='sw')

# configure scroll bar
tree_scroll.config(command=my_tree.yview)

# format columns
my_tree.column(columns[0], anchor=CENTER, width=50)
my_tree.column(columns[1], anchor=W, width=120)
my_tree.column(columns[2], anchor=W, width=120)

for col in columns:
    my_tree.heading(col, text=col, command=lambda _col=col: treeview_sort_column(my_tree, _col, False))

# status bar
sbar = Label(root, textvariable=statusvar, relief=SUNKEN, anchor="w")
sbar.grid(row=14, column=0, columnspan=2, sticky="we")

root.mainloop()
