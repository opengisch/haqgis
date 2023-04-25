import logging
import os
import sys

from arq.connections import RedisSettings
from arq.worker import Retry
from httpx import AsyncClient, ReadTimeout

logging.basicConfig(stream=sys.stdout, level=logging.INFO)


timeout = float(os.environ.get("TIMEOUT", 10))


async def startup(ctx):
    """
    Initialize http client and preload projects (send GetCapabilities). This way we are sure
    we are in a responsive and performant state when we start accepting jobs
    """
    ctx["session"] = AsyncClient()
    preload_projects = os.environ.get("PRELOAD_PROJECTS")
    if preload_projects:
        for project in preload_projects.split(","):
            url = f"http://localhost/ogc/{project}?SERVICE=WMS&REQUEST=GetCapabilities"
            logging.info(f"Preloading project `{project}` from `{url}`")
            await ctx["session"].get(url)


async def shutdown(ctx):
    """
    Cleanup http client
    """
    logging.info("Shutting down")
    await ctx["session"].aclose()


async def download_content(ctx, url, method, params, headers, data):
    """
    Forwards any request to the local http server and returns the response.
    Will signal a `Retry` if the request takes more than the timeout in seconds
    specified via `TIMEOUT` environment variable.
    """
    logging.info(f'{method} {url} (try {ctx["job_try"]})')
    session: AsyncClient = ctx["session"]

    source_path = f"http://localhost/{url}"
    logging.info(headers)
    try:
        if method.upper() == "GET":
            response = await session.get(
                source_path, params=params, headers=headers, timeout=timeout
            )
        elif method.upper() == "POST":
            response = await session.post(
                source_path, params=params, headers=headers, data=data, timeout=timeout
            )
        else:
            raise RuntimeError(f"Method {method} not implemented")
    except ReadTimeout:
        raise Retry()

    return response


# WorkerSettings defines the settings to use when creating the work,
# it's used by the arq cli.
# For a list of available settings, see https://arq-docs.helpmanual.io/#arq.worker.Worker
class WorkerSettings:
    functions = [download_content]
    on_startup = startup
    on_shutdown = shutdown
    max_tries = int(os.environ.get("RETRIES", 10))
    redis_settings = RedisSettings(host="redis")
