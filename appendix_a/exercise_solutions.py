"""Concrete answers for nine exercises; offline and stdout-only."""
import argparse
import json
from .preparation import build_request, classify_error, parse_task


def answers():
    task = {"goal": "检查链接", "max_steps": 3}
    text = json.dumps(task, ensure_ascii=False)
    restored = json.loads(text)
    validation = {}
    for value in (3, "3", True, 0):
        raw = json.dumps({"goal": "检查链接", "max_steps": value}, ensure_ascii=False)
        try:
            parse_task(raw)
            validation[repr(value)] = "accepted"
        except ValueError as error:
            validation[repr(value)] = str(error)
    return {
        "A-1": {"answer": "比较安装包与运行程序的解释器，不更换模型。",
                "commands": ["python -c \"import sys; print(sys.executable)\"", "python -m pip --version"]},
        "A-2": {"answer": "相对路径从当前目录起算；在chapter3内使用python agent_loop.py，或回到根目录使用原命令。"},
        "A-3": {"answer": "不能。not_run表示真实Provider未运行；还需经过授权的实际响应，且只证明该请求的连通性。"},
        "A-4": {"serialized_type": type(text).__name__, "parsed_type": type(restored).__name__,
                "max_steps": restored["max_steps"]},
        "A-5": {"results": validation, "reason": "bool是int子类；本合同使用type(value) is int并限定1至10。"},
        "A-6": {"runtime_output": "31", "reason": "Node移除类型标注，字符串加1发生拼接；运行不是静态检查。",
                "optional_command": "tsc --strict --noEmit appendix_a/examples/unchecked.ts",
                "compiler_status": "not_run"},
        "A-7": {"responses_body": build_request("openai", "responses", "reader-model", "你好")["body"],
                "chat_body": build_request("deepseek", "chat", "reader-model", "你好")["body"],
                "reason": "还要检查所需工具、流式结束、状态及错误语义；忽略参数不一定返回400。"},
        "A-8": {"rate": classify_error(429, code="rate_limit_exceeded")["action"],
                "account": classify_error(429, code="credit_balance_exhausted")["action"],
                "unknown": classify_error(429)["action"]},
        "A-9": {"keep": ["Provider", "endpoint", "protocol", "model ID", "SDK version",
                         "safe error code", "attempt count", "latency", "safe request ID"],
                "exclude": ["API Key", "Authorization header", "private prompt", "personal data"],
                "timeout": "收到状态未知；先核对尝试、费用和副作用，再决定是否重试。"},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--exercise", choices=tuple(answers()))
    args = parser.parse_args()
    result = answers()
    if args.exercise:
        result = {args.exercise: result[args.exercise]}
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
