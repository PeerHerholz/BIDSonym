#Generate Dockerfile.

#!/bin/sh

 set -e

generate_docker() {
  yes | docker run -i --rm repronim/neurodocker:1.0.0 generate docker \
             --base-image ubuntu:20.04 \
             --pkg-manager apt \
	     --env DEBIAN_FRONTEND=noninteractive \
             --install git num-utils gcc g++ curl yarn build-essential nano git-annex npm less unzip tig vim \
             --run-bash "curl -sL https://deb.nodesource.com/setup_18.x | bash - && apt update && apt-get install -y nodejs && rm -rf /tmp/*" \
             --run-bash "npm install -g bids-validator@1.14.6 && rm -rf /tmp/*" \
             --fsl version=6.0.7.4 method=binaries \
             --miniconda \
                version=latest \
		conda_install="python=3.11 numpy nipype nibabel pandas datalad deno" \
                pip_install='tensorflow scikit-image pydeface==2.0.2 nobrainer==1.2.1 quickshear==1.2.0 datalad-osf pybids==0.16.5' \
	     --env PATH="\${PATH}:/opt/miniconda-latest/bin" \
             --run-bash "git config --global user.email 'bidsonym@example.com' && git config --global user.name 'BIDSonym'" \
             --run-bash "cd /opt && mkdir -p nobrainer/models && cd nobrainer/models && datalad clone https://github.com/neuronets/trained-models && cd trained-models && git-annex enableremote osf-storage && datalad get -s osf-storage neuronets/brainy/0.1.0/weights/brain-extraction-unet-128iso-model.h5" \
             --run-bash "cd /opt && mkdir mri-deface-detector && cd mri-deface-detector && npm install sharp --unsafe-perm && npm install -g mri-deface-detector --unsafe-perm && cd ~" \
             --run-bash "cd /opt && git clone --filter=blob:none -b bf-imageio https://github.com/yarikoptic/gif_your_nifti && cd gif_your_nifti && python setup.py install" \
             --run-bash "cd /opt && git clone --filter=blob:none https://github.com/bids-standard/bids-validator && deno compile -o /usr/local/bin/bids-validator-deno -A  bids-validator/bids-validator/src/bids-validator.ts && cd -" \
	     --run-bash "cd /opt && git clone --filter=blob:none https://github.com/mih/mridefacer" \
             --env MRIDEFACER_DATA_DIR=/opt/mridefacer/data \
             --copy . /opt/bidsonym-src \
             --run-bash "cd /opt/bidsonym-src && chmod a+x bidsonym/fs_data/mri_deface && pip install -e ." \
             --env IS_DOCKER=1 \
	     --run-bash 'git config --global safe.directory "*"' \
	     --run-bash "rm -rf /tmp/*" \
             --entrypoint "bidsonym"
}

# generate files
generate_docker > Dockerfile

# check if images should be build locally or not
if [[ $1 == 'local' ]]; then
    echo "docker image will be build locally"
    # build image using the saved files
    docker build -t bidsonym:local .
else
  echo "Image(s) won't be build locally."
fi
