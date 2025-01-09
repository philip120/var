import cv2
import logging
import threading
import queue
import time
from typing import Dict, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)

class CameraThread(threading.Thread):
    def __init__(self, camera_id: int, source: str | int):
        super().__init__(daemon=True)
        self.camera_id = camera_id
        # Handle source conversion
        if isinstance(source, str):
            self.source = int(source) if source.isdigit() else source
        else:
            self.source = source
        self.frame_queue = queue.Queue(maxsize=3)
        self.running = False
        self.cap = None
        self.logger = logging.getLogger(f"{__name__}.CameraThread.{camera_id}")

    def run(self):
        try:
            # Try to open camera with DirectShow backend
            if isinstance(self.source, int):
                # First open with default settings
                self.cap = cv2.VideoCapture(self.source + cv2.CAP_DSHOW)
                if not self.cap.isOpened():
                    self.logger.error("Failed to open camera with DirectShow")
                    return

                # Important: Set codec first, then resolution, then FPS
                # Set MJPG codec
                if not self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G')):
                    self.logger.warning("Failed to set MJPG codec")
                    
                # Release and reopen to ensure codec takes effect
                self.cap.release()
                self.cap = cv2.VideoCapture(self.source + cv2.CAP_DSHOW)
                
                # Now set resolution
                if not self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640):
                    self.logger.warning("Failed to set width")
                if not self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480):
                    self.logger.warning("Failed to set height")
                    
                # Set FPS last
                if not self.cap.set(cv2.CAP_PROP_FPS, 60):
                    self.logger.warning("Failed to set FPS")
                    
                # Minimize buffer size
                if not self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1):
                    self.logger.warning("Failed to set buffer size")
                
                # Verify settings
                actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                actual_fps = self.cap.get(cv2.CAP_PROP_FPS)
                actual_codec = int(self.cap.get(cv2.CAP_PROP_FOURCC))
                codec_str = "".join([chr((actual_codec >> 8 * i) & 0xFF) for i in range(4)])
                
                self.logger.debug(
                    f"Camera initialized: {actual_width}x{actual_height} @ {actual_fps:.1f}fps "
                    f"using codec {codec_str}"
                )
                
                # Test actual achievable FPS
                start_time = time.time()
                frames = 0
                test_duration = 2.0  # Test for 2 seconds
                
                while time.time() - start_time < test_duration:
                    ret, _ = self.cap.read()
                    if ret:
                        frames += 1
                
                achieved_fps = frames / test_duration
                self.logger.debug(f"Achieved FPS in test: {achieved_fps:.1f}")
                
                if achieved_fps < 30:
                    self.logger.warning(f"Low FPS detected: {achieved_fps:.1f}")
                    
                # Release and reopen one final time to ensure clean start
                self.cap.release()
                self.cap = cv2.VideoCapture(self.source + cv2.CAP_DSHOW)
                self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, actual_width)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, actual_height)
                self.cap.set(cv2.CAP_PROP_FPS, 60)
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                
            else:
                self.cap = cv2.VideoCapture(self.source)

            if not self.cap.isOpened():
                self.logger.error("Failed to open camera")
                return

            # Read and discard first few frames
            for _ in range(5):
                ret, _ = self.cap.read()
                if not ret:
                    self.logger.warning("Failed to read initial frame")

            self.running = True
            frames_read = 0
            last_fps_time = time.time()

            while self.running:
                try:
                    # Read frame without any delay
                    ret, frame = self.cap.read()
                    if ret and frame is not None:
                        # Convert BGR to RGB directly
                        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        
                        # Update frame queue - drop frames if queue is full
                        if not self.frame_queue.full():
                            self.frame_queue.put_nowait(rgb_frame)
                            
                            # Log FPS
                            frames_read += 1
                            current_time = time.time()
                            if current_time - last_fps_time >= 1.0:
                                fps = frames_read / (current_time - last_fps_time)
                                self.logger.debug(f"Camera {self.camera_id} FPS: {fps:.1f}")
                                frames_read = 0
                                last_fps_time = current_time
                    else:
                        self.logger.warning("Failed to read frame")
                        
                except Exception as e:
                    self.logger.error(f"Error processing frame: {str(e)}")

        except Exception as e:
            self.logger.error(f"Error in camera thread: {str(e)}", exc_info=True)
        finally:
            self.cleanup()

    def get_frame(self) -> Optional[np.ndarray]:
        """Get the latest frame from the camera"""
        try:
            return self.frame_queue.get_nowait()
        except queue.Empty:
            return None

    def stop(self):
        """Stop the camera thread"""
        self.running = False
        self.cleanup()

    def cleanup(self):
        """Clean up camera resources"""
        if self.cap is not None:
            self.cap.release()
            self.cap = None

class CameraManager:
    def __init__(self):
        self.cameras: Dict[int, CameraThread] = {}
        self.running = False
        self.logger = logging.getLogger(f"{__name__}.CameraManager")

    def add_camera(self, camera_id: int, source: str) -> bool:
        """Add a camera to the manager"""
        try:
            # Stop existing camera if present
            if camera_id in self.cameras:
                self.cameras[camera_id].stop()
                del self.cameras[camera_id]

            # Create and start new camera thread
            camera_thread = CameraThread(camera_id, source)
            camera_thread.start()
            self.cameras[camera_id] = camera_thread
            self.running = True
            return True

        except Exception as e:
            self.logger.error(f"Error adding camera {camera_id}: {str(e)}", exc_info=True)
            return False

    def get_frame(self, camera_id: int) -> Optional[np.ndarray]:
        """Get the latest frame from a camera"""
        if camera_id in self.cameras:
            return self.cameras[camera_id].get_frame()
        return None

    def is_camera_connected(self, camera_id: int) -> bool:
        """Check if a camera is connected"""
        return camera_id in self.cameras

    def start_capture(self):
        """Start capturing from all cameras"""
        self.running = True

    def stop_capture(self):
        """Stop capturing from all cameras"""
        self.running = False
        for camera in self.cameras.values():
            camera.stop()
        self.cameras.clear()

    def __del__(self):
        """Cleanup when the manager is destroyed"""
        self.stop_capture()
