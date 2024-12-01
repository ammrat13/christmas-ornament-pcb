"""
Utility functions for tasks.

This can't be in `__init__.py` because of circular imports. It turns out that
CircuitPython doesn't error out on those.
"""

import asyncio

def periodic(period, delay_start=True):
    def decorator(task):
        async def wrapper():
            # If we were told to delay the start, do so. This is on by default
            # to avoid the thundering herd problem.
            if delay_start:
                await asyncio.sleep(period)
            # Now just run the task every so often.
            while True:
                await task()
                await asyncio.sleep(period)
        return wrapper
    return decorator
