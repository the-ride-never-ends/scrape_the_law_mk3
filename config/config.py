import os

from .utils.config._get_config import get_config as config
from logger.logger import Logger
logger = Logger(logger_name=__name__)

# Define hard-coded constants
script_dir = os.path.dirname(os.path.realpath(__file__))
PROJECT_ROOT = script_dir = os.path.dirname(script_dir)
MAIN_FOLDER = os.path.dirname(script_dir)
YEAR_IN_DAYS: int = 365
DEBUG_FILEPATH: str = os.path.join(MAIN_FOLDER, "debug_logs")
RANDOM_SEED: int = 420

# Get YAML config variables
try:
    # SYSTEM
    path = "SYSTEM"
    SKIP_STEPS: bool = config(path, 'SKIP_STEPS') or True
    FILENAME_PREFIX: str = config(path, 'FILENAME_PREFIX') or f"{MAIN_FOLDER}"

    # FILENAMES
    path = "FILENAMES"
    INPUT_FILENAME: str = config(path, 'INPUT_FILENAME') or "input.csv"

    # PRIVATE PATH FOLDERS
    path = "PRIVATE_FOLDER_PATHS"
    INPUT_FOLDER: str = config(path, 'INPUT_FOLDER') or os.path.join(MAIN_FOLDER, "input")
    OUTPUT_FOLDER: str = config(path, 'OUTPUT_FOLDER') or os.path.join(MAIN_FOLDER, "output")

    # MYSQL
    path = "MYSQL"
    HOST: str = config(path, 'HOST')
    USER: str = config(path, 'USER')
    PORT: int = config(path, 'PORT')
    PASSWORD: str = config(path, 'PASSWORD')
    DATABASE_NAME: str = config(path, 'DATABASE_NAME')
    SQL_SCRIPT_FILE_PATH: str = config(path, 'SQL_SCRIPT_FILE_PATH') or ""
    INSERT_BATCH_SIZE: int = config(path, 'INSERT_BATCH_SIZE') or 20
    MYSQL_SCRIPT_FILE_PATH: str = os.path.join(SQL_SCRIPT_FILE_PATH, "mysql")
    DUCKDB_SCRIPT_FILE_PATH: str = os.path.join(SQL_SCRIPT_FILE_PATH, "duckdb")

    logger.info("YAML configs loaded.")

except KeyError as e:
    logger.exception(f"Missing configuration item: {e}")
    raise KeyError(f"Missing configuration item: {e}")

except Exception as e:
    logger.exception(f"Could not load configs: {e}")
    raise e

