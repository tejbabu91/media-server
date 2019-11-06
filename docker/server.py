#!/usr/bin/env python

import math
import cv2
import os
from flask import Flask, request, send_file, Response
import tempfile
from threading import Thread
from model import Stream, MediaServer
import sys
from c8y import *
import queue

scriptDir = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
staticDir = os.path.abspath(os.path.join(scriptDir, 'static'))
os.makedirs(staticDir, exist_ok=True)
if scriptDir not in sys.path: sys.path.append(scriptDir)

app = Flask(__name__, static_folder=staticDir)
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


@app.route('/streams/data/<sid>', methods=['POST'])
def packages_data_post(sid):
    s = app.data.get_stream(sid)
    (tmpfd, tmpfilepath) = tempfile.mkstemp(dir=staticDir)
    os.close(tmpfd)
    chunk_size = 4094
    with open(os.path.join(staticDir, tmpfilepath), 'wb') as tmpfd:
        while True:
            chunk = request.stream.read(chunk_size)
            if len(chunk) == 0:
                break
            tmpfd.write(chunk)
        tmpfd.close()
    s.datafile = tmpfilepath
    app.data.update_stream(s)
    return Response(status=201)

def gen_live_feed(t, q):
    t.add_live_queue(q)
    while t.is_alive():
        frame = q.get()
        if type(frame) == bool and frame == True:
            break
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame.tobytes() + b'\r\n')
    t.remove_live_queue(q)

@app.route('/streams/live/<sid>', methods=['GET'])
def packages_live_get(sid):
    t = app.data.get_stream_thread(sid)
    q = queue.SimpleQueue()
    return Response(gen_live_feed(t, q), mimetype='multipart/x-mixed-replace; boundary=frame')


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
    print(f'Current Application ID is {get_current_application_id()}')
    print(f'Managed Object mapped to current application is {get_application_managed_object_id()}')
    app.data = MediaServer()
    app.run(host='0.0.0.0', port=(5000 if len(sys.argv) == 1 else int(sys.argv[1])))
