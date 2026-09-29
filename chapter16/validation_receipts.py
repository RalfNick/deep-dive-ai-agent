"""Trusted in-process call order, NOT a durable timestamp/signature service.

Receipts are deliberately outside stable reports. A hash or a future-labelled
clock cannot prove that evaluate_pair actually ran after a release stop.
Keep strong object references: round-tripping JSON does not mint authority,
and separate deterministic rehearsals must not share a hash-keyed stop epoch.
"""
_sequence = 0
_validations = {}
_interruptions = {}


def _remember(value, registry):
    global _sequence
    _sequence += 1
    registry[id(value)] = (value, _sequence)


def _record_validation(evidence):
    _remember(evidence, _validations)


def _record_interruption(record):
    _remember(record, _interruptions)


def validated_after(evidence, interruptions):
    issued = _validations.get(id(evidence))
    if issued is None or issued[0] is not evidence:
        return False
    for record in interruptions:
        stopped = _interruptions.get(id(record))
        if stopped is None or stopped[0] is not record or issued[1] <= stopped[1]:
            return False
    return True
