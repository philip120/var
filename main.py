# main.py
import sys
import logging
from pathlib import Path
from PyQt6.QtWidgets import QApplication

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add src directory to Python path
src_path = str(Path(__file__).parent.parent)
if src_path not in sys.path:
    sys.path.append(src_path)
    logger.debug(f"Added {src_path} to Python path")

from src.ui.main_window import MainWindow

def main():
    try:
        logger.debug("Starting application")
        
        # Create application
        logger.debug("Creating QApplication")
        app = QApplication(sys.argv)
        
        # Create main window with error catching
        logger.debug("Creating MainWindow")
        try:
            window = MainWindow()
        except Exception as e:
            logger.error(f"Failed to create MainWindow: {str(e)}", exc_info=True)
            raise
        
        # Show window
        logger.debug("Showing window")
        window.show()
        
        # Start event loop
        logger.debug("Starting event loop")
        return_code = app.exec()
        logger.debug(f"Application exited with code {return_code}")
        sys.exit(return_code)
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
