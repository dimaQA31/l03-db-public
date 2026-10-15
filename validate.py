import json
import os
from pathlib import Path

from loader import load, set_hash, summarise

path = Path(__file__).resolve().parent / f"{os.environ.get('SET', 'golden')}.jsonl"
print("set", path.name, "set_hash", set_hash(path))
print(json.dumps(summarise(load(path)), indent=2))
