# VectorSlicerGCode

### Description

This program is meant to be used together with Vector Slicer
(https://github.com/Zmmyslony/Vector_Slicer) in order to translate the generated
print paths from a pixel based sequence of coordinates that Vector Slicer generates,
into a gcode files.

The output files have been tested using System 30M by Hyrel 3D printer using KR2 printhead with UV array, and Prusa MK4S
with PLA filament.

Before running the files need to be first sliced using Vector Slicer and environment variables need to set
according to installation guide for the Vector Slicer. If this step is omitted, the output directory should be 
specified within the code. 

### Installation
The easiest installation requires having Git (https://git-scm.com/downloads) and Anaconda (https://www.anaconda.com/download) installed on your device. 
Once they are installed, typing the following commands in the command line in the desired parent directory will complete the installation:
```
git clone https://github.com/Zmmyslony/VectorSlicerGCode.git
cd VectorSlicerGCode
conda create --name VectorSlicerGCode --file requirements.txt
conda activate VectorSlicerGCode
python main.py
```
Provided that the Vector Slicer has been successfully installed with environment paths configured (happens automatically on Windows if the 
install_win.bat was run), and that first example was run which sliced "radial_5_mm" pattern, running main.py will create 
two GCode files: the first for Hyrel 30M system and the second for Prusa's MK4S system printing PLA. The output can be validated 
using CAMotics (https://camotics.org/) which visualises the tool paths.

The programme can be later run from the command line by typing:
```
cd **PATH TO YOUR VectorSlicerGCode DIRECTORY**
conda activate VectorSlicerGCode
python main.py
```

### Issues or queries
In case of any encountered issues with the installation or any later part of the programme, please use the "Issues" tab on GitHub or 
get in touch with Michał Zmyślony (mlz22@cam.ac.uk) or John Biggins (jsb56@cam.ac.uk). The software is meant to be useful for the 3D printing
community and may be lightly maintained.

### Citations
Please cite following publication if you use any part of this code in work you publish or distribute:

    [1] Michał Zmyślony M., Klaudia Dradrach, John S. Biggins,
     Slicing vector fields into tool paths for additive manufacturing of nematic elastomers,
     Additive Manufacturing, Volume 97, 2025, 104604, ISSN 2214-8604, https://doi.org/10.1016/j.addma.2024.104604.


### Guarantee
Software is published without any guarantee or promise of maintenance. It was
developed for internal use, and is published without extensive documentation.

## Funding
<img alt="EU logo" src="https://ec.europa.eu/regional_policy/images/information-sources/logo-download-center/eu_flag.jpg" width="200">
This Project has received funding from the European Union’s Horizon 2020 research and innovation program under the Marie Skłodowska-Curie grant agreement No 956150.




