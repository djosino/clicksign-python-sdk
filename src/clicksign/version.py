import pathlib

__version__ = (pathlib.Path(__file__).parent.parent.parent / "REVISION").read_text().strip()
