import argparse
import json
from pathlib import Path
from .system import new_packet, run_system


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Offline knowledge or trusted-fixture repair")
    parser.add_argument("--mode", choices=("knowledge", "repair"), required=True)
    parser.add_argument("--workdir", type=Path, required=True)
    parser.add_argument("--approve", action="store_true")
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    packet = new_packet(input_refs=("repair_correct",), output_requirements=("repair_correct",)) if args.mode == "repair" else new_packet()
    try:
        result = run_system(args.mode, packet, root=root, workdir=args.workdir, approved=args.approve)
    except ValueError as error:
        parser.exit(2, str(error) + "\n")
    print(json.dumps({"status": result["status"], "reason_code": result["reason_code"], "metrics": result["metrics"],
                      "evidence_verdict": result["evidence_verdict"],
                      "acceptance": result["acceptance"], "receipts": result["receipts"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
