"""
All the tasks we're going to run in the background.

A task is just an `async` function. It has to run forever, but we have no way to
check for that.
"""

import adafruit_logging
import asyncio

import task.heap_monitor

logger = adafruit_logging.getLogger()

_tasks = [
    task.heap_monitor.run,
]
"""List of all the `async` functions to run."""

async def run():
    """
    Run all the tasks in the background, concurrently.
    """

    # Run all the tasks concurrently. Any exceptions will be passed up to the
    # main code.
    logger.info("Starting all the tasks...")
    await asyncio.gather(*[task() for task in _tasks])

    logger.error("All tasks completed!")
