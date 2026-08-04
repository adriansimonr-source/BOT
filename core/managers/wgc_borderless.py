import asyncio
import sys
from functools import lru_cache


MIN_BORDERLESS_BUILD = 20348
ACCESS_ALLOWED = 4


def is_borderless_capture_supported():
    if sys.platform != "win32":
        return False
    try:
        return sys.getwindowsversion().build >= MIN_BORDERLESS_BUILD
    except AttributeError:
        return False


async def _request_access():
    from winrt.windows.graphics.capture import (
        GraphicsCaptureAccess,
        GraphicsCaptureAccessKind,
    )

    return await GraphicsCaptureAccess.request_access_async(
        GraphicsCaptureAccessKind.BORDERLESS
    )


@lru_cache(maxsize=1)
def request_borderless_capture_access():
    if not is_borderless_capture_supported():
        return False
    try:
        return int(asyncio.run(_request_access())) == ACCESS_ALLOWED
    except (ImportError, OSError, RuntimeError, TypeError, ValueError):
        return False
