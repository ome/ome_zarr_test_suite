# OME-Zarr Test Suite

This suite loops over a number of sources of OME-Zarr files,
running any generation code if necessary, and then passes the URI for
the fileset to all registered suites.

In pseudo-code:

```
for source in sources:
    for suite in suites:
        source.setup()
        try:
            suite(source)
        finally:
            source.cleanup()
```

so that at any one time, at most one (potentially generated) resource
is active.

Each suite is expected to take all configuration values it needs
from the Zarr itself. (TBD)

Sources include test files created with `ome-zarr-py`, local files (from `data` directory),
remotely-hosted sample files, files generated by `bioformats2raw` and data served from
OMERO with `omero-ms-zarr`. In the latter 2 cases, Docker environments are used.

The whole test suite can be run locally as shown below. NB: this will take some time as
multiple Docker environments will be created. To limit the number of sources or tests,
the `sources.yml` and `suites.yml` files can first be edited to exclude some items.

```
# this takes a while...
$ conda env create -n ome_zarr_test_suite -f environment.yml

$ conda activate ome_zarr_test_suite

# Run all tests
$ pytest
```
