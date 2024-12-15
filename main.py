import asyncio
from datetime import datetime
import os
import sys
import time


from utils.shared.next_step import next_step
from utils.shared.sanitize_filename import sanitize_filename

import multiprocessing

from database.mysql_database import MySqlDatabase
from config.config import *
from logger.logger import Logger


logger = Logger(logger_name=__name__)


# 1. Get codes from LexisNexus (3,200 codes)
# - 1.1 Make Chrome extension to scrape the pages you visit TODO See if it can be HTML instead of PDF
# - 1.2 Go to law library and run the script
# 2. Scrape Municode (3,528 codes)
# - 2.1 Figure out API
# - 2.2 Scrape via API
# 3. Scrape American Legal (2,180 codes) TODO Ditto API
# 4. Scrape General Code (1,601 codes) TODO Ditto API
# 5. Get all the other websites
# - 5.1 General Crawler.

from dataclasses import dataclass

from utils.shared.make_sha256_hash import make_sha256_hash

from typing import Any


import pandas as pd

# Wrote more SAD.
# Wrote yet more SAD.
# Wrote data dictionaries for MySQL, module inputs/outputs

async def main():

    logger.info("Begin __main__")
    logger.info("Insert program logic here...",t=5)
    logger.info("End __main__")
    sys.exit(0)


if __name__ == "__main__":
    import os
    base_name = os.path.basename(__file__) 
    program_name = os.path.split(os.path.split(__file__)[0])[1] if base_name != "main.py" else os.path.splitext(base_name)[0] 
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"'{program_name}' program stopped.")


