from dataclasses import dataclass
from dataclasses_json import dataclass_json
from dataclasses import field
from typing import Dict
from threading import Thread

import cv2, math


class RTMPReader(Thread):

    def __init__(self, id, url, intervalSecs):
        super(RTMPReader, self).__init__()
        self.url = url
        self.intervalSecs = float(intervalSecs)
        self.frameSkip = 1
        self.id = id
        self._stop = False

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
                    return
                cv2.imwrite(f'img_{self.id}_{count}.jpg', frame)
                count += 1
                i = 0
                while i < self.frameSkip and not self._stop:
                    ret = cap.grab()
                    if not ret:
                        return
                    i += 1

            cap.release()
            cv2.destroyAllWindows()


@dataclass_json()
@dataclass(order=True)
class Stream:
    id: str  = None
    url: str = field(default_factory=lambda : None)


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

    def add_stream(self, s):
        s.id = self.get_next_id()
        if s.id not in self.streams:
            self.streams[s.id] = s
            r = RTMPReader(s.id, s.url, 1)
            self.streamThreads[s.id] = r
            r.start()
            return s
        return None

    def update_stream(self, s):
        os = self.streams[s.id]
        os.url = s.url
        self.streamThreads[s.id].stop()
        r = RTMPReader(os.id, os.url, 1)
        self.streamThreads[os.id] = r
        r.start()
        return os

    def remove_stream(self, sid):
        if sid in self.streams:
            self.streamThreads[sid].stop()
            del self.streams[sid]

