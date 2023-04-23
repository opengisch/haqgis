#!/usr/bin/python
# coding: utf-8
from random import randint
import time
import zmq
import logging
import sys

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

LRU_READY = "\x01"

context = zmq.Context(1)
worker = context.socket(zmq.REQ)

identity = "%04X-%04X" % (randint(0, 0x10000), randint(0, 0x10000))
logging.info("Connecting ...")
worker.setsockopt_string(zmq.IDENTITY, identity)
worker.connect("tcp://qgis-server:5556")
logging.info(f"I: ({identity}) worker ready")
worker.send_string(LRU_READY)

cycles = 0
while True:
    msg = worker.recv_multipart()
    logging.info('Received msg')
    if not msg:
        break

    cycles += 1
    if cycles > 0 and randint(0, 5) == 0:
        print("I: (%s) simulating a crash" % identity)
        break
    elif cycles > 3 and randint(0, 5) == 0:
        print("I: (%s) simulating CPU overload" % identity)
        time.sleep(3)
    print("I: (%s) normal reply" % identity)
    time.sleep(1)  # Do some heavy work
    worker.send_multipart(msg)


# import zmq
# import random
# import time

# import logging
# import sys
# import json
# import requests
# import pickle

# logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

# def consumer():
#     context = zmq.Context()
#     work_receiver = context.socket(zmq.PULL)
#     work_receiver.connect("tcp://qgis-server:5557")

#     # Set up a channel to send result of work to the results reporter
#     results_sender = context.socket(zmq.PUSH)
#     results_sender.connect("tcp://qgis-server:5558")

#     while True:
#         job = work_receiver.recv_json()

#         key = job["id"]

#         source_path = f'http://localhost/{job["path"]}'
#         logging.info(f'Requesting {source_path}')
#         response = requests.get(source_path)
#         # p.hset(key, "data", response.content)
#         result = {
#             'id': key,
#             'status_code': response.status_code,
#             'headers': dict(response.headers),
#         }
#         results_sender.send_multipart([json.dumps(result).encode('utf-8'), response.content])


# consumer()
