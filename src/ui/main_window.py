import logging
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QMessageBox)
from PyQt6.QtCore import Qt, QTimer
from .video_grid import VideoGrid
from .camera_dialog import CameraSelectionDialog
from core.camera_manager import CameraManager
import time
import cv2

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    def __init__(self):
        logger.debug("Initializing MainWindow")
        super().__init__()
        
        try:
            # Basic window setup
            self.setWindowTitle("Sports VAR System")
            self.setMinimumSize(1200, 800)
            logger.debug("Window properties set")
            
            # Initialize camera manager
            logger.debug("Creating CameraManager")
            self.camera_manager = CameraManager()
            self.current_camera_id = 0
            
            # Create main widget and layout
            logger.debug("Creating main layout")
            main_widget = QWidget()
            self.setCentralWidget(main_widget)
            main_layout = QVBoxLayout(main_widget)
            
            # Create video grid
            logger.debug("Creating VideoGrid")
            self.video_grid = VideoGrid()  # Remove rows and cols parameters
            main_layout.addWidget(self.video_grid)
            
            # Initialize with single camera view
            self.video_grid.setup_grid(1)
            
            # Create control panel
            logger.debug("Creating control panel")
            self.control_panel = self.create_control_panel()
            main_layout.addWidget(self.control_panel)
            
            # Setup frame update timer
            self.update_timer = QTimer()
            self.update_timer.setTimerType(Qt.TimerType.PreciseTimer)
            self.update_timer.setInterval(16)  # ~60 FPS to match camera
            self.update_timer.timeout.connect(self.update_video_frames)
            
            # Performance monitoring
            self.frame_count = 0
            self.last_fps_time = time.time()
            
            # Start timer
            self.update_timer.start()
            
            # Disable buttons initially
            self.update_button_states()
            
            logger.debug("MainWindow initialization complete")
            
        except Exception as e:
            logger.error(f"Error in MainWindow initialization: {str(e)}", exc_info=True)
            raise

    def create_control_panel(self):
        try:
            logger.debug("Creating control panel")
            panel = QWidget()
            layout = QHBoxLayout(panel)
            
            # Add camera control buttons
            self.select_camera_btn = QPushButton("Select Camera")
            self.select_camera_btn.clicked.connect(self.show_camera_selection)
            self.connect_camera_btn = QPushButton("Connect Camera")
            self.connect_camera_btn.clicked.connect(self.toggle_camera)
            
            # Add basic playback controls
            self.play_button = QPushButton("Play")
            self.pause_button = QPushButton("Pause")
            self.record_button = QPushButton("Record")
            
            # Disable playback controls initially
            self.play_button.setEnabled(False)
            self.pause_button.setEnabled(False)
            self.record_button.setEnabled(False)
            
            layout.addWidget(self.select_camera_btn)
            layout.addWidget(self.connect_camera_btn)
            layout.addWidget(self.play_button)
            layout.addWidget(self.pause_button)
            layout.addWidget(self.record_button)
            
            logger.debug("Control panel created successfully")
            return panel
            
        except Exception as e:
            logger.error(f"Error creating control panel: {str(e)}", exc_info=True)
            raise

    def update_video_frames(self):
        """Update all video feeds"""
        try:
            # Get frames from all cameras
            frames = self.camera_manager.get_frames()
            
            # Update each camera feed
            for camera_idx, frame in frames.items():
                if frame is not None:
                    # Convert BGR to RGB for display
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    self.video_grid.update_feed(camera_idx, rgb_frame)
                else:
                    self.video_grid.clear_feed(camera_idx)
            
            # Log FPS every second
            self.frame_count += 1
            current_time = time.time()
            if current_time - self.last_fps_time >= 1.0:
                fps = self.frame_count / (current_time - self.last_fps_time)
                logger.debug(f"UI Update FPS: {fps:.1f}")
                self.frame_count = 0
                self.last_fps_time = current_time
                
        except Exception as e:
            logger.error(f"Error updating video frames: {str(e)}", exc_info=True)

    def show_camera_selection(self):
        """Show camera selection dialog"""
        dialog = CameraSelectionDialog(self)
        if dialog.exec():
            selected_cameras = dialog.get_selected_cameras()
            if selected_cameras:
                # Setup video grid for selected number of cameras
                self.video_grid.setup_grid(len(selected_cameras))
                
                # Start camera manager with selected cameras
                for camera_idx in selected_cameras:
                    self.camera_manager.add_camera(camera_idx)
                self.camera_manager.start_capture()
                
                # Update button states
                self.update_button_states()

    def toggle_camera(self):
        """Toggle camera connection on/off"""
        try:
            if self.camera_manager.is_capturing():
                logger.debug("Stopping cameras")
                self.camera_manager.stop_capture()
                self.connect_camera_btn.setText("Connect Camera")
            else:
                self.show_camera_selection()
            self.update_button_states()
        except Exception as e:
            logger.error(f"Error toggling camera: {str(e)}", exc_info=True)

    def update_button_states(self):
        """Update button states based on camera connection"""
        try:
            camera_connected = self.camera_manager.is_capturing()
            self.connect_camera_btn.setText("Disconnect Camera" if camera_connected else "Connect Camera")
            self.select_camera_btn.setEnabled(not camera_connected)
            self.play_button.setEnabled(False)  # Disable unused buttons
            self.pause_button.setEnabled(False)
            self.record_button.setEnabled(False)
        except Exception as e:
            logger.error(f"Error updating button states: {str(e)}", exc_info=True)

    def closeEvent(self, event):
        """Clean up resources when closing the application"""
        try:
            logger.debug("Closing application")
            self.update_timer.stop()
            self.camera_manager.stop_capture()
            event.accept()
        except Exception as e:
            logger.error(f"Error during application closure: {str(e)}", exc_info=True)
            event.accept() 