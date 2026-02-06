import json
import os
from typing import List
from .crawler import Page


class JsonStorage:
    """Save results to JSON file."""

    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def save(self, pages: List[Page], filename: str = "results.json"):
        """Save pages to JSON file."""
        filepath = os.path.join(self.output_dir, filename)
        data = [p.to_dict() for p in pages]

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return filepath

    def load(self, filename: str = "results.json") -> List[dict]:
        """Load results from JSON file."""
        filepath = os.path.join(self.output_dir, filename)

        if not os.path.exists(filepath):
            return []

        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
