import asyncio
import aiohttp
from typing import Optional

from utils.patch.methods import patch, patchable


class AioHttpTimeoutException(asyncio.TimeoutError):
    pass


@patch(aiohttp.helpers.TimerContext)
class TimerContext:
    @patchable
    def __exit__(self, *args, **kwargs) -> Optional[bool]:
        try:
            return self.old___exit__(*args, **kwargs)
        except asyncio.TimeoutError:
            raise AioHttpTimeoutException from None
