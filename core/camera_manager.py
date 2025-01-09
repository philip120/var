import cv2
import numpy as np
from typing import Dict, Optional, List, Tuple
from threading import Thread, Lock
import time
from utils.camera_utils import get_available_cameras

class CameraManager:
    def __init__(self):
        self.cameras: Dict[int, cv2.VideoCapture] = {}
        self.frames: Dict[int, np.ndarray] = {}
        self.running = False
        self.lock = Lock()
        self._capture_thread = None

    def add_camera(self, camera_id: int, source: str) -> bool:
        """
        Add a camera to the manager.
        
        Args:
            camera_id: Unique identifier for the camera
            source: Camera source (can be device index or IP camera URL)
        
        Returns:
            bool: True if camera was successfully added
        """
        cap = cv2.VideoCapture(source)
        if cap.isOpened():
            self.cameras[camera_id] = cap
            return True
        return False

    def start_capture(self):
        """Start capturing frames from all cameras."""
        self.running = True
        self._capture_thread = Thread(target=self._capture_loop, daemon=True)
        self._capture_thread.start()

    def stop_capture(self):
        """Stop capturing frames from all cameras."""
        self.running = False
        if self._capture_thread:
            self._capture_thread.join()

    def _capture_loop(self):
        """Main capture loop that runs in a separate thread."""
        while self.running:
            with self.lock:
                for camera_id, cap in self.cameras.items():
                    ret, frame = cap.read()
                    if ret:
                        # Convert BGR to RGB for Qt
                        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        self.frames[camera_id] = frame
            time.sleep(1/30)  # Limit to ~30 FPS

    def get_frame(self, camera_id: int) -> Optional[np.ndarray]:
        """
        Get the latest frame from a specific camera.
        
        Args:
            camera_id: The camera identifier
            
        Returns:
            Optional[np.ndarray]: The latest frame or None if not available
        """
        with self.lock:
            return self.frames.get(camera_id)

    def __del__(self):
        """Cleanup resources when the manager is destroyed."""
        self.stop_capture()
        for cap in self.cameras.values():
            cap.release()

    def get_available_cameras(self) -> List[int]:
        """
        Get a list of available camera indices.
        
        Returns:
            List[int]: List of available camera indices
        """
        cameras = get_available_cameras()
        return [idx for idx, available in cameras if available]
    
    def is_camera_connected(self, camera_id: int) -> bool:
        """
        Check if a specific camera is connected and working.
        
        Args:
            camera_id: The camera identifier
            
        Returns:
            bool: True if camera is connected and working
        """
        return camera_id in self.cameras and self.cameras[camera_id].isOpened()
