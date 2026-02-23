import argparse
import json
import sys
import difflib
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _normalize_text(s: str) -> str:
    return (s or "").replace("\r\n", "\n")


def _normalize_entities(entities):
    return sorted(
        [{"entity": str(item.get("entity", "")), "text": str(item.get("text", ""))} for item in (entities or [])],
        key=lambda x: (x["text"], x["entity"]),
    )


def run_cases(cases):
    import app

    results = []
    for case in cases:
        output_text, df = app._anonimizar_logica(case["input"])
        entities = []
        if hasattr(df, "empty") and not df.empty:
            for _, row in df.iterrows():
                entities.append(
                    {
                        "entity": str(row.get("Entidade", "")),
                        "text": str(row.get("Texto Detectado", "")),
                    }
                )
        results.append(
            {
                "id": case["id"],
                "input": case["input"],
                "output": _normalize_text(output_text),
                "entities": entities,
            }
        )
    return results


def diff_strings(old: str, new: str) -> str:
    old_lines = old.splitlines(keepends=True)
    new_lines = new.splitlines(keepends=True)
    return "".join(difflib.unified_diff(old_lines, new_lines, fromfile="snapshot", tofile="current"))


def main():
    parser = argparse.ArgumentParser(description="Baseline regression for anonymization outputs")
    parser.add_argument("mode", choices=["snapshot", "verify"], help="Create snapshot or verify against it")
    parser.add_argument("--cases", default="tests/regression/cases.json", help="Path to test cases JSON")
    parser.add_argument("--snapshot", default="tests/regression/baseline_snapshot.json", help="Path to baseline snapshot JSON")
    args = parser.parse_args()

    cases_path = Path(args.cases)
    snapshot_path = Path(args.snapshot)

    if not cases_path.exists():
        print(f"Cases file not found: {cases_path}")
        return 2

    cases = json.loads(cases_path.read_text(encoding="utf-8-sig"))
    current = run_cases(cases)

    if args.mode == "snapshot":
        snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        snapshot_path.write_text(json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Snapshot written: {snapshot_path}")
        return 0

    if not snapshot_path.exists():
        print(f"Snapshot file not found: {snapshot_path}")
        print("Run with mode=snapshot first.")
        return 2

    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8-sig"))
    snap_by_id = {item["id"]: item for item in snapshot}
    cur_by_id = {item["id"]: item for item in current}

    failures = 0

    for case in cases:
        cid = case["id"]
        if cid not in snap_by_id:
            print(f"[FAIL] Missing in snapshot: {cid}")
            failures += 1
            continue
        if cid not in cur_by_id:
            print(f"[FAIL] Missing in current run: {cid}")
            failures += 1
            continue

        snap_item = snap_by_id[cid]
        cur_item = cur_by_id[cid]

        if snap_item["output"] != cur_item["output"]:
            print(f"[FAIL] Output mismatch: {cid}")
            print(diff_strings(snap_item["output"], cur_item["output"]))
            failures += 1

        if _normalize_entities(snap_item["entities"]) != _normalize_entities(cur_item["entities"]):
            print(f"[FAIL] Entities mismatch: {cid}")
            print("  snapshot entities:", json.dumps(snap_item["entities"], ensure_ascii=False))
            print("  current  entities:", json.dumps(cur_item["entities"], ensure_ascii=False))
            failures += 1

    if failures:
        print(f"\nVerification finished with {failures} failure(s).")
        return 1

    print("Verification passed. No differences found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
