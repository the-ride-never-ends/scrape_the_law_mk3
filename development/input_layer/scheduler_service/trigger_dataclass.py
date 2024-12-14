

from dataclasses import dataclass
from typing import Any, Generator
from queue import Queue
from uuid import UUID


@dataclass
class Trigger:
    """
    Triggers a scrape for the URL attached to a specific document.

    Attributes:
        document_id (UUID): The byte form of a UUID for a specific document.
    """
    document_id: UUID


@dataclass
class YieldFunctionalityBaseDataClass:
    """
    A base class that provides functionality for storing and yielding items in batches.

    Attributes:
        yield_size (int): The number of items to yield in each batch.
        _dict_of_lists_to_yield (dict[str, Queue[Any]]): A dictionary mapping queue names to Queue objects.
        _queue_name (str): The name of the default queue for this instance.

    Methods:
        __post_init__(): Initializes the instance after __init__ is called.
        yield_items_from_queue(queue_name: str = None): Yields batches of items from a specified queue.
        add_items_to_specified_queue(queue_name: str, items: list[Any]): Adds items to a specified queue.

    Raises:
        ValueError: If yield_size is not a positive integer.
    """
    yield_size: int
    _dict_of_lists_to_yield: dict[str, Queue[Any]]
    _queue_name: str


    def __post_init__(self):
        if self.yield_size <= 0:
            raise ValueError("yield_size must be a positive integer")
        # The queue's name is based on the subclass calling this function.
        self._queue_name = self.__class__.__qualname__


    def yield_items_from_queue(self, queue_name: str = None) -> Generator[list[Any], None, None]:
        """
        Yield items from a specified queue in batches.

        Args:
            queue_name (str, optional): The name of the queue to yield from. Defaults to the class' main queue.

        Yields:
            list[Any]: A batch of items from the specified queue.
        """
        # Get which queue we're yielding from.
        # Defaults to the class' main queue.
        queue_name = queue_name or self._queue_name
        queue_to_yield: Queue[Any] = self._dict_of_lists_to_yield[queue_name]

        while not queue_to_yield.empty():
            batch = []
            for _ in range(self.yield_size):
                if queue_to_yield.empty():
                    break
                batch.append(queue_to_yield.get())
            
            if batch:
                yield batch

    def add_items_to_specified_queue(self, queue_name: str, items: list[Any]) -> None:
        """
        Add items to a specified queue, creating the queue if it doesn't exist.

        Args:
            queue_name (str): The name of the queue to add items to.
            items (list[Any]): The list of items to add to the queue.
        """
        # If the queue doesn't exist, add it in.
        if queue_name not in self._dict_of_lists_to_yield:
            self._dict_of_lists_to_yield[queue_name] = Queue()

        for item in items:
            self._dict_of_lists_to_yield[queue_name].put(item)



@dataclass
class TriggerList(YieldFunctionalityBaseDataClass):
    """
    A container to store, manage, and yield Triggers in batches based on a specified batch size.

    Methods:
        trigger_list: A property that yields batches of Triggers.
        trigger_list.setter: A method to add new Triggers to the container.
    """

    def __post_init__(self):
        super().__post_init__()
        self._dict_of_lists_to_yield[self._queue_name] = Queue() # type == Queue[Trigger]

    @property
    def trigger_list(self) -> Generator[Trigger]:
        yield self.yield_items_from_queue()

    @trigger_list.setter
    def trigger_list(self, value: list[Trigger]) -> None:
        self.add_items_to_specified_queue(self._queue_name, value)

