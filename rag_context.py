from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List


DEFAULT_SEARCH_ROOTS = [
    Path(r"C:\Users\cyh\Desktop\GOLD-QUANT"),
    Path(r"C:\Users\cyh\.codex\skills\quant-trading-research"),
    Path(r"C:\Users\cyh\.codex\skills\orchestration"),
    Path(r"C:\Users\cyh\Desktop\GOLD-QUANT\_archive\openclaw-main\docs"),
]

DEFAULT_EXTS = {".md", ".txt", ".py", ".yaml", ".yml", ".json"}
IGNORE_DIR_NAMES = {
    ".git",
    "__pycache__",
    "node_modules",
    "output",
    "_deploy_bundle",
}
MAX_FILE_SIZE_BYTES = 1_000_000


@dataclass
class RagHit:
    path: str
    score: int
    snippet: str


class LocalKeywordRAG:
    def __init__(self, roots: Iterable[Path] | None = None):
        self.roots = [p for p in (roots or DEFAULT_SEARCH_ROOTS) if p.exists()]

    def _iter_files(self):
        for root in self.roots:
            for path in root.rglob("*"):
                if not path.is_file():
                    continue
                if any(part in IGNORE_DIR_NAMES for part in path.parts):
                    continue
                if path.suffix.lower() not in DEFAULT_EXTS:
                    continue
                try:
                    if path.stat().st_size > MAX_FILE_SIZE_BYTES:
                        continue
                except Exception:
                    continue
                if path.is_file():
                    yield path

    @staticmethod
    def _tokenize(query: str) -> List[str]:
        parts = re.split(r"[^a-zA-Z0-9_+-]+", query.lower())
        return [p for p in parts if len(p) >= 2]

    def search(self, query: str, top_k: int = 8) -> List[RagHit]:
        terms = self._tokenize(query)
        hits: List[RagHit] = []
        if not terms:
            return hits
        for path in self._iter_files():
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            lowered = text.lower()
            score = sum(lowered.count(term) for term in terms)
            if score <= 0:
                continue
            # pull the first matching region
            snippet = ""
            for term in terms:
                idx = lowered.find(term)
                if idx != -1:
                    start = max(0, idx - 180)
                    end = min(len(text), idx + 420)
                    snippet = text[start:end].replace("\n", " ").strip()
                    break
            hits.append(RagHit(path=str(path), score=score, snippet=snippet[:600]))
        hits.sort(key=lambda h: h.score, reverse=True)
        return hits[:top_k]
