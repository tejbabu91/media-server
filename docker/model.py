from dataclasses import dataclass
from dataclasses_json import dataclass_json
from dataclasses import field
from typing import Dict
from threading import Thread
import copy
import queue

import cv2, math, time


@dataclass_json()
@dataclass(order=True)
class Stream:
    id: str  = None
    url: str = field(default_factory=lambda : None)
    datafile: str = field(default_factory=lambda : None)



class RTMPReader(Thread):

    def __init__(self, stream, intervalSecs):
        super(RTMPReader, self).__init__()
        self.url = stream.url if stream.datafile is None else stream.datafile
        self.simultation_mode = stream.datafile is not None
        self.intervalSecs = float(intervalSecs)
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
                        return
                self.publish_frame_to_live_queues(frame)
                #cv2.imwrite(f'img_{self.id}_{count}.jpg', frame)
                count += 1
                i = 0
                while i < self.frameSkip and not self._stop:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    i += 1
                    self.publish_frame_to_live_queues(frame)
                    time.sleep(1.0/self.frameSkip)

            cap.release()
            cv2.destroyAllWindows()

    def add_live_queue(self, q):
        self.live_queues.append(q)

    def remove_live_queue(self, q):
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
            r = RTMPReader(s, 1)
            self.streamThreads[s.id] = r
            r.start()
            return s
        return None

    def update_stream(self, s):
        os = self.streams[s.id]
        d = os.to_dict()
        d.update(s.to_dict())
        os = Stream(**d)
        self.streamThreads[s.id].stop()
        ql = self.streamThreads[s.id].get_live_queues()
        r = RTMPReader(os, 1)
        r.set_live_queues(ql)
        self.streamThreads[os.id] = r
        r.start()
        return os

    def remove_stream(self, sid):
        if sid in self.streams:
            self.streamThreads[sid].stop()
            del self.streams[sid]

