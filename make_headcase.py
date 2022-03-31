"""Generate an MRI-compatible headcase from a 3D head model acquired with a Structure Sensor."""
from tempfile import NamedTemporaryFile as Temp
from tempfile import mkdtemp
import zipfile
import os
import shlex
import shutil
import subprocess as sp
import pymeshlab
import argparse

from blender_code import blender_carve_model_template


def _call_blender(code):
    """Call blender, while running the given code. If the filename doesn't exist, save a new file in that location.
    New files will be initially cleared by deleting all objects.
    """
    with Temp(mode="w") as tf:
        cmd = "blender -b -P {script}".format(script=tf.name)

        tf.write(code)
        tf.flush()
        sp.call(shlex.split(cmd))


def meshlab_filter(ms, pmlab_version):
    # "Transform: Move, Translate, Center"
    if pmlab_version >= 2022.2:
        ms.apply_filter(filter_name="compute_matrix_from_translation")
    else:
        ms.apply_filter(filter_name="transform_translate_center_set_origin")
    # "Transform: Rotate"
    if pmlab_version >= 2022.2:
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
    else:
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
    if pmlab_version >= 2022.2:
        ms.apply_filter(filter_name="meshing_merge_close_vertices", threshold=pymeshlab.Percentage(0.5))
    else:
        ms.apply_filter(filter_name="merge_close_vertices", threshold=0.5)
    # "Remove Isolated pieces (wrt Diameter)"
    if pmlab_version >= 2022.2:
        ms.apply_filter(
            filter_name="meshing_remove_connected_component_by_diameter",
            mincomponentdiag=pymeshlab.AbsoluteValue(150),
            removeunref=True,
        )
    else:
        ms.apply_filter(
            filter_name="remove_isolated_pieces_wrt_diameter",
            mincomponentdiag=150,
            removeunref=True,
        )
    # "Remove Faces from Non Manifold Edges"
    if pmlab_version >= 2022.2:
        ms.apply_filter(
            filter_name="meshing_repair_non_manifold_edges",
            method="Remove Faces"
        )
    else:
        ms.apply_filter(
            filter_name="repair_non_manifold_edges_by_removing_faces",
            method="Remove Faces"
        )
    # "Close Holes"
    if pmlab_version >= 2022.2:
        ms.apply_filter(
            filter_name="meshing_close_holes", maxholesize=100, newfaceselected=False,
        )
    else:
        ms.apply_filter(
            filter_name="close_holes", maxholesize=100, newfaceselected=False,
        )
    # "Surface Reconstruction: Poisson"
    if pmlab_version >= 2022.2:
        ms.apply_filter(
            filter_name="generate_surface_reconstruction_screened_poisson",
            depth=11,
            fulldepth=2,
            samplespernode=1,
            # pointweight=0,
            preclean=True,
        )
    else:
        ms.apply_filter(
            filter_name="surface_reconstruction_screened_poisson",
            depth=11,
            fulldepth=2,
            samplespernode=1,
            # pointweight=0,
            preclean=True,
        )
    # "Vertex Attribute Transfer"
    if pmlab_version >= 2022.2:
        ms.apply_filter(
            filter_name="transfer_attributes_per_vertex",
            sourcemesh=1,
            targetmesh=0,
            geomtransfer=True,
            colortransfer=False,
            upperbound=pymeshlab.Percentage(8.631),
        )
    else:
        ms.apply_filter(
            filter_name="vertex_attribute_transfer",
            sourcemesh=1,
            targetmesh=0,
            geomtransfer=True,
            colortransfer=False,
            upperbound=8.631,
        )
    return ms


def model_clean(infile, outfile, pmlab_version):
    path = mkdtemp()
    pkg = zipfile.ZipFile(infile)
    pkg.extractall(path)
    pkg.close()

    infile = os.path.join(path, "Model.obj")
    ms = pymeshlab.MeshSet()
    ms.load_new_mesh(infile)
    ms = meshlab_filter(ms, pmlab_version)
    ms.save_current_mesh(outfile)

    shutil.rmtree(path)


def align_scan(infile, outfile):
    from autocase3d.fmin_autograd import fit_xfm_autograd
    from cortex import formats

    cwd, _ = os.path.split(__file__)
    modelfile = os.path.join(cwd, "autocase3d", "gmm_model_3.npy")
    print(modelfile)
    new_pts, new_polys, opt_params = fit_xfm_autograd(infile, modelfile)
    print("Final params: ", opt_params)
    formats.write_stl(outfile, new_pts, new_polys)


def gen_case(scanfile, outfile, casetype="s32", nparts=4):
    cwd, _ = os.path.split(__file__)
    customizations = os.path.join(cwd, "stls", "default_customizations.stl")
    casefile = dict(s32="s32.stl", s64="s64.stl", n32="n32.stl")
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


def pipeline(infile, outfile, pmlab_version, **kwargs):
    with Temp(suffix=".ply") as cleaned, Temp(suffix=".stl") as aligned:
        model_clean(infile, cleaned.name, pmlab_version)
        align_scan(cleaned.name, aligned.name)
        # if not os.path.isdir('temp/'):
        # 	os.mkdir('temp')
        # shutil.copyfile(cleaned.name, 'temp/cleaned.ply')
        # shutil.copyfile(aligned.name, 'temp/aligned.stl')
        gen_case(aligned.name, outfile, **kwargs)
        # gen_case('temp/aligned.stl', outfile, **kwargs)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__
    )
    parser.add_argument(
        "infile", type=str, help="input head model generated by the Structure Sensor (*.zip)",
    )
    parser.add_argument(
        "outfile", type=str, help="output headcase model (*.zip)",
    )
    parser.add_argument(
        "--headcoil",
        "-c",
        type=str,
        default="s32",
        help="Type of headcoil: s32 (siemens 32ch), s64 (siemens 64ch), or "
        "n32 (nova 32ch). Default: s32",
        choices=["s32", "s64", "n32"],
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
    args = parser.parse_args()
    infile = args.infile
    outfile = args.outfile
    casetype = args.headcoil
    nparts = args.nparts
    # Check pymeshlab version to use corresponding filter names
    proc = sp.check_output(["python", "-c", "import pymeshlab ; pymeshlab.pmeshlab.print_pymeshlab_version()"])
    pmlab_version = float(str(proc).split()[1])
    pipeline(infile, outfile, pmlab_version, casetype=casetype, nparts=nparts)
