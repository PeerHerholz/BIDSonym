#Generate Dockerfile.

#!/bin/sh

 set -e

 # Generate Dockerfile.
generate_docker() {
  docker run --rm kaczmarj/neurodocker:0.5.0 generate docker \
             --base neurodebian:stretch-non-free \
             --pkg-manager apt \
             --freesurfer version=6.0.0 min=true \
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
                pip_install='deepdefacer[tf_cpu]' \
                create_env='bidsonym' \
                activate=true \
             --run-bash "source activate bidsonym && git clone https://github.com/poldracklab/pydeface.git && cd pydeface && python setup.py install && cd -" \
             --run-bash "source activate bidsonym && git clone https://github.com/nipy/quickshear.git  && cd quickshear && python setup.py install && cd -" \
             --run-bash "git clone https://github.com/mih/mridefacer" \
             --env MRIDEFACER_DATA_DIR=/mridefacer/data \
             --run-bash "rm -r /usr/share/fsl/data/atlases && rm -r /usr/share/fsl/data/first && rm -r /usr/share/fsl/data/possum" \
             --copy bidsonym/bidsonym.py /home/bidsonym.py \
             --copy bidsonym/version /home/version \
             --copy bidsonym/fs_data /home/fs_data \
             --entrypoint "/neurodocker/startup.sh python /home/bidsonym.py"
}

generate_singularity() {
  docker run --rm kaczmarj/neurodocker:0.5.0 generate singularity \
            --base neurodebian:stretch-non-free \
            --pkg-manager apt \
            --freesurfer version=6.0.0 min=true \
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
               pip_install='deepdefacer[tf_cpu]' \
               create_env='bidsonym' \
               activate=true \
            --run-bash "source activate bidsonym && git clone https://github.com/poldracklab/pydeface.git && cd pydeface && python setup.py install && cd -" \
            --run-bash "source activate bidsonym && git clone https://github.com/nipy/quickshear.git  && cd quickshear && python setup.py install && cd -" \
            --run-bash "git clone https://github.com/mih/mridefacer" \
            --env MRIDEFACER_DATA_DIR=/mridefacer/data \
            --run-bash "rm -r /usr/share/fsl/data/atlases && rm -r /usr/share/fsl/data/first && rm -r /usr/share/fsl/data/possum" \
            --copy bidsonym/bidsonym.py /home/bidsonym.py \
            --copy bidsonym/version /home/version \
            --copy bidsonym/fs_data /home/fs_data \
            --entrypoint "/neurodocker/startup.sh python /home/bidsonym.py"
}

# generate files
generate_docker > Dockerfile
generate_singularity > Singularity

# check if images should be build locally or not
if [ '$1' = 'local' ]; then
  if [ '$2' = 'docker' ]; then
    echo "docker image will be build locally"
    # build image using the saved files
    docker build -t eegprep:test .
  elif [ '$2' = 'singularity']; then
    echo "singularity image will be build locally"
    # build image using the saved files
    singularity build eegprep.simg Singularity
  elif [ '$2' = 'both' ]; then
    echo "docker and singularity images will be build locally"
    # build images using the saved files
    docker build -t eegprep:test .
    singularity build eegprep.simg Singularity
  elif [ -z "$2" ]; then
    echo "Please indicate which image should be build. You can choose from docker, singularity or both."
  fi
else
  echo "Image(s) won't be build locally."
fi
