# OME-Zarr Test Suite

This suite loops over a number of sources of OME-Zarr files (inputs),
running any generation code if necessary, and then passes the URI for
the fileset to all registered suites.

In pseudo-code:

```
for input in inputs:
    for suite in suites:
        input.setup()
        try:
            suite(input)
        finally:
            input.cleanup()
```

so that at any one time, at most one (potentially generated) resource
is active.

Each suite is expected to take all configuration values it needs
from the Zarr itself. (TBD)
