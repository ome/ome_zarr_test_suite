import sys

import yaml

# Change the value of the skip flag depending on the repository used
# repository. Supported value:
# "bioformats2raw": do not skip the tests using bioformats2raw script
# "ome_zarr": do not skip the tests using ome-zarr-py
# "omero_ms_zarr": : do not skip the tests using omero-ms-zarr


def main() -> None:
    argv = sys.argv[1:]
    value = argv[0]
    with open("sources.yml") as f:
        doc = yaml.safe_load(f)
    for k in doc:
        k["skip"] = True
        if "script" in k:
            if k["script"].startswith(value):
                k["skip"] = False
        else:
            if value == "ome_zarr":
                k["skip"] = False

    with open("sources.yml", "w") as f:
        yaml.dump(doc, f, default_flow_style=False, sort_keys=False)


if __name__ == "__main__":
    main()
