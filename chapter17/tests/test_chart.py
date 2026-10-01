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


def test_utf16_entity_document_is_rejected_before_xml_parse():
    source = load_fixture("chart-base.svg").decode("utf-8")
    source = source.replace('<text class="tick" x="45" y="300">0</text>',
                            '<text class="tick" x="45" y="300">&zero;</text>')
    source = '<!DOCTYPE svg [<!ENTITY zero "0">]>' + source
    assert observed(data=source.encode("utf-16")).issues


def test_nested_svg_viewport_cannot_be_flattened_into_root_coordinates():
    source = load_fixture("chart-base.svg")
    start = b'<rect class="bar" x="140" y="140" width="70" height="160" fill="#4c8ccc"/>'
    wrapped = b'<svg width="520" height="380" viewBox="0 0 1040 760">' + start + b'</svg>'
    assert observed(data=source.replace(start, wrapped)).issues


def test_nested_allowed_element_is_not_flattened_either():
    source = load_fixture("chart-base.svg")
    bar = b'<rect class="bar" x="140" y="140" width="70" height="160" fill="#4c8ccc"/>'
    nested = b'<text x="0" y="0">' + bar + b'</text>'
    assert observed(data=source.replace(bar, nested)).issues


def test_duplicate_csv_header_is_unknown_before_dictreader_overwrites_it():
    data = "month,unit,count,count\nJan,千件,999,80\nFeb,千件,999,100\n".encode()
    assert decide_chart(observed(), data).status == "unknown"


def test_zero_denominator_branch_is_reached_with_matching_chart_and_csv():
    chart = load_fixture("chart-base.svg")
    chart = chart.replace(b'<text class="tick" x="45" y="300">0</text>',
                          b'<text class="tick" x="35" y="300">-100</text>')
    chart = chart.replace(b'<rect class="bar" x="140" y="140" width="70" height="160"',
                          b'<rect class="bar" x="140" y="200" width="70" height="100"')
    csv = "month,unit,count\nJan,千件,0\nFeb,千件,100\n".encode()
    observation = observed(data=chart)
    assert dict(observation.values) == {"Jan": Decimal(0), "Feb": Decimal(100)}
    assert decide_chart(observation, csv).reasons == ("zero-denominator",)


def test_expired_chart_requires_refresh_before_arithmetic():
    from chapter17.chart import decide_chart_at

    observation = observed()
    decision = decide_chart_at(observation, load_fixture("chart-values.csv"),
                               now_ms=5000, max_age_ms=2000)
    assert decision.status == "refresh"
    assert "stale" in decision.reasons[0]


@pytest.mark.parametrize("old,new", [
    (b'fill="#4c8ccc"', b'fill="none"'),
    (b'fill="#4c8ccc"', b'fill="#ffffff"'),
    (b'fill="#4c8ccc"', b'fill="rgba(0,0,0,0)"'),
    (b'viewBox="0 0 520 380"', b'viewBox="0 0 520 50"'),
    (b'width="520" height="380"', b'width="520" height="50"'),
    (b'class="unit" x="24" y="30"', b'class="unit" x="24" y="-30"'),
    (b'</svg>', b'<rect x="80" y="80" width="400" height="260" fill="#ffffff"/></svg>'),
])
def test_hidden_cropped_or_overlaid_chart_cannot_be_called_visible(old, new):
    svg = load_fixture("chart-base.svg").replace(old, new, 1)
    decision = decide_chart(observed(data=svg), load_fixture("chart-values.csv"))
    assert decision.status == "unknown"
    assert decision.value is None
