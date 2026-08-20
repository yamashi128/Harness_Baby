from __future__ import annotations

from importlib.metadata import version

from harness_baby import __version__


def test_package_version_has_single_metadata_source() -> None:
    assert version("harness-baby") == __version__
