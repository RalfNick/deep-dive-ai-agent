from collections import Counter
from dataclasses import replace
import pytest
from chapter16.feedback import admit_feedback
from chapter16.serialization import canonical_bytes

def test_dispositions_sensitive_lineage(lab):
    rows = admit_feedback(lab.feedback, lab.sources)
    by_id = {r.feedback_id: r for r in rows}
    assert Counter(r.disposition for r in rows) == {"accepted": 6, "quarantined": 3, "merged": 1, "unknown": 2}
    assert by_id["F02"].source_refs == ("F01", "F02")
    assert by_id["F09"].source_sensitive is True
    assert b"DEMO-SENSITIVE-001" not in canonical_bytes(rows)
    sanitized = replace(lab.feedback[8], payload=by_id["F09"].sanitized_payload, source_sensitive=True)
    assert admit_feedback((sanitized,), lab.sources)[0].disposition == "quarantined"

@pytest.mark.parametrize("change", [{"source_role":"administrator"}, {"permission":False}, {"purpose":"hidden_evaluation"}])
def test_payload_cannot_promote_authority(lab, change):
    record = replace(lab.feedback[0], **change, payload={"trusted":True})
    assert admit_feedback((record,), lab.sources)[0].disposition == "quarantined"

def test_source_revocation_scope_and_duplicate_integrity(lab):
    source = replace(lab.sources[0], revoked=True)
    assert admit_feedback((lab.feedback[0],), (source,))[0].disposition == "quarantined"
    wide = replace(lab.feedback[7], scope=replace(lab.feedback[7].scope, user_id=None))
    assert admit_feedback((wide,), lab.sources)[0].disposition == "quarantined"
    fake = replace(lab.feedback[1], payload={"selection":"all_tenants"})
    assert admit_feedback((lab.feedback[0], fake), lab.sources)[1].disposition == "unknown"
