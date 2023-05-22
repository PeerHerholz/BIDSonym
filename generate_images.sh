#!/bin/sh

#Generate Dockerfile.

set -e

generate_docker() {
  docker run --rm repronim/neurodocker:0.9.5 generate docker \
             --base-image bids/base_validator \
             --yes \
             --pkg-manager apt \
             --install git num-utils gcc g++ curl build-essential nano\
             --miniconda \
                version=latest \
                env_name=bidsonym \
                env_exists=false\
                conda_install="python=3.10 numpy nipype nibabel pandas" \
                pip_install="deepdefacer tensorflow scikit-image pydeface==2.0.2 nobrainer==0.4.0 quickshear==1.2.0 datalad datalad-osf" \
             --fsl version=6.0.6.4 method=binaries \
             --run-bash "conda init bash" \
             --run-bash "mkdir -p /opt/nobrainer/models && cd /opt/nobrainer/models && conda activate bidsonym && datalad datalad clone https://github.com/neuronets/trained-models && cd trained-models && git-annex enableremote osf-storage && datalad get -s osf-storage ." \
             --run-bash "git clone https://github.com/mih/mridefacer" \
             --env MRIDEFACER_DATA_DIR=/mridefacer/data \
             --run-bash "mkdir /home/mri-deface-detector && cd /home/mri-deface-detector && npm install sharp --unsafe-perm && npm install -g mri-deface-detector --unsafe-perm && cd ~" \
             --run-bash "git clone https://github.com/miykael/gif_your_nifti && cd gif_your_nifti && source activate bidsonym && python setup.py install" \
             --copy . /home/bm \
             --run-bash "chmod a+x /home/bm/bidsonym/fs_data/mri_deface" \
             --run-bash "source activate bidsonym && cd /home/bm && pip install -e ." \
             --env IS_DOCKER=1 \
             --workdir '/tmp/' \
             --entrypoint "/neurodocker/startup.sh  bidsonym"
}

# generate files
generate_docker > Dockerfile

# check if images should be build locally or not
if [ '$1' = 'local' ]; then
    echo "docker image will be build locally"
    # build image using the saved files
    docker build -t bidsonym:local .
else
  echo "Image(s) won't be build locally."
fi
