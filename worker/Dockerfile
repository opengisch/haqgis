FROM opengisch/qgis-server:3.28-jammy

WORKDIR /app
RUN apt-get install -y python3-pip
COPY requirements.txt /app
RUN pip3 install -r requirements.txt
COPY main.py /app
COPY start-xvfb-nginx.sh /usr/local/bin
