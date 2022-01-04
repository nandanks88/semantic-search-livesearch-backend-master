FROM python:3.7.4-stretch

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "main:app", "-b", "0.0.0.0:5000", "-k", "uvicorn.workers.UvicornWorker", "--workers", "1", "-t", "180"]
