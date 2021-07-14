import pymeshlab
ms = pymeshlab.MeshSet()

ms.load_new_mesh("Model.obj")

# "Transform: Move, Translate, Center"
# ms.apply_filter(filter_name="transform_translate_camera_or_set_of_cameras",
# 	camera="Mesh Camera",
# 	# axisX=0,
# 	# axisY=0,
# 	# axisZ=0,
# 	centerflag=True,
# 	# toall=False,
# 	)
ms.apply_filter(filter_name="transform_translate_center_set_origin",
	# axisx=0,
	# axisy=0,
	# axisz=0,
	# freeze=True,
	# alllayers=False,
	)

# "Transform: Rotate"
ms.apply_filter(filter_name="transform_rotate",
	rotaxis="X axis",
	rotcenter="barycenter",
	# angle=0,
	# snapflag=False,
	# customAxis=[0, 0, 0],
	# customcenter=[0, 0, 0],
	# snapangle=30,
	# freeze=True,
	# alllayers=False,
	)

# "Transform: Scale"
ms.apply_filter(filter_name="transform_scale_normalize",
	axisx=1000,
	# axisy=1,
	# axisz=1,
	# uniformflag=True,
	scalecenter="barycenter",
	# customCenter=[0, 0, 0],
	unitflag=False,
	# freeze=True,
	# alllayers=False
	)

# "Merge Close Vertices"
ms.apply_filter(filter_name="merge_close_vertices",
	threshold=0.5,
	)

# "Remove Isolated pieces (wrt Diameter)"
ms.apply_filter(filter_name="remove_isolated_pieces_wrt_diameter",
	mincomponentdiag=150,
	removeunref=False, 
	)

# "Remove Faces from Non Manifold Edges"
ms.apply_filter(filter_name="repair_non_manifold_edges_by_removing_faces")

# "Close Holes"
ms.apply_filter(filter_name="close_holes",
	maxholesize=100,
	# selected=False,
	newfaceselected=False,
	# selfintersection=True,
	)

# "Surface Reconstruction: Poisson"
ms.apply_filter(filter_name="surface_reconstruction_screened_poisson",
	# visiblelayer=False,
	depth=4,
	fulldepth=11, #Octree Depth
	# cgdepth=0,
	# scale=1.1,
	samplespernode=1,
	# pointweight=4,
	# iters=8,
	# confidence=False,
	preclean=True,
	)

# "Vertex Attribute Transfer"
ms.apply_filter(filter_name="vertex_attribute_transfer",
	sourcemesh=0,
	targetmesh=1,
	geomtransfer=True,
	# normaltransfer=False,
	colortransfer=False,
	# qualitytransfer=False,
	# selectiontransfer=False,
	# qualitydistance=False,
	upperbound=8.631,
	# onselected=False,
	)

ms.print_filter_script()
ms.save_filter_script("new_meshlab_script.mlx")