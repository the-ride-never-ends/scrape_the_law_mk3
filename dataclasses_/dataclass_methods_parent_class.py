


import duckdb


from dataclasses import dataclass

from database.mysql_database import MySqlDatabase
from database.duckdb_database import DuckDbDatabase

from typing import Any, Callable, AsyncGenerator, Generator
from logger.logger import Logger
logger = Logger(logger_name=__name__)

@dataclass
class DataClassMethods:

    _duckdb_connection: duckdb.DuckDBPyConnection = None

    def __post_init__(self):
        self.table_name = f"{self.__class__.__name__}_database"
        self._duckdb_connection = self._make_duckdb_database()


    def _make_duckdb_database(self):
        """
        Create an in-memory DuckDB database connection and return it.
        """
        logger.info(f"Creating DuckDB database: {self.table_name}...")

        # Create an in-memory DuckDB database connection
        db = duckdb.connect(':memory:')
        name_dict = {name: "" for name in self.column_names}

        # Create a table and return the database.
        logger.info("Creating table...")
        db.register('name_dict', name_dict)
        db.execute(f"CREATE TABLE IF NOT EXISTS {self.table_name} AS SELECT * FROM name_dict")
        logger.info("Table created.")
        return db


    @property
    def database(self) -> list['DataClassMethods']:
        """
        Get all the current contents of the DuckDB database.
        """
        return self._duckdb_connection.execute(f"SELECT * FROM {self.table_name}").fetchall()


    @property.setter
    def database(self, value: 'DataClassMethods') -> None:
        """
        Insert values into the DuckDB database.
        """
        if not self._duckdb_connection:
            self._duckdb_connection = self._make_duckdb_database()
        self._duckdb_connection: duckdb.DuckDBPyConnection

        try:
            if not isinstance(value, 'DataClassMethods'):
                raise ValueError("Value must be a subclass of DataClassMethods")

            self._duckdb_connection.register('value', value)
            self._duckdb_connection.begin()
            self._duckdb_connection.execute(f"INSERT INTO {self.table_name} SELECT * FROM value")
            self._duckdb_connection.commit()

            logger.info(f"Data inserted into database: {self.table_name}")

        except Exception as e:
            logger.warning(f"Error inserting data into DuckDB: {e}")
            self._duckdb_connection.rollback()


    @property.deleter
    def database(self) -> dict[str, list['DataClassMethods']]:
        """
        A 
        """
        return self._duckdb_connection.close()


    @property
    def column_names(self) -> list[str]:
        return [prop for prop in dir(self) if not callable(getattr(self, prop)) and not prop.startswith("__") and not prop.startswith("_")]


    def from_mysql_db(self):
        with MySqlDatabase(database="scrape_the_law") as db:

            # Construct the SQL query to select all the properties from the table
            query = f"SELECT {', '.join(self.column_names)} FROM {self.table_name}"
            
            # Execute the query and fetch all the results
            results_dict = db._execute_sql_command(query, return_dict=True)

        self.dataclass_database = results_dict


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






