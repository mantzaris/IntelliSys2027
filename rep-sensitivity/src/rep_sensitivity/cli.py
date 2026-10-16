import argparse
import json
from pathlib import Path
from .replay import prepare, run


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("generate", "run"):
        p = sub.add_parser(name)
        p.add_argument("--config", required=True)
        if name == "run": p.add_argument("--model", required=True)
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text())
    if args.command == "generate":
        manifest, _, _ = prepare(config, Path("artifacts/runs") / config["name"])
        print(json.dumps({k: v for k, v in manifest.items() if k != "trials"}, indent=2))
    elif args.command == "run": run(config, args.model)


if __name__ == "__main__": main()
