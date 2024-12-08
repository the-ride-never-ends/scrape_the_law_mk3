


import duckdb


from dataclasses import dataclass

from database.mysql_database import MySqlDatabase
from database.duckdb_database import DuckDbDatabase

from typing import Any, Callable, AsyncGenerator, Generator

@dataclass
class DataClassMethods:

    def from_mysql_db(self):
        pass

    async def from_mysql_db_async(self):
        pass

    def from_mysql_db_by_batch(self):
        pass

    async def from_mysql_db_by_batch_async(self):
        pass

    def to_mysql_db(self):
        pass

    async def to_mysql_db_async(self):
        pass

    def from_duckdb_db(self):
        pass

    def from_duckdb_db_by_batch(self):
        pass

    def to_duckdb_db(self):
        pass






