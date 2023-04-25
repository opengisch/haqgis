import logging
import sys

from aioflask import Flask

from proxy import proxy

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

app = Flask(__name__)

app.register_blueprint(proxy)


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
