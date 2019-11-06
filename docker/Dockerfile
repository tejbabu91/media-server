FROM python:3.7-slim

RUN pip install flask opencv-contrib-python imutils dataclasses_json

RUN mkdir media-server
ADD config.py __init__.py  model.py server.py  test.json media-server/
RUN apt-get update && apt-get install -y libopencv-core3.2 && apt-get clean all && apt-get autoclean && apt-get autoremove
