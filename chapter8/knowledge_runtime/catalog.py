from __future__ import annotations

import json
from pathlib import Path

from chapter8.knowledge_runtime.contracts import (
    AnswerStatus,
    DocumentStatus,
    KnowledgeDocument,
    QuestionCase,
    RetrievalQuery,
    TrustLevel,
    Visibility,
)


_METADATA_FIELDS = {
    "document_id",
    "title",
    "version_min",
    "version_max",
    "valid_from",
    "valid_until",
    "allowed_roles",
    "source_type",
    "status",
    "visibility",
    "trust",
    "fact_ids",
    "content_digest",
}
_CASE_FIELDS = {
    "case_id",
    "query",
    "relevant_document_ids",
    "relevant_chunk_ids",
    "required_fact_ids",
    "expected_claims",
    "expected_status",
}
_QUERY_FIELDS = {"text", "role", "target_version", "now", "top_k", "candidate_k"}


def _require_exact_fields(payload: dict[str, object], expected: set[str], reason: str) -> None:
    unknown = sorted(set(payload) - expected)
    if unknown:
        raise ValueError(f"{reason}:{','.join(unknown)}")
    missing = sorted(expected - set(payload))
    if missing:
        raise ValueError(f"missing_metadata_fields:{','.join(missing)}")


def load_documents(root: Path) -> tuple[KnowledgeDocument, ...]:
    markdown = {path.stem: path for path in root.glob("*.md")}
    metadata = {path.name[: -len(".meta.json")]: path for path in root.glob("*.meta.json")}
    if set(markdown) != set(metadata):
        mismatched = sorted(set(markdown) ^ set(metadata))
        raise ValueError(f"unpaired_fixture:{','.join(mismatched)}")

    documents: list[KnowledgeDocument] = []
    seen: set[str] = set()
    for stem in sorted(markdown):
        raw = json.loads(metadata[stem].read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError(f"metadata_not_object:{stem}")
        _require_exact_fields(raw, _METADATA_FIELDS, "unknown_metadata_fields")
        if raw["document_id"] != stem:
            raise ValueError(f"document_id_filename_mismatch:{stem}")
        try:
            document = KnowledgeDocument(
                document_id=str(raw["document_id"]),
                title=str(raw["title"]),
                source_path=markdown[stem].name,
                version_min=str(raw["version_min"]),
                version_max=None if raw["version_max"] is None else str(raw["version_max"]),
                valid_from=str(raw["valid_from"]),
                valid_until=None if raw["valid_until"] is None else str(raw["valid_until"]),
                allowed_roles=tuple(str(role) for role in raw["allowed_roles"]),
                source_type=str(raw["source_type"]),
                status=DocumentStatus(str(raw["status"])),
                visibility=Visibility(str(raw["visibility"])),
                trust=TrustLevel(str(raw["trust"])),
                fact_ids=tuple(str(fact_id) for fact_id in raw["fact_ids"]),
                content=markdown[stem].read_text(encoding="utf-8"),
                content_digest=str(raw["content_digest"]),
            )
        except TypeError as error:
            raise ValueError(f"invalid_metadata_shape:{stem}") from error
        if document.document_id in seen:
            raise ValueError(f"duplicate_document_id:{document.document_id}")
        if document.visibility is Visibility.PUBLIC and "public" not in document.allowed_roles:
            raise ValueError(f"public_document_without_public_role:{document.document_id}")
        seen.add(document.document_id)
        documents.append(document)
    return tuple(documents)


def load_question_cases(path: Path) -> tuple[QuestionCase, ...]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or set(payload) != {"schema_version", "cases"}:
        raise ValueError("invalid_question_fixture")
    if payload["schema_version"] != 1 or not isinstance(payload["cases"], list):
        raise ValueError("unsupported_question_schema")

    cases: list[QuestionCase] = []
    seen: set[str] = set()
    for raw in payload["cases"]:
        if not isinstance(raw, dict):
            raise ValueError("question_case_not_object")
        _require_exact_fields(raw, _CASE_FIELDS, "unknown_question_case_fields")
        query_raw = raw["query"]
        if not isinstance(query_raw, dict):
            raise ValueError("question_query_not_object")
        _require_exact_fields(query_raw, _QUERY_FIELDS, "unknown_question_query_fields")
        query = RetrievalQuery(
            text=str(query_raw["text"]),
            role=str(query_raw["role"]),
            target_version=str(query_raw["target_version"]),
            now=str(query_raw["now"]),
            top_k=int(query_raw["top_k"]),
            candidate_k=int(query_raw["candidate_k"]),
        )
        case = QuestionCase(
            case_id=str(raw["case_id"]),
            query=query,
            relevant_document_ids=tuple(str(item) for item in raw["relevant_document_ids"]),
            relevant_chunk_ids=tuple(str(item) for item in raw["relevant_chunk_ids"]),
            required_fact_ids=tuple(str(item) for item in raw["required_fact_ids"]),
            expected_claims=tuple(str(item) for item in raw["expected_claims"]),
            expected_status=AnswerStatus(str(raw["expected_status"])),
        )
        if case.case_id in seen:
            raise ValueError(f"duplicate_case_id:{case.case_id}")
        seen.add(case.case_id)
        cases.append(case)
    return tuple(cases)


class KnowledgeCatalog:
    def __init__(self, documents: tuple[KnowledgeDocument, ...]) -> None:
        self._by_id = {document.document_id: document for document in documents}
        if len(self._by_id) != len(documents):
            raise ValueError("duplicate_document_id")
        self._withdrawn: set[str] = set()

    @property
    def all_documents(self) -> tuple[KnowledgeDocument, ...]:
        return tuple(self._by_id[key] for key in sorted(self._by_id))

    def _eligible(self, document: KnowledgeDocument, query: RetrievalQuery) -> bool:
        return (
            document.document_id not in self._withdrawn
            and document.status is DocumentStatus.ACTIVE
            and document.valid_at(query.now)
            and document.supports_version(query.target_version)
            and document.visible_to(query.role)
        )

    def current_documents(self, query: RetrievalQuery) -> tuple[KnowledgeDocument, ...]:
        return tuple(document for document in self.all_documents if self._eligible(document, query))

    def resolve_document(self, document_id: str, query: RetrievalQuery) -> KnowledgeDocument | None:
        document = self._by_id.get(document_id)
        if document is None or not self._eligible(document, query):
            return None
        return document

    def withdraw(self, document_id: str) -> None:
        if document_id not in self._by_id:
            raise KeyError(document_id)
        self._withdrawn.add(document_id)
