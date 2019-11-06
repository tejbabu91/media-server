FROM python:3.7-slim

RUN apt-get update && apt-get install -y libopencv-core3.2 libglib2.0-0 && apt-get clean all && apt-get autoclean && apt-get autoremove
RUN pip install flask opencv-python-headless opencv-contrib-python-headless imutils dataclasses_json requests

RUN mkdir media-server

EXPOSE 80

ADD config.py __init__.py model.py server.py c8y.py test.json media-server/
ADD static media-server/static

WORKDIR /media-server

ENTRYPOINT ["python", "server.py", "80"]
