FROM python:3.9
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean
WORKDIR /bot
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY src/ .
CMD [ "python", "./main.py" ]
