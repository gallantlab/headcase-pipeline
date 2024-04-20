#!/bin/bash 
# Use neurodocker to generate a dockerfile
docker run --rm repronim/neurodocker:latest generate docker \
	--pkg-manager apt \
	--base-image ubuntu:20.04 \
	--env "DEBIAN_FRONTEND=noninteractive" \
	--run "chmod 777 /tmp" \
	--install git libopengl0 build-essential curl ca-certificates libxi6 libglu1-mesa libglib2.0-0 libxrender1 \
	--run "mkdir -p /opt/blender
	curl -fL https://download.blender.org/release/Blender2.79/blender-2.79b-linux-glibc219-x86_64.tar.bz2 | tar -xj -C /opt/blender --strip-components 1" \
	--env "PATH=/opt/blender:\$PATH" \
	--run "blender --version" \
	--run "mkdir -p /opt/meshlab
	curl -fL https://github.com/cnr-isti-vclab/meshlab/releases/download/MeshLab-2022.02/MeshLab2022.02d-linux.tar.gz | tar -xz -C /opt/meshlab" \
	--env "PATH=/opt/meshlab/usr/bin:\$PATH" \
	--run "meshlab --version" \
	--env SKLEARN_NO_OPENMP=1 \
	--copy . "/headcase-pipeline" \
	--miniconda \
	version="py39_24.1.2-0" \
	conda_install="python=3.9 gxx_linux-64" \
	pip_install="-r /headcase-pipeline/requirements.txt" \
	--run "useradd -m -s /bin/bash -G users headcase" \
	--env HOME=/home/headcase \
	--run "mkdir /home/headcase/.config" \
	--run "python -c 'import cortex; print(cortex.__version__)'" \
	--run "python -c 'import pymeshlab'" \
	--workdir "/headcase-pipeline" \
	--entrypoint "python /headcase-pipeline/make_headcase.py" \
	> Dockerfile
