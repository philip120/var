import cv2
import numpy as np
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import json
import time
from threading import Thread, Lock, Event

class PlaybackManager:
    def __init__(self):
        self.video_captures: Dict[int, cv2.VideoCapture] = {}
        self.current_position: float = 0.0
        self.playback_speed: float = 1.0
        self.is_playing: bool = False
        self.duration: float = 0.0
        self.lock = Lock()
        self.playback_thread: Optional[Thread] = None
        self.stop_event = Event()
        self.frame_callbacks: List[callable] = []
        
    def load_session(self, session_directory: str) -> bool:
        """Load a recorded session for playback."""
        session_path = Path(session_directory)
        if not session_path.exists():
            return False
            
        # Load metadata
        metadata_path = session_path / "metadata.json"
        if not metadata_path.exists():
            return False
            
        with open(metadata_path, "r") as f:
            metadata = json.load(f)
            
        self.duration = metadata["duration"]
        
        # Load video files
        for camera_id in metadata["cameras"]:
            video_path = session_path / f"camera_{camera_id}.mp4"
            if not video_path.exists():
                continue
                
            cap = cv2.VideoCapture(str(video_path))
            if cap.isOpened():
                self.video_captures[camera_id] = cap
                
        return len(self.video_captures) > 0
        
    def play(self):
        """Start playback."""
        if self.is_playing or not self.video_captures:
            return
            
        self.is_playing = True
        self.stop_event.clear()
        self.playback_thread = Thread(target=self._playback_loop, daemon=True)
        self.playback_thread.start()
        
    def pause(self):
        """Pause playback."""
        self.is_playing = False
        self.stop_event.set()
        if self.playback_thread:
            self.playback_thread.join()
            self.playback_thread = None
            
    def seek_to(self, position: float):
        """Seek to a specific position in seconds."""
        with self.lock:
            position = max(0, min(position, self.duration))
            self.current_position = position
            
            # Seek all videos to the position
            for cap in self.video_captures.values():
                cap.set(cv2.CAP_PROP_POS_MSEC, position * 1000)
                
    def set_playback_speed(self, speed: float):
        """Set playback speed (1.0 is normal speed)."""
        with self.lock:
            self.playback_speed = max(0.1, min(speed, 4.0))
            
    def step_frame(self, forward: bool = True):
        """Step one frame forward or backward."""
        was_playing = self.is_playing
        if was_playing:
            self.pause()
            
        with self.lock:
            frames_dict = {}
            for camera_id, cap in self.video_captures.items():
                if forward:
                    ret, frame = cap.read()
                    if ret:
                        frames_dict[camera_id] = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                else:
                    # Get current frame position
                    current_frame = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
                    if current_frame > 1:
                        # Seek to previous frame
                        cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame - 2)
                        ret, frame = cap.read()
                        if ret:
                            frames_dict[camera_id] = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                            
            if frames_dict:
                self._notify_callbacks(frames_dict)
                
        if was_playing:
            self.play()
            
    def register_frame_callback(self, callback: callable):
        """Register a callback to receive frames during playback."""
        self.frame_callbacks.append(callback)
        
    def _playback_loop(self):
        """Main playback loop."""
        last_update = time.time()
        
        while not self.stop_event.is_set():
            current_time = time.time()
            delta_time = (current_time - last_update) * self.playback_speed
            self.current_position += delta_time
            
            if self.current_position >= self.duration:
                self.current_position = 0
                for cap in self.video_captures.values():
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    
            frames_dict = {}
            with self.lock:
                for camera_id, cap in self.video_captures.items():
                    ret, frame = cap.read()
                    if ret:
                        frames_dict[camera_id] = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        
            if frames_dict:
                self._notify_callbacks(frames_dict)
                
            last_update = current_time
            time.sleep(1/60)  # Limit to 60 FPS max
            
    def _notify_callbacks(self, frames: Dict[int, np.ndarray]):
        """Notify all registered callbacks with new frames."""
        for callback in self.frame_callbacks:
            callback(frames)
            
    def __del__(self):
        """Cleanup resources."""
        self.pause()
        for cap in self.video_captures.values():
            cap.release()
