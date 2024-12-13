# conftest.py
import logging
from pathlib import Path
import time


import pytest


from logger.utils.logger.move_logs_folders_into_this_folder_if_there_are_too_many_of_them import (
    move_logs_folders_into_this_folder_if_there_are_too_many_of_them
)
from logger.utils.logger.delete_empty_files_in import delete_empty_files_in
from logger.utils.logger.delete_empty_folders_in import delete_empty_folders_in
from logger.utils.logger.close_all_loggers import close_all_loggers


def pytest_sessionfinish(session, exitstatus):
    """Run after all tests are completed, regardless of pass/fail status"""

    close_all_loggers()

    # Give OS a moment to release file handles
    time.sleep(0.1)

    debug_folder = Path("debug_logs")  # Adjust path as needed
    overflow_folder = debug_folder / "overflow_debug_logs"
    
    delete_empty_files_in(debug_folder, with_ending=".log")
    delete_empty_folders_in(debug_folder)

    move_logs_folders_into_this_folder_if_there_are_too_many_of_them(
        overflow_debug_folder=str(overflow_folder),
        debug_log_folder=str(debug_folder)
    )