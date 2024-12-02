import asyncio
import time
import pytest
from typing import Optional, List

# Import the original code (assuming it's in a file called async_pipeline.py)
from utils.shared.limiters.async_pipeline import AsyncPipeline, PipelineStage

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
    await pipeline.run(input_data)

    # Input: [1,2,3,4,5] -> Stage1: [2,4,6,8,10] -> Stage2: [3,5,7,9,11]
    expected = [3, 5, 7, 9, 11]
    assert sorted(results) == expected

@pytest.mark.asyncio
async def test_process_pool_execution():
    """Test pipeline with CPU-bound processing in a ProcessPoolExecutor"""
    results = []

    def cpu_bound_work(x: int) -> int:
        # Simulate CPU-intensive work
        time.sleep(0.1)
        return x * x

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

@pytest.fixture
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
    
    # Verify executors are shut down
    for executor in pipeline.executors.values():
        assert executor._shutdown

    # Verify all tasks are completed
    for task_list in pipeline.tasks.values():
        for task in task_list:
            assert task.done()

if __name__ == '__main__':
    pytest.main([__file__])