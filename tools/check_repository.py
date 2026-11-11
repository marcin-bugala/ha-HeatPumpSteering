"""Check local document targets and require HA tests when integration code appears."""

import argparse
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit


def check_links(root: Path) -> list[str]:
    """Validate inline Markdown file targets, without network access or anchors."""
    errors = []
    documents = [*root.glob("*.md"), *root.glob("docs/**/*.md")]
    documents += list(root.glob(".github/*.md"))
    for document in documents:
        content = re.sub(
            r"```.*?```", "", document.read_text(encoding="utf-8"), flags=re.S
        )
        for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", content):
            target = target.strip().strip("<>")
            url = urlsplit(target)
            if url.scheme or url.netloc or not url.path:
                continue
            path = (document.parent / unquote(url.path)).resolve()
            if not path.is_relative_to(root.resolve()) or not path.exists():
                errors.append(
                    f"{document.relative_to(root)}: missing/local escape: {target}"
                )
    return errors


def check_integration(root: Path) -> tuple[bool, list[str]]:
    """Do not silently skip HA checks for new code without a manifest or tests."""
    manifests = list(root.glob("custom_components/*/manifest.json"))
    code = list(root.glob("custom_components/**/*.py"))
    if not manifests and not code:
        return False, []
    errors = []
    if len(manifests) != 1:
        errors.append("Integration code requires exactly one product manifest.json.")
    for source in code:
        relative = source.relative_to(root / "custom_components")
        if relative == Path("__init__.py"):
            continue
        if not (
            root / "custom_components" / relative.parts[0] / "manifest.json"
        ).is_file():
            errors.append(f"Missing manifest for {source.relative_to(root)}")
    requirements = root / "requirements-ha-test.txt"
    pins = requirements.read_text(encoding="utf-8") if requirements.exists() else ""
    if not re.search(r"(?m)^pytest-homeassistant-custom-component==[^\s#]+\s*$", pins):
        errors.append(
            "Pin pytest-homeassistant-custom-component in requirements-ha-test.txt."
        )
    if not list(root.glob("tests/integration/test_*.py")):
        errors.append("Add real HA tests in tests/integration/test_*.py.")
    return True, errors


def main() -> int:
    """Return nonzero on invalid targets or an incomplete integration test setup."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    has_integration, errors = check_integration(root)
    errors.extend(check_links(root))
    for error in errors:
        print(error)
    if errors:
        return 1
    if args.github_output:
        with args.github_output.open("a", encoding="utf-8") as output:
            output.write(f"has_integration={str(has_integration).lower()}\n")
    stage = "HA integration" if has_integration else "documentation/tooling only"
    print(f"Repository checks passed ({stage}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
