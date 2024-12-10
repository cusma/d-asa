# Metadata {#metadata}

> The D-ASA can notarize informative metadata like the debt instrument prospectus.

It is **RECOMMENDED** to use a digest of D-ASA data, instead of full clear text.

The D-ASA data digest **MUST** be computed with SHA-512/256, as defined in
<a href="https://doi.org/10.6028/NIST.FIPS.180-4">NIST FIPS 180-4</a>.

> The digests are a single SHA-256 integrity metadata defined in the
> <a href="https://w3c.github.io/webappsec-subresource-integrity">W3C subresource
> integrity specification</a>. Details on generating those digests can be found
> on the <a href="https://developer.mozilla.org/en-US/docs/Web/Security/Subresource_Integrity">MDN
> Web Docs</a> (only SHA-256 is supported by this specification).

The D-ASA metadata **MAY** be set using the **OPTIONAL** `set_asset_metadata` method.

The D-ASA metadata **MAY** be updated using the **OPTIONAL** `set_asset_metadata`
method.
