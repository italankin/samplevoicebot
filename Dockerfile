FROM python:3.9
RUN apt-get -y update
RUN apt-get install -y ffmpeg
WORKDIR /bot
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY src/ .
CMD [ "python", "./bot.py" ]