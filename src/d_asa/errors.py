class ActusNormalizationError(ValueError):
    """Raised when raw ACTUS attributes cannot be normalized for AVM use."""

    pass


class UnsupportedActusFeatureError(ActusNormalizationError):
    """Raised when normalization encounters an out-of-scope ACTUS feature."""

    pass
