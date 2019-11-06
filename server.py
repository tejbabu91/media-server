#!/usr/bin/env python

import math
import cv2
import os
from flask import Flask, request, send_file, Response
import tempfile
from threading import Thread
from model import Stream, MediaServer

scriptDir = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))

app = Flask(__name__, static_folder=os.path.abspath(os.path.join(scriptDir, 'static')))
app.config.from_object('config.Config')


@app.route('/streams', methods=['GET'])
def packages_get():
    s = app.data.get_all_streams()
    s = {'streams': list(map(lambda x: x.to_dict(), s))}
    return s


@app.route('/streams', methods=['POST'])
def packages_post():
    json = request.stream.read()
    s = Stream.from_json(json)
    print(s.to_dict())
    s = app.data.add_stream(s)
    if s is not None:
        return s.to_dict()
    return Response(status=502)


@app.route('/streams/<sid>', methods=['PUT'])
def packages_put(sid):
    json = request.stream.read()
    s = Stream.from_json(json)
    s.id = sid
    s = app.data.update_stream(s)
    if s is not None:
        return s.to_dict()
    return Response(status=502)


@app.route('/streams/<sid>', methods=['DELETE'])
def packages_delete(sid):
    app.data.remove_stream(sid)
    return Response(status=201)


if __name__ == '__main__':
    print(app.config)
    app.data = MediaServer()
    app.run(host='0.0.0.0')
