blender_carve_model_template = """import sys
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


def intersect_cube(name, loc, radius):
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.mesh.primitive_cube_add(radius=radius, location=loc)
    bpy.data.objects['Cube'].name = name
    bpy.context.scene.objects.active = bpy.data.objects[name]
    bpy.ops.object.modifier_add(type='BOOLEAN')
    bpy.data.objects[name].modifiers['Boolean'].name = 'case'
    bpy.data.objects[name].modifiers['case'].operation = 'INTERSECT'
    bpy.data.objects[name].modifiers['case'].object = bpy.data.objects['preview']
    bpy.ops.object.modifier_apply(apply_as='DATA', modifier='case')
    
    
nparts = {nparts}
radius = 99.9 if nparts == 4 else 199.9

if nparts == 4:
    intersect_cube('front_bottom', (0, -20, 100), radius)
    bpy.ops.transform.rotate(value=3.14159265/2, axis=(-1, 0, 0))
    bpy.ops.export_mesh.stl(filepath='{tempdir}/front_bottom.stl', use_selection=True)
    
    intersect_cube('back_bottom', (0, -20, -100), radius)
    bpy.ops.transform.rotate(value=3.14159265/2, axis=(-1, 0, 0))
    bpy.ops.transform.translate(value=(0, 0, 200))
    bpy.ops.export_mesh.stl(filepath='{tempdir}/back_bottom.stl', use_selection=True)
    
    intersect_cube('front_top', (0, 180, 100), radius)
    bpy.ops.export_mesh.stl(filepath='{tempdir}/front_top.stl', use_selection=True)
    
    intersect_cube('back_top', (0, 180, -100), radius)
    bpy.ops.transform.rotate(value=3.14159265, axis=(-1, 0, 0))
    bpy.ops.export_mesh.stl(filepath='{tempdir}/back_top.stl', use_selection=True)
else:
    intersect_cube('front', (0, 0, 200), radius)
    bpy.ops.transform.rotate(value=3.14159265/2, axis=(-1, 0, 0))
    bpy.ops.export_mesh.stl(filepath='{tempdir}/front.stl', use_selection=True)
    
    intersect_cube('back', (0, 0, -200), radius)
    bpy.ops.transform.rotate(value=3.14159265/2, axis=(-1, 0, 0))
    bpy.ops.export_mesh.stl(filepath='{tempdir}/back.stl', use_selection=True)
"""