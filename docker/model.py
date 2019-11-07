from dataclasses import dataclass
from dataclasses_json import dataclass_json
from dataclasses import field
from typing import Dict
from threading import Thread
import copy
import queue
import requests
from datetime import datetime
datetime.now().isoformat()
from c8y import get_application_managed_object_id, platform_request

import cv2, math, time, sys, os

azure_image_classifier_rest = ''

@dataclass_json()
@dataclass(order=True)
class Stream:
    analyser_url: str
    prediction_key: str
    id: str  = None
    url: str = field(default_factory=lambda : None)
    datafile: str = field(default_factory=lambda : None)
    frame_interval_secs: float = field(default=1.0)


image_analyser_queue = queue.SimpleQueue()
measurement_queue = queue.SimpleQueue()

class MeasurementGenerator(Thread):

    def __init__(self, q):
        super(MeasurementGenerator, self).__init__()
        self.measurement_queue = q

    def run(self):
        while True:
            try:
                m = self.measurement_queue.get()
                print(f'Received measurement: {m}')
                resp = platform_request('POST', '/measurement/measurements', body=m)
                print(f'Raised measurement: {resp}')
            except Exception as e:
                print(f'Failed to raise measurement: {e}')


class ImageAnalyzer(Thread):

    def __init__(self, q):
        super(ImageAnalyzer, self).__init__()
        self.image_queue = q
        self.mobj_id = get_application_managed_object_id()

    def get_measurement_json_template(self, fragment):
        return {
            "time": datetime.utcnow().isoformat() + 'Z',
            "type": "media_server_image_classification",
            "source": {"id": self.mobj_id},
            "color": {
                #f"{series}": {"value": value},
            },
        }

    def run(self):
        while True:
            try:
                stream, frame = self.image_queue.get()
                resp = requests.post(stream.analyser_url, headers={
                    'Content-Type': 'application/octet-stream',
                    'Prediction-Key': stream.prediction_key,
                }, data=frame.tobytes())
                resp_json = resp.json()
                print(f'Azure response: {resp_json}')
                m = self.get_measurement_json_template(stream.id)
                for p in resp_json['predictions']:
                    selected_val = float(p['probability'])
                    selected_tag = p['tagName']
                    m['color'][selected_tag] = {'value': selected_val}
                measurement_queue.put(m)

            except Exception as e:
                print(f'Azure error: {e}')
            sys.stdout.flush()

img_analyser = ImageAnalyzer(image_analyser_queue)
img_analyser.start()
measurement_generator = MeasurementGenerator(measurement_queue)
measurement_generator.start()

class RTMPReader(Thread):

    def __init__(self, stream):
        super(RTMPReader, self).__init__()
        self.stream = stream
        self.url = stream.url if stream.datafile is None else stream.datafile
        self.simultation_mode = stream.datafile is not None
        self.intervalSecs = float(stream.frame_interval_secs)
        self.frameSkip = 1
        self.id = stream.id
        self._stop = False
        self.live_queues = []

    def stop(self):
        self._stop = True

    def run(self):
        count = 0
        while not self._stop:
            cap = cv2.VideoCapture(self.url) # rtmp://fms.105.net/live/rmc1
            fps = cap.get(cv2.CAP_PROP_FPS)
            self.frameSkip = math.floor(fps * self.intervalSecs)

            while cap.isOpened() and not self._stop:
                ret, frame = cap.read()
                if not ret:
                    if self.simultation_mode:
                        break
                    else:
                        self.send_close_to_live_queues()
                        return
                _, jpg = cv2.imencode('.jpg', frame)
                print(f'putting frame on queue')
                image_analyser_queue.put((self.stream, jpg))
                self.publish_frame_to_live_queues(frame)
                time.sleep(1.0 / fps)
                #cv2.imwrite(f'img_{self.id}_{count}.jpg', frame)
                count += 1
                i = 0
                while i < self.frameSkip and not self._stop:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    i += 1
                    self.publish_frame_to_live_queues(frame)
                    time.sleep(1.0/fps)

            cap.release()

    def add_live_queue(self, q):
        self.live_queues.append(q)

    def remove_live_queue(self, q):
        print('##### Remove live queue called')
        self.live_queues.remove(q)

    def get_live_queues(self):
        return self.live_queues

    def set_live_queues(self, ql):
        self.live_queues = ql

    def publish_frame_to_live_queues(self, frame):
        _, f = cv2.imencode('.jpg', frame)
        for q in self.live_queues:
            # print(f'putting frame - {f}')
            q.put(f, block=False)

    def send_close_to_live_queues(self):
        for q in self.live_queues:
            # print(f'putting frame - {f}')
            q.put(True, block=False)


@dataclass()
class MediaServer:

    streams: Dict[str, Stream] = field(default_factory=lambda: {})
    streamThreads: Dict[str, RTMPReader] = field(default_factory=lambda: {})
    counter: int = field(default=0)

    def get_next_id(self):
        self.counter += 1
        return str(self.counter)

    def get_all_streams(self):
        return [self.streams[x] for x in self.streams]

    def get_stream(self, sid):
        return copy.deepcopy(self.streams[sid])

    def get_stream_thread(self, sid):
        return self.streamThreads[sid]

    def add_stream(self, s):
        s.id = self.get_next_id()
        if s.id not in self.streams:
            self.streams[s.id] = s
            r = RTMPReader(s)
            self.streamThreads[s.id] = r
            r.start()
            return s
        return None

    def update_stream(self, s):
        os = self.streams[s.id]
        d = os.to_dict()
        d.update(s.to_dict())
        ns = Stream(**d)
        self.streams[s.id] = ns
        ql = self.streamThreads[s.id].get_live_queues()
        self.streamThreads[s.id].stop()
        r = RTMPReader(os)
        r.set_live_queues(ql)
        self.streamThreads[os.id] = r
        r.start()
        return os

    def remove_stream(self, sid):
        if sid in self.streams:
            self.streamThreads[sid].stop()
            del self.streams[sid]

