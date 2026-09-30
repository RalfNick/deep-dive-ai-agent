"""A deliberately narrow, auditable parser for this book's authored SVG bars.

This is *not* OCR. Unknown SVG grammar is a reason to abstain, not to guess.
"""

from __future__ import annotations

import csv
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from io import StringIO
import xml.etree.ElementTree as ET

from .contracts import Decision, MediaRef, Observation

_SVG = "{http://www.w3.org/2000/svg}"
_ALLOWED = {
    "svg": {"width", "height", "viewBox"},
    "text": {"class", "x", "y"},
    "rect": {"class", "x", "y", "width", "height", "fill"},
    "line": {"x1", "x2", "y1", "y2", "stroke"},
}


def _unknown(media: MediaRef, reason: str) -> Observation:
    return Observation(media, "svg-geometry", "plot", (), None, (reason,))


def observe_svg_chart(svg: bytes, media: MediaRef) -> Observation:
    try:
        source = svg.decode("utf-8-sig")
    except UnicodeError:
        return _unknown(media, "unsupported-svg-encoding")
    upper = source.upper()
    if any(token in upper for token in ("<!DOCTYPE", "<!ENTITY", "<SCRIPT", "<?XML-STYLESHEET")):
        return _unknown(media, "unsafe-svg-declaration")
    try:
        root = ET.fromstring(source)
        if root.tag != _SVG + "svg":
            return _unknown(media, "unsupported-svg-root")
        if any(len(child) for child in root):
            return _unknown(media, "nested-svg-coordinate-space")
        for element in root.iter():
            if not element.tag.startswith(_SVG):
                return _unknown(media, "unsupported-svg-namespace")
            tag = element.tag[len(_SVG):]
            if tag == "svg" and element is not root:
                return _unknown(media, "nested-svg-coordinate-space")
            if tag not in _ALLOWED or set(element.attrib) - _ALLOWED[tag]:
                return _unknown(media, "unsupported-svg-element-or-attribute")
        def nodes(name: str, cls: str):
            return [e for e in root.iter(_SVG + name) if e.get("class") == cls]
        units = nodes("text", "unit")
        legends = nodes("text", "legend")
        ticks = nodes("text", "tick")
        bars = nodes("rect", "bar")
        months = nodes("text", "month")
        if len(units) != 1 or not (units[0].text or "").strip():
            return _unknown(media, "missing-unit")
        if len(legends) != 1 or not (legends[0].text or "").strip():
            return _unknown(media, "ambiguous-legend")
        if len(ticks) != 2 or len(bars) != 2 or len(months) != 2:
            return _unknown(media, "incomplete-or-ambiguous-plot")
        tick_points = [(Decimal(e.get("y", "")), Decimal((e.text or "").strip())) for e in ticks]
        (y1, v1), (y2, v2) = tick_points
        if y1 == y2 or v1 == v2 or (y1 - y2) * (v1 - v2) >= 0:
            return _unknown(media, "invalid-linear-axis")
        baseline_y, baseline_value = max(tick_points)
        month_points = [(Decimal(e.get("x", "")), (e.text or "").strip()) for e in months]
        if any(not label for _, label in month_points) or len(set(label for _, label in month_points)) != 2:
            return _unknown(media, "ambiguous-months")
        result = []
        for bar in bars:
            x = Decimal(bar.get("x", ""))
            width = Decimal(bar.get("width", ""))
            top = Decimal(bar.get("y", ""))
            height = Decimal(bar.get("height", ""))
            if width <= 0 or height <= 0 or top + height != baseline_y:
                return _unknown(media, "bar-does-not-meet-axis-baseline")
            labels = [label for mx, label in month_points if x <= mx <= x + width]
            if len(labels) != 1:
                return _unknown(media, "bar-month-association-unknown")
            value = v1 + (top - y1) * (v2 - v1) / (y2 - y1)
            if not value.is_finite():
                return _unknown(media, "non-finite-value")
            result.append((labels[0], value))
        if len(set(k for k, _ in result)) != 2:
            return _unknown(media, "duplicate-bar-month")
        return Observation(media, "svg-geometry", "plot", tuple(result),
                           (units[0].text or "").strip(), ())
    except (ET.ParseError, InvalidOperation, ValueError, ZeroDivisionError, TypeError):
        return _unknown(media, "unparseable-svg-geometry")


def decide_chart(observation: Observation, csv_bytes: bytes) -> Decision:
    source_ids = (observation.media_ref.source_id, "csv:" + sha256(csv_bytes).hexdigest())
    def abstain(reason: str) -> Decision:
        return Decision("unknown", None, None, (reason,), source_ids)
    if observation.issues:
        return abstain("svg:" + ",".join(observation.issues))
    try:
        reader = csv.DictReader(StringIO(csv_bytes.decode("utf-8-sig"), newline=""), strict=True)
        if reader.fieldnames != ["month", "unit", "count"]:
            return abstain("csv-columns-or-duplicate-header")
        table = list(reader)
        if len(table) != 2 or any(set(row) != {"month", "unit", "count"} for row in table):
            return abstain("csv-columns-or-row-count")
        data = {}
        for row in table:
            if row["month"] in data or not row["month"] or row["unit"] != observation.unit:
                return abstain("csv-duplicate-month-or-mixed-unit")
            data[row["month"]] = Decimal(row["count"])
        seen = dict(observation.values)
        if set(seen) != {"Jan", "Feb"} or set(data) != set(seen):
            return abstain("missing-or-unexpected-month")
        if any(not data[m].is_finite() or data[m] != seen[m] for m in data):
            return abstain("chart-csv-conflict")
        if data["Jan"] == 0:
            return abstain("zero-denominator")
        result = (data["Feb"] - data["Jan"]) / data["Jan"] * Decimal(100)
        reason = f"({data['Feb']}-{data['Jan']})/{data['Jan']}*100={result}"
        return Decision("answer", result, "percent", (reason,), source_ids)
    except (UnicodeError, csv.Error, InvalidOperation, ValueError, TypeError, ZeroDivisionError):
        return abstain("unparseable-csv")


def decide_chart_at(observation: Observation, csv_bytes: bytes, *,
                    now_ms: int, max_age_ms: int) -> Decision:
    """Apply a source-time gate before trusting otherwise valid chart arithmetic."""
    captured = observation.media_ref.captured_at_ms
    if now_ms < captured or max_age_ms < 0 or now_ms - captured > max_age_ms:
        return Decision("refresh", None, None, ("chart-source-stale-or-future",),
                        (observation.media_ref.source_id,))
    return decide_chart(observation, csv_bytes)
