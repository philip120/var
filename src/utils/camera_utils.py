import cv2
import platform
import time
import numpy as np
from threading import Thread
from collections import deque
import logging

logger = logging.getLogger(__name__)

def get_camera_backend():
    """Get the appropriate backend for the current operating system."""
    system = platform.system().lower()
    if system == "windows":
        # Force DirectShow backend and disable RealSense checks
        return cv2.CAP_DSHOW
    elif system == "darwin":
        return cv2.CAP_AVFOUNDATION
    else:
        return cv2.CAP_V4L2

def create_camera_capture(camera_id: int, for_preview: bool = False) -> tuple:
    """Create an optimized camera capture."""
    try:
        backend = get_camera_backend()
        
        if for_preview:
            # Quick preview mode
            cap = cv2.VideoCapture(camera_id, backend)
            if not cap.isOpened():
                return None, None
            return cap, None

        # Full initialization
        cap = cv2.VideoCapture(camera_id, backend)
        if not cap.isOpened():
            return None, None

        # Configure camera
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        cap.set(cv2.CAP_PROP_FPS, 30)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        # Verify camera is working
        ret, frame = cap.read()
        if not ret or frame is None:
            logger.error(f"Failed to get frame from camera {camera_id}")
            cap.release()
            return None, None

        # Create async reader
        reader = AsyncFrameReader(camera_id)
        reader.start(cap)
        return cap, reader

    except Exception as e:
        logger.error(f"Error creating camera {camera_id}: {str(e)}")
        if 'cap' in locals() and cap is not None:
            cap.release()
        return None, None

def get_available_cameras(max_cameras: int = 2) -> list:
    """Quick scan for available cameras."""
    available_cameras = []
    backend = get_camera_backend()
    
    for i in range(max_cameras):
        try:
            # Use DirectShow/specific backend to avoid RealSense detection
            cap = cv2.VideoCapture(i, backend)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None:
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    fps = int(cap.get(cv2.CAP_PROP_FPS))
                    available_cameras.append((i, True, (width, height, fps)))
                    logger.debug(f"Found camera {i}: {width}x{height} @ {fps}fps")
                else:
                    available_cameras.append((i, False, None))
                    logger.debug(f"Camera {i} found but not readable")
            else:
                available_cameras.append((i, False, None))
                logger.debug(f"No camera found at index {i}")
            cap.release()
        except Exception as e:
            logger.error(f"Error checking camera {i}: {str(e)}")
            available_cameras.append((i, False, None))
    
    return available_cameras

class AsyncFrameReader:
    """Asynchronous frame reader to decouple capture from display"""
    def __init__(self, camera_id):
        self.camera_id = camera_id
        self.queue = deque(maxlen=1)
        self.running = False
        self.thread = None
        self.cap = None
        self.logger = logging.getLogger(f"{__name__}.AsyncFrameReader.{camera_id}")

    def start(self, cap):
        """Start async frame reading"""
        if self.running:
            return
            
        self.cap = cap
        self.running = True
        self.thread = Thread(target=self._read_frames, daemon=True)
        self.thread.start()
        self.logger.debug("Frame reader started")

    def stop(self):
        """Stop async frame reading"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        if self.cap:
            self.cap.release()
            self.cap = None
        self.logger.debug("Frame reader stopped")

    def _read_frames(self):
        """Frame reading thread"""
        frames_read = 0
        last_fps_time = time.time()
        
        while self.running and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                # Convert BGR to RGB directly using numpy (faster than cv2.cvtColor)
                frame = frame[..., ::-1].copy()
                self.queue.clear()
                self.queue.append(frame)
                
                # Log FPS every second
                frames_read += 1
                current_time = time.time()
                if current_time - last_fps_time >= 1.0:
                    self.logger.debug(f"Current FPS: {frames_read}")
                    frames_read = 0
                    last_fps_time = current_time
            else:
                time.sleep(0.001)

    def get_frame(self):
        """Get the latest frame"""
        try:
            return self.queue[-1] if self.queue else None
        except:
            return None 