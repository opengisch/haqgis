#!/usr/bin/python
# coding: utf-8

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from pydantic import BaseSettings
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

LRU_READY = "\x01"

context = zmq.asyncio.Context()

frontend = context.socket(zmq.ROUTER)  # ROUTER
backend = context.socket(zmq.ROUTER)  # ROUTER
frontend.bind("inproc://queue")  # For clients
backend.bind("tcp://*:5556")  # For workers

poll_workers = zmq.asyncio.Poller()
poll_workers.register(backend, zmq.POLLIN)

poll_both = zmq.asyncio.Poller()
poll_both.register(frontend, zmq.POLLIN)
poll_both.register(backend, zmq.POLLIN)

workers = []

timeout = 10


async def client_loop():
    while True:
        if workers:
            logging.info('waiting for things')
            msg = frontend.recv_multipart()
            logging.info('got a message')
            socks = dict(await poll_both.poll())
        else:
            logging.info('waiting for workers')
            socks = dict(await poll_workers.poll())
        logging.info('got something')

        # Handle worker activity on backend
        if socks.get(backend) == zmq.POLLIN:
            logging.info('backend')
            # Use worker address for LRU routing
            msg = await backend.recv_multipart()
            if not msg:
                break
            address = msg[0]
            workers.append(address)
            logging.info(f"Registered worker {address}")

            # Everything after the second (delimiter) frame is reply
            reply = msg[2:]

            # Forward message to client if it's not a READY
            if reply[0] != LRU_READY:
                frontend.send_multipart(reply)

        if socks.get(frontend) == zmq.POLLIN:
            logging.info('frontend')
            #  Get client request, route to first available worker
            msg = frontend.recv_multipart()
            request = [workers.pop(0), "".encode()] + msg
            backend.send_multipart(request)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup code
    zmq_loop = client_loop()
    asyncio.create_task(zmq_loop)
    yield
    # teardown code
    pass


class Settings(BaseSettings):
    openapi_url: str = ""

settings = Settings()

app = FastAPI(openapi_url=settings.openapi_url, lifespan=lifespan)


@app.api_route("/{path_name:path}", methods=["GET", "POST"])
async def catch_all(request: Request, path_name: str):
    job_id = str(uuid4())

    logging.info(f"Path {path_name} requested")
    logging.info(f" - Method: {request.method}")
    logging.info(f" - Headers: {request.headers}")  # Get raw request data
    logging.info(f" - Body: {request.body}")  # Get raw request data

    job = {"id": job_id, "path": path_name}
    
    queue = context.socket(zmq.REQ)
    queue.connect("inproc://queue")
    queue.send_multipart([1,2,3])
    logging.info('Sent something')

    try:
        async with async_timeout.timeout(timeout):
            while True:
                meta, data = await backend.recv_multipart()
                metadata = json.loads(meta)
                if metadata["id"] == job_id:
                    logging.info(meta)
                    return data, metadata["status_code"], metadata["headers"]
    except TimeoutError:
        return "Timeout"


# async def main():
#     asyncio.create_task(client_loop())
#     config = Config()
#     config.bind = ["0.0.0.0:5000"]  # As an example configuration setting
#     asgi_app = WsgiToAsgi(app)
#     logging.info('Starting server ...')
#     await serve(asgi_app, config)

# if __name__ == "__main__":
#     asyncio.run(main())
