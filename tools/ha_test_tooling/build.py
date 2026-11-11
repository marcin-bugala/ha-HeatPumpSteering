"""Build Core's standalone fixtures from an exact, verified Git checkout.

No upstream generator is executed. Core 2026.11.1 already ships the standalone
package, so extraction needs only a local version and an exact HA dependency.
"""

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from email.parser import BytesParser
from importlib.metadata import version
from pathlib import Path
from zipfile import ZipFile

CORE_SHA = "d8a0dc698c8946b44e455d904000db563cfbf1ba"
HA_VERSION = "2026.11.1"
FIXTURES_VERSION = "0.0.0+ha2026.11.1"
PACKAGE_PATH = "packages/pytest-homeassistant"
REPOSITORY = "https://github.com/home-assistant/core.git"


def git(checkout: Path, *args: str) -> str:
    """Run Git without shell interpolation, failing on any source error."""
    return subprocess.check_output(
        ["git", "-C", str(checkout), *args], text=True
    ).strip()


def verify_source(checkout: Path) -> None:
    """Reject a different commit or locally modified/untracked package inputs."""
    if git(checkout, "rev-parse", "HEAD") != CORE_SHA:
        raise ValueError("Core commit differs from the approved source")
    if git(
        checkout, "status", "--porcelain", "--untracked-files=all", "--", PACKAGE_PATH
    ):
        raise ValueError("Core fixtures source is not clean")


def checkout_source(destination: Path) -> None:
    """Fetch only the pinned commit and package, without tags or moving refs."""
    destination.mkdir(parents=True, exist_ok=False)
    git(destination, "init")
    git(destination, "config", "core.autocrlf", "false")
    git(destination, "remote", "add", "origin", REPOSITORY)
    git(destination, "sparse-checkout", "init", "--cone")
    git(destination, "sparse-checkout", "set", PACKAGE_PATH)
    git(destination, "fetch", "--depth=1", "--filter=blob:none", "origin", CORE_SHA)
    git(destination, "checkout", "--detach", "FETCH_HEAD")
    verify_source(destination)


def prepare_package(checkout: Path, destination: Path) -> None:
    """Copy immutable source; change only the two declared metadata fields."""
    verify_source(checkout)
    shutil.copytree(checkout / PACKAGE_PATH, destination)
    metadata = destination / "pyproject.toml"
    content = metadata.read_text(encoding="utf-8")
    replacements = {
        'version = "0.0.0"': f'version = "{FIXTURES_VERSION}"',
        '  "homeassistant",': f'  "homeassistant=={HA_VERSION}",',
    }
    for original, replacement in replacements.items():
        if content.count(original) != 1:
            raise ValueError(f"Unexpected upstream metadata: {original}")
        content = content.replace(original, replacement)
    metadata.write_text(content, encoding="utf-8", newline="\n")


def wheel_content(path: Path) -> dict[str, str]:
    """Hash unpacked content, ignoring ZIP timestamps (including METADATA)."""
    with ZipFile(path) as archive:
        return {
            name: hashlib.sha256(archive.read(name)).hexdigest()
            for name in sorted(archive.namelist())
            if not name.endswith("/")
        }


def compare_wheels(first: Path, second: Path) -> dict[str, str]:
    """Reject nondeterministic contents or metadata, not just fixture differences."""
    content = wheel_content(first)
    if content != wheel_content(second):
        raise ValueError("Repeated builds have different unpacked wheel contents")
    return content


def verify_wheel(checkout: Path, wheel: Path) -> None:
    """Require every original Python file, the license and exact HA metadata."""
    source = checkout / PACKAGE_PATH
    with ZipFile(wheel) as archive:
        for path in (source / "pytest_homeassistant").rglob("*.py"):
            if archive.read(path.relative_to(source).as_posix()) != path.read_bytes():
                raise ValueError(f"Wheel changed upstream fixture: {path.name}")
        prefix = f"pytest_homeassistant-{FIXTURES_VERSION}.dist-info"
        if (
            archive.read(f"{prefix}/licenses/LICENSE.md")
            != (source / "LICENSE.md").read_bytes()
        ):
            raise ValueError("Wheel did not retain Core's license")
        metadata = BytesParser().parsebytes(archive.read(f"{prefix}/METADATA"))
        if metadata["Version"] != FIXTURES_VERSION or (
            f"homeassistant=={HA_VERSION}" not in metadata.get_all("Requires-Dist", [])
        ):
            raise ValueError("Wheel version or HA dependency is incorrect")


def build(checkout: Path, destination: Path) -> Path:
    """Build twice from fresh copies using the caller's pinned build tools."""
    destination.mkdir(parents=True, exist_ok=False)
    wheels = []
    for iteration in (1, 2):
        package = destination / f"source-{iteration}"
        prepare_package(checkout, package)
        output = destination / f"wheel-{iteration}"
        subprocess.run(
            [
                sys.executable,
                "-m",
                "build",
                "--wheel",
                "--no-isolation",
                "--outdir",
                str(output),
                str(package),
            ],
            check=True,
        )
        (wheel,) = output.glob("*.whl")
        verify_wheel(checkout, wheel)
        wheels.append(wheel)
    contents = compare_wheels(*wheels)
    report = {
        "core_repository": REPOSITORY,
        "core_sha": CORE_SHA,
        "source_path": PACKAGE_PATH,
        "ha_version": HA_VERSION,
        "fixtures_version": FIXTURES_VERSION,
        "license": "Apache-2.0 (Core package LICENSE.md, included in wheel)",
        "wheel_sha256": hashlib.sha256(wheels[0].read_bytes()).hexdigest(),
        "repeated_build_equivalent": True,
        "build_tools": {
            name: version(name) for name in ("build", "setuptools", "wheel")
        },
        "content_sha256": contents,
    }
    (destination / "provenance.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2))
    return wheels[0]


def main() -> None:
    """Keep all generated files in an explicitly selected new output directory."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--fetch", action="store_true")
    args = parser.parse_args()
    if args.fetch:
        checkout_source(args.core.resolve())
    build(args.core.resolve(), args.output.resolve())


if __name__ == "__main__":
    main()
