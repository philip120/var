import cv2
import numpy as np
from typing import Dict, List, Optional
from threading import Thread, Lock, Event
import time
from pathlib import Path
import json
from datetime import datetime

from .video_sync import VideoSync
from .camera_manager import CameraManager

class Recorder:
    def __init__(self, camera_manager: CameraManager):
        self.camera_manager = camera_manager
        self.video_sync = VideoSync()
        self.recording = False
        self.recording_thread = None
        self.stop_event = Event()
        self.lock = Lock()
        self.output_writers: Dict[int, cv2.VideoWriter] = {}
        self.recording_start_time: Optional[float] = None
        self.recording_path: Optional[Path] = None
        
    def start_recording(self, output_directory: str):
        """Start recording from all active cameras."""
        if self.recording:
            return False
            
        # Create output directory with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.recording_path = Path(output_directory) / timestamp
        self.recording_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize video writers for each camera
        active_cameras = []
        for camera_id in self.camera_manager.cameras.keys():
            if self.camera_manager.is_camera_connected(camera_id):
                video_path = self.recording_path / f"camera_{camera_id}.mp4"
                cap = self.camera_manager.cameras[camera_id]
                fps = int(cap.get(cv2.CAP_PROP_FPS))
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                
                writer = cv2.VideoWriter(
                    str(video_path),
                    cv2.VideoWriter_fourcc(*'mp4v'),
                    fps,
                    (width, height)
                )
                self.output_writers[camera_id] = writer
                active_cameras.append(camera_id)
        
        if not active_cameras:
            return False
            
        # Start recording
        self.recording = True
        self.recording_start_time = time.time()
        self.stop_event.clear()
        self.video_sync.start_recording(active_cameras)
        
        # Start recording thread
        self.recording_thread = Thread(target=self._record_loop, daemon=True)
        self.recording_thread.start()
        return True
        
    def stop_recording(self):
        """Stop recording and save metadata."""
        if not self.recording:
            return
            
        self.stop_event.set()
        if self.recording_thread:
            self.recording_thread.join()
            
        self.video_sync.stop_recording()
        
        # Save metadata
        if self.recording_path:
            metadata = {
                "start_time": self.recording_start_time,
                "duration": time.time() - self.recording_start_time,
                "cameras": list(self.output_writers.keys())
            }
            
            with open(self.recording_path / "metadata.json", "w") as f:
                json.dump(metadata, f)
        
        # Cleanup
        for writer in self.output_writers.values():
            writer.release()
        self.output_writers.clear()
        self.recording = False
        self.recording_start_time = None
        
    def _record_loop(self):
        """Main recording loop."""
        while not self.stop_event.is_set():
            for camera_id, writer in self.output_writers.items():
                frame = self.camera_manager.get_frame(camera_id)
                if frame is not None:
                    # Convert RGB back to BGR for OpenCV
                    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    writer.write(frame_bgr)
                    self.video_sync.add_frame(camera_id, frame)
            time.sleep(1/60)  # Limit to 60 FPS max
            
    def is_recording(self) -> bool:
        """Check if currently recording."""
        return self.recording
