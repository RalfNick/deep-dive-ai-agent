"""Reserve fresh output, reject link-like parents, never replace evidence."""
import hashlib
import re
import stat
from pathlib import Path
from .serialization import canonical_bytes, plain

def is_linklike(path):
    if path.is_symlink():
        return True
    try:
        return bool(getattr(path.lstat(), "st_file_attributes", 0) & getattr(stat,"FILE_ATTRIBUTE_REPARSE_POINT",1024))
    except FileNotFoundError:
        return False

def safe_path(destination, *, root):
    root = Path(root).absolute()
    path = Path(destination)
    path = path.absolute() if path.is_absolute() else (root / path).absolute()
    try:
        relative = path.relative_to(root)
    except ValueError as exc:
        raise ValueError("outside project output") from exc
    if ".." in relative.parts or len(relative.parts) < 2 or relative.parts[:2] not in (("chapter16",".runs"),("chapter16","reports")):
        raise ValueError("output prefix denied")
    for parent in (path, *path.parents):
        if is_linklike(parent):
            raise ValueError("link/reparse parent denied")
        if parent == root:
            break
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("resolved output outside project")
    return path

def safe_data(value):
    def inspect(v):
        if isinstance(v, dict):
            for item in v.values():
                inspect(item)
        elif isinstance(v,list):
            for item in v:
                inspect(item)
        elif isinstance(v,str) and (re.search(r"[A-Za-z]:[\\/]|file://",v) or v.startswith("/")):
            raise ValueError("host path in stable output")
    inspect(plain(value))
    return canonical_bytes(value)

def exclusive_bytes(path, data):
    with path.open("xb") as stream:
        stream.write(data)

def write_new_json(value, destination, *, root):
    data = safe_data(value)
    path = safe_path(destination,root=root)
    if path.suffix != ".json":
        raise ValueError("JSON output required")
    path.parent.mkdir(parents=True,exist_ok=True)
    safe_path(path,root=root)
    exclusive_bytes(path,data)
    return path

def write_report_bundle(report, destination, *, root, exercises=None):
    from .experiments import validate_report
    validate_report(report)
    path = safe_path(destination,root=root)
    payload = {f"group-{g['group']}.json":safe_data(g) for g in report.groups}
    payload["improvement-report.json"] = safe_data(report)
    text = "# 第16章规范报告\n\n" + "\n".join(f"- {k}: {v}" for k,v in sorted(report.summary.items())) + "\n\n"
    text += "\n".join("- " + limit for limit in report.limits) + "\n"
    payload["improvement-report.md"] = text.encode("utf-8")
    if exercises is not None:
        payload["exercise-results.json"] = safe_data(exercises)
    manifest = {"schema_version":"chapter16.artifact-manifest.v1","files":[
        {"name":name,"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest()} for name,data in sorted(payload.items())]}
    payload["manifest.json"] = canonical_bytes(manifest)
    path.parent.mkdir(parents=True,exist_ok=True)
    safe_path(path,root=root)
    path.mkdir()  # atomic reservation; even an existing empty directory is evidence ownership.
    try:
        for name,data in payload.items():
            exclusive_bytes(path/name,data)
    except OSError:
        exclusive_bytes(path/"PARTIAL-OUTPUT.txt",b"Partial output: generation failed; preserved, never auto-replaced.\n")
        raise
    return tuple(path/name for name in payload)
