import csv
import logging
from pathlib import Path


logger = logging.getLogger(__name__)

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


# Get rid of the proxies we've already used.
def get_rid_of_the_proxies_we_have_already_used(proxies_set: set, used_proxies_set: set) -> tuple[set, set]:
    """
    Remove used proxies from the set of available proxies.
    NOTE: The sets in the tuple may or may not be empty.

    Args:
        proxies_set (set): Set of available proxies.
        used_proxies_set (set): Set of already used proxies.

    Returns:
        tuple: Updated proxies_set and used_proxies_set.
    """
    proxies_set.difference_update(used_proxies_set)
    if len(proxies_set) == 0:
        logger.warning(f"WARNING: All the proxies in proxies_set were already used. Skipping...")
    else:
        logger.info(f"Loaded {len(proxies_set)} proxies from proxies_set.")
    return proxies_set, used_proxies_set