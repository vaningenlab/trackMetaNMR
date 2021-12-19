import os
import subprocess
import re
from tkinter import *
from tkinter import filedialog as fd
from tkinter import ttk

root = Tk()

#to remember spectra
intvar_dict={}
checkbutton_list=[]

# set window size
root.geometry("700x700")

#define the function to open NMR folder
def open_folder():
    global foldername
    global folder_path
    foldername = fd.askdirectory()
    folder_path.set(foldername)

#define the function to open NMR folder
def select_folder():
    global foldername_select
    global folder_path_select
    foldername_select = fd.askdirectory()
    folder_path_select.set(foldername_select)

#define function to creat a new folder
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

#fedine convert2sparky
def cvt2sparky():
    #make folders if not exist
    if not os.path.exists(entry10.get()):
        os.mkdir(entry10.get())
    sparky_data_path = os.path.join(entry10.get(),"Data")
    if not os.path.exists(sparky_data_path):
        os.mkdir(sparky_data_path)
    sparky_list_path = os.path.join(entry10.get(), "List")
    if not os.path.exists(sparky_list_path):
        os.mkdir(sparky_list_path)
    sparky_save_path = os.path.join(entry10.get(), "Save")
    if not os.path.exists(sparky_save_path):
        os.mkdir(sparky_save_path)
    sparky_proj_path = os.path.join(entry10.get(), "Projects")
    if not os.path.exists(sparky_proj_path):
        os.mkdir(sparky_proj_path)

    #convert the 2rr to ucsf
    for item in my_tree.selection():
        #convert 2rr to ucsf
        spectra_folder = str(my_tree.item(item, 'values'))
        selected_folder = re.split('\W+', spectra_folder)[1]

        ucsf_name1 = str(my_tree.item(item)["values"][2]).replace(' ','')
        ucsf_name = selected_folder + '-' + ucsf_name1

        itm_2rr = entry1.get() + '/' + selected_folder + '/pdata/1/2rr'
        itm_3rrr = entry1.get() + '/' + selected_folder + '/pdata/1/3rrr'
        if os.path.exists(itm_2rr):
            bruk_spectra = entry1.get() + '/' + selected_folder + '/pdata/1/2rr'
        elif os.path.exists(itm_3rrr):
            bruk_spectra = entry1.get() + '/' + selected_folder + '/pdata/1/3rrr'
        sparky_spectra = sparky_data_path + '/' + ucsf_name + '.ucsf'
        bash_command = '/Applications/nmrfam-sparky-mac/NMRFAM-SPARKY.app/Contents/Resources/bin/bruk2ucsf' + ' ' + bruk_spectra + ' ' + sparky_spectra
        subprocess.call(bash_command, shell=True)


    #make sparky project file
    projectFile = sparky_proj_path + '/' + entry9.get() + '.proj'

    #include createSparky.sh direct in this python script
    # write .proj file
    f_proj = open(projectFile, 'w')
    f_proj.write('<sparky project file>' + '\n' +
                '<version 3.135>' + '\n' +
                '<savefiles>' +'\n')
    i_save = 0      #for color of each spectra
    for item in my_tree.selection():
        spectra_folder = str(my_tree.item(item, 'values'))
        selected_folder = re.split('\W+', spectra_folder)[1]
        ucsf_name1 = str(my_tree.item(item)["values"][2]).replace(' ','')
        ucsf_name = selected_folder + '-' + ucsf_name1
        f_proj.write('../Save/' + ucsf_name + '.save' + '\n')

        # write .save file
        colorPosList=("red", "orange", "gold", "magenta", "maroon", "royal blue", "coral", "dark orange", "lime green", "purple")
        colorNegList=("green", "cyan", "pink", "white", "tomato", "light green", "gray", "turquoise", "yellow", "light blue")

        os.chdir(sparky_data_path)
        dim_command='/Applications/nmrfam-sparky-mac/NMRFAM-SPARKY.app/Contents/Resources/bin/ucsfdata ' + ucsf_name + ".ucsf | head -1 | awk '{print NF-1}'"
        points_command='/Applications/nmrfam-sparky-mac/NMRFAM-SPARKY.app/Contents/Resources/bin/ucsfdata ' + ucsf_name + ".ucsf | head -3 | tail -1 | awk '{print $3, $4, $5}'"
        dim = int(subprocess.check_output(dim_command, shell=True).decode('ascii').rstrip('\n'))
        points = subprocess.check_output(points_command, shell=True).decode('ascii').rstrip('\n')
    
        clevel_path = entry1.get() + '/' + selected_folder + '/pdata/1/clevels'
        clevel = open(clevel_path, 'r')
        for line in clevel:
            if line.startswith('##$POSBASE='):
                noise_val = line.split()[1]

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
                    'condition ' + ucsf_name1 + '\n' +
                    'name ' + ucsf_name + '\n' +
                    'pathname ../Data/' + ucsf_name + '.ucsf' + '\n' +
                    'dimension ' + str(dim) + '\n' )
        if dim == 3:
            f_save.write('shift 0 0 0' + '\n')
        elif dim == 2:
            f_save.write('shift 0 0' + '\n')
        
        f_save.write('points ' + str(points) + '\n')

        if dim == 3:
            f_save.write('extraPeakPlanes 0 0 0' + '\n' +
                        'extraContourPlanes false' + '\n' +
                        'assignMultiAxisGuess 7' + '\n')
        elif dim == 2:
            f_save.write('assignMultiAxisGuess 3' + '\n')

        f_save.write('assignGuessThreshold 0.000000'  + '\n' +
                    'assignRelation 1 1' + '\n' +
                    'assignRelation 2 1' + '\n')

        if dim == 3:
            f_save.write('assignRelation 3 1' + '\n')

        f_save.write('assignRange 1 0.000000' + '\n' +
                    'assignRange 2 0.000000' + '\n')

        if dim == 3:
            f_save.write('assignRange 3 0.000000' + '\n' +
                        'assignFormat %a2' + '\n')
        elif dim == 2:
            f_save.write('assignFormat %a1' + '\n')

        f_save.write('listTool sortBy label' + '\n' +
                    'listTool nameType assignment' + '\n' +
                    'listTool sortAxis w1' + '\n' +
                    'listTool showFlags frequency' + '\n')

        if dim == 3:
            f_save.write('integrate.overlapped_sep 300.00 120.000 30.000' + '\n')
        elif dim == 2:
            f_save.write('integrate.overlapped_sep 120.000 30.000' + '\n')

        f_save.write('integrate.methods 1 0 1' + '\n' +
                    'integrate.allow_motion 1' + '\n' +
                    'integrate.adjust_linewidths 1' + '\n')

        if dim == 3:
            f_save.write('integrate.motion_range 0.100 0.040 0.010' + '\n' +
                    'integrate.min_linewidth 0.0329 0.0132 0.0033' + '\n' +
                    'integrate.max_linewidth 3.2872 1.3248 0.3331' + '\n')
        elif dim == 2:
            f_save.write('integrate.motion_range 0.040 0.010' + '\n' +
                    'integrate.min_linewidth 0.0132 0.0033' + '\n' +
                    'integrate.max_linewidth 1.3248 0.3331' + '\n')

        f_save.write('integrate.fit_baseline 0' + '\n' +
                    'integrate.subtract_peaks 0' + '\n' +
                    'integrate.contoured_data 1' + '\n' +
                    'integrate.rectangle_data 0' + '\n' +
                    'integrate.maxiterations 10000' + '\n' +
                    'integrate.tolerance 0.001000' + '\n' +
                    'integrate.pseudo_voigt_mixing 0.500000' + '\n' +
                    'peak.pick 0.000000 0.000000 0.000000 0.000000 0' + '\n')

        if dim == 3:
            f_save.write('peak.pick-minimum-linewidth 0.000000 0.000000 0.000000' + '\n')
        elif dim == 2:
            f_save.write('peak.pick-minimum-linewidth 0.000000 0.000000' + '\n')

        f_save.write('peak.pick-minimum-dropoff 0.00' + '\n' +
                     'noise.sigma ' + noise_val + '\n' +
                    'ornament.label.size 2.5' + '\n' +
                    'ornament.line.size 0.4' + '\n' +
                    'ornament.peak.size 1.2' + '\n' +
                    'ornament.grid.size 0.400000' + '\n' +
                    'ornament.peakgroup.size 0.8' + '\n' +
                    'ornament.selectsize 0.500000' + '\n' +
                    'ornament.pointersize 0.500000' + '\n' +
                    'ornament.lineendsize 0.500000' + '\n' +
                    '<attached data>' + '\n' +
                    '<end attached data>' + '\n' +
                    '<view>' + '\n' +
                    'name ' + ucsf_name + '\n' +
                    'precision 0' + '\n' +
                    'precision_by_units 0 0 0' + '\n' +
                    'viewmode 0' + '\n' +
                    'show 1 label line peak grid peakgroup' + '\n' +
                    'axistype 2' + '\n')

        if dim == 3:
            f_save.write('flags crosshair crosshair2' + '\n')
        elif dim == 2:
            f_save.write('flags crosshair crosshair2' + '\n')

        f_save.write('contour.pos 20 '+ noise_val + ' 1.200000 0.0000 ' + colorPosList[i_save] + '\n' +
                    'contour.neg 20 -' + noise_val + ' 1.200000 0.00000 ' + colorNegList[i_save] + '\n' +
                    '<params>' + '\n')

        if dim == 3:
            f_save.write('orientation 2 1 0' + '\n')
        elif dim == 2:
            f_save.write('orientation 1 0' + '\n')

        f_save.write('location 300 200' + '\n' +
                    'size 500 400' + '\n')

        if dim == 3:
            f_save.write('offset 127.500000 61.999856 91.000000' + '\n' +
                    'scale 1.000000 2.865254 0.781977' + '\n')
        elif dim == 2:
            f_save.write('offset 61.999856 91.000000' + '\n' +
                    'scale 1.000000 0.781977' + '\n')

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
                '<syncaxes>' + '\n' +
                '<end syncaxes>' + '\n' +
                '<overlays>' + '\n' +
                '<end overlays>' + '\n' +
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
    if len(entry10.get()) == 0:
        meta_data_path = entry1.get()
    else:
        meta_data_path = entry10.get()

    meta_exp = entry1.get()
    meta_prt = entry2.get()
    meta_con = entry2_1.get()
    meta_ttr = entry11.get()
    meta_lab = labeling.get()
    meta_buf = entry4.get()
    meta_tmp = entry5.get()
    meta_pre = entry5_1.get()
    meta_fld = entry6.get()
    meta_ref = ref_mol.get()
    meta_sparky_proj = entry9.get()
    meta_sparky_folder = entry10.get()

    f_meta_name = os.path.join(meta_data_path+'/metadata.txt')
    f_meta = open(f_meta_name,'w')

    f_meta.write('experiment raw data: ' + meta_exp + '\n'
                 + '----------------------------' + '\n'
                 + 'sample condition' + '\n' + '\n'
                 + 'labeled sample: ' + meta_prt + '\n'
                 + 'concentration: ' + meta_con + '\n'
                 + 'titration: ' + meta_ttr + '\n'
                 + 'labeling scheme: ' + meta_lab + '\n'
                 + 'buffer: ' + meta_buf + '\n' + '\n'
                 + '----------------------------' + '\n'
                 + 'machine condition' + '\n' + '\n'
                 + 'temperature: ' + meta_tmp + ' K\n'
                 + 'pressure: ' + meta_pre + ' bar\n'
                 + 'magnetic field: ' + meta_fld + ' MHz\n'
                 + 'reference molecule: ' + meta_ref + '\n' + '\n'
                 + '----------------------------' + '\n'
                 + 'selected spectra in Sparky project:' + '\n' )
    for row_id in my_tree.selection():
        row = str(my_tree.item(row_id)['values'])
        f_meta.write(row + '\n')

    f_meta.write('\n' + 'selected spectra in Sparky project:' + meta_sparky_proj + '\n'
                 + 'Sparky project folder: ' + meta_sparky_folder + '\n')

    f_meta.write('\n' + '------------------------' + '\n' +
                 'spectra list:' + '\n')
    for row_id in my_tree.get_children():
        row = str(my_tree.item(row_id)['values'])
        f_meta.write(row + '\n')



    f_meta.close()


# declaring string variable
# for storing nmr folder path
folder_path = StringVar()
#for storing selected SPARKY path
folder_path_select = StringVar()

# for storing protein name
protein_name = StringVar()
#for storing concentration
concentration = StringVar()
# for storing titration name
titration_name = StringVar()
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

# define the function to update fields
# with metadata in the bruker nmr folder
def update():
    #Eextract temperature, magnetic field
    bruker_file = str(entry1.get() + '/1/acqus')
    x=open(bruker_file,'r')
    for line in x:
        if line.startswith("##$TE= "):
            tempature = line.split()[1]
            temp.set(tempature)
        elif line.startswith("##$SFO1="):
            field_strength = line.split()[1]
            field.set(field_strength)

    #extract protein name, buffer info, etc.
    title_file = str(entry1.get() + '/1/pdata/1/title')

    f = open(title_file, 'r')
    for line in f:
        if "protein" in line:
            name = line.split()[1]
            conc = line.split()[3] #looks better if there is a space between number and unit
            protein_name.set(name)
            concentration.set(conc)
        elif "buffer" in line:
            buff = line.split()[1:]
            buffer.set(buff)
        elif "ligand:" in line:
            ligand = line.split()[3]
            titration_name.set(ligand)
    #by default set sparky folder in NMR folder
    sf_name = str(entry1.get()+'/Sparky')
    sparky_folder.set(sf_name)


    #by default set project name of protein-ligand
    proj_name.set(ligand + '-titration')


    #list all spectra
    directory_contents = os.listdir(entry1.get())
    for item in directory_contents:
        item_dir = os.path.join(entry1.get(),item)
        item_2rr = str(item_dir + '/pdata/1/2rr')
        item_3rrr = str(item_dir + '/pdata/1/3rrr')
        #if os.path.exists(item_2rr) or os.path.exists(item_3rrr):
        if os.path.exists(item_2rr):
            if os.path.isdir(item_dir):
                pulse_program = str(item_dir + '/pulseprogram')
                title_file_2 = str(item_dir + '/pdata/1/title')
                f2 = open(title_file_2, 'r')
                if os.path.isfile(pulse_program):
                    ff = open(pulse_program, 'r')
                    pg = ff.readline().split('/')[-1]
                    ligand_detail = ''
                    for line in f2:
                        #if "ligand" in line:
                        if line.startswith("ligand"):
                            ligand_detail = line.split()[1:4]
                    my_tree.insert(parent='', index='end', text="", values=(item, pg, ligand_detail))

    #sort the spectra list based on titration points
    l = [(int((my_tree.item(k)["values"][2]).split()[0]), k) for k in my_tree.get_children('')]
    l.sort(key=lambda t: t[0])

    # rearrange items in sorted positions
    for index, (val, k) in enumerate(l):
        my_tree.move(k, '', index)

    #default select all spectra in the treeview
    children = my_tree.get_children()
    my_tree.selection_set(children)

#sort spectra by experiment number
def treeview_sort_column(my_tree, col, reverse):
    l = [(my_tree.set(k, col), k) for k in my_tree.get_children('')]
    l.sort(key=lambda columns: int(columns[0]), reverse=reverse)

    # rearrange items in sorted positions
    for index, (val, k) in enumerate(l):
        my_tree.move(k, '', index)

    # reverse sort next time
    my_tree.heading(col, command=lambda _col=col: treeview_sort_column(my_tree, _col, not reverse))






#creat labels
myLabel1 = Label(root, text = "NMR folder")
myLabel5 = Label(root, text = "temperature(K)")
myLabel5_1 = Label(root, text = "pressure(bar)")
myLabel6 = Label(root, text = "magnatic field(MHz)")

myLabel2 = Label(root, text = "protein")
myLabel2_1 = Label(root, text = "Conc.")
myLabel3 = Label(root, text = "labeling")
myLabel4 = Label(root, text = "buffer")

myLabel11 = Label(root, text = "titration")
myLabel7 = Label(root, text = "reference molecule")
myLabel8 = Label(root, text = "spectra")

myLabel10 = Label(root, text = "SPARKY folder")
myLabel9 = Label(root, text = "project name")



#position labels
myLabel1.grid(row=0, column=0)
myLabel5.grid(row=1, column=0)
myLabel5_1.grid(row=2, column=0)
myLabel6.grid(row=3, column=0)
myLabel2.grid(row=4, column=0)
myLabel2_1.grid(row=4, column=4, sticky="w")
myLabel3.grid(row=5, column=0)
myLabel4.grid(row=6, column=0)
myLabel11.grid(row=7, column=0)
myLabel7.grid(row=8, column=0)
myLabel8.grid(row=9, column=0)
myLabel10.grid(row=10, column=0)
myLabel9.grid(row=11, column=0)

#creat input box
entry1 = Entry(root, textvariable=folder_path)
entry5 = Entry(root, width=5, textvariable=temp) #temperature
entry5_1 = Entry(root, width=5, textvariable=press) #Pressure
entry6 = Entry(root, width=5, textvariable=field) #magnetic field

entry2 = Entry(root, textvariable=protein_name)
entry2_1 = Entry(root, width=5, textvariable=concentration)
entry4 = Entry(root, textvariable=buffer)

entry11 = Entry(root, textvariable=titration_name)
entry10 = Entry(root, textvariable=sparky_folder) #sparky folder path
entry9 = Entry(root, textvariable=proj_name) #sparky project name


#position entry box
entry1.grid(row=0, column=1, columnspan=3)
entry5.grid(row=1, column=1)
entry5_1.grid(row=2, column=1)
entry6.grid(row=3, column=1)
entry2.grid(row=4, column=1, columnspan=3)
entry2_1.grid(row=4, column=5)
entry4.grid(row=6, column=1, columnspan=3)
entry11.grid(row=7, column=1, columnspan=3)
entry10.grid(row=10, column=1, columnspan=3)
entry9.grid(row=11, column=1, columnspan=3)


#creat button
button1 = Button(root, text = "Open", command=open_folder)
button2 = Button(root, text = "Update", command=update)
button5 = Button(root, text = "Convert to SPARKY", command=cvt2sparky)
button6 = Button(root, text = "Select", command=select_folder)
button7 = Button(root, text = "Create",command=creat_folder)

#position button
button1.grid(row=0, column=4, sticky="sw")
button2.grid(row=0, column=5, sticky="sw")
button5.grid(row=11, column=4, sticky="sw", columnspan=2)
button6.grid(row=10, column=4, sticky="sw")
button7.grid(row=10, column=5, sticky="sw")

#dropdown menu for labeling scheme
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
labeling_choice.grid(row=5, column=1, columnspan=2)

#reference molecule dropdown menu
ref_mol = StringVar(root)
ref_mol.set(" water") #default value
ref_mol_choice = OptionMenu(root, ref_mol,
                            " DSS", " TSP", " water", " DMSO", " DMSO-d5", " DMSO-d6",
                            " methanol", " TMS", " acetate", " dioxane",
                            " ammonium chloride","[15N] ammonium chloride",
                            " ammonium hydroxide", " ammonium nitrate",
                            "[15N] ammonium nitrate", "[15N, 15N] ammonium nitrate",
                            " ammonium nitrite", " ammonium sulfate",
                            "[15N] ammonium sulfate", " liquid anhydrous ammonia",
                            " formamide", " nitric acid", "[15N] nitric acid",
                            " nitromethane", "[15N] nitromethane", " urea",
                            " phosphoric acid", " phosphoric acid (85%)", " TMP",
                            " cadmium perchlorate", " adamantane", " DMPC"," HFIP"," TFA",
                            " TFE"," TFE-d2"," TMPS"," TMSPA"," TSP-d4"," TSPA"," borate",
                            " glucose"," hexamethylbenzene"," methyl iodide"," p-dioxane",
                            " sodium acetate"," sodium phosphate"," suberic acid bis",
                            " trichlorofluoromethane", " na")
ref_mol_choice.config(width=30, anchor='w')
ref_mol_choice.grid(row=8, column=1, columnspan=2)

#tree_view frame, is necessary for the scroll bar
tree_frame = Frame(root)
tree_frame.grid(row=9, column=1, columnspan=3)

#creat scroll bar
tree_scroll = Scrollbar(tree_frame)
tree_scroll.grid(row=9, column=7, sticky='ns')

#creat treeview for spectra
columns = ("ID","EXPERIMENT","titration")
my_tree = ttk.Treeview(tree_frame, show='headings', columns=columns, yscrollcommand=tree_scroll.set)
my_tree.grid(row=9, column=1, sticky='sw')

#configure scroll bar
tree_scroll.config(command=my_tree.yview)

#format columns
my_tree.column(columns[0], anchor=CENTER, width=50)
my_tree.column(columns[1], anchor=W, width=120)
my_tree.column(columns[2], anchor=W, width=120)

for col in columns:
    my_tree.heading(col, text=col, command=lambda _col=col: treeview_sort_column(my_tree, _col, False))



root.mainloop()
