from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QMessageBox)
from PyQt6.QtCore import Qt, QTimer
from .video_grid import VideoGrid
from .camera_dialog import CameraSelectionDialog
from core.camera_manager import CameraManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sports VAR System")
        self.setMinimumSize(1200, 800)
        
        # Initialize camera manager
        self.camera_manager = CameraManager()
        self.current_camera_id = 0
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        
        # Create video grid
        self.video_grid = VideoGrid(rows=2, cols=2)
        main_layout.addWidget(self.video_grid)
        
        # Create control panel
        self.control_panel = self.create_control_panel()
        main_layout.addWidget(self.control_panel)
        
        # Setup camera refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.update_camera_feeds)
        self.refresh_timer.start(33)  # ~30 FPS
    
    def create_control_panel(self):
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
        
        layout.addWidget(self.select_camera_btn)
        layout.addWidget(self.connect_camera_btn)
        layout.addWidget(self.play_button)
        layout.addWidget(self.pause_button)
        layout.addWidget(self.record_button)
        
        return panel
    
    def show_camera_selection(self):
        """Show camera selection dialog"""
        dialog = CameraSelectionDialog(self)
        if dialog.exec() == CameraSelectionDialog.DialogCode.Accepted:
            device_path = dialog.get_selected_camera()
            if device_path:
                # Stop current camera if running
                if self.camera_manager.running:
                    self.camera_manager.stop_capture()
                
                # Try to connect to selected camera
                if self.camera_manager.add_camera(self.current_camera_id, device_path):
                    self.camera_manager.start_capture()
                    self.connect_camera_btn.setText("Disconnect Camera")
                else:
                    QMessageBox.warning(self, "Camera Error", 
                                      f"Could not connect to camera: {device_path}")
    
    def toggle_camera(self):
        """Toggle camera connection on/off"""
        if self.camera_manager.running:
            self.camera_manager.stop_capture()
            self.connect_camera_btn.setText("Connect Camera")
        else:
            if self.camera_manager.is_camera_connected(self.current_camera_id):
                self.camera_manager.start_capture()
                self.connect_camera_btn.setText("Disconnect Camera")
    
    def update_camera_feeds(self):
        """Update all camera feeds with latest frames"""
        for camera_id in self.camera_manager.cameras.keys():
            frame = self.camera_manager.get_frame(camera_id)
            self.video_grid.update_feed(camera_id, frame)
    
    def closeEvent(self, event):
        """Clean up resources when closing the application"""
        self.camera_manager.stop_capture()
        event.accept() 