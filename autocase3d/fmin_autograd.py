import autograd.numpy as np
from autograd import grad, elementwise_grad
from autograd.numpy import sin, cos
import scipy.optimize

from .util import get_ply_features
from . import squash_features, unsquash_xyz

def rot3(ph, th, ps):
    return np.array([[cos(th)*cos(ps), -cos(ph)*sin(ps) + sin(ph)*sin(th)*cos(ps), sin(ph)*sin(ps) + cos(ph)*sin(th)*cos(ps)],
                     [cos(th)*sin(ps), cos(ph)*cos(ps) + sin(ph)*sin(th)*sin(ps), -sin(ph)*cos(ps) + cos(ph)*sin(th)*sin(ps)],
                     [-sin(th), sin(ph)*cos(th), cos(ph)*cos(th)]])

def rot_trans(xyz, rots, trans):
    rmat = rot3(rots[0], rots[1], rots[2])
    return np.dot(xyz, rmat) + trans

def prob(params, new_feats, the_gmm):
    rots = params[:3]
    trans = params[3:]

    rmat = rot3(rots[0], rots[1], rots[2])
    
    i63 = np.eye(6)[:3]
    d6 = np.diag([0,0,0,1,1,1])
    
    big_rmat = np.dot(i63.T, np.dot(rmat, i63)) + d6
    big_trans = np.dot(i63.T, trans)
    xfm_feats = np.dot(new_feats, big_rmat) + big_trans
    
    return -np.log(np.dot(np.exp(np.array(_estimate_log_gaussian_prob(xfm_feats, the_gmm.means_, the_gmm.precisions_cholesky_, "full"))).T, the_gmm.weights_)).mean()

prob_grad = elementwise_grad(prob)

def _estimate_log_gaussian_prob(X, means, precisions_chol, covariance_type):
    """Estimate the log Gaussian probability.
    Parameters
    ----------
    X : array-like, shape (n_samples, n_features)
    means : array-like, shape (n_components, n_features)
    precisions_chol : array-like
        Cholesky decompositions of the precision matrices.
        'full' : shape of (n_components, n_features, n_features)
        'tied' : shape of (n_features, n_features)
        'diag' : shape of (n_components, n_features)
        'spherical' : shape of (n_components,)
    covariance_type : {'full', 'tied', 'diag', 'spherical'}
    Returns
    -------
    log_prob : array, shape (n_samples, n_components)
    """
    n_samples, n_features = X.shape
    n_components, _ = means.shape
    # det(precision_chol) is half of det(precision)
    log_det = _compute_log_det_cholesky(
        precisions_chol, covariance_type, n_features)

    if covariance_type == 'full':
        #log_prob = np.empty((n_samples, n_components))
        log_prob = []
        for k, (mu, prec_chol) in enumerate(zip(means, precisions_chol)):
            y = np.dot(X, prec_chol) - np.dot(mu, prec_chol)
            log_prob.append(-.5 * (n_features * np.log(2 * np.pi) + np.sum(np.square(y), axis=1)) + log_det[k])
            
    #return -.5 * (n_features * np.log(2 * np.pi) + log_prob) + log_det
    return log_prob

def _compute_log_det_cholesky(matrix_chol, covariance_type, n_features):
    """Compute the log-det of the cholesky decomposition of matrices.
    Parameters
    ----------
    matrix_chol : array-like
        Cholesky decompositions of the matrices.
        'full' : shape of (n_components, n_features, n_features)
        'tied' : shape of (n_features, n_features)
        'diag' : shape of (n_components, n_features)
        'spherical' : shape of (n_components,)
    covariance_type : {'full', 'tied', 'diag', 'spherical'}
    n_features : int
        Number of features.
    Returns
    -------
    log_det_precision_chol : array-like, shape (n_components,)
        The determinant of the precision matrix for each component.
    """
    if covariance_type == 'full':
        n_components, _, _ = matrix_chol.shape
        log_det_chol = (np.sum(np.log(
            matrix_chol.reshape(
                n_components, -1)[:, ::n_features + 1]), 1))

    elif covariance_type == 'tied':
        log_det_chol = (np.sum(np.log(np.diag(matrix_chol))))

    elif covariance_type == 'diag':
        log_det_chol = (np.sum(np.log(matrix_chol), axis=1))

    else:
        log_det_chol = n_features * (np.log(matrix_chol))

    return log_det_chol



def fit_xfm_autograd(infile, modelfile, **fmin_kwargs):
    new_features, new_polys = get_ply_features(infile)
    gmm, means, stds = np.load(modelfile, encoding="bytes")

    sq_new_features = squash_features(new_features, means, stds)


    init_score = -gmm.score(sq_new_features)
    print("Init score:", init_score)
    if init_score > 6.0: # ~?
        print("This looks wildly mis-aligned. Check results.")

    opt_params = scipy.optimize.fmin_bfgs(prob, np.zeros(6), prob_grad,
                                          args=(sq_new_features, gmm), 
                                          **fmin_kwargs)

    new_xyz = rot_trans(sq_new_features[:,:3], opt_params[:3], opt_params[3:])
    final_score = -gmm.score(np.hstack([new_xyz, sq_new_features[:,3:]]))
    print("Final score:", final_score)

    unsq_new_xyz = unsquash_xyz(new_xyz, means, stds)

    return unsq_new_xyz, new_polys, opt_params
