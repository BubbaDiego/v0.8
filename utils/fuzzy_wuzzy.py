import re
from enum import Enum
from typing import Optional, Type, List, Dict, Any, Tuple
from rapidfuzz import process, fuzz
from utils.console_logger import ConsoleLogger as log


def normalize(text: str) -> str:
    return re.sub(r'[\W_]+', '', text.lower())


def fuzzy_match_enum(
    input_str: str,
    enum_class: Type[Enum],
    aliases: Optional[Dict[str, List[str]]] = None,
    threshold: float = 60.0
) -> Optional[Enum]:
    """
    Fuzzy match an input string to an enum with score logging.
    Returns enum or None if match score < threshold.
    """
    norm_input = normalize(input_str)
    enum_names = [e.name for e in enum_class]
    candidate_list = enum_names[:]

    # 🔁 Add alias names to candidate pool
    alias_map = {}
    if aliases:
        for k, v_list in aliases.items():
            for alias in v_list:
                candidate_list.append(alias)
                alias_map[alias] = k

    # 🔎 Run fuzzy match
    best_match, score, _ = process.extractOne(norm_input, candidate_list, scorer=fuzz.ratio)

    # 🐻 Log the match confidence
    log.debug(f"🐻 Fuzzy match for '{input_str}' → '{best_match}' ({score}%)", source="FuzzyMatch")

    if score < threshold:
        log.warning(f"Low confidence match for '{input_str}' → {score}%", source="FuzzyMatch")
        return None

    resolved = alias_map.get(best_match, best_match)
    try:
        return enum_class[resolved]
    except KeyError:
        log.error(f"Resolved match '{resolved}' not in enum {enum_class.__name__}", source="FuzzyMatch")
        return None


def fuzzy_match_key(
    input_str: str,
    target_dict: Dict[str, Any],
    aliases: Optional[Dict[str, List[str]]] = None,
    threshold: float = 60.0
) -> Optional[str]:
    """
    Fuzzy match a string to a dictionary key, with confidence score.
    """
    norm_input = normalize(input_str)
    keys = list(target_dict.keys())
    candidate_list = keys[:]

    alias_map = {}
    if aliases:
        for k, v_list in aliases.items():
            for alias in v_list:
                candidate_list.append(alias)
                alias_map[alias] = k

    best_match, score, _ = process.extractOne(norm_input, candidate_list, scorer=fuzz.ratio)

    log.debug(f"🐻 Fuzzy key match for '{input_str}' → '{best_match}' ({score}%)", source="FuzzyMatch")

    if score < threshold:
        log.warning(f"Low confidence key match for '{input_str}' → {score}%", source="FuzzyMatch")
        return None

    return alias_map.get(best_match, best_match)
import re
from enum import Enum
from typing import Optional, Type, List, Dict, Any, Tuple
from rapidfuzz import process, fuzz
from utils.console_logger import ConsoleLogger as log


def normalize(text: str) -> str:
    return re.sub(r'[\W_]+', '', text.lower())


def fuzzy_match_enum(
    input_str: str,
    enum_class: Type[Enum],
    aliases: Optional[Dict[str, List[str]]] = None,
    threshold: float = 60.0
) -> Optional[Enum]:
    """
    Fuzzy match an input string to an enum with score logging.
    Returns enum or None if match score < threshold.
    """
    norm_input = normalize(input_str)
    enum_names = [e.name for e in enum_class]
    candidate_list = enum_names[:]

    # 🔁 Add alias names to candidate pool
    alias_map = {}
    if aliases:
        for k, v_list in aliases.items():
            for alias in v_list:
                candidate_list.append(alias)
                alias_map[alias] = k

    # 🔎 Run fuzzy match
    best_match, score, _ = process.extractOne(norm_input, candidate_list, scorer=fuzz.ratio)

    # 🐻 Log the match confidence
    log.debug(f"🐻 Fuzzy match for '{input_str}' → '{best_match}' ({score}%)", source="FuzzyMatch")

    if score < threshold:
        log.warning(f"Low confidence match for '{input_str}' → {score}%", source="FuzzyMatch")
        return None

    resolved = alias_map.get(best_match, best_match)
    try:
        return enum_class[resolved]
    except KeyError:
        log.error(f"Resolved match '{resolved}' not in enum {enum_class.__name__}", source="FuzzyMatch")
        return None


def fuzzy_match_key(
    input_str: str,
    target_dict: Dict[str, Any],
    aliases: Optional[Dict[str, List[str]]] = None,
    threshold: float = 60.0
) -> Optional[str]:
    """
    Fuzzy match a string to a dictionary key, with confidence score.
    """
    norm_input = normalize(input_str)
    keys = list(target_dict.keys())
    candidate_list = keys[:]

    alias_map = {}
    if aliases:
        for k, v_list in aliases.items():
            for alias in v_list:
                candidate_list.append(alias)
                alias_map[alias] = k

    best_match, score, _ = process.extractOne(norm_input, candidate_list, scorer=fuzz.ratio)

    log.debug(f"🐻 Fuzzy key match for '{input_str}' → '{best_match}' ({score}%)", source="FuzzyMatch")

    if score < threshold:
        log.warning(f"Low confidence key match for '{input_str}' → {score}%", source="FuzzyMatch")
        return None

    return alias_map.get(best_match, best_match)
