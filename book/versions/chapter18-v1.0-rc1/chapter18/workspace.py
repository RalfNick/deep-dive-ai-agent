from hashlib import sha256
from pathlib import Path
import shutil
from .contracts import PatchProposal, TaskPacket, relative_path
from .fixtures import checked_path


def snapshot_workspace(root: Path, source: Path, destination: Path) -> Path:
    checked_path(root, source, prefixes=("chapter18/.runs",))
    dest = checked_path(root, destination, prefixes=("chapter18/.runs",), new=True)
    for path in source.rglob("*"):
        checked_path(root, path, prefixes=("chapter18/.runs",))
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, dest)
    return dest


def source_path(workspace: Path, path: str) -> Path:
    relative_path(path)
    return checked_path(workspace, Path(path), prefixes=("src",))


def propose_patch(packet: TaskPacket, workspace: Path, *, path: str, replacement: str,
                  proposal_id: str, action_id: str) -> PatchProposal:
    if path not in packet.allowed_writes or "propose" not in packet.allowed_tools:
        raise ValueError("proposal outside authorized scope")
    digest = sha256(source_path(workspace, path).read_bytes()).hexdigest()
    expected = dict(packet.base_hashes).get(path)
    if expected and expected != digest:
        raise ValueError("snapshot differs from task baseline")
    return PatchProposal(proposal_id, action_id, packet.task_id, path, digest, replacement)


def repair_text(text: str) -> str:
    old = "    return path\n"
    if text.count(old) != 1:
        raise ValueError("trusted repair precondition not found")
    return text.replace(old, "    return posixpath.normpath(posixpath.join(posixpath.dirname(document), path))\n")
