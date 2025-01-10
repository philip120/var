import cv2
import collections
import time

class VideoRecorder:
    def __init__(self, buffer_duration=10, frame_width=640, frame_height=480, fps=30):
        self.buffer_duration = buffer_duration
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.fps = fps
        self.buffer_size = buffer_duration * fps
        self.buffer = collections.deque(maxlen=self.buffer_size)
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)
        self.cap.set(cv2.CAP_PROP_FPS, fps)
        self.is_recording = False

    def start_recording(self):
        self.is_recording = True
        while self.is_recording:
            ret, frame = self.cap.read()
            if ret:
                timestamp = time.time()
                self.buffer.append((timestamp, frame))
                cv2.imshow("Live Stream", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    self.is_recording = False
            else:
                print("Failed to capture frame")

    def stop_recording(self):
        self.is_recording = False
        self.cap.release()
        cv2.destroyAllWindows()

    def get_last_seconds(self, seconds):
        end_time = time.time()
        start_time = end_time - seconds
        return [frame for timestamp, frame in self.buffer if timestamp >= start_time]