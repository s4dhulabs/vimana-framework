import asyncio


def run_async(coro):
    """Run an async coroutine from synchronous code.
    Safe for Python 3.10+ where get_event_loop() may raise."""
    try:
        asyncio.get_running_loop()
        raise RuntimeError(
            "run_async() called from within a running event loop. "
            "Use 'await' instead."
        )
    except RuntimeError as exc:
        if "no running event loop" not in str(exc).lower():
            raise
    return asyncio.run(coro)
