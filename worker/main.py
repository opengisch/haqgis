#!/usr/bin/python
# coding: utf-8
import zmq
import random
import time

import logging
import sys
import json
import requests
import pickle

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

def consumer():
    context = zmq.Context()
    work_receiver = context.socket(zmq.PULL)
    work_receiver.connect("tcp://qgis-server:5557")

    # Set up a channel to send result of work to the results reporter
    results_sender = context.socket(zmq.PUSH)
    results_sender.connect("tcp://qgis-server:5558")

    while True:
        job = work_receiver.recv_json()

        key = job["id"]
        
        source_path = f'http://localhost/{job["path"]}'
        logging.info(f'Requesting {source_path}')
        response = requests.get(source_path)
        # p.hset(key, "data", response.content)
        result = {
            'id': key,
            'status_code': response.status_code,
            'headers': dict(response.headers),
        }
        results_sender.send_multipart([json.dumps(result).encode('utf-8'), response.content])


consumer()
