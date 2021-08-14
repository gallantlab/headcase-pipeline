blender_gen_output = """import sys
import bpy
import bpy.ops
from bpy import context as C
from bpy import data as D
import os.path

bpy.context.scene.objects.active = bpy.data.objects['Cube']
bpy.ops.object.delete()

def readstl(path, name):
    tempname = bpy.path.display_name(os.path.basename(path))
    bpy.ops.import_mesh.stl(filepath=path)
    bpy.data.objects[tempname].name = name

readstl('{preview}', 'preview')
readstl('{scan}', 'scan')


bpy.ops.object.select_all(action='DESELECT')
bpy.context.scene.objects.active = bpy.data.objects['scan']
bpy.ops.object.mode_set(mode = 'EDIT')
bpy.ops.mesh.select_all(action='SELECT')
for _ in range(3):
    bpy.ops.mesh.remove_doubles(threshold=0.75)
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_non_manifold()
    bpy.ops.mesh.edge_collapse()
    bpy.ops.mesh.select_non_manifold()
    bpy.ops.mesh.edge_collapse()
    bpy.ops.mesh.select_non_manifold()
    bpy.ops.mesh.edge_collapse()
bpy.ops.object.mode_set(mode = 'OBJECT')

# shrinking
bpy.ops.object.select_all(action='DESELECT')
bpy.context.scene.objects.active = bpy.data.objects['scan']
bpy.ops.object.mode_set(mode = 'OBJECT')
bpy.ops.object.modifier_add(type='DISPLACE')
bpy.data.objects['scan'].modifiers['Displace'].name = 'shrinking'
bpy.data.objects['scan'].modifiers['shrinking'].direction = 'NORMAL'
bpy.data.objects['scan'].modifiers['shrinking'].mid_level = 0
bpy.data.objects['scan'].modifiers['shrinking'].strength = 0.1

try:
    readstl('{customizations}', 'customizations')
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.scene.objects.active = bpy.data.objects['scan']
    bpy.ops.object.modifier_add(type='BOOLEAN')
    bpy.data.objects['scan'].modifiers['Boolean'].name = 'Customizations'
    bpy.data.objects['scan'].modifiers['Customizations'].operation = 'UNION'
    bpy.data.objects['scan'].modifiers['Customizations'].solver = 'CARVE'
    bpy.data.objects['scan'].modifiers['Customizations'].object = bpy.data.objects['customizations']
except:
    pass

bpy.ops.object.select_all(action='DESELECT')
bpy.context.scene.objects.active = bpy.data.objects['preview']
bpy.ops.object.modifier_add(type='BOOLEAN')
bpy.data.objects['preview'].modifiers['Boolean'].name = 'scan'
bpy.data.objects['preview'].modifiers['scan'].operation = 'DIFFERENCE'
bpy.data.objects['preview'].modifiers['scan'].solver = 'CARVE'
bpy.data.objects['preview'].modifiers['scan'].object = bpy.data.objects['scan']

def intersect_cube(name, loc):
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.mesh.primitive_cube_add(radius=99.9, location=loc)
    bpy.data.objects['Cube'].name = name
    bpy.context.scene.objects.active = bpy.data.objects[name]
    bpy.ops.object.modifier_add(type='BOOLEAN')
    bpy.data.objects[name].modifiers['Boolean'].name = 'case'
    bpy.data.objects[name].modifiers['case'].operation = 'INTERSECT'
    bpy.data.objects[name].modifiers['case'].object = bpy.data.objects['preview']
    bpy.ops.object.modifier_apply(apply_as='DATA', modifier='case')

intersect_cube('front_bottom', (0, -20, 100))
bpy.ops.transform.rotate(value=3.14159265/2, axis=(-1, 0, 0))
bpy.ops.export_mesh.stl(filepath='{tempdir}/front_bottom.stl', use_selection=True)

intersect_cube('back_bottom', (0, -20, -100))
bpy.ops.transform.rotate(value=3.14159265/2, axis=(-1, 0, 0))
bpy.ops.transform.translate(value=(0, 0, 200))
bpy.ops.export_mesh.stl(filepath='{tempdir}/back_bottom.stl', use_selection=True)

intersect_cube('front_top', (0, 180, 100))
bpy.ops.export_mesh.stl(filepath='{tempdir}/front_top.stl', use_selection=True)

intersect_cube('back_top', (0, 180, -100))
bpy.ops.transform.rotate(value=3.14159265, axis=(-1, 0, 0))
bpy.ops.export_mesh.stl(filepath='{tempdir}/back_top.stl', use_selection=True)

"""

from tempfile import NamedTemporaryFile as Temp
from tempfile import mkdtemp
import zipfile
import os
import shlex
import shutil
import subprocess as sp
import pymeshlab
import argparse


def _call_blender(code):
    """Call blender, while running the given code. If the filename doesn't exist, save a new file in that location.
    New files will be initially cleared by deleting all objects.
    """
    with Temp(mode="w") as tf:
        cmd = "blender -b -P {script}".format(script=tf.name)

        tf.write(code)
        tf.flush()
        sp.call(shlex.split(cmd))


def meshlab_filter(ms):
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
    path = mkdtemp()
    pkg = zipfile.ZipFile(infile)
    pkg.extractall(path)
    pkg.close()

    infile = os.path.join(path, "Model.obj")
    ms = pymeshlab.MeshSet()
    ms.load_new_mesh(infile)
    ms = meshlab_filter(ms)
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


def gen_case(scanfile, outfile, casetype="s32"):
    cwd, _ = os.path.split(__file__)
    customizations = os.path.join(cwd, "stls", "default_customizations.stl")
    casefile = dict(s32="s32.stl", s64="s64.stl", n32="n32.stl")
    casefile = os.path.join(cwd, "stls", casefile[casetype])

    tempdir = mkdtemp()
    _call_blender(
        blender_gen_output.format(
            preview=casefile,
            scan=scanfile,
            customizations=customizations,
            tempdir=tempdir,
        )
    )

    with zipfile.ZipFile(outfile, mode="w") as pkg:
        pkg.write(os.path.join(tempdir, "back_bottom.stl"), "back_bottom.stl")
        pkg.write(os.path.join(tempdir, "back_top.stl"), "back_top.stl")
        pkg.write(os.path.join(tempdir, "front_bottom.stl"), "front_bottom.stl")
        pkg.write(os.path.join(tempdir, "front_top.stl"), "front_top.stl")

    shutil.rmtree(tempdir)


def pipeline(infile, outfile, **kwargs):
    with Temp(suffix=".ply") as cleaned, Temp(suffix=".stl") as aligned:
        model_clean(infile, cleaned.name)
        align_scan(cleaned.name, aligned.name)
        # if not os.path.isdir('temp/'):
        # 	os.mkdir('temp')
        # shutil.copyfile(cleaned.name, 'temp/cleaned.ply')
        # shutil.copyfile(aligned.name, 'temp/aligned.stl')
        gen_case(aligned.name, outfile, **kwargs)
        # gen_case('temp/aligned.stl', outfile, **kwargs)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="load zip object and output zip object"
    )
    parser.add_argument(
        "infile",
        type=str,
        help="input object filename (*.zip)",
    )
    parser.add_argument(
        "outfile",
        type=str,
        help="output object filename (*.zip)",
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
    args = parser.parse_args()
    infile = args.infile
    outfile = args.outfile
    casetype = args.casetype
    pipeline(infile, outfile, casetype=casetype)
