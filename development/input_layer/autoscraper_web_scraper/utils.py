from collections import OrderedDict
from difflib import SequenceMatcher
import random
import string
from typing import Any, Pattern, Optional, Hashable
import unicodedata


from bs4 import Tag


def unique_stack_list(stack_list: list[Hashable]) -> list[Hashable]:
    seen = set()
    unique_list = []
    for stack in stack_list:
        stack_hash = stack['hash']
        if stack_hash in seen:
            continue
        unique_list.append(stack)
        seen.add(stack_hash)
    return unique_list


def unique_hashable(hashable_items: list[Hashable]) -> list[OrderedDict]:
    """Removes duplicates from the list. Must preserve the orders."""
    return list(OrderedDict.fromkeys(hashable_items))


def get_random_str(n: int) -> str:
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choice(chars) for i in range(n))


def get_non_rec_text(element: Tag) -> str:
    return ''.join(element.find_all(text=True, recursive=False)).strip()


def normalize(item: Any) -> Any | str:
    if not isinstance(item, str):
        return item
    return unicodedata.normalize("NFKD", item.strip())


def text_match(t1: str|Pattern, t2: str|Pattern, ratio_limit: float) -> bool:
    if hasattr(t1, 'fullmatch'):
        return bool(t1.fullmatch(t2))
    if ratio_limit >= 1:
        return t1 == t2
    return SequenceMatcher(None, t1, t2).ratio() >= ratio_limit


class ResultItem():
    def __init__(self, text: str, index: int):
        self.text: str = text
        self.index: int = index

    def __str__(self):
        return self.text


class FuzzyText(object):
    def __init__(self, text: str, ratio_limit: float):
        self.text: str = text
        self.ratio_limit: float = ratio_limit
        self.match: Optional[bool] = None

    def search(self, text: str) -> bool:
        return SequenceMatcher(None, self.text, text).ratio() >= self.ratio_limit
