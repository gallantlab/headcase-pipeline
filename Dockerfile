# Generated by Neurodocker and Reproenv.

FROM ubuntu:bionic
RUN chmod 777 /tmp
RUN apt-get update -qq \
           && apt-get install -y -q --no-install-recommends \
                  blender=2.79.b+dfsg0-1ubuntu1.18.04.1 \
                  build-essential \
                  libopengl0 \
                  meshlab \
           && rm -rf /var/lib/apt/lists/*
ENV SKLEARN_NO_OPENMP="1"
COPY [".", \
      "/headcase-pipeline"]
ENV CONDA_DIR="/opt/miniconda-latest" \
    PATH="/opt/miniconda-latest/bin:$PATH"
RUN apt-get update -qq \
    && apt-get install -y -q --no-install-recommends \
           bzip2 \
           ca-certificates \
           curl \
    && rm -rf /var/lib/apt/lists/* \
    # Install dependencies.
    && export PATH="/opt/miniconda-latest/bin:$PATH" \
    && echo "Downloading Miniconda installer ..." \
    && conda_installer="/tmp/miniconda.sh" \
    && curl -fsSL -o "$conda_installer" https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh \
    && bash "$conda_installer" -b -p /opt/miniconda-latest \
    && rm -f "$conda_installer" \
    && conda update -yq -nbase conda \
    # Prefer packages in conda-forge
    && conda config --system --prepend channels conda-forge \
    # Packages in lower-priority channels not considered if a package with the same
    # name exists in a higher priority channel. Can dramatically speed up installations.
    # Conda recommends this as a default
    # https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-channels.html
    && conda config --set channel_priority strict \
    && conda config --system --set auto_update_conda false \
    && conda config --system --set show_channel_urls true \
    # Enable `conda activate`
    && conda init bash \
    && conda install -y  --name base \
           "python=3.9" \
           "numpy" \
           "scipy" \
           "cython<3.0" \
    && bash -c "source activate base \
    &&   python -m pip install --no-cache-dir  \
             "-r" \
             "/headcase-pipeline/requirements.txt"" \
    # Clean up
    && sync && conda clean --all --yes && sync \
    && rm -rf ~/.cache/pip/*
RUN useradd -m -s /bin/bash -G users headcase
ENV HOME="/home/headcase"
RUN mkdir /home/headcase/.config
RUN python -c 'import cortex'
WORKDIR /headcase-pipeline
ENTRYPOINT ["python", "/headcase-pipeline/make_headcase.py"]

# Save specification to JSON.
RUN printf '{ \
  "pkg_manager": "apt", \
  "existing_users": [ \
    "root" \
  ], \
  "instructions": [ \
    { \
      "name": "from_", \
      "kwds": { \
        "base_image": "ubuntu:bionic" \
      } \
    }, \
    { \
      "name": "run", \
      "kwds": { \
        "command": "chmod 777 /tmp" \
      } \
    }, \
    { \
      "name": "install", \
      "kwds": { \
        "pkgs": [ \
          "libopengl0", \
          "build-essential", \
          "meshlab", \
          "blender=2.79.b+dfsg0-1ubuntu1.18.04.1" \
        ], \
        "opts": null \
      } \
    }, \
    { \
      "name": "run", \
      "kwds": { \
        "command": "apt-get update -qq \\\\\\n    && apt-get install -y -q --no-install-recommends \\\\\\n           blender=2.79.b+dfsg0-1ubuntu1.18.04.1 \\\\\\n           build-essential \\\\\\n           libopengl0 \\\\\\n           meshlab \\\\\\n    && rm -rf /var/lib/apt/lists/*" \
      } \
    }, \
    { \
      "name": "env", \
      "kwds": { \
        "SKLEARN_NO_OPENMP": "1" \
      } \
    }, \
    { \
      "name": "copy", \
      "kwds": { \
        "source": [ \
          ".", \
          "/headcase-pipeline" \
        ], \
        "destination": "/headcase-pipeline" \
      } \
    }, \
    { \
      "name": "env", \
      "kwds": { \
        "CONDA_DIR": "/opt/miniconda-latest", \
        "PATH": "/opt/miniconda-latest/bin:$PATH" \
      } \
    }, \
    { \
      "name": "run", \
      "kwds": { \
        "command": "apt-get update -qq\\napt-get install -y -q --no-install-recommends \\\\\\n    bzip2 \\\\\\n    ca-certificates \\\\\\n    curl\\nrm -rf /var/lib/apt/lists/*\\n# Install dependencies.\\nexport PATH=\\"/opt/miniconda-latest/bin:$PATH\\"\\necho \\"Downloading Miniconda installer ...\\"\\nconda_installer=\\"/tmp/miniconda.sh\\"\\ncurl -fsSL -o \\"$conda_installer\\" https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh\\nbash \\"$conda_installer\\" -b -p /opt/miniconda-latest\\nrm -f \\"$conda_installer\\"\\nconda update -yq -nbase conda\\n# Prefer packages in conda-forge\\nconda config --system --prepend channels conda-forge\\n# Packages in lower-priority channels not considered if a package with the same\\n# name exists in a higher priority channel. Can dramatically speed up installations.\\n# Conda recommends this as a default\\n# https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-channels.html\\nconda config --set channel_priority strict\\nconda config --system --set auto_update_conda false\\nconda config --system --set show_channel_urls true\\n# Enable `conda activate`\\nconda init bash\\nconda install -y  --name base \\\\\\n    \\"python=3.9\\" \\\\\\n    \\"numpy\\" \\\\\\n    \\"scipy\\" \\\\\\n    \\"cython<3.0\\"\\nbash -c \\"source activate base\\n  python -m pip install --no-cache-dir  \\\\\\n      \\"-r\\" \\\\\\n      \\"/headcase-pipeline/requirements.txt\\"\\"\\n# Clean up\\nsync && conda clean --all --yes && sync\\nrm -rf ~/.cache/pip/*" \
      } \
    }, \
    { \
      "name": "run", \
      "kwds": { \
        "command": "useradd -m -s /bin/bash -G users headcase" \
      } \
    }, \
    { \
      "name": "env", \
      "kwds": { \
        "HOME": "/home/headcase" \
      } \
    }, \
    { \
      "name": "run", \
      "kwds": { \
        "command": "mkdir /home/headcase/.config" \
      } \
    }, \
    { \
      "name": "run", \
      "kwds": { \
        "command": "python -c '"'"'import cortex'"'"'" \
      } \
    }, \
    { \
      "name": "workdir", \
      "kwds": { \
        "path": "/headcase-pipeline" \
      } \
    }, \
    { \
      "name": "entrypoint", \
      "kwds": { \
        "args": [ \
          "python", \
          "/headcase-pipeline/make_headcase.py" \
        ] \
      } \
    } \
  ] \
}' > /.reproenv.json
# End saving to specification to JSON.
