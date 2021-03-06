## Stepwise model clean implemented in meshlab

1. [Transform: Move, Translate, and center](https://github.com/gallantlab/caseforge-pipeline/blob/master/simple_serve.py#L3)

	![step1](./explanatory_ims/step1_moveTranslateCenter.png)

* Major observable shift

	![step1_res](./explanatory_ims/step1_res.png)

* [meshlab function translate2](https://github.com/3DLIRIOUS/MeshLabXML/blob/ba2c13ba7cd785b94add9b95bf33414c7099be70/meshlabxml/transform.py#L11)

2. [Transform: Rotate](https://github.com/gallantlab/caseforge-pipeline/blob/master/simple_serve.py#L11)

	![step2](./explanatory_ims/step2_rotate.png)

* (LG think no rotated was implemented, as angle of rotation is set to 0)

* [meshlab function rotate2](https://github.com/3DLIRIOUS/MeshLabXML/blob/ba2c13ba7cd785b94add9b95bf33414c7099be70/meshlabxml/transform.py#L85)

3. [Transform: Scale](https://github.com/gallantlab/caseforge-pipeline/blob/master/simple_serve.py#L22)

	![step3](./explanatory_ims/step3_scale.png)

* (LG tested 1000 should be the same as 1: meaning no scaling was implemented)

* [meshlab function scale2](https://github.com/3DLIRIOUS/MeshLabXML/blob/ba2c13ba7cd785b94add9b95bf33414c7099be70/meshlabxml/transform.py#L223)

4. [Merge Close Vertex](https://github.com/gallantlab/caseforge-pipeline/blob/master/simple_serve.py#L33)

	![step4](./explanatory_ims/step4_mergeVertex.png)

* Not much observable changes

* [meshlab function merge_vert](https://github.com/3DLIRIOUS/MeshLabXML/blob/ba2c13ba7cd785b94add9b95bf33414c7099be70/meshlabxml/clean.py#L8)

5. [Remove Isolated Pieces](https://github.com/gallantlab/caseforge-pipeline/blob/master/simple_serve.py#L36)

	![step5](./explanatory_ims/step5_removeIsolatePieces.png)

* observable changes: isolated pieces are removed

	![step5_before](./explanatory_ims/step5_before.png)  ![step5_after](./explanatory_ims/step5_after.png)

6. [Close holes: (aka. Remove Faces from Non Manifold Edges)](https://github.com/gallantlab/caseforge-pipeline/blob/master/simple_serve.py#L39)

	![step6](./explanatory_ims/step6_closeHoles.png)

* Observable changes: holes are filled
	
	![step6_before](./explanatory_ims/step6_before.png)  ![step6_after](./explanatory_ims/step6_after.png)

* [meshlab function close_holes](https://github.com/3DLIRIOUS/MeshLabXML/blob/ba2c13ba7cd785b94add9b95bf33414c7099be70/meshlabxml/clean.py#L40)

7. [Surface Reconstruction using Poisson](https://github.com/gallantlab/caseforge-pipeline/blob/master/simple_serve.py#L46)

	![step7](./explanatory_ims/step7_surfaceReconstructionPoisson.png)

* Observable changes: smoother surface (but not sure why some isolated pieces come back?)

	![step7_res](./explanatory_ims/step7_res.png)

* [meshlab function surface_poisson](https://github.com/3DLIRIOUS/MeshLabXML/blob/ba2c13ba7cd785b94add9b95bf33414c7099be70/meshlabxml/remesh.py#L294)

8. [Vertex Attribute Transfer](https://github.com/gallantlab/caseforge-pipeline/blob/master/simple_serve.py#L52) 

	![step8](./explanatory_ims/step8_vertexAttributeTransfer.png)

* [meshlab function vert_attr_2_meshes](https://github.com/3DLIRIOUS/MeshLabXML/blob/ba2c13ba7cd785b94add9b95bf33414c7099be70/meshlabxml/transfer.py#L120)
