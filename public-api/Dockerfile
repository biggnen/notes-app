FROM python:3.11-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8080

ENV MONGO_URI mongodb://mongodb:27017

ENV CONSUL_HTTP_ADDR consul:8500

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]

