
import os
from pathlib import Path

from .trigger_dataclass import Trigger, TriggerList
from utils.shared.open_and_save_any_file import FileOpener
from utils.shared.open_csv_file_as_set import open_csv_file_as_set

open_ = FileOpener()

class SchedulerService:

    def __init__(self):
        self.trigger_list_folder = Path("trigger_lists").resolve()
        self.trigger_list: TriggerList = None

    def get_triggers(self):
        open


    def load_latest_trigger_list_from_triggers_lists_folder(self):
        file_path = 
        open_.this_file()


    def main(self):
        # Pre-step: Receive start-up signal. 
        # NOTE This is done automatically when the input layer sub-program is started.

        # Step 1: Load in the trigger list from the most recently created CSV file in the trigger lists folder.

        # Step 2: Format the imported CSV data as a TriggerList

        # Step 3: Get the documents from the server based on trigger list.

        # Step 4: Group the documents by number of sources.

        # Step 5: Assign each
        pass