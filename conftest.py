"""Ensure the project root is importable so `import app...` works under pytest."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
