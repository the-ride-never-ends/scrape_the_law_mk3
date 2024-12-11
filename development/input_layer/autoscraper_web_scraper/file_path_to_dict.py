


from abc import ABC, abstractmethod
from collections import defaultdict
import hashlib
from html import unescape
import json
import os
import pathlib
import pickle
import re
from typing import Any, Callable
import xml.etree.ElementTree as ET


import duckdb
import yaml


from utils.shared.make_id import make_id
from utils.shared.safe_format import safe_format
from .file_path_to_dict import file_path_to_dict
from database.mysql_database import MySqlDatabase
from config.config import (
    HOST,
    USER,
    PASSWORD
)
from logger.logger import Logger


def _sql_filepath_to_dict(file_path: str, open_as: str = 'dict') -> dict[str, str]:
    """
    Split a file_path where the last part is "mysql_{database}_{table}_{var}_{id_var}_{id}".
    The 'var' part can contain underscores.

    Args:
        file_path (str): The file_path to split
    Returns: 
        A dictionary containing keys: "database", "table", "id_var", "id"
    Example:
        result = _sql_filepath_to_dict("path/to/mysql_mydb_users_user_name_id_123")
        # result = {"database": "mydb", "table": "users", "id_var": "id", "id": "123"}
    """
    pattern = r'^(.+)mysql_([^_]+)_([^_]+)_([^_]+)_([^_]+)$'
    match = re.match(pattern, file_path)

    if match:
        database, table, id_var, id = match.groups()
        return {"database": database, "table": table, "id_var": id_var, "id": id}
    else:
        raise ValueError(f"The mysql file_path does not match the expected pattern.\nfilepath: {file_path}")

def _open_json(file_path: str, open_as: str = 'dict') -> dict[str, Any]:
    with open(file_path, "r") as f:
        return json.load(f)

def _open_delineated_file_(file_path: str, delimiter: str = ':') -> dict[str, Any]:
    with open(file_path, "r") as f:
        return dict(row.split(delimiter, 1) for row in f.read().splitlines())

def _open_delineated_file(file_path: str, open_as: str = 'dict') -> dict[str, Any]:
    delimiters = [':', ',', ';', '|', '\t']
    delimiter = next((d for d in delimiters if d in open(file_path, 'r').readline().strip()), None)
    return _open_delineated_file_(file_path, delimiter=delimiter)

def _open_yaml(file_path: str, open_as: str = 'dict') -> dict[str, Any]:
    with open(file_path, "r") as f:
        return yaml.safe_load(f)

def _get_from_mysql_server(file_path: str, open_as: str = 'dict') -> dict[str, Any]:
    # with MySqlDatabase(file_path) as db:
    #     data = db.execute_sql_command("SELECT {var} FROM {table}", args=_sql_filepath_to_dict(file_path), return_dict=True)
    raise NotImplementedError("mysql database not implemented yet.")

def _open_xml(file_path: str, open_as: str = 'dict') -> dict[str, Any]:
    return {elem.tag: elem.text for elem in ET.parse(file_path).getroot().iter()}

def _get_from_duck_db(file_path: str, open_as: str = 'dict') -> dict[str, Any]:
    conn = duckdb.connect(database=file_path, read_only=True)
    data = conn.execute("SELECT * FROM data").fetchall() # -> list[Any]
    conn.close()
    return {row[0]: row[1] for row in data}

def _get_from_sql_server(file_path: str, open_as: str = 'dict') -> dict[str, Any]:
    # Assume mysql for the moment. Else, throw an error.
    args = _sql_filepath_to_dict(file_path)
    database = args.pop("database_name", "")
    with MySqlDatabase(database=database) as db:
        data = db.execute_sql_command(
            "SELECT * FROM {table} WHERE {var_id} = {id}", 
            args=_sql_filepath_to_dict(file_path), 
            return_dict=True
        )
    return data


file_opener_func_dict = {
    ".json": _open_json,
    ".yaml": _open_yaml,
    ".csv": _open_delineated_file,
    ".log": _open_delineated_file,
    ".txt": _open_delineated_file,
    ".xml": _open_xml,
    ".mysql": _get_from_mysql_server,
    ".sql": _get_from_sql_server,
    ".db": _get_from_duck_db,
}

def file_path_to_dict(file_path: str, logger: Logger = None) -> dict | None:
    if not logger:
        logger = Logger(logger_name=f"{__name__}__{file_path_to_dict.__name__}__{str(make_id())}")
    
    if (os.path.exists(file_path) and os.path.isfile(file_path)) or "mysql" in file_path:
        # Since mysql paths aren't really paths to a file, we call it directly 
        if "mysql" in file_path:
            func = file_opener_func_dict[".mysql"]
        else:
            try:
                func: Callable = file_opener_func_dict[pathlib.Path(file_path).stem]
            except KeyError as e:
                logger.warning(f"Unsupported file type: {pathlib.Path(file_path).suffix}")
                return None
        try:
            data = func(file_path)
            logger.info(f"Loaded data from file '{pathlib.Path(file_path).stem}' successfully.")
            return data
        except Exception as e:
            logger.exception(f"Unexpected error loading data from file '{file_path}': {e}")
            return None
