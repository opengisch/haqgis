import logging
import sys

from arq.connections import RedisSettings
from httpx import AsyncClient

logging.basicConfig(stream=sys.stdout, level=logging.INFO)


async def startup(ctx):
    ctx["session"] = AsyncClient()


async def shutdown(ctx):
    await ctx["session"].aclose()


async def download_content(ctx, url, method, params, headers, data):
    session: AsyncClient = ctx["session"]

    source_path = f"http://localhost/{url}"
    if method.upper() == "GET":
        response = await session.get(source_path, params=params, headers=headers)
    elif method.upper() == "POST":
        response = await session.post(source_path, params=params, headers=headers)
    else:
        raise RuntimeError(f"Method {method} not implemented")
    # wait = random.random() * 10
    # logging.info(f"Waiting {wait} seconds")
    # time.sleep(wait)
    return response


# WorkerSettings defines the settings to use when creating the work,
# it's used by the arq cli.
# For a list of available settings, see https://arq-docs.helpmanual.io/#arq.worker.Worker
class WorkerSettings:
    functions = [download_content]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings(host="redis")
