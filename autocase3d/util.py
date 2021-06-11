import numpy as np
import cortex
import plyfile

def load_ply(ply_file):
    plydata = plyfile.PlyData.read(ply_file)
    vertex = plydata.elements[0]
    pts = np.vstack([vertex['x'], vertex['y'], vertex['z']]).T

    face = plydata.elements[1]
    polys = np.vstack(face.data['vertex_indices'])
    
    return pts, polys

def get_features(pts, polys, smooths=[5, 20, 200]):
    surf = cortex.polyutils.Surface(pts, polys)
    curv = np.nan_to_num(surf.mean_curvature())
    sm_curvs = np.vstack([surf.smooth(curv, factor=sm, iterations=3) 
                         for sm in smooths])
    
    return np.hstack([pts, sm_curvs.T]), polys

def get_ply_features(ply_file, smooths=[5, 20, 200]):
    pts, polys = load_ply(ply_file)
    return get_features(pts, polys, smooths)

def get_stl_features(stl_file, smooths=[5, 20, 200]):
    pts, polys = cortex.formats.read_stl(stl_file)
    return get_features(pts, polys, smooths)

def save_stl_features(stl_file, feature_file, smooths=[5, 20, 200]):
    feats, polys = get_stl_features(stl_file, smooths)
    np.savez(feature_file, features=feats)