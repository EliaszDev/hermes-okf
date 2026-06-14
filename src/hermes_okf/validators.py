"""OKF conformance validators.

Check that a bundle (or individual file) conforms to the OKF v0.1 spec.
Minimal enforcement: only ``type`` frontmatter field is required.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from hermes_okf.bundle import OKFBundle


class OKFValidationError:
    """A single validation error with file location and message."""

    def __init__(self, file: str, message: str, line: int | None = None) -> None:
        self.file = file
        self.message = message
        self.line = line

    def __repr__(self) -> str:
        if self.line:
            return f"OKFValidationError({self.file}:{self.line} -> {self.message})"
        return f"OKFValidationError({self.file} -> {self.message})"


class OKFValidator:
    """Validate OKF bundle conformance."""

    REQUIRED_RESERVED_FILES = ("index.md", "log.md")

    def __init__(self, bundle: OKFBundle) -> None:
        self.bundle = bundle
        self.errors: list[OKFValidationError] = []

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    def validate(self) -> list[OKFValidationError]:
        """Run full validation and return a list of errors."""
        self.errors = []
        self._check_reserved_files()
        self._check_all_concepts()
        return self.errors

    def is_valid(self) -> bool:
        """Run validation and return ``True`` if no errors found."""
        return len(self.validate()) == 0

    def _check_reserved_files(self) -> None:
        for name in self.REQUIRED_RESERVED_FILES:
            if not (self.bundle.root / name).exists():
                self.errors.append(
                    OKFValidationError(name, f"Missing required reserved file: {name}")
                )

    def _check_all_concepts(self) -> None:
        for md_file in self.bundle.root.rglob("*.md"):
            if md_file.name in self.REQUIRED_RESERVED_FILES:
                continue
            rel = str(md_file.relative_to(self.bundle.root))
            self._check_file(md_file, rel)

    def _check_file(self, file_path: Path, rel_path: str) -> None:
        content = file_path.read_text(encoding="utf-8")

        if not content.startswith("---"):
            self.errors.append(
                OKFValidationError(rel_path, "Missing YAML frontmatter (must start with ---)")
            )
            return

        parts = content.split("---", 2)
        if len(parts) < 3:
            self.errors.append(
                OKFValidationError(rel_path, "Malformed frontmatter: missing closing ---")
            )
            return

        try:
            metadata = yaml.safe_load(parts[1]) or {}
        except yaml.YAMLError as exc:
            self.errors.append(OKFValidationError(rel_path, f"Invalid YAML frontmatter: {exc}"))
            return

        if not isinstance(metadata, dict):
            self.errors.append(
                OKFValidationError(rel_path, "Frontmatter must be a YAML mapping (dict)")
            )
            return

        if "type" not in metadata:
            self.errors.append(
                OKFValidationError(rel_path, "Missing required 'type' field in frontmatter", line=1)
            )

    # ------------------------------------------------------------------
    # Static helpers
    # ------------------------------------------------------------------
    @staticmethod
    def validate_file(path: str | Path) -> list[OKFValidationError]:
        """Validate a single ``.md`` file without a full bundle context."""
        errors: list[OKFValidationError] = []
        file_path = Path(path)
        if not file_path.exists():
            errors.append(OKFValidationError(str(file_path), "File does not exist"))
            return errors

        content = file_path.read_text(encoding="utf-8")
        if not content.startswith("---"):
            errors.append(OKFValidationError(str(file_path), "Missing YAML frontmatter"))
            return errors

        parts = content.split("---", 2)
        if len(parts) < 3:
            errors.append(OKFValidationError(str(file_path), "Malformed frontmatter"))
            return errors

        try:
            metadata = yaml.safe_load(parts[1]) or {}
        except yaml.YAMLError as exc:
            errors.append(OKFValidationError(str(file_path), f"Invalid YAML: {exc}"))
            return errors

        if not isinstance(metadata, dict) or "type" not in metadata:
            errors.append(OKFValidationError(str(file_path), "Missing required 'type' field"))

        return errors

    @staticmethod
    def quick_check(path: str | Path) -> bool:
        """Return ``True`` if the file passes OKF validation."""
        return len(OKFValidator.validate_file(path)) == 0
