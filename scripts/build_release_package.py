from __future__ import annotations

import hashlib
import shutil
import tarfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"

PACKAGE_FILES = {
    ROOT / "release" / "compose.yaml": Path("compose.yaml"),
    ROOT / "release" / ".env.example": Path(".env.example"),
    ROOT / "release" / "install.ps1": Path("install.ps1"),
    ROOT / "release" / "install.sh": Path("install.sh"),
    ROOT / "release" / "update.ps1": Path("update.ps1"),
    ROOT / "release" / "update.sh": Path("update.sh"),
    ROOT / "release" / "INSTALLATION.md": Path("INSTALLATION.md"),
    ROOT / "CHANGELOG.md": Path("CHANGELOG.md"),
    ROOT / "VERSION": Path("VERSION"),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    version = (ROOT / "VERSION").read_text(encoding="utf-8-sig").strip()
    if not version:
        raise RuntimeError("VERSION ist leer")

    package_name = f"KickerKasse-{version}"
    stage = DIST / package_name
    shutil.rmtree(DIST, ignore_errors=True)
    stage.mkdir(parents=True)

    files = dict(PACKAGE_FILES)
    license_file = ROOT / "LICENSE"
    if license_file.exists():
        files[license_file] = Path("LICENSE")

    for source, relative_target in files.items():
        if not source.is_file():
            raise FileNotFoundError(source)
        target = stage / relative_target
        target.parent.mkdir(parents=True, exist_ok=True)
        content = source.read_bytes()
        if source.name == ".env.example":
            content = content.replace(b"__VERSION__", version.encode("ascii"))
        target.write_bytes(content)

    zip_path = DIST / f"{package_name}.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(stage.rglob("*")):
            if path.is_file():
                archive.write(path, Path(package_name) / path.relative_to(stage))

    tar_path = DIST / f"{package_name}.tar.gz"
    with tarfile.open(tar_path, "w:gz") as archive:
        archive.add(stage, arcname=package_name)

    checksum_path = DIST / "SHA256SUMS"
    checksum_path.write_text(
        "".join(
            f"{sha256(path)}  {path.name}\n"
            for path in (zip_path, tar_path)
        ),
        encoding="ascii",
    )

    print(f"Release-Paket erstellt: {stage}")


if __name__ == "__main__":
    main()
