import numpy as np
import cortex
import plyfile
import os
import sklearn.mixture
import scipy.optimize
from numpy import sin, cos

from .util import get_ply_features

def fit_model(feature_dir="autocase/features", n_ppl=50, n_pts=1000, 
              n_components=100):
    """
    """
    # load all the feature files, one for each head
    features = [np.load(os.path.join(feature_dir, f), encoding='bytes')["features"] 
                for f in os.listdir(feature_dir)]

    # compute means & stds for z-scoring
    stds = np.vstack([f.std(0) for f in features])
    means = np.vstack([f.mean(0) for f in features])

    mean_stds = stds.mean(0)
    print(mean_stds)

    # but let's make sure we use the same scale for each spatial dim
    use_stds = np.hstack([[50, 50, 50], mean_stds[3:]])

    mean_means = means.mean(0)
    print(mean_means)

    sq_features = [squash_features(f, mean_means, use_stds) 
                   for f in features]

    # sample some people, sample some points
    sample_ppl = np.random.permutation(len(features))[:n_ppl]
    sample_inds = [np.random.permutation(len(features[ii]))[:n_pts] 
                   for ii in sample_ppl]

    sample_pts = np.vstack([sq_features[ii][pp] 
                            for ii,pp in zip(sample_ppl, sample_inds)])
    print(sample_pts.shape)

    print("Fitting GMM..")
    gmm = sklearn.mixture.GaussianMixture(n_components=n_components, verbose=1)
    gmm.fit(sample_pts)

    return gmm, mean_means, use_stds

def squash_features(f, means, stds, which_tanh=(3,4,5)):
    new_f = f.copy()
    for fi in range(f.shape[1]):
        new_f[:,fi] = (f[:,fi] - means[fi]) / stds[fi]
    
    for fi in which_tanh:
        #new_f[:,fi] = np.tanh((f[:,fi] - means[fi]) / stds[fi])
        new_f[:,fi] = np.tanh(new_f[:,fi])
    
    return new_f

def unsquash_xyz(f, means, stds):
    new_f = f.copy()
    for fi in range(3):
        new_f[:,fi] = f[:,fi] * stds[fi] + means[fi]
    
    return new_f

def rot3(ph, th, ps):
    return np.array([[cos(th)*cos(ps), -cos(ph)*sin(ps) + sin(ph)*sin(th)*cos(ps), sin(ph)*sin(ps) + cos(ph)*sin(th)*cos(ps)],
                     [cos(th)*sin(ps), cos(ph)*cos(ps) + sin(ph)*sin(th)*sin(ps), -sin(ph)*cos(ps) + cos(ph)*sin(th)*sin(ps)],
                     [-sin(th), sin(ph)*cos(th), cos(ph)*cos(th)]])

def rot_trans(xyz, rots, trans):
    """to points `xyz`, apply rotations `rots`, translations `trans`
    """
    rmat = rot3(*rots)
    return xyz.dot(rmat) + trans

def score(params, new_head, the_gmm):
    rots = params[:3]
    trans = params[3:]
    
    orig_xyz = new_head[:,:3]
    xfm_xyz = rot_trans(orig_xyz, rots, trans)
    xfm_feats = np.hstack([xfm_xyz, new_head[:,3:]])
    return -the_gmm.score(xfm_feats)

def fit_xfm_fmin(infile, modelfile, init=(0,0,0,0,0,0), **fmin_kwargs):
    new_features, new_polys = get_ply_features(infile)
    gmm, means, stds = np.load(modelfile, encoding="bytes")

    sq_new_features = squash_features(new_features, means, stds)

    init_score = -gmm.score(sq_new_features)
    print("Init score:", init_score)
    if init_score > 6.0: # ~?
        print("This looks wildly mis-aligned. Check results.")

    opt_params = scipy.optimize.fmin(score, init, 
                                     args=(sq_new_features, gmm), 
                                     **fmin_kwargs)

    new_xyz = rot_trans(sq_new_features[:,:3], opt_params[:3], opt_params[3:])
    final_score = -gmm.score(np.hstack([new_xyz, sq_new_features[:,3:]]))
    print("Final score:", final_score)

    unsq_new_xyz = unsquash_xyz(new_xyz, means, stds)

    return unsq_new_xyz, new_polys, opt_params
