#Generate Dockerfile.

docker run --rm kaczmarj/neurodocker:master generate docker \
           --base neurodebian:stretch-non-free \
           --pkg-manager apt \
           --install fsl \
           --add-to-entrypoint "source /etc/fsl/fsl.sh" \
           --freesurfer version=6.0.0 min=true \
           --miniconda create_env=bidsonym \
              conda_install="python=3.6 traits nipype" \
              pip_install="nibabel pydeface quickshear" \
              activate=true \ > Dockerfile

# Build Docker image using the saved Dockerfile.
docker build -t bidsonym .
