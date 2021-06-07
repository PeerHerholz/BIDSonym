#Generate Dockerfile.

#!/bin/sh

 set -e

generate_docker() {
  docker run --rm kaczmarj/neurodocker:0.6.0 generate docker \
             --base neurodebian:stretch-non-free \
             --pkg-manager apt \
             --install fsl-core fsl-mni152-templates git num-utils gcc g++ curl build-essential nano\
             --run-bash "curl -sL https://deb.nodesource.com/setup_10.x | bash - && apt-get install -y nodejs && apt-get install -y npm"\
             --add-to-entrypoint "source /etc/fsl/fsl.sh" \
             --miniconda \
                conda_install="python=3.6 numpy nipype nibabel pandas" \
                pip_install='deepdefacer tensorflow scikit-image' \
                create_env='bidsonym' \
                activate=true \
             --run-bash "source activate bidsonym && git clone https://github.com/poldracklab/pydeface.git && cd pydeface && python setup.py install && cd -" \
             --run-bash "source activate bidsonym && git clone https://github.com/nipy/quickshear.git  && cd quickshear && python setup.py install && cd -" \
             --run-bash "source activate bidsonym && git clone https://github.com/neuronets/nobrainer.git  && cd nobrainer && python setup.py install && cd -" \
             --run-bash "mkdir -p /opt/nobrainer/models && cd /opt/nobrainer/models && curl -LJO  https://github.com/neuronets/nobrainer-models/releases/download/0.1/brain-extraction-unet-128iso-model.h5 && cd ~ " \
             --run-bash "git clone https://github.com/mih/mridefacer" \
             --env MRIDEFACER_DATA_DIR=/mridefacer/data \
             --run-bash "npm install -g bids-validator@1.5.4" \
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
