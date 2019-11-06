FROM python:3.7-slim

RUN apt-get update && apt-get install -y libopencv-core3.2 libglib2.0-0 && apt-get clean all && apt-get autoclean && apt-get autoremove
RUN pip install flask opencv-python-headless opencv-contrib-python-headless imutils dataclasses_json

RUN mkdir media-server

ADD config.py __init__.py  model.py server.py test.json media-server/

WORKDIR /media-server

ENTRYPOINT ["python", "server.py", "80"]
