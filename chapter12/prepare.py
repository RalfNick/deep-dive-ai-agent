"""Create a fresh fixture; control data lives outside the model's work directory."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil

FIXTURE = Path(__file__).parent / 'fixtures' / 'link-checker'


def control_path(root: Path) -> Path:
    return root.parent / f'.{root.name}.agent'


def create_workspace(destination: Path) -> Path:
    from .tools import workspace_manifest

    destination = destination.absolute()
    control = control_path(destination)
    if destination.exists() or destination.is_symlink() or control.exists():
        raise FileExistsError('workspace_exists')
    destination.parent.mkdir(parents=True, exist_ok=True)
    # The shipped fixture contains no symlinks, VCS hooks, or user-owned content.
    shutil.copytree(FIXTURE, destination, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    control.mkdir()
    baseline = {'schema_version': 1, 'files': workspace_manifest(destination),
        'text': {p.relative_to(destination).as_posix(): p.read_text(encoding='utf-8')
                 for p in sorted(destination.rglob('*')) if p.is_file()}}
    (control / 'baseline.json').write_text(json.dumps(baseline, ensure_ascii=False,
        sort_keys=True), encoding='utf-8', newline='\n')
    return destination


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create a new teaching repository, never reset it.')
    parser.add_argument('destination', type=Path)
    print(create_workspace(parser.parse_args().destination))
