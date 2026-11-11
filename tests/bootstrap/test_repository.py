"""Regression tests for CI gates; these do not test the future product."""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.check_repository import check_integration, check_links


class RepositoryChecks(unittest.TestCase):
    """Ensure new integration code cannot accidentally bypass HA checks."""

    def setUp(self) -> None:
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def write(self, name: str, content: str = "") -> None:
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def test_docs_stage(self) -> None:
        self.assertEqual(check_integration(self.root), (False, []))

    def test_code_without_manifest_is_rejected(self) -> None:
        self.write("custom_components/example/__init__.py")
        active, errors = check_integration(self.root)
        self.assertTrue(active)
        self.assertTrue(any("manifest" in error for error in errors))

    def test_manifest_requires_pinned_ha_plugin_and_tests(self) -> None:
        self.write("custom_components/example/manifest.json", "{}")
        active, errors = check_integration(self.root)
        self.assertTrue(active)
        self.assertEqual(len(errors), 2)
        self.write(
            "requirements-ha-test.txt", "pytest-homeassistant-custom-component\n"
        )
        self.assertEqual(len(check_integration(self.root)[1]), 2)
        self.write(
            "requirements-ha-test.txt", "pytest-homeassistant-custom-component==1.0\n"
        )
        self.write("tests/integration/test_setup.py")
        self.assertEqual(check_integration(self.root), (True, []))

    def test_wildcard_ha_plugin_versions_are_rejected(self) -> None:
        self.write("custom_components/example/manifest.json", "{}")
        self.write("tests/integration/test_setup.py")
        for version in ("1.*", "1.0.*"):
            with self.subTest(version=version):
                self.write(
                    "requirements-ha-test.txt",
                    f"pytest-homeassistant-custom-component=={version}\n",
                )
                active, errors = check_integration(self.root)
                self.assertTrue(active)
                self.assertEqual(
                    errors,
                    [
                        "Pin pytest-homeassistant-custom-component "
                        "in requirements-ha-test.txt."
                    ],
                )

    def test_unmanifested_second_component_is_rejected(self) -> None:
        self.write("custom_components/example/manifest.json", "{}")
        self.write("custom_components/other/sensor.py")
        self.assertTrue(
            any("other" in error for error in check_integration(self.root)[1])
        )

    def test_local_targets_and_external_links(self) -> None:
        self.write("README.md", "[ok](docs/a.md#anchor) [web](https://example.com/a)")
        self.write("docs/a.md", "[up](../README.md) [same](#section)")
        self.assertEqual(check_links(self.root), [])
        self.write("docs/a.md", "[broken](missing.md)")
        self.assertEqual(len(check_links(self.root)), 1)

    def test_escaping_repository_is_rejected(self) -> None:
        self.write("README.md", "[outside](../outside.md)")
        self.assertEqual(len(check_links(self.root)), 1)


if __name__ == "__main__":
    unittest.main()
