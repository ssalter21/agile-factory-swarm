"""What earlier runs already established, keyed so an edit invalidates only what it touched.

This is the whole reason a second mutation run is cheap. Without it every run pays for every
mutant again, which is the single largest cost in a build chain.
"""

import json
from pathlib import Path

from mutate.units import compare_tests

VERSION = 1


class Manifest:
    def __init__(self, path, tests):
        self.path = Path(path)
        self.state = "changed"
        self.data = {"version": VERSION, "tests": {}, "files": {}}
        self.breaches = {}
        if self.path.is_file():
            try:
                loaded = json.loads(self.path.read_text(encoding="utf-8"))
            except ValueError:
                loaded = {}
            if loaded.get("version") == VERSION:
                self.data = loaded
                self.state = compare_tests(loaded.get("tests") or {}, tests)
        self.data["tests"] = tests
        self.data.setdefault("files", {})

    def sites_for(self, relative):
        return (self.data["files"].get(relative) or {}).get("sites") or {}

    def cached(self, relative, mutant, hashes):
        """The stored verdict, when it is still sound to reuse it. Otherwise None."""
        entry = self.sites_for(relative).get(mutant.key)
        if not entry or entry.get("unit") != hashes.get(mutant.unit):
            return None
        if self.state == "same":
            return entry.get("verdict")
        # Tests only grew, so a mutant the old suite killed is still killed. One that survived
        # might not survive the new tests, so that one is run again.
        if self.state == "additive" and entry.get("verdict") == "killed":
            return "killed"
        return None

    def record(self, relative, mutant, hashes, verdict):
        record = self.data["files"].setdefault(relative, {"sites": {}})
        record.setdefault("sites", {})[mutant.key] = {
            "verdict": verdict,
            "unit": hashes.get(mutant.unit),
            "desc": mutant.label,
        }

    def prune(self, relative, mutants):
        """Forget mutants that no longer exist, so the manifest cannot grow without bound."""
        if not self.data["files"].get(relative):
            return
        live = {mutant.key for mutant in mutants}
        self.data["files"][relative]["sites"] = {
            key: value for key, value in self.sites_for(relative).items() if key in live
        }

    def breach(self, relative, count):
        self.breaches[relative] = count

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self.data, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
