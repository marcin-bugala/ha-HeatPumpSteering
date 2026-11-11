"""Offline regressions for immutable sources and reproducible fixtures builds."""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from zipfile import ZipFile

from tools.ha_test_tooling.build import (
    CORE_SHA,
    FIXTURES_VERSION,
    PACKAGE_PATH,
    compare_wheels,
    prepare_package,
    verify_source,
    verify_wheel,
)


class FixturesBuildTests(unittest.TestCase):
    """Do not weaken source checks to make a fixtures build appear valid."""

    @patch("tools.ha_test_tooling.build.git", return_value="different-sha")
    def test_wrong_commit_rejected(self, git) -> None:
        with self.assertRaisesRegex(ValueError, "commit"):
            verify_source(Path("unused"))

    @patch("tools.ha_test_tooling.build.git", side_effect=[CORE_SHA, " M file"])
    def test_dirty_source_rejected(self, git) -> None:
        with self.assertRaisesRegex(ValueError, "clean"):
            verify_source(Path("unused"))

    @patch("tools.ha_test_tooling.build.verify_source")
    def test_only_metadata_is_adapted(self, verify) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "core" / PACKAGE_PATH
            source.mkdir(parents=True)
            (source / "pyproject.toml").write_text(
                'version = "0.0.0"\ndependencies = [\n  "homeassistant",\n]\n',
                encoding="utf-8",
            )
            fixture = b'"""An unchanged fixture."""\nassert True\n'
            (source / "plugins.py").write_bytes(fixture)
            prepare_package(root / "core", root / "result")
            verify.assert_called_once_with(root / "core")
            result = root / "result"
            self.assertEqual((result / "plugins.py").read_bytes(), fixture)
            metadata = (result / "pyproject.toml").read_text(encoding="utf-8")
            self.assertIn('version = "0.0.0+ha2026.11.1"', metadata)
            self.assertIn('"homeassistant==2026.11.1"', metadata)

    def test_wheel_comparison_checks_metadata_and_fixture_bytes(self) -> None:
        with TemporaryDirectory() as temporary:
            first, second = (Path(temporary) / name for name in ("a.whl", "b.whl"))
            for path in (first, second):
                with ZipFile(path, "w") as archive:
                    archive.writestr("fixtures/plugins.py", b"original")
                    archive.writestr("test.dist-info/METADATA", b"Version: 1")
            self.assertEqual(len(compare_wheels(first, second)), 2)
            for name in ("fixtures/plugins.py", "test.dist-info/METADATA"):
                with self.subTest(name=name):
                    with ZipFile(second, "w") as archive:
                        archive.writestr("fixtures/plugins.py", b"original")
                        archive.writestr("test.dist-info/METADATA", b"Version: 1")
                    # Rebuild a changed archive without duplicate ZIP entries.
                    with ZipFile(second) as archive:
                        entries = {n: archive.read(n) for n in archive.namelist()}
                    entries[name] = b"changed"
                    with ZipFile(second, "w") as archive:
                        for entry, content in entries.items():
                            archive.writestr(entry, content)
                    with self.assertRaisesRegex(ValueError, "contents"):
                        compare_wheels(first, second)

    def test_wheel_requires_original_fixtures_license_and_dependency(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / PACKAGE_PATH
            (source / "pytest_homeassistant").mkdir(parents=True)
            (source / "pytest_homeassistant/plugins.py").write_bytes(b"fixture")
            (source / "LICENSE.md").write_bytes(b"license")
            prefix = f"pytest_homeassistant-{FIXTURES_VERSION}.dist-info"
            original = {
                "pytest_homeassistant/plugins.py": b"fixture",
                f"{prefix}/licenses/LICENSE.md": b"license",
                f"{prefix}/METADATA": (
                    f"Version: {FIXTURES_VERSION}\n"
                    "Requires-Dist: homeassistant==2026.11.1\n"
                ).encode(),
            }
            wheel = root / "package.whl"
            with ZipFile(wheel, "w") as archive:
                for name, content in original.items():
                    archive.writestr(name, content)
            verify_wheel(root, wheel)
            for changed in original:
                with self.subTest(changed=changed):
                    with ZipFile(wheel, "w") as archive:
                        for name, content in original.items():
                            archive.writestr(
                                name, b"changed" if name == changed else content
                            )
                    with self.assertRaises(ValueError):
                        verify_wheel(root, wheel)
