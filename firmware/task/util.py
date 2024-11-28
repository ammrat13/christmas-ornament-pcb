"""
Utility functions for tasks.

This can't be in `__init__.py` because of circular imports. It turns out that
CircuitPython doesn't error out on those.
"""

import asyncio

def periodic(period):
    def decorator(task):
        async def wrapper():
            while True:
                # Make sure to sleep first to avoid the thundering herd problem.
                await asyncio.sleep(period)
                await task()
        return wrapper
    return decorator
