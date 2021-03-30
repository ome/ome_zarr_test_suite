# OME-Zarr Test Suite

This suite loops over a number of inputs, generating them
if necessary, and then passes them to a number of suites.

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

so that at most one (potentially generated) resource is active
at any one time.

Each suite is expected to take all configuration values it needs
from the Zarr itself. (TBD)
