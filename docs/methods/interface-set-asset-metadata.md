# Set Asset Metadata

```json
{{#include ../.include/interface.set-asset-metadata.json}}
```

The call **MUST** fail with the `UNAUTHORIZED` error code if not called by an authorized
caller.

The call **MUST** fail with the `DEFAULTED` error code if the asset is defaulted.

The call **MAY** fail with the `SUSPENDED` error code if the asset is suspended.
