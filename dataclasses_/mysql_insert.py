

from dataclasses import dataclass
from typing import Any, Container, NamedTuple, Never, Mapping
import pandas as pd
import os
import inspect

from dataclasses_.utils.html_to_text import html_to_text
from utils.shared.make_sha256_hash import make_sha256_hash

from database.mysql_database import MySqlDatabase
from utils.shared.safe_format import safe_format

from config.config import PROJECT_ROOT, DATABASE

def read_mysql_script(sql_file_name: str) -> str:
    sql_script_file_path  = os.path.join(PROJECT_ROOT, "sql_scripts", sql_file_name)

    # Type check the sql_script_file_path variable
    if sql_script_file_path is None or not os.path.exists(sql_script_file_path):
         raise ValueError("Invalid file path")
    if not sql_script_file_path.endswith('.sql'):
        raise ValueError("Invalid file extension. Expected '.sql'.")

    try: # Try to load the SQL file.
        with open(sql_script_file_path, 'r') as file:
            return file.read()
    except FileNotFoundError as e:
        raise FileNotFoundError(f"File not found: {sql_script_file_path}") from e
    except Exception as e:
        raise Exception(f"An error occurred while reading the file: {e}") from e

# NOTE Since dataclasses insert ALL attributes into the database by default, 
# we must assign certain attributes outside of it.

_CANNOT_BE_NONE = [

]












from dataclasses import dataclass
from typing import TypeVar, Generic, Union, Type, Any, Optional, get_args, get_origin
from datetime import datetime, date
from decimal import Decimal
from collections.abc import Container, Sequence
from enum import Enum
import re

T = TypeVar('T')

class MySQLType(Enum):
    """
    MySQL data types with their Python equivalents and validation rules.
    See: https://www.w3schools.com/mysql/mysql_datatypes.asp

    ## Numeric Data Types:
    - #### BIT(size): A bit-value type. The number of bits per value is specified in size. 
            The size parameter can hold a value from 1 to 64. The default value for size is 1.
    - ####  TINYINT(size): A very small integer. Signed range is from -128 to 127. 
            Unsigned range is from 0 to 255. The size parameter specifies the maximum display width (which is 255)
    - ####  BOOL: Zero is considered as false, nonzero values are considered as true.
    - ####  BOOLEAN: Equal to BOOL
    - ####  SMALLINT(size): A small integer. Signed range is from -32768 to 32767. Unsigned range is from 0 to 65535. 
            The size parameter specifies the maximum display width (which is 255)
    - ####  MEDIUMINT(size): A medium integer. Signed range is from -8388608 to 8388607. Unsigned range is from 0 to 16777215. 
            The size parameter specifies the maximum display width (which is 255)
    - ####  INT(size): A medium integer. Signed range is from -2147483648 to 2147483647. Unsigned range is from 0 to 4294967295. 
            The size parameter specifies the maximum display width (which is 255)
    - ####  INTEGER(size): Equal to INT(size)
    - ####  BIGINT(size): A large integer. Signed range is from -9223372036854775808 to 9223372036854775807. 
            Unsigned range is from 0 to 18446744073709551615. The size parameter specifies the maximum display width (which is 255)
    - ####  FLOAT(size, d): A floating point number. The total number of digits is specified in size. 
            The number of digits after the decimal point is specified in the d parameter. 
            NOTE This syntax is deprecated in MySQL 8.0.17, and it will be removed in future MySQL versions
    - ####  FLOAT(p): A floating point number. MySQL uses the p value to determine whether to use FLOAT or DOUBLE for the resulting data type. 
            If p is from 0 to 24, the data type becomes FLOAT(). If p is from 25 to 53, the data type becomes DOUBLE()
    - ####  DOUBLE(size, d): A normal-size floating point number. The total number of digits is specified in size. 
            The number of digits after the decimal point is specified in the d parameter
    - ####  DOUBLE PRECISION(size, d):  
    - ####  DECIMAL(size, d): An exact fixed-point number. The total number of digits is specified in size. 
            The number of digits after the decimal point is specified in the d parameter. 
            The maximum number for size is 65. The maximum number for d is 30. The default value for size is 10. The default value for d is 0.
    - ####  DEC(size, d): Equal to DECIMAL(size,d)

    String Data Types: 
    - ####  CHAR(size): A FIXED length string (can contain letters, numbers, and special characters). 
            The size parameter specifies the column length in characters - can be from 0 to 255. Default is 1
    - ####  VARCHAR(size): A VARIABLE length string (can contain letters, numbers, and special characters). 
            The size parameter specifies the maximum column length in characters - can be from 0 to 65535
    - ####  BINARY(size): Equal to CHAR(), but stores binary byte strings. 
            The size parameter specifies the column length in bytes. Default is 1
    - ####  VARBINARY(size): Equal to VARCHAR(), but stores binary byte strings. 
            The size parameter specifies the maximum column length in bytes.
    - ####  TINYBLOB: For BLOBs (Binary Large OBjects). Max length: 255 bytes
    - ####  TINYTEXT: Holds a string with a maximum length of 255 characters
    - ####  TEXT(size): Holds a string with a maximum length of 65,535 bytes
    - ####  BLOB(size): For BLOBs (Binary Large OBjects). Holds up to 65,535 bytes of data
    - ####  MEDIUMTEXT: Holds a string with a maximum length of 16,777,215 characters
    - ####  MEDIUMBLOB: For BLOBs (Binary Large OBjects). Holds up to 16,777,215 bytes of data
    - ####  LONGTEXT: Holds a string with a maximum length of 4,294,967,295 characters
    - ####  LONGBLOB: For BLOBs (Binary Large OBjects). Holds up to 4,294,967,295 bytes of data
    - ####  ENUM(val1, val2, val3, ...): A string object that can have only one value, chosen from a list of possible values. 
            You can list up to 65535 values in an ENUM list. If a value is inserted that is not in the list, a blank value will be inserted. 
            The values are sorted in the order you enter them
    - ####  SET(val1, val2, val3, ...): A string object that can have 0 or more values, chosen from a list of possible values. 
            You can list up to 64 values in a SET list

    Date and Time Data Types
    - ####  DATE: A date. Format: YYYY-MM-DD. The supported range is from '1000-01-01' to '9999-12-31'
    - ####  DATETIME(fsp): A date and time combination. Format: YYYY-MM-DD hh:mm:ss. 
        The supported range is from '1000-01-01 00:00:00' to '9999-12-31 23:59:59'. 
        Adding DEFAULT and ON UPDATE in the column definition to get automatic initialization and updating to the current date and time
    - ####  TIMESTAMP(fsp): A timestamp. TIMESTAMP values are stored as the number of seconds since the Unix epoch ('1970-01-01 00:00:00' UTC). 
        Format: YYYY-MM-DD hh:mm:ss. The supported range is from '1970-01-01 00:00:01' UTC to '2038-01-09 03:14:07' UTC. 
        Automatic initialization and updating to the current date and time can be specified 
        using DEFAULT CURRENT_TIMESTAMP and ON UPDATE CURRENT_TIMESTAMP in the column definition
    - ####  TIME(fsp): A time. Format: hh:mm:ss. The supported range is from '-838:59:59' to '838:59:59'
    - ####  YEAR: A year in four-digit format. Values allowed in four-digit format: 1901 to 2155, and 0000. 
        MySQL 8.0 does not support year in two-digit format
    """

    # String types
    # NOTE Type = (python type, min_val, max_val)
    CHAR = ('str', 0, 255)
    VARCHAR = ('str', 0, 65535)
    TINYTEXT = ('str', 0, 255)
    TEXT = ('str', 0, 65535)
    MEDIUMTEXT = ('str', 0, 16777215)
    LONGTEXT = ('str', 0, 4294967295)
    BINARY = ('bytes', 0, 255)
    VARBINARY = ('bytes', 0, 65535)
    TINYBLOB = ('bytes', 0, 255)
    BLOB = ('bytes', 0, 65535)
    MEDIUMBLOB = ('bytes', 0, 16777215)
    LONGBLOB = ('bytes', 0, 4294967295)
    ENUM = ('str', None, None)  # Specific validation required
    SET = ('str', None, None)   # Specific validation required


    # Numeric types
    BIT = ('int', 1, 64)  # Represents 1 to 64 bits
    BOOL = ('bool', None, None)
    BOOLEAN = ('bool', None, None)
    TINYINT = ('int', -128, 127)
    SMALLINT = ('int', -32768, 32767)
    MEDIUMINT = ('int', -8388608, 8388607)
    INT = ('int', -2147483648, 2147483647)
    INTEGER = ('int', -2147483648, 2147483647)
    BIGINT = ('int', -9223372036854775808, 9223372036854775807)
    FLOAT = ('float', None, None)
    DOUBLE = ('float', None, None)
    DOUBLE_PRECISION = ('float', None, None)
    DECIMAL = ('Decimal', None, None)
    DEC = ('Decimal', None, None)

    # Date and time types
    DATE = ('date', None, None)
    DATETIME = ('datetime', None, None)
    TIMESTAMP = ('datetime', None, None)
    TIME = ('str', None, None)  # Stored as string 'HH:MM:SS'
    YEAR = ('int', 1901, 2155)

    # Binary types
    BINARY = ('bytes', 0, 255)
    VARBINARY = ('bytes', 0, 65535)
    BLOB = ('bytes', 0, 65535)

    # Special Type
    JSON = ('dict', None, None)

    def __init__(self, 
                 python_type: str, 
                 min_val: Any, 
                 max_val: Any
                ):
        self.python_type = python_type
        self.min_val = min_val
        self.max_val = max_val

class MySQLValidator(Generic[T]):
    """
    A descriptor that validates values for MySQL database insertion.
    Handles both single values and containers of values.
    """
    
    def __init__(self, 
                 mysql_type: MySQLType, 
                 nullable: bool = True, 
                 length: Optional[int] = None, 
                 unsigned: bool = False
                ):
        self.mysql_type = mysql_type
        self.nullable = nullable
        self.length = length
        self.unsigned = unsigned
        self.private_name = None

        # Adjust numeric ranges for unsigned values
        if unsigned and mysql_type.min_val is not None:
            self.min_val = 0
            self.max_val = mysql_type.max_val * 2 + 1
        else:
            self.min_val = mysql_type.min_val
            self.max_val = mysql_type.max_val
    
    def __set_name__(self, owner, name):
        self.private_name = f'_{name}'

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return getattr(instance, self.private_name, None)

    def validate_single_value(self, value: Any) -> bool:
        """Validate a single value against MySQL type constraints."""
        if value is None:
            if not self.nullable:
                raise ValueError(f"NULL value not allowed for non-nullable field")
            return True

        # Get expected Python type
        expected_type = {
            'int': int,
            'float': float,
            'Decimal': Decimal,
            'str': str,
            'bytes': bytes,
            'date': date,
            'datetime': datetime
        }[self.mysql_type.python_type]

        if not isinstance(value, expected_type):
            raise TypeError(f"Expected {expected_type.__name__}, got {type(value).__name__}")

        # Length validation for string and binary types
        if isinstance(value, (str, bytes)):
            if self.length is not None and len(value) > self.length:
                raise ValueError(f"Value length {len(value)} exceeds maximum length {self.length}")
            if len(value) > self.mysql_type.max_val:
                raise ValueError(f"Value length {len(value)} exceeds type maximum {self.mysql_type.max_val}")

        # Range validation for numeric types
        if isinstance(value, (int, float, Decimal)):
            if self.min_val is not None and value < self.min_val:
                raise ValueError(f"Value {value} below minimum {self.min_val}")
            if self.max_val is not None and value > self.max_val:
                raise ValueError(f"Value {value} exceeds maximum {self.max_val}")

        # Special validation for specific types
        if self.mysql_type == MySQLType.TIME:
            if not re.match(r'^([0-1][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]$', value):
                raise ValueError("Invalid TIME format. Use 'HH:MM:SS'")

        return True
    
    def validate_value(self, value: Any) -> bool:
        """Validate a value or container of values."""
        if isinstance(value, (list, tuple, set)):
            return all(self.validate_single_value(v) for v in value)
        return self.validate_single_value(value)
    
    def __set__(self, instance, value):
        self.validate_value(value)
        setattr(instance, self.private_name, value)

@dataclass
class TableRecord:
    """
    Base class for database table records.
    """
    # TODO Write to_csv_via_pandas method
    # TODO get_as_pandas_dataframe

    def to_sql_values(self) -> tuple:
        """
        Convert all fields to a tuple suitable for SQL insertion.
        """
        values = []
        for field_name in self.__annotations__:
            value = getattr(self, field_name)
            if isinstance(value, (list, tuple, set)):
                # Join multiple values with commas for MySQL's SET or similar types
                values.append(','.join(str(v) for v in value))
            else:
                values.append(value)
        return tuple(values)

    # TODO
    def to_csv_via_pandas(self):
        pass

    # TODO
    def get_as_pandas_dataframe(self):
        pass

    async def async_insert_into_mysql_server(self, sql_file_name: str, args: dict):
        statement = read_mysql_script(sql_file_name)
        params = self.to_sql_values()
        async with await MySqlDatabase(database=DATABASE) as db:
            db: MySqlDatabase
            await db.async_execute_sql_command(
                statement, args=args, params=params
            )
        return



# Example usage for a specific table
@dataclass
class UserRecord(TableRecord):
    id: int | None = MySQLValidator(MySQLType.INT, nullable=False, unsigned=True)
    username: str | None = MySQLValidator(MySQLType.VARCHAR, length=50, nullable=False)
    emails: str | list[str] = MySQLValidator(MySQLType.VARCHAR, length=255)
    scores: int | list[int] = MySQLValidator(MySQLType.SMALLINT, unsigned=True)
    created_at: datetime = MySQLValidator(MySQLType.DATETIME, nullable=False)

    def __post_init__(self):
        # Initialize unset fields with None
        for field_name in self.__annotations__:
            if not hasattr(self, f'_{field_name}'):
                setattr(self, f'_{field_name}', None)

# Example database interface
class Database:
    def __init__(self, connection):
        self.connection = connection
    
    def insert_record(self, table_name: str, record: TableRecord) -> None:
        """Insert a record into the database."""
        values = record.to_sql_values()
        placeholders = ','.join(['%s'] * len(values))
        fields = ','.join(record.__annotations__.keys())
        
        query = f"INSERT INTO {table_name} ({fields}) VALUES ({placeholders})"
        
        with self.connection.cursor() as cursor:
            cursor.execute(query, values)
        self.connection.commit()
































@dataclass
class SqlInsert:
    """
    Parent class for SQL insertion classes.
    Contains various methods for inserting data into a MySQL database including:
    - type-checking
    - 256-bit SHA256 hashing
    - basic data cleaning
    """
    # TODO Write create_node_id method.
    # TODO Finish async_insert_into_mysql_table method
    # TODO Finish async_insert_into_mysql_table method

    def __post_init__(self):
        pass

    def _create_sha256_hash(self, *args) -> str:
        return make_sha256_hash(*args)

    # TODO
    def _create_node_id(self, url: str) -> int:
        # domain, node_id = url.split("//")[1].split("/")[:2]
        return

    def get_current_dataclass_values_as_dictionary(self, print_only = False) -> dict[str, Any] | None:
        if not print_only:
            return self.__dict__
        else:
            print(self.__dict__)

    def get_current_dataclass_keys_as_tuple(self, print_only = False) -> tuple[str] | None:
        if not print_only:
            return tuple(self.__dict__.keys())
        else:
            print(tuple(self.__dict__.keys()))

    def get_current_dataclass_values_as_tuple(self, print_only = False) -> tuple[Any] | None:
        if not print_only:
            return tuple(self.__dict__.values())
        else:
            print(tuple(self.__dict__.values()))


    async def async_insert_into_mysql_table(self, 
                                            table_name: str, 
                                            database_name: str = "socialtoolkit",
                                            args: dict = None,
                                            column_names: tuple[str] | list[str] = None,
                                            statement: str = None,
                                            sql_file_name: str = None,
                                            ) -> None:
        async with await MySqlDatabase(database=database_name) as db:
            db: MySqlDatabase
            db.async_execute_sql_command


    # TODO
    async def async_insert_into_mysql_table(self, 
                                            table_name: str, 
                                            database_name: str = "socialtoolkit",
                                            statement: str = None,
                                            sql_file_name: str = None,
                                            ) -> None:
        async with await MySqlDatabase(database=database_name) as db:
            pass


    # TODO
    async def async_select_from_mysql_table(self, table_name: str, args: dict = None, database_name: str = "socialtoolkit",) -> None:
        async with await MySqlDatabase(database=database_name) as db:
            pass


    def save_to_csv_via_pandas(self, file_path: str, file_name: str = None) -> None:
        if not os.path.exists(file_path):
            os.mkdir(file_path)
        _file_name = file_name or f"{self.__class__.__name__}_{self.gnis}.csv"
        _path = os.path.join(file_path, _file_name)
        pd.DataFrame([self.__dict__]).to_csv(_path, mode='a', index=False)


    def assign_values_from_mapping_to_dataclass_attributes(self, mapping_: Mapping):
        if issubclass(type(mapping_), Mapping):
            for key, value in mapping_.items():
                if key in _CANNOT_BE_NONE and value is None:
                    raise AttributeError(f"Attribute '{key}' cannot be assigned None.")
                if hasattr(self, key):
                    setattr(self, key, value)
                else:
                    raise AttributeError(f"'{mapping_}' object has no attribute '{key}'.")
        else:
            raise TypeError(f"Expected a Mapping object, but got {type(mapping_)}.")


    def _clean_and_formate_html_as_text(html, ignore_links=True):
        return html_to_text(html, ignore_links=ignore_links)


    def _assign_values_to_attributes(self, key: Any, value: Any):
        if hasattr(self, key):
            setattr(self, key, value)
        else:
            raise AttributeError(f"'{series}' object has no attribute '{key}'.")


    def _parse_pandas_series_then_assign_them_to_attributes(self, series: pd.Series) -> None:
        for key in series.keys():
            
            raise ValueError("")

        for key, value in series.items():
            if key in _CANNOT_BE_NONE and value is None:
                raise AttributeError(f"Attribute '{key}' cannot be assigned None.")

            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise AttributeError(f"'{series}' object has no attribute '{key}'.")

    def _parse_named_tuple_then_assign_them_to_attributes(self, named_tuple: NamedTuple) -> None:
        for key, value in named_tuple._asdict().items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise AttributeError(f"'{named_tuple}' object has no attribute '{key}'.")

    def _parse_dictionary_then_assign_them_to_attributes(self, dictionary: dict) -> None:
        for key, value in dictionary.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise AttributeError(f"'{dictionary}' object has no attribute '{key}'.")

    #### Type-checking functions ####
    # NOTE These are primarily to make sure we catch insert errors BEFORE we try to insert values into the database.

    def _type_check_value(value: Any, type_: type) -> Never:
        caller_name = inspect.currentframe().f_back.f_code.co_name or "unknown"
        if value is None:
            raise ValueError(f"Value assigned to '{caller_name}' cannot be None.")
        if not value:
            raise ValueError(f"Value assigned to '{caller_name}' cannot be empty.")
        if not isinstance(value, type_):
            raise ValueError(f"Value assigned to '{caller_name}' not the correct type '{type_}', but type '{type(value)}'")


    def _type_check_sign(self, value: int|float, sign: str = '+') -> Never:
        """
        Type-check a
        """
        caller_name = inspect.currentframe().f_back.f_code.co_name or "unknown"
        _acceptable_values_for_sign = ["+", "-", "positive", "negative"]
        sign = sign.lower()
        if sign is None or sign not in _acceptable_values_for_sign:
            raise ValueError(f"Invalid sign '{sign}'. Acceptable values are '+', '-', 'positive', 'negative', 'Positive', 'Negative'.")
        if not isinstance(value, (int, float)):
            raise ValueError(f"Value '{value}' assigned to '{caller_name}' is not an integer or float.")
        if sign in ["+", "positive"] and value < 0:
            raise ValueError(f"Value '{value}' assigned to '{caller_name}' cannot be positive.")
        if sign in ["-", "negative"] and value > 0:
            raise ValueError(f"Value '{value}' assigned to '{caller_name}' cannot be negative.")


    def _type_check_value_length(self, 
                                 value: Any, 
                                 max_length: int = 64, 
                                 min_length: int = 1, 
                                 exact_length: int = None
                                ) -> Never:
        """
        Type-check the length of a value. If the value is not the correct length, raise a ValueError.
        """
        caller_name = inspect.currentframe().f_back.f_code.co_name or "unknown"

        if not hasattr(value, '__len__'):
            raise ValueError(f"Value assigned to '{caller_name}' does not have a length.")

        # Type-check exact length. NOTE If present, this overrides the max_length and min_length checks.
        if exact_length is not None:
            if len(value) != exact_length:
                raise ValueError(f"""
                    Value assigned to '{caller_name}' is not the correct length. Expected length is {exact_length}, but value length is {len(value)}
                """)
        else:
            # Type-check max length.
            if max_length is None or 0 >= max_length or not isinstance(max_length, int):
                raise ValueError(f"Invalid max_length value. It must be a positive integer, but got {max_length}")
            else:
                if len(value) > max_length:
                    raise ValueError(f"""
                        Value assigned to '{caller_name}' is too long. Max length is {max_length}, but value length is {len(value)}
                        """)
            # Type-check min length.
            if min_length is None or 0 >= min_length or not isinstance(min_length, int):
                raise ValueError(f"Invalid min_length value. It must be a positive integer, but got {max_length}")
            else:
                if len(value) < min_length:
                    raise ValueError(f"""
                        Value assigned to '{caller_name}' is too short. Min length is {min_length}, but value length is {len(value)}"
                    """)

