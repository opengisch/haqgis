import logging
import os
import sys

from aioflask import Flask

from proxy import proxy

loglevel_config = os.environ.get("QGIS_PROXY_FLASK_APP_LOG_LEVEL", "info").lower()

if loglevel_config == "error":
    log_level = logging.ERROR
elif loglevel_config == "warning":
    log_level = logging.WARNING
elif loglevel_config == "debug":
    log_level = logging.DEBUG
else:
    log_level = logging.INFO

logging.basicConfig(
    stream=sys.stdout, level=log_level, format="%(asctime)s [%(levelname)s] %(message)s"
)

app = Flask(__name__)

app.register_blueprint(proxy)


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        debug=os.environ.get("QGIS_PROXY_FLASK_APP_DEBUG", False) in ["True", "1", 1],
    )
