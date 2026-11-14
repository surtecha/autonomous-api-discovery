"""Score a completed observation bundle without participating in discovery."""

import argparse
import json
from pathlib import Path

from packages.discovery.evaluation import evaluate
from packages.discovery.models import Knowledge
from scripts.paths import workspace_path

parser = argparse.ArgumentParser()
parser.add_argument("--knowledge", type=Path, required=True)
parser.add_argument("--truth", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
args.knowledge = workspace_path(args.knowledge)
args.truth = workspace_path(args.truth)
args.output = workspace_path(args.output)
result = evaluate(
    Knowledge.from_dict(json.loads(args.knowledge.read_text())), json.loads(args.truth.read_text())
)
args.output.write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result))
