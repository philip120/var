import logging
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QMessageBox)
from PyQt6.QtCore import Qt, QTimer
from .video_grid import VideoGrid
from .camera_dialog import CameraSelectionDialog
from core.camera_manager import CameraManager
import time

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
            self.video_grid = VideoGrid(rows=2, cols=2)
            main_layout.addWidget(self.video_grid)
            
            # Create control panel
            logger.debug("Creating control panel")
            self.control_panel = self.create_control_panel()
            main_layout.addWidget(self.control_panel)
            
            # Setup frame update timer with precise timing
            self.update_timer = QTimer()
            self.update_timer.setTimerType(Qt.TimerType.PreciseTimer)
            self.update_timer.setInterval(33)  # ~30 FPS
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
        """Update all video frames"""
        if not self.camera_manager.running:
            return
            
        try:
            current_time = time.time()
            
            for camera_id in self.camera_manager.cameras.keys():
                frame = self.camera_manager.get_frame(camera_id)
                if frame is not None:
                    self.video_grid.update_feed(camera_id, frame)
                    self.frame_count += 1
                else:
                    self.video_grid.clear_feed(camera_id)
            
            # Log FPS every second
            if current_time - self.last_fps_time >= 1.0:
                fps = self.frame_count / (current_time - self.last_fps_time)
                logger.debug(f"UI Update FPS: {fps:.1f}")
                self.frame_count = 0
                self.last_fps_time = current_time
                
        except Exception as e:
            logger.error(f"Error updating video frames: {str(e)}", exc_info=True)

    def show_camera_selection(self):
        """Show camera selection dialog"""
        try:
            logger.debug("Opening camera selection dialog")
            dialog = CameraSelectionDialog(self)
            if dialog.exec() == CameraSelectionDialog.DialogCode.Accepted:
                device_path = dialog.get_selected_camera()
                if device_path is not None:
                    logger.debug(f"Selected camera: {device_path}")
                    # Stop current camera if running
                    if self.camera_manager.running:
                        self.camera_manager.stop_capture()
                        self.video_grid.clear_feed(self.current_camera_id)
                    
                    # Try to connect to selected camera
                    if self.camera_manager.add_camera(self.current_camera_id, device_path):
                        logger.debug("Camera connected successfully")
                        self.camera_manager.start_capture()
                        self.connect_camera_btn.setText("Disconnect Camera")
                        self.update_button_states()
                    else:
                        logger.error(f"Failed to connect to camera: {device_path}")
                        QMessageBox.warning(self, "Camera Error", 
                                          f"Could not connect to camera: {device_path}")
        except Exception as e:
            logger.error(f"Error in camera selection: {str(e)}", exc_info=True)

    def toggle_camera(self):
        """Toggle camera connection on/off"""
        try:
            if self.camera_manager.running:
                logger.debug("Stopping camera capture")
                self.camera_manager.stop_capture()
                self.connect_camera_btn.setText("Connect Camera")
            else:
                if self.camera_manager.is_camera_connected(self.current_camera_id):
                    logger.debug("Starting camera capture")
                    self.camera_manager.start_capture()
                    self.connect_camera_btn.setText("Disconnect Camera")
            self.update_button_states()
        except Exception as e:
            logger.error(f"Error toggling camera: {str(e)}", exc_info=True)

    def update_button_states(self):
        """Update button states based on camera connection"""
        try:
            camera_connected = self.camera_manager.is_camera_connected(self.current_camera_id)
            camera_running = self.camera_manager.running
            
            self.connect_camera_btn.setEnabled(camera_connected)
            self.play_button.setEnabled(camera_connected and not camera_running)
            self.pause_button.setEnabled(camera_connected and camera_running)
            self.record_button.setEnabled(camera_connected and camera_running)
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