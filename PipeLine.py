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

def _call_blender(code):
		"""Call blender, while running the given code. If the filename doesn't exist, save a new file in that location.
		New files will be initially cleared by deleting all objects.
		"""
		with Temp(mode="w") as tf:
				cmd = "blender -b -P {script}".format(script=tf.name)

				tf.write(code)
				tf.flush()
				sp.call(shlex.split(cmd))


# def model_clean(infile, outfile):
# 		with Temp(mode='w') as script:
# 				path = mkdtemp()
# 				pkg = zipfile.ZipFile(infile)
# 				pkg.extractall(path)
# 				pkg.close()
# 				print(path)

# 				# script.write(meshlab_script)
# 				# script.flush()
				
# 				# cmd = "meshlabserver -i {infile} -o {temp} -s {ms} -om vc"
# 				# infile = os.path.join(path, "Model.obj")
# 				# call = shlex.split(cmd.format(infile=infile, temp=outfile, ms=script.name))
# 				# sp.call(call, cwd=path)

# 				# infile = "Model.obj"
# 				# ms = pymeshlab.MeshSet()
# 				# ms.load_new_mesh(infile)
# 				# ms.load_filter_script("meshlab_script.mlx")
# 				# ms.apply_filter_script()
# 				# ms.save_current_mesh(outfile)
				
# 				shutil.rmtree(path)

def model_clean(infile, outfile):
    with Temp(suffix='.mlx', mode='w') as script:
        path = mkdtemp()
        pkg = zipfile.ZipFile(infile)
        pkg.extractall(path)
        pkg.close()

        # script.write(meshlab_script)
        # script.flush()
        
        cmd = "meshlabserver -i {infile} -o {temp} -s {ms} -om vc"
        infile = os.path.join(path, "Model.obj")
        call = shlex.split(cmd.format(infile=infile, temp=outfile, ms="new_meshlab_script.mlx"))
        sp.call(call)
        
        shutil.rmtree(path)
        print("clean done!")


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
		_call_blender(blender_gen_output.format(
				preview=casefile,
				scan=scanfile, 
				customizations=customizations, 
				tempdir=tempdir))
		
		with zipfile.ZipFile(outfile, mode='w') as pkg:
				pkg.write(os.path.join(tempdir, "back_bottom.stl"), "back_bottom.stl")
				pkg.write(os.path.join(tempdir, "back_top.stl"), "back_top.stl")
				pkg.write(os.path.join(tempdir, "front_bottom.stl"), "front_bottom.stl")
				pkg.write(os.path.join(tempdir, "front_top.stl"), "front_top.stl")

		shutil.rmtree(tempdir)

def pipeline(infile, outfile, **kwargs):
		with Temp(suffix='.ply') as cleaned, Temp(suffix='.stl') as aligned:
			ff = "clean.ply"
			with open(ff, 'wb') as f:
				pass
			model_clean(infile, ff)
			# align_scan(ff, aligned.name)
			# gen_case(aligned.name, outfile, **kwargs)



if __name__ == "__main__":
	infile = input("Scan: ")
	outfile = input("Save: ")
	casetype_idx = input("Casetype: (1)s32, (2)s64, (3)n32")
	if casetype_idx == "1":
		casetype = 's32'
	elif casetype_idx == "2":
		casetype = 's64'
	elif casetype_idx == "3":
		casetype = 'n32'
	else:
		print("Invalid casetype")
		raise
	pipeline(infile, outfile, casetype=casetype)
	


# from flask import Flask
# from flask import request, make_response
# app = Flask(__name__)

# @app.route('/')
# def main():
#     return """<!doctype html>
# <title>Headcase generator</title>
# <form action="/upload" method="post" enctype="multipart/form-data">
#     <label for="casetype">Headcoil:</label>
#     <select id="casetype" name="casetype">
#         <option value="s32">Siemens 32ch</option>
#         <option value="s64">Siemens 64ch</option>
#         <option value="n32">Nova 32ch</option>
#     </select>
#     <br/>
#     <label for="scanfile">Scan:</label>
#     <input id="scanfile" type="file" name="scanfile">
#     <br/>
#     <input type="submit">
# </form>"""

# @app.route('/upload', methods=['POST'])
# def upload():
#     with Temp(suffix='.zip') as outfile:
#         pipeline(request.files['scanfile'], outfile.name, casetype=request.form['casetype'])
#         resp = make_response(outfile.read())
#         resp.headers['Content-Disposition'] = "attachment; filename=case.zip"
#         resp.headers['Content-Type'] = 'application/zip'
#         return resp


# if __name__ == '__main__':
#    app.run(debug = True, host='0.0.0.0')
