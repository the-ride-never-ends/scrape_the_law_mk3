

from dataclasses import dataclass
from typing import Any
import pandas as pd
import os


from dataclasses_.utils.html_to_text import html_to_text
from utils.shared.make_sha256_hash import make_sha256_hash


@dataclass
class SqlInsert:
    # TODO Write create_node_id method.

    gnis: int # MEDIUMINT UNSIGNED NOT NULL,

    def __post_init__(self):
        pass

    def _create_sha256_hash(self, *args) -> str:
        return make_sha256_hash(*args)

    def _create_node_id(self, url: str) -> int:
        domain, node_id = 
        return 

    def save_to_csv(self, file_path: str, file_name: str = None) -> None:
        if not os.path.exists(file_path):
            os.mkdir(file_path)
        _file_name = file_name or f"{self.__class__.__name__}_{self.gnis}.csv"
        _path = os.path.join(file_path, _file_name)
        pd.DataFrame([self.__dict__]).to_csv(_path, mode='a', index=False)

    def _html_to_text(html, ignore_links=True):
        return html_to_text(html, ignore_links=ignore_links)

    def _type_check_value(value: Any, type_: type) -> None:
        if not isinstance(value, type_):
            raise ValueError(f"value for  is not a {type_}, but a {type(value)}")
        
