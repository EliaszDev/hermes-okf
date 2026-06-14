"""Tests for hermes_okf.validators."""

import tempfile
from pathlib import Path

from hermes_okf.bundle import OKFBundle
from hermes_okf.validators import OKFValidator


class TestValidators:
    def test_valid_bundle(self):
        with tempfile.TemporaryDirectory() as tmp:
            bundle = OKFBundle(tmp)
            bundle.write_concept("a", body="A", type="A")
            validator = OKFValidator(bundle)
            assert validator.is_valid()
            assert validator.validate() == []

    def test_missing_type(self):
        with tempfile.TemporaryDirectory() as tmp:
            bundle = OKFBundle(tmp)
            # Write a file with frontmatter but no type
            Path(tmp, "bad.md").write_text("---\ntitle: Bad\n---\n\nBody\n")
            validator = OKFValidator(bundle)
            errors = validator.validate()
            assert any("type" in e.message for e in errors)

    def test_missing_frontmatter(self):
        with tempfile.TemporaryDirectory() as tmp:
            bundle = OKFBundle(tmp)
            Path(tmp, "bad.md").write_text("No frontmatter here\n")
            validator = OKFValidator(bundle)
            errors = validator.validate()
            assert any("frontmatter" in e.message for e in errors)

    def test_static_validate_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            good = Path(tmp, "good.md")
            good.write_text("---\ntype: Test\n---\n\nBody\n")
            assert OKFValidator.quick_check(good)

            bad = Path(tmp, "bad.md")
            bad.write_text("No frontmatter\n")
            assert not OKFValidator.quick_check(bad)
