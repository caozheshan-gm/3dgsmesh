"""Archive the previous run and prepare empty data/ and output/ folders."""

from datetime import datetime
from pathlib import Path


def has_previous_run(data: Path, output: Path) -> bool:
    if data.exists():
        for path in data.iterdir():
            if path.name != "input" or not path.is_dir():
                return True
        images = data / "input"
        if images.is_dir() and any(path.name != ".gitkeep" for path in images.iterdir()):
            return True
    if output.exists() and any(path.name != ".gitkeep" for path in output.iterdir()):
        return True
    return False


def create_empty_folders(data: Path, output: Path) -> None:
    images = data / "input"
    images.mkdir(parents=True, exist_ok=True)
    output.mkdir(parents=True, exist_ok=True)
    (images / ".gitkeep").touch(exist_ok=True)
    (output / ".gitkeep").touch(exist_ok=True)


def main() -> None:
    repo = Path(__file__).resolve().parents[2]
    data = repo / "data"
    output = repo / "output"
    if any(path.is_symlink() for path in (data, output)):
        raise SystemExit("data/ and output/ must be ordinary directories, not links.")

    if not has_previous_run(data, output):
        create_empty_folders(data, output)
        print(f"Ready: {data / 'input'} and {output} are empty.")
        return

    archive_root = repo.parent / f"{repo.name}-archive"
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    for number in range(100):
        name = stamp if number == 0 else f"{stamp}_{number:02d}"
        archive = archive_root / name
        if not archive.exists():
            archive.mkdir(parents=True)
            break
    else:
        raise SystemExit("Could not find an unused archive folder name.")

    moved: list[tuple[Path, Path]] = []
    try:
        for source in (data, output):
            if source.exists():
                target = archive / source.name
                source.rename(target)
                moved.append((source, target))
    except OSError:
        # A failed move leaves the original run in its original location.
        for source, target in reversed(moved):
            target.rename(source)
        archive.rmdir()
        raise

    # If creating the new folders fails, the archived run remains safe.
    create_empty_folders(data, output)

    print(f"Previous run archived at: {archive}")
    print(f"Ready for new frames: {data / 'input'}")
    print(f"Ready for new training: {output}")


if __name__ == "__main__":
    main()
