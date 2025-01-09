import cv2
import logging
import threading
import time

logger = logging.getLogger(__name__)

class CameraManager:
    def __init__(self):
        self.cameras = {}  # Dictionary to store camera captures {camera_idx: cv2.VideoCapture}
        self.frames = {}   # Dictionary to store latest frames {camera_idx: frame}
        self.running = False
        self.capture_thread = None
        self.lock = threading.Lock()
        
    def add_camera(self, camera_idx):
        """Add a camera to the manager"""
        try:
            # Use DirectShow backend for better performance on Windows
            cap = cv2.VideoCapture(camera_idx, cv2.CAP_DSHOW)
            if cap.isOpened():
                # Set camera properties in specific order
                settings = [
                    (cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')),  # MJPG format
                    (cv2.CAP_PROP_FRAME_WIDTH, 1280),
                    (cv2.CAP_PROP_FRAME_HEIGHT, 720),
                    (cv2.CAP_PROP_FPS, 60),
                    (cv2.CAP_PROP_BUFFERSIZE, 1),  # Minimize latency
                    (cv2.CAP_PROP_AUTOFOCUS, 0),   # Disable autofocus
                    (cv2.CAP_PROP_AUTO_EXPOSURE, 0.75),  # Auto exposure
                ]
                
                for prop, value in settings:
                    if not cap.set(prop, value):
                        logger.warning(f"Failed to set camera property {prop} to {value}")
                
                # Verify settings
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = cap.get(cv2.CAP_PROP_FPS)
                logger.debug(f"Camera {camera_idx} initialized: {width}x{height} @ {fps}fps")
                
                with self.lock:
                    self.cameras[camera_idx] = cap
                    self.frames[camera_idx] = None
                return True
            else:
                logger.error(f"Failed to open camera {camera_idx}")
                return False
        except Exception as e:
            logger.error(f"Error adding camera {camera_idx}: {str(e)}")
            return False
            
    def start_capture(self):
        """Start capturing from all cameras"""
        if not self.running:
            self.running = True
            self.capture_thread = threading.Thread(target=self._capture_loop)
            self.capture_thread.daemon = True
            self.capture_thread.start()
            logger.debug("Started camera capture thread")
            
    def stop_capture(self):
        """Stop capturing from all cameras"""
        self.running = False
        if self.capture_thread:
            self.capture_thread.join()
        
        # Release all cameras
        with self.lock:
            for cap in self.cameras.values():
                cap.release()
            self.cameras.clear()
            self.frames.clear()
        logger.debug("Stopped all cameras")
            
    def _capture_loop(self):
        """Main capture loop for all cameras"""
        while self.running:
            with self.lock:
                for camera_idx, cap in self.cameras.items():
                    if cap.isOpened():
                        ret, frame = cap.read()
                        if ret:
                            self.frames[camera_idx] = frame
                        else:
                            logger.warning(f"Failed to read frame from camera {camera_idx}")
                            self.frames[camera_idx] = None
            time.sleep(0.016)  # ~60 FPS
            
    def get_frames(self):
        """Get the latest frames from all cameras"""
        with self.lock:
            return self.frames.copy()
            
    def is_capturing(self):
        """Check if any cameras are capturing"""
        return self.running and bool(self.cameras)
