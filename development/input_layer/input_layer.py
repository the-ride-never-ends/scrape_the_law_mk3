import asyncio
from datetime import datetime
import multiprocessing
from typing import (Any, Generator, Never)


import duckdb
import pandas as pd


from database.mysql_database import MySqlDatabase
from config.config import PROJECT_ROOT

from logger.logger import Logger
logger = Logger(logger_name=__name__)

from development.input_layer.autoscraper_web_scraper.auto_scraper_base_class import (
    TriggerList,
    Trigger
)

import asyncio
from asyncio import Task
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from typing import Any, Callable, Optional


from logger.logger import Logger
logger = Logger(logger_name=__name__)


@dataclass
class PipelineStage:
    name: str
    worker_count: int
    handler: Callable
    use_executor: bool = False
    max_concurrent: Optional[int] = None

class AsyncPipeline:
    """
    Generic async pipeline system that can handle multiple stages of processing
    with configurable concurrency and execution strategies.
    """
    def __init__(self, stages: list[PipelineStage]):
        self.stages: list[PipelineStage] = stages
        self.queues: dict[str, asyncio.Queue] = {}
        self.tasks: dict[str, list[Task]] = {}
        self.executors: dict[str, ProcessPoolExecutor] = {}
        self.semaphores: dict[str, asyncio.Semaphore] = {}
        
        # Set up queues and concurrency controls
        for stage in stages:
            self.queues[stage.name] = asyncio.Queue()
            if stage.max_concurrent:
                self.semaphores[stage.name] = asyncio.Semaphore(stage.max_concurrent)
            if stage.use_executor:
                self.executors[stage.name] = ProcessPoolExecutor(max_workers=stage.worker_count)

    async def stage_worker(self, 
                         stage: PipelineStage,
                         worker_id: int,
                         input_queue: asyncio.Queue,
                         output_queue: Optional[asyncio.Queue] = None
                        ) -> None:
        """
        Asynchronous worker function for a pipeline stage.

        This function processes items from the input queue, applies the stage's handler,
        and optionally forwards results to the output queue. It handles concurrency limits,
        process pool execution, and graceful shutdown. 
        NOTE: The worker continues processing until it receives a None item, signaling shutdown.

        Args:
            stage (PipelineStage): The pipeline stage configuration.
            worker_id (int): Unique identifier for this worker within the stage.
            input_queue (asyncio.Queue): Queue from which to receive input items.
            output_queue (Optional[asyncio.Queue]): Queue to send processed items to the next stage, if any.
        """
        logger.info(f"Starting {stage.name}_{worker_id}")
        
        while True:
            try:
                # Get input with optional rate limiting
                if stage.name in self.semaphores:
                    async with self.semaphores[stage.name]:
                        item = await input_queue.get()
                else:
                    item = await input_queue.get()

                if item is None:
                    logger.info(f"{stage.name}_{worker_id} received shutdown signal")
                    input_queue.task_done()

                    # Only propagate shutdown signal if this is the last worker to receive it
                    if output_queue and input_queue.empty():
                        for _ in range(self.stages[self.stages.index(stage) + 1].worker_count):
                            await output_queue.put(None)
                    break

                # Process the item with semaphore around the entire processing
                try:
                    if stage.name in self.semaphores:
                        async with self.semaphores[stage.name]:
                            if stage.use_executor:
                                loop = asyncio.get_running_loop()
                                result = await loop.run_in_executor(
                                    self.executors[stage.name],
                                    stage.handler,
                                    item
                                )
                            else:
                                result = await stage.handler(item)
                    else:
                        if stage.use_executor:
                            loop = asyncio.get_running_loop()
                            result = await loop.run_in_executor(
                                self.executors[stage.name],
                                stage.handler,
                                item
                            )
                        else:
                            result = await stage.handler(item)

                    # Forward result to next stage if it exists
                    if output_queue and result is not None:
                        await output_queue.put(result)
                        
                    logger.info(f"{stage.name}_{worker_id} processed item successfully")
                
                except Exception as e:
                    logger.exception(f"Error in {stage.name}_{worker_id}: {e}")
                    
                finally:
                    input_queue.task_done()

            except Exception as e:
                logger.error(f"Critical error in {stage.name}_{worker_id}: {e}")
                break

    async def run(self, input_items: list[Any]) -> None:
        """
        Run the pipeline with the given input items
        """
        try:
            # Start all workers for each stage
            for i, stage in enumerate(self.stages):
                output_queue = self.queues[self.stages[i + 1].name] if i < len(self.stages) - 1 else None
                
                self.tasks[stage.name] = [
                    asyncio.create_task(
                        self.stage_worker(
                            stage,
                            worker_id,
                            self.queues[stage.name],
                            output_queue
                        )
                    )
                    for worker_id in range(stage.worker_count)
                ]

            # Feed initial items into first stage
            first_queue = self.queues[self.stages[0].name]
            for item in input_items:
                await first_queue.put(item)

            # Add shutdown signals to first stage only
            for _ in range(self.stages[0].worker_count):
                await first_queue.put(None)

            # Wait for all stages to complete
            for stage in self.stages:
                await self.queues[stage.name].join()

            # Wait for all tasks to complete
            for task_list in self.tasks.values():
                await asyncio.gather(*task_list)

        finally:
            # Clean up executors
            for executor in self.executors.values():
                executor.shutdown()


@dataclass
class PipelineConfig:
    """
    table: (str) Name of the SQL table to pull from the on-disk MySQL database.
    url_id_bin: (list[bytes]) List of bytes versions of the URL id.
    date_range: (tuple[datetime, datetime]) Date range from which the URLs must have been last updated. 
        NOTE: Due to the computational intensity of dates in MySQL, we compare strings instead of pure dates.
    """
    table: str = None
    url_id_bin: list[bytes] = None
    date_range: tuple[datetime, datetime] = None

    def __post_init__(self):
        self.type_check_date_range()

    def type_check_date_range(self) -> Never:
        raise_error_message = None

        if not isinstance(self.date_range, tuple):
            raise_error_message = f"data_range is not a tuple, but a {type(self.date_range)}"

        if len(self.date_range) != 2:
            raise_error_message = f"len of self.date_range was not 2, but {len(self.date_range)}"

        if isinstance((self.date_range[0], self.date_range[0],), str):
            raise_error_message = f"self.date_range values are not both strings, but {type(self.date_range[0])} and {type(self.date_range[1])}"

        if raise_error_message is not None:
            logger.error()
            logger.debug(f"self.date_range: {self.date_range}")
            raise AttributeError(raise_error_message)


class InputLayer:

    def __init__(self, max_workers: int = multiprocessing.cpu_count()):
        self.max_workers = max_workers - 1 # Leave open 1 core for other uses


    @classmethod
    async def start(cls):
        instance = cls()
        instance.parse_schedular_trigger()
        return instance


    async def parse_schedular_trigger(self, trigger: Trigger):
        """
        Define a pipeline start-up config based on information in the trigger.
        Args:
            trigger (SchedularTrigger): Dataclass containing trigger.
        Returns:
            PipelineConfig: DataClass containing information necessary to start a pipleine.
        """

    async def define_workers(self):
        pass


    async def get_data_for_pipeline(self):
        pass


    async def run_pipline(self, pipeline):
        # Get the data from the database
        await self.get_data_for_pipeline()


    async def main(self, trigger_list, pipeline):
        # Check for the schedular_trigger.
        # If one occurs, read it and start the process
        for trigger in trigger_list:
            if trigger:
                input_layer: InputLayer = await InputLayer.start()
                await self.parse_schedular_trigger(trigger)
                await self.run_pipline(self, pipeline)
                await self.run_pipeline(pipeline)


@dataclass
class PipelineStage:
    """
    Represents a stage in the pipeline with its configuration.

    Attributes:
        name (str): The name of the pipeline stage.
        worker_count (int): The number of worker processes or threads for this stage.
        handler (Callable): The function to be executed for processing in this stage.
        use_executor (bool): Whether to use a ProcessPoolExecutor for this stage. Defaults to False.
        max_concurrent (Optional[int]): The maximum number of concurrent operations allowed. 
                                        If None, no limit is applied. Defaults to None.
        next_stage (Union[str, list[str]]): The name(s) of the next stage(s) in the pipeline. 
                                            Can be a single string or a list of strings. 
                                            If None, this is the final stage. Defaults to None.
    """
    name: str = None
    worker_count: int = None
    handler: Callable = None
    use_executor: bool = False
    max_concurrent: int = None,
    next_stage: str|list[str] = None

from utils.shared.open_and_save_any_file import FileOpener
import os
from config.config import PROJECT_ROOT
from pathlib import Path


import os
from datetime import datetime

def get_path_to_the_most_recently_created_file_in_this_directory(file_dir: str | Path, return_this_many_files: int = 1) -> str:
    """
    Find the most recently created file in the specified directory.

    This function scans the given directory and returns the full path to the file
    with the most recent creation time.

    Args:
        file_dir (str | Path): The directory to search for files.

    Returns:
        str: The full path to the most recently created file.

    Raises:
        ValueError: If no files are found in the specified directory.

    Example:
        >>> latest_file = get_path_to_the_most_recently_created_file_in_this_directory("/path/to/directory")
        >>> print(latest_file)
        /path/to/directory/most_recent_file.txt
    """
    if not os.path.exists(file_dir):
        raise FileNotFoundError(f"Folder '{file_dir}' does not exist.")

    file_creation_times = []
    for file in os.listdir(file_dir):
        this_files_path = os.path.join(file_dir, file)
        try:
            this_files_timestamp = datetime.fromtimestamp(os.path.getctime(this_files_path))
        except Exception:
            pass
        file_creation_times.append((this_files_timestamp, this_files_path,))

    if file_creation_times: # Sort the files by their creation date.
        latest_file = sorted(file_creation_times, key=lambda x: x[0])[-1][1]
        logger.info(f"Latest file: {latest_file}")
        return latest_file
    else:
        raise ValueError(f"No files in input directory '{file_dir}'.")

async def main():

    # Get the latest file in the trigger lists folder
    this_files_dir = os.path.dirname(os.path.realpath(__file__))
    trigger_list_dir = os.path.join(this_files_dir, "schedular_service", "trigger_lists")
    latest_trigger_list = get_path_to_the_most_recently_created_file_in_this_directory(trigger_list_dir)


    # Get the trigger from the file.
    # File should be a CSV file.
    open_ = FileOpener()
    latest_trigger_list: dict = open_.this_file(latest_trigger_list)


    # Get the number of available CPUs and divide them equally.
    num_cpus_per_process = abs((multiprocessing.cpu_count() - 1) // 3)  # NOTE '//' means Integer division (Floor division). See: https://www.geeksforgeeks.org/division-operators-in-python/
    if num_cpus_per_process <= 0:
        raise ValueError(f"No CPUs are available to run the input_layer. num_cpus_per_process: '{num_cpus_per_process}'")


    # Define the parameters of the pipeline.
    web_scraper = PipelineStage(
                        name="web_scraper", 
                        worker_count=num_cpus_per_process, 
                        handler=None,
                        use_executor=False,
                        max_concurrent=2,
                        next_stage=["pdf_processor", "html_processor"]
                        )
    pdf_processor = PipelineStage(
                        name="pdf_processor", 
                        worker_count=num_cpus_per_process, 
                        handler=None,
                        use_executor=True,
                        max_concurrent=2
                        )
    html_processor = PipelineStage(
                        name="html_processor", 
                        worker_count=num_cpus_per_process, 
                        handler=None,
                        use_executor=True,
                        max_concurrent=2
                        )

    pipeline = AsyncPipeline([web_scraper, pdf_processor, html_processor])


    # Load the trigger from trigger list.


    pipeline.run(trigger)

    for trigger in TriggerList:
        pass

    args = {
        "desired_documents": ','.join(['%s'] * len(doc_id_bin))
    }

    with MySqlDatabase() as db:
        db: MySqlDatabase
        db.execute_sql_command(
            """
            SELECT * FROM documents WHERE doc_id_bin IN ({desired_documents})
            """,
            args=args
        )

    conn = duckdb.connect(":memory:")
    query = "SELECT * FROM data"
    _trigger_list: list[Any] = conn.execute(query).fetchall()

    if _trigger_list is not None:
        trigger_list = TriggerList(_trigger_list)
        run: InputLayer = await InputLayer().start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("input_layer stopped")
