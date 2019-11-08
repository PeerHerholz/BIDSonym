#Generate Dockerfile.

#!/bin/sh

 set -e

 # Generate Dockerfile.
 #--freesurfer version=6.0.0 min=true \
#--entrypoint "/neurodocker/startup.sh python /home/bidsonym/bidsonym/run_deeid.py"

generate_docker() {
  docker run --rm kaczmarj/neurodocker:0.5.0 generate docker \
             --base neurodebian:stretch-non-free \
             --pkg-manager apt \
             --install fsl-complete git num-utils gcc g++ curl build-essential\
             --run-bash "curl -sL https://deb.nodesource.com/setup_8.x | bash - && apt-get install -y nodejs && apt-get install -y npm"\
             --add-to-entrypoint "source /etc/fsl/fsl.sh" \
             --env FSLDIR=/usr/share/fsl/5.0 \
                   FSLOUTPUTTYPE=NIFTI_GZ \
                   FSLMULTIFILEQUIT=TRUE \
                   POSSUMDIR=/usr/share/fsl/5.0 \
                   LD_LIBRARY_PATH=/usr/lib/fsl/5.0:$LD_LIBRARY_PATH \
                   FSLTCLSH=/usr/bin/tclsh \
                   FSLWISH=/usr/bin/wish \
                   PATH=/usr/lib/fsl/5.0:$PATH \
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
             --run-bash "rm -r /usr/share/fsl/data/atlases && rm -r /usr/share/fsl/data/first && rm -r /usr/share/fsl/data/possum" \
             --run-bash "npm install -g bids-validator@1.2.3" \
             --run-bash "mkdir /home/mri-deface-detector && cd /home/mri-deface-detector && npm install sharp --unsafe-perm && npm install -g mri-deface-detector --unsafe-perm && cd ~" \
             --run-bash "git clone https://github.com/miykael/gif_your_nifti && cd gif_your_nifti && source activate bidsonym && python setup.py install" \
             --copy . /home/bm \
             --run-bash "chmod a+x /home/bm/bidsonym/fs_data/mri_deface" \
             --run-bash "source activate bidsonym && cd /home/bm && pip install -e ." \
             --copy example_data /home/bidsonym/example_data \
             --env IS_DOCKER=1 \
             --workdir '/tmp/' \
             --entrypoint "/neurodocker/startup.sh  bidsonym"
}

generate_singularity() {
  docker run --rm kaczmarj/neurodocker:0.5.0 generate singularity \
            --base neurodebian:stretch-non-free \
            --pkg-manager apt \
            --install fsl-complete git num-utils gcc \
            --add-to-entrypoint "source /etc/fsl/fsl.sh" \
            --env FSLDIR=/usr/share/fsl/5.0 \
                  FSLOUTPUTTYPE=NIFTI_GZ \
                  FSLMULTIFILEQUIT=TRUE \
                  POSSUMDIR=/usr/share/fsl/5.0 \
                  LD_LIBRARY_PATH=/usr/lib/fsl/5.0:$LD_LIBRARY_PATH \
                  FSLTCLSH=/usr/bin/tclsh \
                  FSLWISH=/usr/bin/wish \
                  PATH=/usr/lib/fsl/5.0:$PATH \
            --miniconda \
               conda_install="python=3.6 numpy nipype nibabel pandas" \
               pip_install='deepdefacer nobrainer tensorflow' \
               create_env='bidsonym' \
               activate=true \
            --run-bash "source activate bidsonym && git clone https://github.com/poldracklab/pydeface.git && cd pydeface && python setup.py install && cd -" \
            --run-bash "source activate bidsonym && git clone https://github.com/nipy/quickshear.git  && cd quickshear && python setup.py install && cd -" \
            --run-bash "git clone https://github.com/mih/mridefacer" \
            --env MRIDEFACER_DATA_DIR=/mridefacer/data \
            --run-bash "rm -r /usr/share/fsl/data/atlases && rm -r /usr/share/fsl/data/first && rm -r /usr/share/fsl/data/possum" \
            --copy . /home/bm \
            --run-bash "chmod a+x /home/bm/bidsonym/fs_data/mri_deface" \
            --run-bash "source activate bidsonym && cd /home/bm && pip install -e ." \
            --copy example_data /home/bidsonym/example_data \
            --env IS_DOCKER=1 \
            --entrypoint "/neurodocker/startup.sh  bidsonym"
}

# generate files
generate_docker > Dockerfile
generate_singularity > Singularity

# check if images should be build locally or not
if [ '$1' = 'local' ]; then
  if [ '$2' = 'docker' ]; then
    echo "docker image will be build locally"
    # build image using the saved files
    docker build -t bidsonym:test .
  elif [ '$2' = 'singularity']; then
    echo "singularity image will be build locally"
    # build image using the saved files
    singularity build bidsonym.simg Singularity
  elif [ '$2' = 'both' ]; then
    echo "docker and singularity images will be build locally"
    # build images using the saved files
    docker build -t bidsonym:test .
    singularity build bidsonym.simg Singularity
  elif [ -z "$2" ]; then
    echo "Please indicate which image should be build. You can choose from docker, singularity or both."
  fi
else
  echo "Image(s) won't be build locally."
fi
