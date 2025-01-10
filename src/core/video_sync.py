import cv2
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from threading import Lock
import time

@dataclass
class VideoFrame:
    frame: np.ndarray
    timestamp: float
    camera_id: int

class VideoSync:
    def __init__(self):
        self.recordings: Dict[int, List[VideoFrame]] = {}
        self.current_position: float = 0.0
        self.playback_speed: float = 1.0
        self.is_playing: bool = False
        self.lock = Lock()
        
    def start_recording(self, camera_ids: List[int]):
        """Start recording for specified cameras."""
        with self.lock:
            for camera_id in camera_ids:
                self.recordings[camera_id] = []
                
    def add_frame(self, camera_id: int, frame: np.ndarray):
        """Add a frame to the recording with current timestamp."""
        if camera_id in self.recordings:
            timestamp = time.time()
            video_frame = VideoFrame(frame, timestamp, camera_id)
            with self.lock:
                self.recordings[camera_id].append(video_frame)
    
    def stop_recording(self):
        """Stop recording and finalize the recordings."""
        with self.lock:
            # Normalize timestamps relative to the earliest frame
            min_timestamp = float('inf')
            for frames in self.recordings.values():
                if frames and frames[0].timestamp < min_timestamp:
                    min_timestamp = frames[0].timestamp
            
            # Adjust all timestamps relative to start
            for frames in self.recordings.values():
                for frame in frames:
                    frame.timestamp -= min_timestamp
    
    def seek_to(self, position: float):
        """Seek to a specific position in seconds."""
        with self.lock:
            self.current_position = max(0, position)
    
    def get_frames_at_position(self) -> Dict[int, np.ndarray]:
        """Get frames from all cameras at current position."""
        frames = {}
        with self.lock:
            for camera_id, recording in self.recordings.items():
                # Find the closest frame to current position
                closest_frame = None
                min_diff = float('inf')
                
                for frame in recording:
                    diff = abs(frame.timestamp - self.current_position)
                    if diff < min_diff:
                        min_diff = diff
                        closest_frame = frame
                
                if closest_frame:
                    frames[camera_id] = closest_frame.frame
        
        return frames
    
    def set_playback_speed(self, speed: float):
        """Set playback speed (1.0 is normal speed)."""
        with self.lock:
            self.playback_speed = max(0.1, min(speed, 4.0))
    
    def step_frame(self, forward: bool = True):
        """Step one frame forward or backward."""
        with self.lock:
            # Find the smallest frame interval across all recordings
            min_interval = float('inf')
            for recording in self.recordings.values():
                if len(recording) > 1:
                    interval = recording[1].timestamp - recording[0].timestamp
                    min_interval = min(min_interval, interval)
            
            if min_interval != float('inf'):
                step = min_interval if forward else -min_interval
                self.current_position = max(0, self.current_position + step)
    
    def get_duration(self) -> float:
        """Get total duration of the recordings in seconds."""
        max_duration = 0
        for recording in self.recordings.values():
            if recording:
                duration = recording[-1].timestamp
                max_duration = max(max_duration, duration)
        return max_duration

