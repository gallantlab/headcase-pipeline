#!/bin/bash 
# Use neurodocker to generate a dockerfile
docker run --rm repronim/neurodocker:latest generate docker \
	--pkg-manager apt \
	--base-image ubuntu:bionic \
	--run "chmod 777 /tmp" \
	--install libopengl0 build-essential meshlab blender=2.79.b+dfsg0-1ubuntu1.18.04.1 \
	--env SKLEARN_NO_OPENMP=1 \
	--copy . "/headcase-pipeline" \
	--miniconda \
	version=latest \
	conda_install="python=3.9 numpy scipy cython<3.0" \
	pip_install="-r /headcase-pipeline/requirements.txt" \
	--run "useradd -m -s /bin/bash -G users headcase" \
	--env HOME=/home/headcase \
	--run "mkdir /home/headcase/.config" \
	--run "python -c 'import cortex'" \
	--workdir "/headcase-pipeline" \
	--entrypoint "python /headcase-pipeline/make_headcase.py" \
	> Dockerfile
