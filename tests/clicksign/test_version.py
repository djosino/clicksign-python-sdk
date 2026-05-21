import clicksign
from clicksign.version import __version__, _resolve_version


def test_clicksign_exports_version():
    assert clicksign.__version__
    assert clicksign.__version__ == __version__


def test_version_matches_revision_or_metadata():
    v = _resolve_version()
    assert v
    assert v != "0.0.0+unknown"
