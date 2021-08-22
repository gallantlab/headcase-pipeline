# Use neurodocker to generate a dockerfile
docker run --rm repronim/neurodocker:latest generate docker \
	--pkg-manager apt \
	--base ubuntu:bionic \
	--install libopengl0 build-essential meshlab blender=2.79.b+dfsg0-1ubuntu1.18.04.1 \
	--env SKLEARN_NO_OPENMP=1 \
	--copy . "/headcase-pipeline" \
	--miniconda \
	use_env=base \
	activate=True \
	conda_install="python=3 numpy scipy cython" \
	pip_install="-r /headcase-pipeline/requirements.txt" \
	--run "useradd -m -s /bin/bash -G users headcase" \
	--env HOME=/home/headcase \
	--run "mkdir /home/headcase/.config" \
	--run "python -c 'import cortex'" \
	--workdir "/headcase-pipeline" \
	--entrypoint "python /headcase-pipeline/make_headcase.py" \
	> Dockerfile
