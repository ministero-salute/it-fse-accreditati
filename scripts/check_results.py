from pathlib import Path
import json
from results_type import Results


RESULTS_PATH = Path("RESULTS/results.json")
with RESULTS_PATH.open("r", encoding="utf8") as results_file:
    data = json.load(results_file)
results = Results(**data)
print("results.json conforms to spec!")
