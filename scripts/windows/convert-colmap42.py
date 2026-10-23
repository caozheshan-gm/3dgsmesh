"""Run the installed official 3DGS convert.py with COLMAP 4.2 flag names.

The upstream source stays untouched. This adapter only updates two renamed CLI
options before executing that source; fail loudly if upstream changes.
"""

from pathlib import Path

source_path = Path(r"D:\3dgs\apps\gaussian-src\convert.py")
source = source_path.read_text(encoding="utf-8")
for old, new in (
    ("--SiftExtraction.use_gpu", "--FeatureExtraction.use_gpu"),
    ("--SiftMatching.use_gpu", "--FeatureMatching.use_gpu"),
):
    if source.count(old) != 1:
        raise RuntimeError(f"Expected one occurrence of {old} in {source_path}; review the installed version")
    source = source.replace(old, new)
exec(compile(source, str(source_path), "exec"), {"__name__": "__main__", "__file__": str(source_path)})
