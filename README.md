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
