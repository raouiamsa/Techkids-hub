# benchmarking/utils/json_parser.py
"""Shared JSON extraction utilities (DRY principle)."""

import json
from typing import Dict, List, Optional, Union


def _extract_balanced_json_candidates(text: str) -> List[str]:
    """Return balanced JSON object/array substrings found in text.

    Handles nested braces/brackets while respecting quoted strings.
    """
    candidates: List[str] = []
    n = len(text)

    for i, ch in enumerate(text):
        if ch not in "{[":
            continue

        opening = ch
        closing = "}" if opening == "{" else "]"
        depth = 0
        in_string = False
        escape = False

        for j in range(i, n):
            c = text[j]

            if in_string:
                if escape:
                    escape = False
                elif c == "\\":
                    escape = True
                elif c == '"':
                    in_string = False
                continue

            if c == '"':
                in_string = True
                continue

            if c == opening:
                depth += 1
            elif c == closing:
                depth -= 1
                if depth == 0:
                    candidates.append(text[i : j + 1])
                    break

    return candidates


def extract_json_from_text(text: str) -> Optional[Union[Dict, List]]:
    """Extract JSON from text with non-greedy regex and fallback methods.
    
    This is the single source of truth for JSON extraction across all metrics modules.
    
    Args:
        text: Raw text potentially containing JSON
        
    Returns:
        Parsed JSON object/list, or None if parsing fails
    """
    if not text:
        return None

    text = text.strip()

    # Method 1: Direct JSON parse
    try:
        return json.loads(text)
    except Exception:
        pass

    # Method 2: Extract from markdown code block (json)
    if "```json" in text:
        try:
            candidate = text.split("```json")[1].split("```")[0].strip()
            return json.loads(candidate)
        except Exception:
            pass

    # Method 3: Extract from generic code block
    if "```" in text:
        try:
            candidate = text.split("```")[1].split("```")[0].strip()
            return json.loads(candidate)
        except Exception:
            pass

    # Method 4: Balanced JSON candidates from raw text (robust nested parsing)
    for candidate in _extract_balanced_json_candidates(text):
        try:
            return json.loads(candidate)
        except Exception:
            continue

    return None
