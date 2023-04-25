import logging
import os

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


timeout = int(os.environ.get("TIMEOUT", 30))  # Timeout in seconds

logging.info(f"Timeout {timeout} seconds")


@proxy.route("/", defaults={"path": ""}, methods=["GET", "POST"])
@proxy.route("/<path:path>", methods=["GET", "POST"])
async def catch_all(path):
    logging.info(f"{request.method} {request.host}{path}")
    logging.info(f" - Method: {request.method}")
    logging.info(f" - Params: {dict(request.args)}")
    logging.info(f" - Data: {request.get_data()}")  # Get raw request data

    redis = await get_redis_connection()
    headers = dict(request.headers)
    # Inject X-Forwarded-Host headers in case they are not already set by an earlier reverse proxy
    headers["X-Forwarded-Host"] = headers.get("X-Forwarded-Host", request.host)
    job = await redis.enqueue_job(
        "download_content",
        path,
        request.method,
        dict(request.args),
        headers,
        request.get_data(),
    )

    job_response = await job.result(timeout=timeout)
    response = make_response(job_response.content)
    response.headers = dict(job_response.headers)
    return response
