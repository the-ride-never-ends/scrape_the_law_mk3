import asyncio
import time
import pytest
import pytest_asyncio
from typing import Any, Optional, List

# Import the original code (assuming it's in a file called async_pipeline.py)
from utils.shared.pipelines.async_pipeline import AsyncPipeline, PipelineStage

from logger.logger import Logger

logger = Logger(logger_name=__name__)



def cpu_bound_work(x: int) -> int:
    # Simulate CPU-intensive work
    time.sleep(0.1)
    return x * x


# Configure pytest-asyncio as the default async backend
pytest_plugins = ["pytest_asyncio"]

# Set asyncio as the default event loop
@pytest_asyncio.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.mark.asyncio
async def test_basic_pipeline():
    """Test a simple pipeline with three stages"""
    results = []
    
    async def stage1(x: int) -> int:
        await asyncio.sleep(0.1)  # Simulate async work
        return x * 2

    async def stage2(x: int) -> int:
        await asyncio.sleep(0.1)
        return x + 1

    async def stage3(x: int) -> Optional[int]:
        results.append(x)
        return None

    stages = [
        PipelineStage("multiply", 2, stage1),
        PipelineStage("add", 2, stage2),
        PipelineStage("collect", 1, stage3)
    ]

    pipeline = AsyncPipeline(stages)
    input_data = [1, 2, 3, 4, 5]

    try:
        # Run the pipeline with a 15-second timeout
        await asyncio.wait_for(pipeline.run(input_data), timeout=15)
    except asyncio.TimeoutError:
        pytest.fail("Pipeline execution timed out after 15 seconds")

    # Input: [1,2,3,4,5] -> Stage1: [2,4,6,8,10] -> Stage2: [3,5,7,9,11]
    expected = [3, 5, 7, 9, 11]
    logger.debug(f"results: {results}")
    assert sorted(results) == expected

@pytest.mark.asyncio
async def test_process_pool_execution():
    """Test pipeline with CPU-bound processing in a ProcessPoolExecutor"""
    results = []

    async def collect(x: int) -> Optional[int]:
        results.append(x)
        return None

    stages = [
        PipelineStage("square", 2, cpu_bound_work, use_executor=True),
        PipelineStage("collect", 1, collect)
    ]

    pipeline = AsyncPipeline(stages)
    input_data = [1, 2, 3, 4]
    await pipeline.run(input_data)

    expected = [1, 4, 9, 16]  # squares of input numbers
    assert sorted(results) == expected

@pytest.mark.asyncio
async def test_concurrent_limit():
    """Test max_concurrent parameter works correctly"""
    execution_times: List[float] = []
    max_concurrent = 2

    async def limited_stage(x: int) -> int:
        execution_times.append(time.time())
        await asyncio.sleep(0.2)  # Simulate work that takes time
        return x

    stages = [
        PipelineStage("limited", 4, limited_stage, max_concurrent=max_concurrent)
    ]

    pipeline = AsyncPipeline(stages)
    input_data = list(range(6))  # 6 items
    await pipeline.run(input_data)

    # Check that no more than max_concurrent tasks were running simultaneously
    # by analyzing the timestamps when tasks started
    execution_times.sort()
    concurrent_executions = 1
    for i in range(1, len(execution_times)):
        if execution_times[i] - execution_times[i-1] < 0.1:  # Tasks started almost simultaneously
            concurrent_executions += 1
        else:
            concurrent_executions = 1
        assert concurrent_executions <= max_concurrent

@pytest.mark.asyncio
async def test_error_handling():
    """Test that errors in one item don't crash the pipeline"""
    results = []

    async def may_fail(x: int) -> int:
        if x == 2:
            raise ValueError("Simulated error")
        return x

    async def collect(x: int) -> Optional[int]:
        results.append(x)
        return None

    stages = [
        PipelineStage("may_fail", 2, may_fail),
        PipelineStage("collect", 1, collect)
    ]

    pipeline = AsyncPipeline(stages)
    input_data = [1, 2, 3, 4]
    await pipeline.run(input_data)

    # Should have all results except 2 which raised an error
    expected = [1, 3, 4]
    assert sorted(results) == expected

@pytest.mark.asyncio
async def test_empty_input():
    """Test pipeline behavior with empty input"""
    results = []

    async def stage(x: int) -> int:
        results.append(x)
        return x

    stages = [PipelineStage("stage", 1, stage)]
    pipeline = AsyncPipeline(stages)
    
    await pipeline.run([])
    assert len(results) == 0

@pytest_asyncio.fixture
async def simple_pipeline():
    """Fixture providing a simple pipeline for testing"""
    results = []
    
    async def process(x: int) -> int:
        return x * 2

    async def collect(x: int) -> None:
        results.append(x)
        return None

    stages = [
        PipelineStage("process", 2, process),
        PipelineStage("collect", 1, collect)
    ]

    pipeline = AsyncPipeline(stages)
    return pipeline, results

@pytest.mark.asyncio
async def test_pipeline_with_fixture(simple_pipeline):
    """Test using the pipeline fixture"""
    pipeline, results = simple_pipeline
    await pipeline.run([1, 2, 3])
    assert sorted(results) == [2, 4, 6]

@pytest.mark.asyncio
async def test_pipeline_shutdown():
    """Test that pipeline properly shuts down and cleans up resources"""
    async def slow_process(x: int) -> int:
        await asyncio.sleep(0.1)
        return x

    def cpu_work(x: int) -> int:
        time.sleep(0.1)
        return x

    stages = [
        PipelineStage("slow", 2, slow_process),
        PipelineStage("cpu", 2, cpu_work, use_executor=True)
    ]

    pipeline = AsyncPipeline(stages)
    await pipeline.run([1, 2, 3])
    
    # Check if executors are shut down by trying to submit a new task
    # A shutdown executor will raise RuntimeError
    for executor in pipeline.executors.values():
        with pytest.raises(RuntimeError):
            executor.submit(lambda: None)

    # Verify all tasks are completed
    for task_list in pipeline.tasks.values():
        for task in task_list:
            assert task.done()


@pytest.mark.asyncio
async def test_pipeline_order_preservation():
    """Test that the pipeline preserves order of items when using a single worker"""
    results: List[int] = []
    
    async def process(x: int) -> int:
        # Add random delays to ensure order isn't preserved by timing
        await asyncio.sleep(0.1 * (x % 2))  # alternate delays
        return x

    async def collect(x: int) -> None:
        results.append(x)
        return None

    stages = [
        PipelineStage("process", 1, process),  # Single worker to maintain order
        PipelineStage("collect", 1, collect)
    ]
    
    pipeline = AsyncPipeline(stages)
    input_data = list(range(5))
    await pipeline.run(input_data)
    
    assert results == input_data  # Order should be preserved

@pytest.mark.asyncio
async def test_pipeline_backpressure():
    """Test that pipeline handles backpressure when downstream stages are slow"""
    processed_count = 0
    start_time = time.time()
    
    async def fast_producer(x: int) -> int:
        return x

    async def slow_consumer(x: int) -> Optional[int]:
        nonlocal processed_count
        await asyncio.sleep(0.2)  # Simulate slow processing
        processed_count += 1
        return None

    stages = [
        PipelineStage("producer", 3, fast_producer),
        PipelineStage("consumer", 1, slow_consumer, max_concurrent=2)
    ]
    
    pipeline = AsyncPipeline(stages)
    input_data = list(range(10))
    await pipeline.run(input_data)
    
    duration = time.time() - start_time
    assert processed_count == len(input_data)
    assert duration >= 1.0  # Should take at least 1 second due to rate limiting


def sync_handler(x: int) -> int:
    time.sleep(0.1)  # Simulate CPU work
    return x * 2


@pytest.mark.asyncio
async def test_mixed_sync_async_handlers():
    """Test pipeline with mixture of sync and async handlers"""
    results: List[int] = []

    async def async_handler(x: int) -> int:
        await asyncio.sleep(0.1)  # Simulate I/O work
        return x + 1

    async def collect(x: int) -> None:
        results.append(x)
        return None

    stages = [
        PipelineStage("sync", 2, sync_handler, use_executor=True),
        PipelineStage("async", 2, async_handler),
        PipelineStage("collect", 1, collect)
    ]
    
    pipeline = AsyncPipeline(stages)
    await pipeline.run([1, 2, 3])
    
    # 1: (1*2)+1=3, 2: (2*2)+1=5, 3: (3*2)+1=7
    assert sorted(results) == [3, 5, 7]

@pytest.mark.asyncio
async def test_pipeline_cancellation():
    """Test pipeline handles task cancellation gracefully"""
    async def slow_process(x: int) -> int:
        await asyncio.sleep(1.0)
        return x

    stages = [PipelineStage("slow", 2, slow_process)]
    pipeline = AsyncPipeline(stages)
    
    # Start pipeline but cancel it quickly
    task = asyncio.create_task(pipeline.run(list(range(10))))
    await asyncio.sleep(0.1)
    task.cancel()
    
    try:
        await task
    except asyncio.CancelledError:
        # Ensure executors are still properly shut down
        for executor in pipeline.executors.values():
            with pytest.raises(RuntimeError):
                executor.submit(lambda: None)

@pytest.mark.asyncio
async def test_large_data_volume():
    """Test pipeline with larger volume of data"""
    processed = 0
    
    async def counter(x: int) -> int:
        nonlocal processed
        processed += 1
        return x

    stages = [PipelineStage("counter", 4, counter)]
    pipeline = AsyncPipeline(stages)
    
    large_input = list(range(1000))
    await pipeline.run(large_input)
    assert processed == len(large_input)


@pytest.mark.asyncio
async def test_exception_propagation():
    """Test that exceptions in one stage don't affect processing of other items"""
    results: List[int] = []
    
    async def may_fail(x: int) -> int:
        if x % 3 == 0:
            raise ValueError(f"Error processing {x}")
        return x

    async def collect(x: int) -> None:
        results.append(x)
        return None

    stages = [
        PipelineStage("may_fail", 2, may_fail),
        PipelineStage("collect", 1, collect)
    ]
    
    pipeline = AsyncPipeline(stages)
    await pipeline.run(list(range(5)))
    
    # Should have all numbers except multiples of 3
    assert sorted(results) == [1, 2, 4]


@pytest.mark.asyncio
async def test_empty_stage():
    """Test pipeline behavior when a stage's handler returns None for all items"""
    results: List[int] = []
    
    async def filter_all(x: int) -> Optional[int]:
        return None  # Filter out everything
        
    async def collect(x: int) -> None:
        results.append(x)
        return None

    stages = [
        PipelineStage("filter", 2, filter_all),
        PipelineStage("collect", 1, collect)
    ]
    
    pipeline = AsyncPipeline(stages)
    await pipeline.run([1, 2, 3])
    assert len(results) == 0  # Nothing should make it to collection

@pytest.mark.asyncio
@pytest.mark.asyncio
async def test_nested_pipeline():
    """Test pipeline handling nested data structures"""
    results = []
    
    async def flatten(x: Any) -> Optional[int]:
        if isinstance(x, list):
            # Skip lists - we'll process their items individually
            return None
        return x
        
    async def collect(x: int) -> None:
        results.append(x)
        return None

    stages = [
        PipelineStage("flatten", 2, flatten),
        PipelineStage("collect", 1, collect)
    ]
    
    # Flatten the input before sending to pipeline
    flattened_input = []
    for item in [1, [2, 3], 4]:
        if isinstance(item, list):
            flattened_input.extend(item)
        else:
            flattened_input.append(item)
    
    pipeline = AsyncPipeline(stages)
    await pipeline.run(flattened_input)
    assert sorted(results) == [1, 2, 3, 4]

@pytest.mark.asyncio
async def test_long_pipeline():
    """Test pipeline with many stages to ensure proper propagation"""
    results = []
    
    async def add_one(x: int) -> int:
        return x + 1
        
    async def collect(x: int) -> None:
        results.append(x)
        return None

    # Create a pipeline with 10 stages that each add 1
    stages = [PipelineStage(f"add_{i}", 1, add_one) for i in range(10)]
    stages.append(PipelineStage("collect", 1, collect))
    
    pipeline = AsyncPipeline(stages)
    await pipeline.run([0])
    assert results[0] == 10  # Should have added 1 ten times

@pytest.mark.asyncio
async def test_worker_count_stress():
    """Test pipeline with varying worker counts to ensure proper load distribution"""
    processed_by_worker: dict[str, int] = {}
    
    async def track_worker(x: int) -> int:
        worker_id = f"worker_{asyncio.current_task().get_name()}"
        processed_by_worker[worker_id] = processed_by_worker.get(worker_id, 0) + 1
        await asyncio.sleep(0.01)  # Small delay to ensure work distribution
        return x

    stages = [
        PipelineStage("track", 4, track_worker)  # Use 4 workers
    ]
    
    pipeline = AsyncPipeline(stages)
    await pipeline.run(list(range(20)))
    
    # Verify work was distributed across workers
    assert len(processed_by_worker) == 4
    # Check that no single worker did more than 50% of the work
    assert all(count <= 10 for count in processed_by_worker.values())

@pytest.mark.asyncio
async def test_pipeline_filtering():
    """Test pipeline's ability to filter items by returning None"""
    results = []
    
    async def filter_evens(x: int) -> Optional[int]:
        return x if x % 2 == 0 else None
        
    async def collect(x: int) -> None:
        results.append(x)
        return None

    stages = [
        PipelineStage("filter", 2, filter_evens),
        PipelineStage("collect", 1, collect)
    ]
    
    pipeline = AsyncPipeline(stages)
    await pipeline.run(range(5))
    assert sorted(results) == [0, 2, 4]


@pytest.mark.asyncio
async def test_pipeline_dynamic_timing():
    """Test pipeline with handlers that take variable time to complete"""
    results = []
    execution_order = []
    
    async def variable_delay(x: int) -> int:
        delay = 0.1 if x % 2 == 0 else 0.05  # even numbers take longer
        await asyncio.sleep(delay)
        execution_order.append(x)
        return x
        
    async def collect(x: int) -> None:
        results.append(x)
        return None

    stages = [
        PipelineStage("delay", 3, variable_delay),  # Multiple workers to handle varying delays
        PipelineStage("collect", 1, collect)
    ]
    
    pipeline = AsyncPipeline(stages)
    input_data = list(range(6))
    await pipeline.run(input_data)
    
    assert sorted(results) == input_data  # All items processed
    assert execution_order != input_data  # Order changed due to varying delays

@pytest.mark.asyncio
async def test_pipeline_memory_behavior():
    """Test pipeline handles large items without keeping them all in memory"""
    results = []
    current_memory_items = set()
    max_concurrent_items = 0
    
    async def track_memory(x: int) -> int:
        nonlocal max_concurrent_items
        current_memory_items.add(x)
        max_concurrent_items = max(max_concurrent_items, len(current_memory_items))
        await asyncio.sleep(0.01)  # Small delay to ensure overlap
        current_memory_items.remove(x)
        return x
        
    async def collect(x: int) -> None:
        results.append(x)
        return None

    stages = [
        PipelineStage("memory_track", 2, track_memory, max_concurrent=3),
        PipelineStage("collect", 1, collect)
    ]
    
    pipeline = AsyncPipeline(stages)
    await pipeline.run(range(20))
    
    assert max_concurrent_items <= 3  # Never more than 3 items in memory
    assert sorted(results) == list(range(20))  # All items processed


from concurrent.futures import ProcessPoolExecutor


@pytest.mark.asyncio
async def test_pipeline_shutdown_during_processing():
    """Test pipeline handles shutdown gracefully while items are still processing"""
    processed = set()
    shutdown_called = False
    
    async def slow_process(x: int) -> int:
        await asyncio.sleep(0.1)
        processed.add(x)
        return x
    
    # Create a custom executor that tracks shutdown
    class TrackingExecutor(ProcessPoolExecutor):
        def shutdown(self, *args, **kwargs):
            nonlocal shutdown_called
            shutdown_called = True
            super().shutdown(*args, **kwargs)
    
    stages = [PipelineStage("slow", 2, slow_process, use_executor=True)]
    pipeline = AsyncPipeline(stages)
    
    # Replace the executor with our tracking version
    pipeline.executors["slow"] = TrackingExecutor(max_workers=2)
    
    # Start processing but don't wait for completion
    task = asyncio.create_task(pipeline.run(range(10)))
    await asyncio.sleep(0.05)  # Let some processing start
    
    # Cancel the task mid-processing
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    
    assert shutdown_called  # Executor was properly shut down
    assert len(processed) < 10  # Not all items were processed


if __name__ == '__main__':
    pytest.main([__file__])