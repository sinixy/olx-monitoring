import asyncio
from functools import wraps, partial


def async_wrap(func):
    @wraps(func)
    async def run(*args, loop=None, executor=None, **kwargs):
        if loop is None:
            loop = asyncio.get_event_loop()
        pfunc = partial(func, *args, **kwargs)
        return await loop.run_in_executor(executor, pfunc)
    return run


def prettify_duration(tdelta):
    total = tdelta.total_seconds()
    if total >= 3600 * 24:
        return str(round(total / (3600*24), 1)) + ' дн.'
    elif total >= 3600:
        return str(round(total / 3600, 1)) + ' год.'
    elif total >= 60:
        return str(round(total / 60, 1)) + ' хв.'
    else:
        return str(total) + ' с.'