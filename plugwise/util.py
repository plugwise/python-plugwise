"""Plugwise Shared functionality definitions."""


def version_to_model(hw_models: dict[str, str], version: str | None) -> str | None:
    """Translate hardware_version to device type."""
    if version is None:
        return None

    model = hw_models.get(version)
    if model is None:
        model = hw_models.get(version[4:10])
    if model is None:
        # Try again with reversed order
        model = hw_models.get(version[-2:] + version[-4:-2] + version[-6:-4])

    return model if model is not None else "Unknown"
