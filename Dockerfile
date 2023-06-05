FROM python:3.10.11-buster

RUN apt-get update && apt-get install -y pandoc

COPY requirements.txt .

RUN pip install -r requirements.txt

WORKDIR /app

RUN wget https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin

COPY . .
