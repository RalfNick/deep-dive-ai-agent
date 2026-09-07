"""A descriptor catalog, not a model or a collection of live connectors."""
from dataclasses import dataclass, asdict
import hashlib
import json


def canonical(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def byte_size(value) -> int:
    return len(canonical(value).encode("utf-8"))


class CatalogError(ValueError):
    pass


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    keywords: tuple[str, ...]
    permission: str
    effect: str
    version: str = "1"

    def definition(self) -> dict:
        # Fixed fixture schema. Real adapters provide each tool's real schema.
        return {
            "name": self.name, "description": self.description,
            "version": self.version, "effect": self.effect,
            "parameters": {"type": "object", "properties": {
                "record_id": {"type": "string", "description": "调用者有权访问的业务记录编号"}},
                "required": ["record_id"], "additionalProperties": False},
        }

    @property
    def digest(self) -> str:
        return hashlib.sha256(canonical(asdict(self)).encode("utf-8")).hexdigest()


class Catalog:
    def __init__(self, tools: list[Tool]):
        self.tools = {tool.name: tool for tool in tools}
        if len(self.tools) != len(tools):
            raise ValueError("duplicate tool name")

    def search(self, query: str, grants: set[str], limit: int = 3) -> list[dict]:
        if limit < 1:
            raise ValueError("limit must be positive")
        words = set(query.casefold().split())
        ranked = []
        for tool in self.tools.values():
            if tool.permission not in grants:
                continue
            score = len(words.intersection(tool.keywords))
            if score:
                ranked.append((score, tool))
        ranked.sort(key=lambda pair: (-pair[0], pair[1].name))
        return [{"name": tool.name, "description": tool.description,
                 "version": tool.version, "digest": tool.digest,
                 "effect": tool.effect, "score": score}
                for score, tool in ranked[:limit]]

    def load(self, hits: list[dict], grants: set[str], budget_bytes: int = 4096) -> list[dict]:
        definitions = []
        for hit in hits:
            tool = self.tools.get(hit["name"])
            if tool is None or tool.permission not in grants:
                raise CatalogError("denied")
            if (tool.version, tool.digest) != (hit["version"], hit["digest"]):
                raise CatalogError("stale_definition")
            definitions.append({**tool.definition(), "digest": tool.digest})
        if byte_size(definitions) > budget_bytes:
            raise CatalogError("definition_budget_exceeded")
        return definitions

    def authorize(self, loaded: dict, grants: set[str]) -> Tool:
        tool = self.tools.get(loaded["name"])
        if tool is None or tool.permission not in grants:
            raise CatalogError("denied")
        if loaded != {**tool.definition(), "digest": tool.digest}:
            raise CatalogError("stale_definition")
        return tool


def fixture_tools() -> list[Tool]:
    tools = [
        Tool("orders.get", "查询一笔订单的支付与履约状态；只读，不发起退款。",
             ("查询", "订单", "状态"), "orders:read", "read"),
        Tool("shipments.get", "查询一笔订单的物流运输状态；不返回支付状态。",
             ("查询", "物流", "状态"), "orders:read", "read"),
        Tool("refunds.create", "为已支付订单创建退款申请；会产生写入，需要审批。",
             ("订单", "退款", "申请"), "refunds:write", "write"),
        Tool("reports.export", "提交月度销售报表导出作业；返回作业编号，不是成品。",
             ("报表", "导出", "月度"), "reports:write", "write"),
    ]
    # Artificial breadth, clearly marked. Never claim 300 working integrations.
    tools += [Tool(f"archive.lookup_{i:03}", f"演示归档目录 {i:03} 的只读检索定义。",
                   ("归档", f"目录{i}"), "archive:read", "read") for i in range(296)]
    return tools
