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
