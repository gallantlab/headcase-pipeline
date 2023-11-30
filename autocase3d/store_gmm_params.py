"""Script to store the GMM parameters in a format that can be loaded with numpy. 
Hopefully this provides a more future-proof way of storing the GMM parameters."""
import numpy as np

# Load the GMM model
gmm_model = "gmm_model_3.npy"
gmm, means, stds = np.load(gmm_model, encoding="bytes", allow_pickle=True)

to_save = {"means": means, "stds": stds}

# now loop through the gmm components and save everything
params_to_save = [
    "weights_",
    "means_",
    "covariances_",
    "precisions_",
    "precisions_cholesky_",
    "converged_",
    "n_iter_",
    "lower_bound_",
]

# to_save["gmm_params"] = gmm.get_params()
for param in params_to_save:
    to_save["gmm_" + param] = getattr(gmm, param)
print(to_save)

np.savez("gmm_params.npz", **to_save)