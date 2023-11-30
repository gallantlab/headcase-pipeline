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
    ms = pymeshlab.MeshSet()
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
    from cortex import formats

    from autocase3d.fmin_autograd import fit_xfm_autograd

    new_pts, new_polys, opt_params = fit_xfm_autograd(infile)
    print("Final params: ", opt_params)
    formats.write_stl(outfile, new_pts, new_polys)


def gen_case(scanfile, outfile, casetype="s32", nparts=4):
    cwd, _ = os.path.split(__file__)
    customizations = os.path.join(cwd, "stls", "default_customizations.stl")
    casefile = dict(
        s32="s32.stl", s64="s64.stl", n32="n32.stl", meg_ctf275="meg_ctf275.stl"
    )
    casefile = os.path.join(cwd, "stls", casefile[casetype])

    tempdir = mkdtemp()
    _call_blender(
        blender_carve_model_template.format(
            preview=casefile,
            scan=scanfile,
            customizations=customizations,
            tempdir=tempdir,
            nparts=nparts,
        )
    )

    pieces = {
        2: ["back.stl", "front.stl"],
        4: ["back_bottom.stl", "back_top.stl", "front_bottom.stl", "front_top.stl"],
    }
    with zipfile.ZipFile(outfile, mode="w") as pkg:
        for fn in pieces[nparts]:
            pkg.write(os.path.join(tempdir, fn), fn)

    shutil.rmtree(tempdir)


def pymeshlab_version():
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


def pipeline(infile, outfile, casetype="s32", nparts=4, workdir=None):
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
    gen_case(aligned, outfile, casetype=casetype, nparts=nparts)

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
        "--generate-headcase-only",
        action="store_true",
        help="Only generate the headcase given the input stl file. This assumes that "
        "the input stl contains a head model that is already cleaned and aligned.",
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
    args = parser.parse_args()
    infile = os.path.abspath(args.infile)
    outfile = os.path.abspath(args.outfile)
    casetype = args.headcoil
    nparts = args.nparts
    workdir = args.workdir
    generate_headcase_only = args.generate_headcase_only

    if generate_headcase_only:
        print("Making head case")
        gen_case(infile, outfile, casetype=casetype, nparts=nparts)
    else:
        pipeline(infile, outfile, casetype=casetype, nparts=nparts, workdir=workdir)
