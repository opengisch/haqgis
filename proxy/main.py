#!/usr/bin/python
# coding: utf-8
from aioflask import Flask
from aioflask import request
import zmq
import zmq.asyncio
import async_timeout
import logging
import os
import sys
from uuid import uuid4
import json
import asyncio

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

app = Flask(__name__)


# Initialize a zeromq context
context = zmq.asyncio.Context()

# Set up a channel to send work
ventilator_send = context.socket(zmq.PUSH)
ventilator_send.bind("tcp://0.0.0.0:5557")

# Set up a channel to receive results
results_receiver = context.socket(zmq.PULL)
results_receiver.bind("tcp://0.0.0.0:5558")

timeout = 10


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
async def catch_all(path):
    job_id = str(uuid4())

    logging.info(f"Path {path} requested")
    logging.info(f" - Method: {request.method}")
    logging.info(f" - Data: {request.get_data()}") # Get raw request data

    job = {
        'id': job_id,
        'path': path
    }
    ventilator_send.send_json(job)

    try:
        async with async_timeout.timeout(timeout):
            while True:
                meta, data = await results_receiver.recv_multipart()
                metadata = json.loads(meta)
                if metadata['id'] == job_id:
                    logging.info(meta)
                    return data, metadata['status_code'], metadata['headers']
    except TimeoutError:
        return 'Timeout'


if __name__ == "__main__":
    app.run(host="0.0.0.0")
