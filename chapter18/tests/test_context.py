from dataclasses import replace
from hashlib import sha256
from chapter18.tests.helpers import ROOT, packet


def test_context_is_only_sent_eligible_fragment_not_whole_document():
    from chapter18.context import assemble_context
    from chapter18.fixtures import load_sources
    sources = load_sources(ROOT)
    p = packet(allowed_sources=frozenset({"public-current", "restricted-current"}))
    context = assemble_context(p, sources)
    assert len(context.sent) == 1
    assert "内部额度" not in str(context.sent)
    assert context.sent_digest != next(s.digest for s in sources if s.source_id == "public-current")
    secret_changed = tuple(replace(s, text="different secret") if s.source_id == "restricted-current" else s for s in sources)
    assert assemble_context(p, secret_changed).sent_digest == context.sent_digest
    public_changed = tuple(replace(s, text="共享支持（更正）", digest=sha256("共享支持（更正）".encode()).hexdigest()) if s.source_id == "public-current" else s for s in sources)
    assert assemble_context(p, public_changed).sent_digest != context.sent_digest


def test_missing_input_is_not_replaced_by_all_document_text():
    from chapter18.context import assemble_context
    from chapter18.fixtures import load_sources
    context = assemble_context(packet(input_refs=("nonexistent",)), load_sources(ROOT))
    assert context.sent == ()
