FROM centos:centos8

RUN yum install -y gcc openssl-devel bzip2-devel libffi-devel
RUN yum install -y wget
RUN wget https://www.python.org/ftp/python/3.7.5/Python-3.7.5.tgz
RUN tar -xaf Python-3.7.5.tgz
RUN yum install -y make
RUN cd Python-3.7.5 && ./configure --enable-optimizations
RUN cd Python-3.7.5 && make -j 16 altinstall
RUN yum install -y which
RUN ln -s $(which python3.7) /usr/bin/python
RUN ln -s $(which pip3.7) /usr/bin/pip
RUN pip install flask opencv-contrib-python imutils dataclasses_json
RUN rm -rf Python-3.7.5 Python-3.7.5.tgz

RUN mkdir media-server
ADD config.py __init__.py  model.py server.py  test.json media-server/
RUN dnf install -y opencv-core
