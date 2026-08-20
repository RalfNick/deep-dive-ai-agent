from chapter5.context.trace import canonical_json, stable_digest


def serialized_bytes(value: object) -> int:
    return len(canonical_json(value).encode("utf-8"))
