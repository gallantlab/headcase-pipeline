# CaseForge automated pipeline

## Requirements

Python requirements are listed under `requirements.txt`. You can install them with

```bash
pip install -r requirements.txt
```

We also provide a conda environment file that you can try to use. The
environment was created on Ubuntu, so it will likely not work on other
operating systems. You can install the environment from the conda environment
file with

```bash
conda env create -f conda-environment.yml --name headcase
```

In addition, the code requires

- Blender 2.7.9. **Do not use newer versions of Blender. The code will not work.**
- Meshlab (the code works with meshlab 1.3.2 and it has not been tested with other versions)

## Usage

You need to use a structure sensor to generate a head model of the subject. Use the iOS app to send the model over email. Save the `Model.zip` file, then use `make_headcase.py` as

```bash
python make_headcase.py Model.zip Headcase.zip --headcoil s32
```

This will generate a headcase model split into four parts and zipped in `Headcase.zip`. It is possible to generate headcases for the Siemens 32ch head-coil (`--headcoil s32`), Siemens 64ch head-coil (`--headcoil s64`), or Nova 32ch head-coil (`--headcoil n32`).
