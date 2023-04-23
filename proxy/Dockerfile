FROM python:latest
WORKDIR /app
COPY requirements.txt /app
RUN pip install -r requirements.txt
COPY main.py /app
EXPOSE 8000
CMD ["uvicorn", "--host", "0.0.0.0", "main:app"]
