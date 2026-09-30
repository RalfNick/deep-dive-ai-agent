from decimal import Decimal

import pytest

from chapter17.chart import observe_svg_chart, decide_chart
from chapter17.contracts import make_media_ref
from chapter17.fixtures import load_fixture


def observed(name="chart-base.svg", data=None):
    data = load_fixture(name) if data is None else data
    ref = make_media_ref("svg", name, data, name, 0, "book")
    return observe_svg_chart(data, ref)


@pytest.mark.parametrize("name", ["chart-base.svg", "chart-truncated-axis.svg"])
def test_80_to_100_yields_25_percent_with_two_sources(name):
    observation = observed(name)
    assert dict(observation.values) == {"Jan": Decimal("80"), "Feb": Decimal("100")}
    decision = decide_chart(observation, load_fixture("chart-values.csv"))
    assert decision.status == "answer"
    assert decision.value == Decimal("25")
    assert decision.unit == "percent"
    assert name in decision.evidence_ids
    assert any(item.startswith("csv:") for item in decision.evidence_ids)
    assert any("80" in reason and "100" in reason for reason in decision.reasons)


def test_truncated_axis_70_still_yields_25():
    assert decide_chart(observed("chart-truncated-axis.svg"), load_fixture("chart-values.csv")).value == 25


@pytest.mark.parametrize("old,new", [
    (b'<text class="tick" x="45" y="300">0</text>', b""),
    (b'<text class="legend" x="330" y="30">', b'<text class="legend" x="330" y="30">other</text><text class="legend" x="330" y="30">'),
    (b'<svg ', b'<!DOCTYPE svg SYSTEM "https://example.invalid/secret"><svg '),
    (b'</svg>', b'<image href="https://example.com/a.png"/></svg>'),
    (b'<rect class="bar"', b'<rect transform="scale(2)" class="bar"'),
])
def test_malformed_or_unsafe_chart_is_unknown(old, new):
    svg = load_fixture("chart-base.svg").replace(old, new, 1)
    assert decide_chart(observed(data=svg), load_fixture("chart-values.csv")).status == "unknown"


def test_zero_denominator_and_source_mismatch_are_unknown():
    csv = b"month,unit,count\nJan,\xe5\x8d\x83\xe4\xbb\xb6,0\nFeb,\xe5\x8d\x83\xe4\xbb\xb6,100\n"
    assert decide_chart(observed(), csv).status == "unknown"
    assert decide_chart(observed(), load_fixture("chart-values.csv").replace(b"80", b"81")).status == "unknown"


@pytest.mark.parametrize("csv", [
    b"month,unit,count\nJan,units,80\nJan,units,90\nFeb,units,100\n",
    "month,unit,count\nJan,千件,80\nFeb,件,100\n".encode(),
])
def test_ambiguous_csv_is_unknown(csv):
    assert decide_chart(observed(), csv).status == "unknown"


def test_utf8_bom_csv_is_accepted():
    csv = b"\xef\xbb\xbf" + load_fixture("chart-values.csv")
    assert decide_chart(observed(), csv).value == Decimal("25")
