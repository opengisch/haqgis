#!/usr/bin/python
# coding: utf-8
import redis
import random
import time

import logging
import sys
import json
import requests
import pickle

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

def consumer():
    r = redis.Redis(host='redis')
    while True:
        try:
            _, job_info = r.blpop("jobs")
        except Exception as e:
            # TODO handle known exceptions like redis.exceptions.ConnectionError separately
            retry_count += 1
            logging.error(e, exc_info=True)
            retry_rate = math.pow(2, retry_count) * 0.01
            logging.warning(f"Retrying in {retry_rate} seconds...")
            time.sleep(retry_rate)
            continue

        job = json.loads(job_info)

        key = job["id"]

        # Pipelines send multiple commands in a single batch
        # thus minimizing roadtrips. https://github.com/redis/redis-py#pipelines
        p = r.pipeline()
        
        source_path = f'http://localhost/{job["path"]}'
        logging.info(f'Requesting {source_path}')
        response = requests.get(source_path)
        result = {
            'id': key,
            'status_code': response.status_code,
        }
        p.hset(key, "data", response.content)
        p.publish("notifications", key)
        p.execute()


consumer()
