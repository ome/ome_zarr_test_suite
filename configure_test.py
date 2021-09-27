import sys

import yaml

# Change the value of the skip flag depending on the repository used
# repository:
# value = "bioformats2raw", "ome_zarr", "omero_ms_zarr"
ref_value = "ome_zarr"


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
            if value == ref_value:
                k["skip"] = False

    with open("sources.yml", "w") as f:
        yaml.dump(doc, f, default_flow_style=False, sort_keys=False)


if __name__ == "__main__":
    main()
