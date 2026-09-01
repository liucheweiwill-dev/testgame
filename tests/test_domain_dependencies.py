import ast
import sys
from pathlib import Path


def _repository_root() -> Path:
    test_path = Path(__file__).resolve()
    for parent in test_path.parents:
        if parent.name == "mutants":
            return parent.parent
    return test_path.parents[1]


REPOSITORY_ROOT = _repository_root()
DOMAIN_ROOT = REPOSITORY_ROOT / "src" / "domain"


def test_domain_imports_only_standard_library() -> None:
    assert DOMAIN_ROOT.is_dir(), (
        f"Repository root resolution failed: resolved {REPOSITORY_ROOT}; "
        f"expected {DOMAIN_ROOT} to be an existing src/domain directory"
    )

    module_paths = sorted(DOMAIN_ROOT.rglob("*.py"))
    assert module_paths, (
        f"Repository root resolution failed: resolved {REPOSITORY_ROOT}; "
        f"found no Python modules under {DOMAIN_ROOT}"
    )

    violations: list[str] = []

    for module_path in module_paths:
        tree = ast.parse(
            module_path.read_text(encoding="utf-8"), filename=str(module_path)
        )
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_names = (alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                imported_names = (node.module,)
            else:
                continue

            for imported_name in imported_names:
                top_level_name = imported_name.partition(".")[0]
                if (
                    top_level_name not in sys.stdlib_module_names
                    and top_level_name != DOMAIN_ROOT.name
                ):
                    relative_path = module_path.relative_to(DOMAIN_ROOT.parent)
                    violations.append(f"{relative_path}:{node.lineno}: {imported_name}")

    assert not violations, (
        "Domain modules import non-standard-library names:\n" + "\n".join(violations)
    )
