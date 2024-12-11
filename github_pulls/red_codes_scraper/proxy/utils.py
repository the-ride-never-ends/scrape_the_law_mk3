import csv
import logging
from pathlib import Path


logger = logging.getLogger(__name__)


def open_csv_file_as_set(file_path: Path) -> set[str]:
    """
    Opens a CSV file and returns its contents as a set of strings.

    Args:
        file_path (Path): The path to the CSV file.

    Returns:
        set[str]: A set containing the non-empty values from the first column of the CSV file.

    Raises:
        FileNotFoundError: If the file does not exist.
        PermissionError: If there's no permission to read the file.
        IOError: If an I/O error occurs while reading the file.
        csv.Error: If there's an error in CSV format.
        Exception: For any other unexpected errors.

    Note:
        This function assumes that the CSV file contains one value per row in the first column.
        Empty rows are skipped.

    Example:
        >>> file_path = Path('proxies.csv')
        >>> proxies = open_csv_file_as_set(file_path)
        >>> print(proxies)
        {'http://www.proxy1.com', 'http://www.proxy2.com', 'http://www.proxy3.com'}
    """
    raise_these_errors = (
        FileNotFoundError,
        PermissionError,
        IOError,
        csv.Error,
        Exception,
    )
    try:
        with open(file_path, 'r', newline='') as file:
            csv_reader = csv.reader(file) # Skip rows that have more than two values in them.
            set_ = set(row[0] for row in csv_reader if row and len(row) == 1)
    except raise_these_errors as e:
        logger.error(f"{e.__class__.__qualname__} error opening file '{file_path}': {e}")
        raise e

    if len(set_) == 0:
        logger.warning(f"WARNING: No items were loaded from '{file_path}'.")

    return set_


def save_set_to_csv_file(set_to_save: set, file_path: Path, dont_raise: bool = True) -> None:
    """
    Saves a set of items to a CSV file.

    Args:
        set_to_save (set): The set of items to save to the CSV file.
        file_path (Path): The path to the CSV file.

    Raises:
        PermissionError: If unable to write to the file.
        IOError: If an IO error occurs while writing to the file.
        csv.Error: If a CSV writing error occurs.
        Exception: For any unexpected errors.

    Example CSV Format:
        http://www.proxy1.com
        http://www.proxy2.com
        http://www.proxy3.com
    """
    raise_these_errors = (
        FileNotFoundError,
        PermissionError,
        IOError,
        csv.Error,
        Exception,
    )
    try:
        with open(file_path, 'a', newline='') as file:
            writer = csv.writer(file)
            for item in set_to_save:
                writer.writerow([item])
    except raise_these_errors as e:
        logger.error(f"{e.__class__.__qualname__} error writing to file '{file_path}': {e}")
        if dont_raise:
            return
        else:
            raise e


def validate_path_then_return_it(file_path: str) -> str:
    """
    Validates the given file path and returns its resolved absolute path.

    Args:
        file_path (str): The path to the file to validate.

    Returns:
        str: The resolved absolute path of the file.

    Raises:
        FileNotFoundError: If the file does not exist at the given path.

    Example:
        >>> validate_path_then_return_it('/path/to/existing/file.txt')
        '/absolute/path/to/existing/file.txt'
        >>> validate_path_then_return_it('/path/to/non_existent_file.txt')
        FileNotFoundError: Could not find file '/path/to/non_existent_file.txt'
    """
    path = Path(file_path)
    if path.exists():
        return str(path.resolve())
    else:
        raise FileNotFoundError(f"Could not find file '{file_path}'")