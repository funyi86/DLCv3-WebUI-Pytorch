#!/usr/bin/env python3
import ast
import os
from pathlib import Path
from typing import Dict, List, Set, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]


def list_py_files(base: Path) -> List[Path]:
    files = []
    for root, _dirs, fs in os.walk(base):
        # Skip cache and virtualenv-like dirs
        if "__pycache__" in root or ".venv" in root or "venv" in root:
            continue
        for f in fs:
            if f.endswith(".py"):
                files.append(Path(root) / f)
    return files


def read_ast(p: Path):
    try:
        src = p.read_text(encoding="utf-8")
    except Exception:
        return None
    try:
        return ast.parse(src, filename=str(p))
    except SyntaxError:
        return None


def collect_info(py_files: List[Path]):
    # Maps
    module_imports: Dict[str, Set[str]] = {}
    module_defs: Dict[str, Set[str]] = {}
    name_usages_by_module: Dict[str, Set[str]] = {}

    for file in py_files:
        mod = str(file.relative_to(REPO_ROOT))
        tree = read_ast(file)
        if tree is None:
            continue

        imports: Set[str] = set()
        defs: Set[str] = set()
        uses: Set[str] = set()

        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    for n in node.names:
                        if n.name:
                            imports.add(n.name)
                else:  # ImportFrom
                    modname = node.module or ""
                    if modname:
                        imports.add(modname)
                    for n in node.names:
                        if n.name:
                            # Also count imported symbol names as usage
                            uses.add(n.name)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                # Only top-level definitions
                if isinstance(getattr(node, "parent", None), ast.Module) or not hasattr(node, "parent"):
                    defs.add(node.name)
            elif isinstance(node, ast.Assign):
                # Collect simple constant/var names at module level
                if isinstance(getattr(node, "parent", None), ast.Module) or not hasattr(node, "parent"):
                    for t in node.targets:
                        if isinstance(t, ast.Name):
                            defs.add(t.id)
            elif isinstance(node, ast.Name):
                if isinstance(node.ctx, ast.Load):
                    uses.add(node.id)
            elif isinstance(node, ast.Attribute):
                # Attribute access: record attr name (best-effort)
                if isinstance(getattr(node, "ctx", None), ast.Load):
                    uses.add(node.attr)

        module_imports[mod] = imports
        module_defs[mod] = defs
        name_usages_by_module[mod] = uses

    return module_imports, module_defs, name_usages_by_module


def annotate_parents(tree: ast.AST):
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            setattr(child, "parent", node)


def to_dotted_module(p: Path) -> Tuple[str, str]:
    rel = p.relative_to(REPO_ROOT)
    parts = rel.with_suffix("").parts
    if p.name == "__init__.py":
        # __init__.py represents the package; do not include __init__ in dotted name
        dotted = ".".join(parts[:-1])
        pkg = dotted
    else:
        dotted = ".".join(parts)
        pkg = ".".join(parts[:-1]) if len(parts) > 1 else ""
    return dotted, pkg


def resolve_relative_import(base_pkg: str, level: int, module: str) -> str:
    # Trim packages according to level
    pkgs = base_pkg.split(".") if base_pkg else []
    trimmed = pkgs[: max(0, len(pkgs) - level + 1)] if level > 0 else pkgs
    if module:
        trimmed.append(module)
    return ".".join([p for p in trimmed if p])


def collect_with_parents(py_files: List[Path]):
    module_imports: Dict[str, Set[str]] = {}
    module_defs: Dict[str, Set[str]] = {}
    name_usages_by_module: Dict[str, Set[str]] = {}

    for file in py_files:
        mod = str(file.relative_to(REPO_ROOT))
        dotted_mod, dotted_pkg = to_dotted_module(file)
        tree = read_ast(file)
        if tree is None:
            continue
        annotate_parents(tree)

        imports: Set[str] = set()
        defs: Set[str] = set()
        uses: Set[str] = set()

        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    for n in node.names:
                        if n.name:
                            imports.add(n.name)
                else:
                    modname = node.module or ""
                    level = getattr(node, "level", 0) or 0
                    if level > 0:
                        resolved = resolve_relative_import(dotted_pkg, level, modname)
                        if resolved:
                            imports.add(resolved)
                    else:
                        if modname:
                            imports.add(modname)
                    for n in node.names:
                        if n.name:
                            uses.add(n.name)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if isinstance(getattr(node, "parent", None), ast.Module):
                    defs.add(node.name)
            elif isinstance(node, ast.Assign):
                if isinstance(getattr(node, "parent", None), ast.Module):
                    for t in node.targets:
                        if isinstance(t, ast.Name):
                            defs.add(t.id)
            elif isinstance(node, ast.Name):
                if isinstance(node.ctx, ast.Load):
                    uses.add(node.id)
            elif isinstance(node, ast.Attribute):
                if isinstance(getattr(node, "ctx", None), ast.Load):
                    uses.add(node.attr)

        module_imports[mod] = imports
        module_defs[mod] = defs
        name_usages_by_module[mod] = uses

    return module_imports, module_defs, name_usages_by_module


def main():
    py_files = list_py_files(REPO_ROOT)
    # Focus on project code only
    py_files = [p for p in py_files if not any(part in {".venv", "venv"} for part in p.parts)]

    module_imports, module_defs, name_usages_by_module = collect_with_parents(py_files)

    # Roots: entrypoints executed by Streamlit
    roots: Set[str] = set()
    for f in py_files:
        rel = str(f.relative_to(REPO_ROOT))
        if rel == "Home.py" or rel.startswith("pages/"):
            roots.add(rel)

    # Determine module usage based on imports
    imported_by: Dict[str, Set[str]] = {}
    for mod, imports in module_imports.items():
        for imp in imports:
            imported_by.setdefault(imp, set()).add(mod)

    # Compute unused modules: those under src/** that are not imported by anything,
    # and are not roots themselves (roots are only Home.py and pages/*)
    unused_modules: List[str] = []
    for mod in module_imports.keys():
        if mod.startswith("src/") and mod.endswith(".py"):
            if os.path.basename(mod) == "__init__.py":
                continue
            # Consider both dotted and path-like forms for imports
            path_without_py = mod[:-3].replace("/", ".")
            imported_anywhere = False
            for key in (mod, path_without_py):
                if key in imported_by and len(imported_by[key]) > 0:
                    imported_anywhere = True
                    break
            if not imported_anywhere:
                unused_modules.append(mod)

    # Compute potentially unused top-level symbols
    # Build a global usage set of names across all modules
    all_usages: Set[str] = set()
    for uses in name_usages_by_module.values():
        all_usages.update(uses)

    unused_symbols: Dict[str, Set[str]] = {}
    for mod, defs in module_defs.items():
        if not mod.startswith("src/"):
            continue
        unused = set()
        for d in defs:
            # Skip dunder and constants often used by frameworks indirectly
            if d.startswith("__") and d.endswith("__"):
                continue
            if d in {"__all__"}:
                continue
            if d not in all_usages:
                unused.add(d)
        if unused:
            unused_symbols[mod] = unused

    # Output report
    print("== Import Graph Summary ==")
    print(f"Total Python files: {len(py_files)}")
    print(f"Roots (executed): {len(roots)} -> " + ", ".join(sorted(roots)))
    print()
    print("== Potentially Unused Modules (under src/) ==")
    if unused_modules:
        for m in sorted(unused_modules):
            print(f"- {m}")
    else:
        print("- None detected")
    print()
    print("== Potentially Unused Top-level Symbols (under src/) ==")
    if unused_symbols:
        for mod, names in sorted(unused_symbols.items()):
            snippet = ", ".join(sorted(names))
            print(f"- {mod}: {snippet}")
    else:
        print("- None detected")
    print()
    print("Note: Static analysis; Streamlit callbacks, dynamic imports, and reflection may hide valid usages.")


if __name__ == "__main__":
    main()
