"""Generate an MRI-compatible headcase from a 3D head model acquired with a Structure Sensor."""

import argparse
import os
import shlex
import shutil
import subprocess as sp
import zipfile
from tempfile import NamedTemporaryFile as Temp
from tempfile import mkdtemp

import pymeshlab
from packaging.version import Version

from blender_code import blender_carve_model_template

cwd, _ = os.path.split(__file__)
DEFAULT_CUSTOMIZATIONS = os.path.join(cwd, "stls", "default_customizations.stl")


def _call_blender(code):
    """Call blender, while running the given code. If the filename doesn't exist,
    save a new file in that location. New files will be initially cleared by deleting
    all objects.
    """
    with Temp(mode="w") as tf:
        cmd = "blender -b -P {script}".format(script=tf.name)

        tf.write(code)
        tf.flush()
        sp.call(shlex.split(cmd))


def meshlab_filter(ms):
    """Apply mesh filters to clean and process a 3D model using PyMeshLab."""
    # "Transform: Move, Translate, Center"
    ms.apply_filter(filter_name="compute_matrix_from_translation")
    # "Transform: Rotate"
    ms.apply_filter(
        filter_name="compute_matrix_from_rotation",
        rotaxis="Z axis",
        rotcenter="barycenter",
        angle=0,
    )
    ms.apply_filter(
        filter_name="compute_matrix_from_scaling_or_normalization",
        axisx=1000,
        scalecenter="barycenter",
        unitflag=False,
    )
    # "Merge Close Vertices"
    ms.apply_filter(
        filter_name="meshing_merge_close_vertices", threshold=pymeshlab.Percentage(0.5)
    )
    # "Remove Isolated pieces (wrt Diameter)"
    ms.apply_filter(
        filter_name="meshing_remove_connected_component_by_diameter",
        mincomponentdiag=pymeshlab.AbsoluteValue(150),
        removeunref=True,
    )
    # "Remove Faces from Non Manifold Edges"
    ms.apply_filter(
        filter_name="meshing_repair_non_manifold_edges", method="Remove Faces"
    )
    # "Close Holes"
    ms.apply_filter(
        filter_name="meshing_close_holes",
        maxholesize=100,
        newfaceselected=False,
    )
    # "Surface Reconstruction: Poisson"
    ms.apply_filter(
        filter_name="generate_surface_reconstruction_screened_poisson",
        depth=11,
        fulldepth=2,
        samplespernode=1,
        # pointweight=0,
        preclean=True,
    )
    # "Vertex Attribute Transfer"
    ms.apply_filter(
        filter_name="transfer_attributes_per_vertex",
        sourcemesh=1,
        targetmesh=0,
        geomtransfer=True,
        colortransfer=False,
        upperbound=pymeshlab.Percentage(8.631),
    )
    return ms


def meshlab_filter_pre2022(ms):
    """Apply mesh filters to clean and process a 3D model using PyMeshLab (pre-2022)."""
    # "Transform: Move, Translate, Center"
    ms.apply_filter(filter_name="transform_translate_center_set_origin")
    # "Transform: Rotate"
    ms.apply_filter(
        filter_name="transform_rotate",
        rotaxis="Z axis",
        rotcenter="barycenter",
        angle=0,
    )
    ms.apply_filter(
        filter_name="transform_scale_normalize",
        axisx=1000,
        scalecenter="barycenter",
        unitflag=False,
    )
    # "Merge Close Vertices"
    ms.apply_filter(filter_name="merge_close_vertices", threshold=0.5)
    # "Remove Isolated pieces (wrt Diameter)"
    ms.apply_filter(
        filter_name="remove_isolated_pieces_wrt_diameter",
        mincomponentdiag=150,
        removeunref=True,
    )
    # "Remove Faces from Non Manifold Edges"
    ms.apply_filter(filter_name="repair_non_manifold_edges_by_removing_faces")
    # "Close Holes"
    ms.apply_filter(
        filter_name="close_holes",
        maxholesize=100,
        newfaceselected=False,
    )
    # "Surface Reconstruction: Poisson"
    ms.apply_filter(
        filter_name="surface_reconstruction_screened_poisson",
        depth=11,
        fulldepth=2,
        samplespernode=1,
        # pointweight=0,
        preclean=True,
    )
    # "Vertex Attribute Transfer"
    ms.apply_filter(
        filter_name="vertex_attribute_transfer",
        sourcemesh=1,
        targetmesh=0,
        geomtransfer=True,
        colortransfer=False,
        upperbound=8.631,
    )
    return ms


def model_clean(infile, outfile):
    """
    Clean and process a 3D model file.

    Parameters
    ----------
    infile : str
        The input file path of the 3D model. It can be a zip file containing the model
        or a direct path to the model file.
    outfile : str
        The output file path to save the cleaned and processed 3D model.

    Notes
    -----
    This function cleans and processes a 3D model file using PyMeshLab.
    If the input file is a zip file, it will be extracted to a temporary directory
    before processing. The cleaned and processed model will be saved to the specified
    output file.

    The function checks the version of PyMeshLab installed and applies the appropriate
    mesh filters accordingly.

    If the input file is a zip file, the temporary directory will be deleted after
    processing.

    Examples
    --------
    >>> model_clean("input.zip", "output.ply")
    """

    clean_tmp = False
    if infile.endswith("zip"):
        path = mkdtemp()
        pkg = zipfile.ZipFile(infile)
        pkg.extractall(path)
        pkg.close()
        clean_tmp = True

        infile = os.path.join(path, "Model.obj")
    else:
        infile = os.path.abspath(infile)
    ms = pymeshlab.MeshSet(verbose=True)
    ms.load_new_mesh(infile)

    PYMESHLAB_VERSION = pymeshlab_version()
    if PYMESHLAB_VERSION >= Version("2022.2"):
        ms = meshlab_filter(ms)
    else:
        ms = meshlab_filter_pre2022(ms)

    ms.save_current_mesh(outfile)
    if clean_tmp:
        shutil.rmtree(path)


def align_scan(infile, outfile):
    """
    Automatically aligns a head scan and saves the aligned scan as an STL file.

    Parameters
    ----------
    infile : str
        The path to the input scan file.
    outfile : str
        The path to save the aligned scan as an STL file.
    """
    from cortex import formats

    from autocase3d.fmin_autograd import fit_xfm_autograd

    new_pts, new_polys, opt_params = fit_xfm_autograd(infile)
    print("Final params: ", opt_params)
    formats.write_stl(outfile, new_pts, new_polys)


def gen_case(
    scanfile,
    outfile,
    workdir=None,
    casetype="s32",
    nparts=4,
    customizations=DEFAULT_CUSTOMIZATIONS,
    expand_head_model=0.1):
    """
    Generate a headcase.

    Parameters
    ----------
    scanfile : str
        Path to the cleaned and aligned head model.
    outfile : str
        Path to the output file where the generated head case will be saved.
    workdir : str, optional
        Path to the working directory. If not provided, a temporary directory will be
        created and deleted after processing.
    casetype : str, optional
        Type of head case to generate.
        Possible values are 's32', 's64', 'n32', 'meg_ctf275'.
        Default is 's32'.
    nparts : int, optional
        Number of parts to divide the head case into. Possible values are 2 or 4.
        Default is 4.
    customizations : str, optional
        Path to the customizations file to remove additional parts from the headcase.
        Default is `default_customizations.stl` in the `stls` folder.
    expand_head_model : float, optional
        Factor (in mm) to expand the head model by. Default is 0.1.

    Examples
    --------
    >>> gen_case("02aligned.stl", "head_case.zip", casetype="s64", nparts=2)
    """

    customizations = os.path.abspath(customizations)
    casefile = dict(
        s32="s32.stl", s64="s64.stl", n32="n32.stl", meg_ctf275="meg_ctf275.stl"
    )
    casefile = os.path.join(cwd, "stls", casefile[casetype])

    cleanup = False
    if workdir is None:
        workdir = mkdtemp()
        cleanup = True

    blender_params = dict(
        preview=casefile,
        scan=scanfile,
        customizations=customizations,
        tempdir=workdir,
        nparts=nparts,
        shrinking_factor=expand_head_model,
    )
    print("Generating head model by calling Blender with the following parameters:")
    print(blender_params)
    _call_blender(blender_carve_model_template.format(**blender_params))

    pieces = {
        2: ["back.stl", "front.stl"],
        4: ["back_bottom.stl", "back_top.stl", "front_bottom.stl", "front_top.stl"],
    }
    with zipfile.ZipFile(outfile, mode="w") as pkg:
        for fn in pieces[nparts]:
            pkg.write(os.path.join(workdir, fn), fn)

    if cleanup:
        shutil.rmtree(workdir)


def pymeshlab_version():
    """Return the version of PyMeshLab installed."""
    out = sp.check_output(
        [
            "python",
            "-c",
            "import pymeshlab ; pymeshlab.pmeshlab.print_pymeshlab_version()",
        ]
    )
    # b'PyMeshLab 2021.10 based on MeshLab 2021.10d\n'
    version = Version(out.decode().split()[1])
    return version


def pipeline(
    infile,
    outfile,
    casetype="s32",
    nparts=4,
    workdir=None,
    customizations=DEFAULT_CUSTOMIZATIONS,
    expand_head_model=0.1,
):
    """
    Run the pipeline to generate a head case from a head model.

    Parameters
    ----------
    infile : str
        Path to the input file containing the head model. It can either be a zip file
        generated by the Structure Sensor or an obj file containing the head model.
    outfile : str
        Path to the output file containing the generated head case.
    casetype : str, optional
        Type of head case, default is "s32" (Siemens 32ch). Possible values are
        "s32", "s64", "n32", "meg_ctf275".
    nparts : int, optional
        Number of parts, default is 4.
    workdir : str, optional
        Path to the working directory, default is None.
    customizations : dict, optional
        Customizations for the head case, default is `default_customizations.stl`.
    expand_head_model : float, optional
        Factor (in mm) to expand the head model by, default is 0.1.

    Notes
    -----
    This function performs the following steps:
    1. If `workdir` is provided, creates the working directory if it does not exist.
    2. Cleans the head model by calling `model_clean` function.
    3. Aligns the cleaned head model by calling `align_scan` function.
    4. Generates the head case by calling `gen_case` function.
    5. If `workdir` is not provided, removes the working directory.

    Examples
    --------
    >>> pipeline("Model.zip", "Headcase.zip", casetype="s32", nparts=4)
    """

    if workdir is not None:
        working_dir = os.path.abspath(workdir)
        os.makedirs(working_dir, exist_ok=True)
        print(f"Intermediate files will be stored in in {working_dir}")
    else:
        working_dir = mkdtemp()
    cleaned = os.path.join(working_dir, "01cleaned.ply")
    aligned = os.path.join(working_dir, "02aligned.stl")
    print("Cleaning head model")
    model_clean(infile, cleaned)
    print("Aligning head model")
    align_scan(cleaned, aligned)
    print("Making head case")
    gen_case(
        aligned,
        outfile,
        working_dir,
        casetype=casetype,
        nparts=nparts,
        customizations=customizations,
        expand_head_model=expand_head_model
    )

    if workdir is None:
        shutil.rmtree(working_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "infile",
        type=str,
        help="Input head model generated by the Structure Sensor (.zip or .obj). "
        "Alternatively, if the flag --generate-headcase-only is passed, the input "
        "file should be an stl file containing a cleaned and aligned head model.",
    )
    parser.add_argument(
        "outfile",
        type=str,
        help="output headcase model (*.zip)",
    )
    parser.add_argument(
        "--headcoil",
        "-c",
        type=str,
        default="s32",
        help="Type of headcoil: s32 (siemens 32ch), s64 (siemens 64ch), "
        "n32 (nova 32ch), or meg_ctf275 (MEG CTF275). Default: s32",
        choices=["s32", "s64", "n32", "meg_ctf275"],
    )
    parser.add_argument(
        "--nparts",
        "-p",
        type=int,
        default=4,
        required=False,
        choices=[2, 4],
        help="Split the headcase model into 4 (default) or 2 parts. Four parts require "
        "less support material when 3d printing the headcase.",
    )
    parser.add_argument(
        "--workdir",
        type=str,
        required=False,
        default=None,
        help="Working directory to use. If this flag is not used, "
        "then a temporary directory is created and deleted at the end. "
        "If this flag is used, the intermediate models are stored "
        "in the working directory and not deleted. "
        "This option is useful for manual tuning of the alignment, "
        "in combination with the flag --generated-headcase-only",
    )
    parser.add_argument(
        "--generate-headcase-only",
        action="store_true",
        help="Only generate the headcase given the input stl file. This assumes that "
        "the input stl contains a head model that is already cleaned and aligned.",
    )
    parser.add_argument(
        "--customizations-file",
        type=str,
        default=DEFAULT_CUSTOMIZATIONS,
        help="File containing additional shapes that will be removed from the headcase "
        "after carving out the head model. For example, this file is used to carve out "
        "space near the ears and the nose bridge. This customization file can be edited "
        f"to fine-tune the headcase. The default file is {DEFAULT_CUSTOMIZATIONS}",
    )
    parser.add_argument(
        "--expand-head-model",
        type=float,
        default=0.1,
        help="Expand the head model by this amount (in mm) before generating the "
        "headcase. The default (0.1 mm) should work for most cases. If the resulting "
        "headcase is too tight, one can try increasing this value. If the resulting "
        "headcase is too loose, one can try passing a negative value to shrink the head"
        "model. It is not recommended to pass a value greater than 1 mm or less than "
        "-1 mm.",
    )
    args = parser.parse_args()
    infile = os.path.abspath(args.infile)
    outfile = os.path.abspath(args.outfile)
    casetype = args.headcoil
    nparts = args.nparts
    workdir = args.workdir
    customizations = args.customizations_file
    generate_headcase_only = args.generate_headcase_only
    expand_head_model = args.expand_head_model

    if generate_headcase_only:
        print("Making head case")
        gen_case(
            infile,
            outfile,
            casetype=casetype,
            nparts=nparts,
            workdir=workdir,
            customizations=customizations,
            expand_head_model=expand_head_model,
        )
    else:
        pipeline(
            infile,
            outfile,
            casetype=casetype,
            nparts=nparts,
            workdir=workdir,
            customizations=customizations,
            expand_head_model=expand_head_model,
        )
