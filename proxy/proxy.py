import asyncio
import logging

from aioflask import Blueprint, g, make_response, request
from arq import create_pool
from arq.connections import RedisSettings

proxy = Blueprint("proxy", __name__)


async def get_redis_connection():
    redis_connection = getattr(g, "_redis_connection", None)
    if redis_connection is None:
        redis_connection = g._redis_connection = await create_pool(
            RedisSettings(host="redis")
        )
    return redis_connection


@proxy.route("/", defaults={"path": ""})
@proxy.route("/<path:path>")
async def catch_all(path):
    logging.info(f"Path {path} requested")
    logging.info(f" - Method: {request.method}")
    logging.info(f" - Data: {request.get_data()}")  # Get raw request data

    redis = await get_redis_connection()
    for i in range(3):
        job = await redis.enqueue_job(
            "download_content", path, request.method, request.get_data()
        )
        try:
            job_response = await job.result(timeout=5)
            response = make_response(job_response.text)
            response.headers = dict(job_response.headers)
            return response

        except asyncio.TimeoutError:
            if i == 2:
                return "Timeout"
            job.abort()
            logging.info(f"Retrying job {job.job_id} ({i+2} of 3)")
            continue
