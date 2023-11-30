#!/bin/bash 
# Use neurodocker to generate a dockerfile
docker run --rm repronim/neurodocker:latest generate docker \
	--pkg-manager apt \
	--base-image ubuntu:20.04 \
	--env "DEBIAN_FRONTEND=noninteractive" \
	--run "chmod 777 /tmp" \
	--install libopengl0 build-essential meshlab curl ca-certificates libxi6 \
	--run "mkdir -p /opt/blender
	curl -fL https://download.blender.org/release/Blender2.79/blender-2.79b-linux-glibc219-x86_64.tar.bz2 | tar -xj -C /opt/blender --strip-components 1" \
	--env "PATH=/opt/blender:\$PATH" \
	--run "blender --version" \
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
