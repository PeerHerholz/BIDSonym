#Generate Dockerfile.

docker run --rm kaczmarj/neurodocker:0.4.0 generate docker \
  --base debian:stretch --pkg-manager apt \
  --fsl version=5.0.10 \
  --freesurfer version=6.0.0 min=true \
  --miniconda create_env=bidsonym \
              conda_install="python=3.6 traits" \
              pip_install="nipype nibabel pydeface quickshear" \
              activate=true \ > Dockerfile

# Build Docker image using the saved Dockerfile.
docker build -t bidsonym .
