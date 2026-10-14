## createPOKYproject.py
#
# 2021-2022 Heyi Zhang / Hugo van Ingen / Utrecht University
# funded by iNEXT-Discovery program WP5 Data Management project
# 2026 - edit HVI for Windows and update with help of Claude
#
# to run:   python3 createSparkyProject.py
#
# recommended use:
#   - save alias in your shell settings, e.g. "alias createSparkyProj 'python3.10 ~/bin/createSparkyProject.py'" for tcsh
#   - then simply execute script from command line in the folder that contains the Bruker NMR dataset 
#   - click Update in the GUI
#   - edit the metadata where necessary
#   - select the spectra you want to convert; any remark will be added to the output file name
#   - click Convert if you're happy with the extracted data
#   - the POKY folder is created in same dir as the one that contains the NMR dataset
#   - it also contains "metadata.txt" which contains all extracted metadata
#   - open the POKY project file and you're good to go!
#
# this script needs:
# 1, Python 3.9 or higher
# 2, Python module tkinter
# 3, POKY/NMRFAM-SPARKY.app w/ bruk2ucsf and ucsfdata 

from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple
import os
import re
import shutil
import subprocess
from tkinter import *
from tkinter import filedialog as fd, messagebox, ttk

# Optional override. Leave as None to auto-discover POKY/NMRFAM-Sparky.
# Example Windows setting: Path(r"C:\poky_win\bin")
SPARKY_BIN_DIR: Optional[Path] = Path(r"C:\poky_win\bin")

# These paths are text stored INSIDE Sparky files, so forward slashes are intentional.
PROJECT_SAVE_PREFIX = "../Save"
SAVE_SPECTRA_PREFIX = "../Spectra"
SAVE_PLOTS_PREFIX = "../Plots"

# Tweak these values to get the aspect ratios you want
# The save files values are stored in different values than in vt windows aspect ppms
aspect_15N_2D = 0.643
aspect_13C_2D = 0.2315
aspect_13C_3D = 0.2315
aspect_13C_3D_swap = 0.347

WORK_DIR = Path.cwd().resolve()


def home_short(path: Path) -> str:
    """Show a path with the home directory replaced by ~."""
    path = Path(path)
    try:
        rel = path.relative_to(Path.home())
        return "~" if not rel.parts else "~/" + rel.as_posix()
    except ValueError:
        return str(path)

def short_path(path, parts: int = 3) -> str:
    """Show only the last `parts` components, e.g. .../NMR/POKY/Spectra"""
    p = Path(path)
    if len(p.parts) <= parts:
        return str(p)
    return ".../" + "/".join(p.parts[-parts:])

def rel_to_work(path) -> str:
    """Path relative to the working directory, for display in the GUI."""
    p = Path(path).resolve()
    try:
        return os.path.relpath(p, WORK_DIR)
    except ValueError:          # e.g. different drive on Windows
        return str(p)

def from_gui(text: str) -> Path:
    """Turn a GUI entry (relative to WORK_DIR, or absolute) into a real path."""
    p = Path(text.strip()).expanduser()
    return p if p.is_absolute() else (WORK_DIR / p).resolve()

def executable_names(name: str) -> List[str]:
    return [name + ".exe", name] if os.name == "nt" else [name]

def candidate_bin_dirs() -> List[Path]:
    """Likely POKY/Sparky locations; avoids a costly full-disk scan."""
    candidates: List[Path] = []
    if SPARKY_BIN_DIR:
        candidates.append(SPARKY_BIN_DIR)
    for env_name in ("POKY_BIN", "SPARKY_BIN"):
        if os.environ.get(env_name):
            candidates.append(Path(os.environ[env_name]))

    home = Path.home()
    roots = [home, Path.cwd()]
    if os.name == "nt":
        for env_name in ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA"):
            if os.environ.get(env_name):
                roots.append(Path(os.environ[env_name]))
        app_names = ("POKY", "NMRFAM-Sparky", "Sparky")
        for root in roots:
            for app in app_names:
                candidates += [root / app / "bin", root / app, root / app / "Contents" / "Resources" / "bin"]
    elif os.sys.platform == "darwin":
        roots += [Path("/Applications"), home / "Applications"]
        for root in roots:
            for app in ("POKY.app", "NMRFAM-Sparky.app", "Sparky.app"):
                candidates += [root / app / "Contents" / "Resources" / "bin", root / app / "Contents" / "MacOS"]
    else:
        candidates += [Path("/usr/local/bin"), Path("/opt/poky/bin"), home / "poky" / "bin"]

    # Preserve order while removing duplicates.
    return list(dict.fromkeys(path.expanduser() for path in candidates))


def find_tools() -> Tuple[Path, Path]:
    """Find a directory containing both tools, first on PATH then in standard locations."""
    # seem a bit overly complicated
    for name in executable_names("bruk2ucsf"):
        found = shutil.which(name)
        if found:
            directory = Path(found).parent
            for ucsf_name in executable_names("ucsfdata"):
                ucsf = directory / ucsf_name
                if ucsf.is_file():
                    return Path(found), ucsf

    for directory in candidate_bin_dirs():
        for bruk_name in executable_names("bruk2ucsf"):
            for ucsf_name in executable_names("ucsfdata"):
                bruk, ucsf = directory / bruk_name, directory / ucsf_name
                if bruk.is_file() and ucsf.is_file():
                    return bruk, ucsf
    searched = "\n".join(str(p) for p in candidate_bin_dirs())
    raise FileNotFoundError(
        "Could not locate both bruk2ucsf and ucsfdata.\n"
        "Set SPARKY_BIN_DIR at the top of this script or set POKY_BIN/SPARKY_BIN.\n\n"
        "Locations checked:\n" + searched
    )


def run_program(args: Sequence[object]) -> str:
    """No shell=True: spaces and backslashes in paths are handled correctly."""
    cmd = [str(x) for x in args]
    print("RUN:", " ".join(f'"{c}"' if " " in c else c for c in cmd))
    result = subprocess.run(
        [str(x) for x in args], check=True, capture_output=True,
        text=True, encoding="utf-8", errors="replace"
    )
    #print("RETURNCODE:", result.returncode)
    #print("STDOUT:", result.stdout)
    #print("STDERR:", result.stderr)
    return result.stdout

def dataset_root(start: Path) -> Path:
    """Use the nearest subfolder to find the Bruker experiment directories."""
    start = start.expanduser().resolve()
    subfolders = [ f.path for f in os.scandir(start) if f.is_dir() ]
    for directory in subfolders:
        try:
            if experiment_dirs(Path(directory)):
                return Path(directory)
        except OSError:
            pass
    return start

def processed_spectrum(experiment: Path) -> Optional[Path]:
    for filename in ("2rr", "3rrr"):
        candidate = experiment / "pdata" / "1" / filename
        if candidate.is_file():
            return candidate
    return None

def experiment_dirs(dataset: Path) -> List[Path]:
    return [p for p in dataset.iterdir() if p.is_dir() and processed_spectrum(p) is not None]

def safe_component(text: str) -> str:
    # Windows forbids these characters in output names. Keep dots/hyphens/underscores.
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "_", text.strip())
    return cleaned.rstrip(". ")

def output_name(base: str, prefix: str, suffix: str) -> str:
    return safe_component(f"{prefix}{base}{suffix}")

def sparky_rel(folder: str, filename: str) -> str:
    return f"{folder}/{filename}"

def experiment_label(pulse_program: str) -> str:
    # derive root of sparky file by keeping only:
    # {HN}{NH}{HA}{HB}{CA}{CB}{CO}{HSQC}{TROSY}{NOESY}{TOCSY}{ME} etc
    pattern = r"hn|co|ca|cb|ha|hb|nh|hc|ch|cc|hsqc|hmqc|trosy|noesy|tocsy|cosy|me|ch3|ex|noe|t1|t2|dipsi"
    return "".join(re.findall(pattern, pulse_program.lower())).upper() or pulse_program

def parse_acqus(experiment: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    acqu_file = experiment / "acqus"
    if not acqu_file.is_file():
        return values
    with acqu_file.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if line.startswith("##$TE= "):
                values["temperature"] = "{:.2f}".format(float(line.split()[1].strip()))
            elif line.startswith("##$SFO1="):
                values["field_strength"] = "{:.2f}".format(float(line.split()[1].strip()))
            elif line.startswith("##$PULPROG="):
                values["pulprog"]=line.split()[1][1:len(line.split()[1])-1]
            elif line.startswith("$$"):
                if len(line.split()) == 5:
                    values["spec_usr"] = line.split()[4]
                    values["spec_date"]= ' '.join(line.split()[1:3])
                elif len(line.split()) == 2:
                    values["spec_sdf"] = '/'.join(' '.join(line.split()[1:]).split('/')[0:-2])
                elif len(line.split()) == 3:
                     if "topspin4" in line:
                        # TS4
                        values["spec_swr"] = str(' '.join(line.split()[1:]).split('/')[2])
                    elif "TopSpinProcessing5" in line:
                        # TS5
                        values["spec_swr"] = "TopSpinProcessing5"
                    else:
                        # TS3
                        values["spec_swr"] = str(' '.join(line.split()[2:]).split('/')[1])
    return values

def parse_procs(experiment: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    proc_file = experiment / "pdata" / "1" / "procs"
    if not proc_file.is_file():
        return values
    with proc_file.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if line.startswith("##$NC_proc= "):
                values["nc_proc"] = "{:.2f}".format(float(line.split()[1].strip()))
            elif line.startswith("##$S_DEV="):
                values["sdev"] = "{:.2f}".format(float(line.split()[1].strip()))
    return values

def parse_title(experiment: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    title = experiment / "pdata" / "1" / "title"
    if not title.is_file():
        return values
    with title.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if "protein" in line and ":" in line:
                fields = [x.strip() for x in line.split(":", 1)[1].split("/")]
                for key, value in zip(("protein", "concentration", "labeling", "volume", "tube"), fields):
                    values[key] = value
            elif "buffer" in line and ":" in line:
                values["buffer"] = line.split(":", 1)[1].strip()
            elif "titration w/ ligand:" in line:
                words = line.split()
                values["ligand"] = words[3] if len(words) > 3 else "ligand"
            elif line.startswith("ligand"):
                values["ligand_concentration"] = " ".join(line.split()[2:]).strip()
    return values


def nuclei_from_ucsfdata(output: str, dimension: int) -> List[str]:
    """Extract axis nucleus labels from common ucsfdata output formats."""
    nuclei: List[str] = []
    for line in output.splitlines():
        if re.search(r"\bnucleus\b", line, re.IGNORECASE):
            fields = re.split(r"\s+", line.strip())
            index = next((i for i, x in enumerate(fields) if x.lower().startswith("nucleus")), None)
            if index is not None:
                nuclei.extend(fields[index + 1:])
    # Use only nucleus-looking tokens and normalise styles such as H1 -> 1H.
    result: List[str] = []
    for item in nuclei:
        token = item.strip(" ,;:=()[]")
        match = re.search(r"(?:(\d+)\s*)?([A-Za-z]+)|([A-Za-z]+)\s*(\d+)", token)
        if not match:
            continue
        isotope, symbol, symbol2, isotope2 = match.groups()
        normalized = f"{isotope or isotope2 or ''}{(symbol or symbol2).upper()}"
        if normalized:
            result.append(normalized)
    return result[:dimension]


def ucsf_info(ucsfdata: Path, spectrum: Path) -> Tuple[int, List[str], List[str]]:
    text = run_program([ucsfdata, spectrum])
    lines = text.splitlines()
    if not lines:
        raise RuntimeError(f"ucsfdata returned no output for {spectrum}")
    dimension = len(lines[0].split())-1
    if dimension not in (2, 3):
        raise RuntimeError(f"Could not determine 2D/3D dimensionality from ucsfdata output:\n{text}")
    if len(lines) < 3 or len(lines[2].split()) < 4:
        raise RuntimeError(f"Could not determine point counts from ucsfdata output:\n{text}")
    return dimension, lines[2].split()[2:4], nuclei_from_ucsfdata(text, dimension)

def existing_project_save_names(project: Path) -> List[str]:
    """Read existing save-file lines; preserves existing project entries on update."""
    if not project.is_file():
        return []
    names: List[str] = []
    in_savefiles = False
    with project.open("r", encoding="utf-8", errors="replace") as f:
        for raw in f:
            line = raw.strip()
            if line == "<savefiles>":
                in_savefiles = True
            elif line == "<end savefiles>":
                break
            elif in_savefiles and line:
                names.append(line)
    return names


def write_save(path: Path, name: str, dim: int, nuclei: List[str], points: List[str], level: float,
               sequence_number: int, pos_colour: str, neg_colour: str) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as f:
        buffer_short = "_".join("".join(buffer.get().split("/")[0:3]).split())
        f.write("<sparky save file by poky!>\n<version 0.1>\n<user>\nset mode 10\nset saveprompt 0\nset disregardborders 0\nset saveinterval 0\nset resizeViews 0\nset keytimeout 3000\nset cachesize 4\nset contourgraying 1\ndefault print command lpr\n")
        f.write(f"default print file {sparky_rel(SAVE_PLOTS_PREFIX, name + '.ps')}\ndefault print options 2 27 1.000000 1.000000\n<end user>\n<spectrum>\n")
        f.write(f"molecule {protein_name.get()}\ncondition {buffer_short}\nname {name}\npathname {sparky_rel(SAVE_SPECTRA_PREFIX, name + '.ucsf')}\ndimension {dim}\n")
        f.write("shift 0 0 0\n" if dim == 3 else "shift 0 0\n")
        f.write(f"points {' '.join(points)}\n")
        f.write("extraPeakPlanes 0 0 0\nextraContourPlanes false\nassignFormat %a2\n" if dim == 3 else "assignFormat %a1\n")
        flags = "flags crosshair crosshair2 curpos" if dim == 3 else ("flags crosshair crosshair2" if sequence_number == 1 else "flags hidden crosshair crosshair2")
        f.write(f"<attached data>\n<end attached data>\n<view>\nname {name}\nprecision 0\nprecision_by_units 0 0 0\nviewmode 0\nshow 1 label line peak grid peakgroup\naxistype 2\n{flags}\n")
        f.write(f"contour.pos 20 {level:.1g} 1.200000 0.0000 {pos_colour}\ncontour.neg 20 -{level:.1g} 1.200000 0.0000 {neg_colour}\n<params>\n")
        if dim == 3:
            # make sure 13C is y-axis, 15N is z-axis for triple resonance data
            # also adjust scale to ppm axis ratio 10 for 1H/15N and 8 for 1H/13C
            # last number controls 1H (w3) size wrt to other dims (w1/w2)
            # teh correct number also depends on display size, as ppm/cm with certain dpi translates to ppm/pixel
            # vt aspect of 1 ppm makes 1ppm vertical = x cm = 1ppm horizonal y cm
            #                          1000 pi / 1500 pi
            # scale = 0.23 ==> 
            if nuclei[0] == "13C" and nuclei[1] == "15N":
                f.write(f"orientation 1 2 0\nlocation {300 + 20*(sequence_number-1)} {200 + 20*(sequence_number-1)}\nsize 500 400\noffset 0 {int(points[1])//2} 0\n")
                # should be 0.125 but ...
                f.write(f"scale 1 1 {aspect_13C_3D_swap}\n")
            elif nuclei[1] == "13C" and nuclei[0] == "15N":
                # Tammo's sequences
                f.write(f"orientation 2 1 0\nlocation {300 + 20*(sequence_number-1)} {200 + 20*(sequence_number-1)}\nsize 500 400\noffset 0 {int(points[1])//2} 0\n")
                # should be 0.125 but ...
                f.write(f"scale 1 1 {aspect_13C_3D}\n")
            else:
                f.write(f"orientation 2 1 0\nlocation {300 + 20*(sequence_number-1)} {200 + 20*(sequence_number-1)}\nsize 500 400\noffset 0 {int(points[1])//2} 0\n")
                f.write(f"scale 1 1 1\n")
        else:
            f.write(f"orientation 1 0\nlocation {300 + 20*(sequence_number-1)} {200 + 20*(sequence_number-1)}\nsize 500 400\noffset 0 0\nscale 1 1\n")
            if nuclei[0] == "15N":
                # should be 0.1 but ... 
                f.write(f"scale 1 {aspect_15N_2D}\n")
            elif nuclei[0] == "13C":
                # should be 0.25 or 0.125 but ...
                f.write(f"scale 1 {aspect_13C_2D}\n")
            else:
                f.write(f"scale 1 1\n")
        f.write("zoom 1\nflags 0\n<end params>\n<end view>\n<ornament>\n<end ornament>\n<end spectrum>\n")


def sync_lines(records: List[Tuple[str, List[str]]]) -> List[str]:
    """Synchronise every matching nucleus axis with the first spectrum containing it."""
    first_axis: Dict[str, Tuple[str, int]] = {}
    lines: List[str] = []
    for name, nuclei in records:
        for axis, nucleus in enumerate(nuclei):
            if not nucleus:
                continue
            if nucleus in first_axis:
                ref_name, ref_axis = first_axis[nucleus]
                if ref_name != name:
                    lines.append(f"{ref_name} {ref_axis} {name} {axis}")
            else:
                first_axis[nucleus] = (name, axis)
    return lines


def create_projections(ucsfdata: Path, source: Path, source_name: str, spectra_dir: Path,
                       save_dir: Path, level: float, seq: int, pos: str, neg: str) -> List[Tuple[str, List[str]]]:
    """Create one projection along each 3D axis. Failed axes are reported but do not abort conversion."""
    records: List[Tuple[str, List[str]]] = []
    for axis in ("1", "2"):
        name = safe_component(f"{source_name}_p{axis}")
        output = spectra_dir / f"{name}.ucsf"
        try:
            statusvar.set(f"Projecting: {short_path(source)}")
            root.update()
            run_program([ucsfdata, f"-p{axis}","-o", output, source])
            dim, points, nuclei = ucsf_info(ucsfdata, output)
            if dim != 2:
                raise RuntimeError("projection was not 2D")
            write_save(save_dir / f"{name}.save", name, dim, nuclei, points, level, seq, pos, neg)
            records.append((name, nuclei))
        except (OSError, subprocess.CalledProcessError, RuntimeError) as exc:
            statusvar.set(f"Projection {axis} skipped for {source_name}: {exc}")
            root.update()
    return records

root = Tk()
root.geometry("800x700")
root.title("Create POKY/Sparky Project")
# select the folder where the program is started as the NMR data folder
initial_dataset = dataset_root(WORK_DIR)
folder_path = StringVar(root, value=rel_to_work(initial_dataset))
sparky_folder = StringVar(root, value=rel_to_work(initial_dataset.parent / "POKY"))
# initialize variables
protein_name, concentration, buffer, buffer_short = StringVar(root), StringVar(root), StringVar(root), StringVar(root)
temp, field, press, pulprog = StringVar(root), StringVar(root), StringVar(root, value="1"), StringVar(root)
tube, volume, info_line, proj_name = StringVar(root), StringVar(root), StringVar(root), StringVar(root)
nc_proc, sdev = StringVar(root), StringVar(root)
prefix, suffix = StringVar(root), StringVar(root)
spec_usr, spec_sdf, spec_swr, spec_date = StringVar(root), StringVar(root), StringVar(root), StringVar(root)
labeling, ref_mol = StringVar(root, value=" unknown"), StringVar(root, value="water")
projections = BooleanVar(root, value=False)
statusvar = StringVar(root, value="Click Update or select the NMR dataset with Open...")
titration_flag = False
ligand_name = ""


def selected_dataset() -> Path:
    path = dataset_root(from_gui(folder_path.get()))
    if not path.is_dir() or not experiment_dirs(path):
        raise ValueError("Choose the directory that contains the numbered Bruker experiment folders.")
    return path

def open_dataset() -> None:
    chosen = fd.askdirectory(initialdir=str(WORK_DIR))
    if chosen:
        root_dir = dataset_root(Path(chosen))
        folder_path.set(rel_to_work(root_dir))
        sparky_folder.set(rel_to_work(root_dir.parent / "POKY"))

def select_project_dir() -> None:
    chosen = fd.askdirectory(initialdir=str(WORK_DIR))
    if chosen:
        sparky_folder.set(rel_to_work(chosen))

def create_project_dir() -> None:
    try:
        target = from_gui(sparky_folder.get())
        target.mkdir(parents=True, exist_ok=False)
        statusvar.set(f"Created {short_path(target)}")
    except FileExistsError:
        messagebox.showinfo("Folder exists", "The project folder already exists; it can be updated/extended.")
    except OSError as exc:
        messagebox.showerror("Cannot create folder", str(exc))

# define the function to update fields
# with metadata from the Bruker Topspin NMR folder
def update() -> None:
    global titration_flag, ligand_name
    try:
        dataset = selected_dataset()
    except ValueError as exc:
        messagebox.showerror("Invalid dataset", str(exc))
        return
    for item in tree.get_children():
        tree.delete(item)
    titration_flag, ligand_name = False, ""
    # find all expno folders
    folders = sorted(experiment_dirs(dataset), key=lambda p: (not p.name.isdigit(), int(p.name) if p.name.isdigit() else p.name))
    first_metadata: Dict[str, str] = {}
    for index, experiment in enumerate(folders):
        title = parse_title(experiment)
        acq_info = parse_acqus(experiment)
        if index == 0:
            # meta data only form first expno -- assumed the same in the rest
            # from acqus and title
            first_metadata = acq_info
            temp.set(acq_info.get("temperature", temp.get()))
            field.set(acq_info.get("field_strength", field.get()))
            spec_usr.set(acq_info.get("spec_usr", spec_usr.get()))
            spec_sdf.set(acq_info.get("spec_sdf", spec_sdf.get()))
            spec_swr.set(acq_info.get("spec_swr", spec_swr.get()))
            spec_date.set(acq_info.get("spec_date", spec_date.get()))
            first_metadata = title
            protein_name.set(title.get("protein", protein_name.get()))
            concentration.set(title.get("concentration", concentration.get()))
            labeling.set(title.get("labeling", labeling.get()))
            tube.set(title.get("tube", tube.get()))
            volume.set(title.get("volume", volume.get()))
            buffer.set(title.get("buffer", buffer.get()))
            if "ligand" in title:
                titration_flag, ligand_name = True, title["ligand"]
                info_line.set(f"titration w/ {ligand_name}")
        pulprog.set(acq_info.get("pulprog", pulprog.get()))
        if titration_flag:
            remark = f"{title.get('ligand_concentration', '')} {ligand_name}".strip()  
        else:
            remark = f"{title.get('remark', '')}".strip()
        tree.insert("", "end", values=(experiment.name, pulprog.get(), experiment_label(pulprog.get()), remark))
    tree.selection_set(tree.get_children())
    base = first_metadata.get("protein", protein_name.get() or "sample")
    proj_name.set(f"{base}_titration_{ligand_name}" if titration_flag else f"{base}_CHANGE-THIS")
    statusvar.set(f"Found {len(folders)} processed spectra in dataset root: {short_path(dataset)}")

def convert() -> None:
    try:
        dataset, project = selected_dataset(), Path(sparky_folder.get()).expanduser()
        selected = tree.selection()
        if not selected:
            raise ValueError("Select one or more spectra.")
        if not proj_name.get().strip():
            raise ValueError("Enter a project name.")
        bruk2ucsf, ucsfdata = find_tools()
    except (ValueError, FileNotFoundError) as exc:
        messagebox.showerror("Cannot convert", str(exc))
        return

    spectra, saves, projects = project / "Spectra", project / "Save", project / "Projects"
    for directory in (spectra, saves, projects, project / "List", project / "Plots"):
        directory.mkdir(parents=True, exist_ok=True)
    project_file = projects / f"{safe_component(proj_name.get())}.proj"
    # store any already save files from project file
    save_entries = existing_project_save_names(project_file)
    seen_entries = set(save_entries)
    records: List[Tuple[str, List[str]]] = []
    colours_pos = ("red", "orange", "gold", "magenta", "maroon", "royal blue", "coral", "dark orange", "lime green", "purple")
    colours_neg = ("green", "cyan", "pink", "white", "tomato", "light green", "gray", "turquoise", "yellow", "light blue")

    try:
        for seq, item in enumerate(selected, 1):
            expno, pulprog, expname, remark = (str(x).replace(" ", "") for x in tree.item(item)["values"])
            if remark != "":
                core = f"{expno}-{expname}-{protein_name.get()}-{remark}"
            else:
                core = f"{expno}-{expname}-{protein_name.get()}"
            name = output_name(core, prefix.get(), suffix.get())
            raw = processed_spectrum(dataset / expno)
            if raw is None:
                raise FileNotFoundError(f"No 2rr/3rrr for experiment {expno}")
            # get nc_proc and noise level from processed data in expno 
            proc_info = parse_procs(dataset / expno)
            sdev.set(proc_info.get("sdev", sdev.get()))
            nc_proc.set(proc_info.get("nc_proc", nc_proc.get()))
            # set contour level to 6x noise level extracted from procs file
            level = 6.0*float(sdev.get())
            # now make save files
            ucsf = spectra / f"{name}.ucsf"
            save = saves / f"{name}.save"
            statusvar.set(f"Converting experiment {expno} ...")
            root.update()
            if not ucsf.exists():
                # nc_proc 0 to not scale intensities; +n = divide by 2^n; -n is multiply by 2^n
                run_program([bruk2ucsf, raw, ucsf, "0"])
            dim, points, nuclei = ucsf_info(ucsfdata, ucsf)
            if not save.exists():
                write_save(save, name, dim, nuclei, points, level, seq, colours_pos[(seq-1) % 10], colours_neg[(seq-1) % 10])
            entry = sparky_rel(PROJECT_SAVE_PREFIX, save.name)
            if entry not in seen_entries:
                save_entries.append(entry); seen_entries.add(entry)
            records.append((name, nuclei))

            if projections.get() and dim == 3:
                #create_projections(ucsfdata, ucsf, name, spectra, saves, level, seq, colours_pos[(seq-1) % 10], colours_neg[(seq-1) % 10])
                for projection_name, projection_nuclei in create_projections(ucsfdata, ucsf, name, spectra, saves, level, seq, colours_pos[(seq-1) % 10], colours_neg[(seq-1) % 10]):
                    pentry = sparky_rel(PROJECT_SAVE_PREFIX, f"{projection_name}.save")
                    if pentry not in seen_entries:
                        save_entries.append(pentry); seen_entries.add(pentry)
                    records.append((projection_name, projection_nuclei))

        with project_file.open("w", encoding="utf-8", newline="\n") as f:
            f.write("<sparky project file by poky!>\n<version 0.1>\n<savefiles>\n")
            f.write("\n".join(save_entries) + "\n<end savefiles>\n<options>\n<end options>\n<syncaxes>\n")
            f.write("\n".join(sync_lines(records)) + "\n<end syncaxes>\n<overlays>\n<end overlays>\n<attached data>\n<end attached data>\n<molecule>\nname\n<attached data>\n<end attached data>\n<condition>\nname\n<resonances>\n<end resonances>\n<end condition>\n<end molecule>\n")
        # also store plain text meta data file
        write_metadata(project, dataset)
        statusvar.set(f"Done: {short_path(project_file)}")
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        details = exc.stderr if isinstance(exc, subprocess.CalledProcessError) and exc.stderr else str(exc)
        messagebox.showerror("Conversion failed", details)
        statusvar.set("Conversion failed; see error dialog.")


def write_metadata(project: Path, dataset: Path) -> None:
    metadata = project / "metadata.txt"
    with metadata.open("w", encoding="utf-8", newline="\n") as f:
        f.write("### meta data file ###\n\n")
        f.write("----------------------------\n## experiment ##\n")
        f.write(f"NMR data           : {dataset}\nSPARKY data        : {project}\nSPARKY project     : {proj_name.get()}\n\n")
        f.write("----------------------------\n## sample condition ##\n")
        f.write(f"protein            : {protein_name.get()}\nlabeling scheme    : {labeling.get()}\nconcentration      : {concentration.get()}\nbuffer             : {buffer.get()}\nother info         : {info_line.get()}\n")
        f.write(f"sample volume      : {volume.get()}\ntube type          : {tube.get()}\n")
        f.write(f"temperature        : {temp.get()} K\npressure           : {press.get()} bar\nreference molecule : {ref_mol.get()}\ntitration          : {info_line.get() if titration_flag else 'n/a'}\n\n")
        f.write("----------------------------\n## spectrometer details ##\n")
        f.write(f"magnetic field        : {field.get()} MHz\ndate                  : {spec_date.get()}\nuser/spectrometer     : {spec_usr.get()}\nspectrometer data     : {spec_sdf.get()}\nspectrometer software : {spec_swr.get()}\n\n")
        f.write(f"---------------------------\n## POKY project contents ##\n")
        for row in tree.selection():
            f.write(f"  - {tree.item(row)['values']}\n")
        f.write(f"---------------------------\n### end meta data file ###\n")
    # copy metafile also to parent folder
    shutil.copy2(metadata, dataset / "metadata.txt")

def edit_remark(event) -> None:
    """Double-click on REMARK cell -> inline Entry to edit it."""
    row_id = tree.identify_row(event.y)
    col_id = tree.identify_column(event.x)
    if not row_id or col_id != "#4":     # #4 = 4th displayed column = REMARK
        return

    x, y, width, height = tree.bbox(row_id, col_id)
    current = tree.set(row_id, "REMARK")

    edit_var = StringVar(root, value=current)
    entry = Entry(tree, textvariable=edit_var)
    entry.place(x=x, y=y, width=width, height=height)
    entry.focus_set()
    entry.select_range(0, "end")

    def save(event=None) -> None:
        tree.set(row_id, "REMARK", edit_var.get().strip())
        entry.destroy()

    def cancel(event=None) -> None:
        entry.destroy()

    entry.bind("<Return>", save)
    entry.bind("<KP_Enter>", save)
    entry.bind("<FocusOut>", save)
    entry.bind("<Escape>", cancel)

# GUI
Label(root, text=f"Working dir: {home_short(WORK_DIR)}", anchor="w", fg="gray30")\
    .grid(row=1, column=0, columnspan=6, sticky="we")

labels = [("NMR dataset root (rel.)", 3), ("temperature (K)", 4), ("pressure (bar)", 5), ("magnetic field (MHz)", 6), ("tube type", 7), ("sample volume", 8), ("protein", 9), ("buffer", 10), ("other", 11), ("labeling", 12), ("reference molecule", 13), ("spectra", 14), ("POKY folder (rel.)", 15), ("project name", 16), ("file prefix (optional)", 17), ("file suffix (optional)", 18)]
for text, row in labels:
    Label(root, text=text).grid(row=row, column=0, sticky="w")

for row, variable, width in [(3, folder_path, 40), (4, temp, 10), (5, press, 10), (6, field, 10), (7, tube, 10), (8, volume, 10), (9, protein_name, 35), (10, buffer, 35), (11, info_line, 35), (15, sparky_folder, 40), (16, proj_name, 35), (17, prefix, 20), (18, suffix, 20)]:
    Entry(root, textvariable=variable, width=width).grid(row=row, column=1, columnspan=3, sticky="w")

Button(root, text="Open", command=open_dataset).grid(row=3, column=4)
Button(root, text="Update", command=update).grid(row=3, column=5)
Button(root, text="Select", command=select_project_dir).grid(row=15, column=4)
Button(root, text="Create", command=create_project_dir).grid(row=15, column=5)
Button(root, text="Convert/Update", command=convert).grid(row=18, column=3)
Checkbutton(root, text="Create 2D projections from selected 3D spectra", variable=projections).grid(row=19, column=1, columnspan=4, sticky="w")

OptionMenu(root, labeling, " unknown", " natural abundance", "[U - 15N]", "[U - 13C]", "[U - 13C;U - 15N]", "[U - 13C;U - 15N;U - 2H]", "[U - 2H]").grid(row=12, column=1, columnspan=2, sticky="w")
OptionMenu(root, ref_mol, "water", "DSS", "TSP", "TMS", "DMSO", "DMSO-d5", "DMSO-d6", "methanol", "acetate", "dioxane", "na").grid(row=13, column=1, columnspan=2, sticky="w")

frame = Frame(root); frame.grid(row=14, column=1, columnspan=4, sticky="w")
scroll = Scrollbar(frame); scroll.grid(row=0, column=1, sticky="ns")

tree = ttk.Treeview(frame, show="headings", columns=("EXPNO", "PULPROG", "EXPERIMENT", "REMARK"), yscrollcommand=scroll.set, height=8)
tree.grid(row=0, column=0)
tree.bind("<Double-1>", edit_remark)
scroll.config(command=tree.yview)
for col, width in (("EXPNO", 55), ("PULPROG", 140), ("EXPERIMENT", 140), ("REMARK", 200)):
    tree.column(col, width=width, anchor=W); tree.heading(col, text=col)

Label(root, textvariable=statusvar, relief=SUNKEN, anchor="w").grid(row=20, column=0, columnspan=6, sticky="we")
root.mainloop()
