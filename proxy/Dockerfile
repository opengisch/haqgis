FROM python:latest
WORKDIR /app
COPY REQUIREMENTS.txt /app
RUN pip install -r REQUIREMENTS.txt
COPY main.py /app
EXPOSE 5000
ENTRYPOINT ["python3", "main.py"]
