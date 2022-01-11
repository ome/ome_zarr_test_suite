MS_SUITE="omero-ms-zarr-suite"
BF_SUITE="ome-zarr-bf2raw-suite"
ZARR_SUITE="ome-zarr-py-suite"

REPO=$1
# Configure the repository to run the tests on
eval "$(conda shell.bash hook)"
conda activate test
if [[ $REPO =~ 'omero-ms-zarr' ]]; then
    git clone https://github.com/$REPO $MS_SUITE
    python configure_test.py omero_ms_zarr
 elif [[ $REPO =~ 'bioformats2raw' ]]; then
    git clone https://github.com/$REPO $BF_SUITE
    python configure_test.py bioformats2raw
elif [[ $repo =~ 'ome-zarr-py' ]]; then
    git clone https://github.com/$REPO $ZARR_SUITE
    cd $ZARR_SUITE
    pip install -e .
    cd ..
    python configure_test.py ome_zarr
fi
conda deactivate
