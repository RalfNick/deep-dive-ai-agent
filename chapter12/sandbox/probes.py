"""Code executed inside the sandbox by a future authorized integration probe."""
from __future__ import annotations

import json
import os
from pathlib import Path


def facts() -> dict[str, object]:
    return {
        "uid": os.getuid() if hasattr(os, "getuid") else None,
        "root_writable": os.access("/", os.W_OK),
        "credentials_present": any(key.endswith("_API_KEY") for key in os.environ),
        "control_socket_present": Path("/var/run/docker.sock").exists(),
    }


if __name__ == "__main__":
    print(json.dumps(facts(), sort_keys=True))
