This directory needs to contain (at least links to) directories called `oriented/`, and `features/` (this should be empty to start).

First, generate features for each image by running `python gen_features.py`. This creates `.npz` files in `features/` with curvature info about each head.

Second, train the GMM by running `python create_model.py`, this creates the model file `gmm_model_1.npy`.

Now to align a new head, run `python align_head.py gmm_model_1.npy [cleaned_head].ply [aligned_head].stl`