import duckdb
import pandas as pd

from utils.shared.pipelines.async_pipline import AsyncPipeline

from database.mysqldatabase import MySqlDatabase
from config import PROJECT_ROOT

from logger.logger import Logger
logger = Logger(logger_name=__name__)


@dataclass
PipelineConfig:
			table: str # Name of the SQL table to pull from.
			url_id_bin: list[bytes] # Bytes version of the URL id.
			available_cpu_cores: int # Number of CPU cores available for use by the program.
   date_range: tuple(datetime, datetime) # Date range from which the URLs must have been last updated. Due to the computational intensity of dates in MySQL, we compare strings instead of pure dates.

			def __post_init__(self):

		def type_check_date_range(self) -> Never:
					raise_error_message = None
					if not isinstance(date_range, tuple):
								raise_error_message = "data_range is not a tuple, but a {type(date_range)}"
					if len(date_range) != 2
      raise_error_messsage = "len of date_range was not 2, but {len(date_range}"
 				if isinstance((date_range[0], date_range[0],), str):
							raise_error_message = f"date_range values are not both strings, but {type(date_range[0])} and {type(date_range[1])}"
					if raise_error_message:
							logger.error()
							logger.debug(f"date_range: {date_range}")
							raise AttributeError(raise_error_message)

class InputLayer:

			def __init__(self):
					self.max_workers = get_cpu_core_count() - 1 # Leave open 1 core for other uses

			@classmethod
			async def start(cls):
					instance = cls()
					self.parse_schedular_trigger()
					return instance

			async def parse_schedular_trigger(self, trigger: SchedularTrigger):
						"""
						Define a pipeline start-up config based on information in the trigger.
						Args:
								trigger (SchedularTrigger): Dataclass containing trigger.
						Returns:
									PipelineConfig: DataClass containing information necessary to start a pipleine.
						"""

			async def run_pipline(self):
							# Get the data from the database
							self.get_data_for_pipeline()

	async def main():
			# Check for the schedular_trigger.
			# If one occurs, read it and start the process
			if trigger:
							input_layer = await InputLayer.start()
							await input_layer.parse_schedular_trigger(trigger)
							await input_layer.run_pipeline()

if __main__ == "__main__":
							asyncio.run(main())

