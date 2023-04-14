#!/usr/bin/python
# coding: utf-8
from aioflask import Flask
from aioflask import request
import redis.asyncio as redis
import async_timeout
import logging
import os
import sys
from uuid import uuid4
import json
import asyncio

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

app = Flask(__name__)

pool = redis.BlockingConnectionPool(host='redis')

timeout = 1000


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
async def catch_all(path):
    r = await redis.Redis(connection_pool=pool)
    job_id = str(uuid4())

    logging.info(f"Path {path} requested")
    logging.info(f" - Method: {request.method}")
    logging.info(f" - Data: {request.get_data()}") # Get raw request data

    job = {
        'id': job_id,
        'path': path
    }
    async with r.pipeline() as p:
        p.rpush("jobs", json.dumps(job))
        await p.execute()

        async with r.pubsub() as ps:
            await ps.subscribe("notifications")
            async with async_timeout.timeout(timeout):
                while True:
                    message = await ps.get_message(timeout=timeout)
                    logging.info(message)
                    try:
                        if message and message.get("data").decode() == job_id:
                            break
                    except:
                        continue  # Message could not be decoed
                    await asyncio.sleep(
                        0.01
                    )  # We normally should not run in a spin loop, but better safe than sorry

    data = await r.hget(job_id, "data")
    return data


if __name__ == "__main__":
    app.run(host="0.0.0.0")
