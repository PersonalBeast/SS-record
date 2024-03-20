import sys
import cv2
import numpy as np
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog, QMessageBox, QInputDialog
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QIcon
from mss import mss
from screeninfo import get_monitors

class ScreenRecordThread(QThread):
    # Custom signal to update the UI or save the file when recording stops
    update = pyqtSignal()

    def __init__(self, monitor_index=0):
        super().__init__()
        self.is_running = False
        self.monitor_index = monitor_index

    def run(self):
        # Set thread to running state
        self.is_running = True
        # Dynamically determine screen dimensions based on the selected monitor
        monitor = get_monitors()[self.monitor_index]
        screen_width = monitor.width
        screen_height = monitor.height

        # Use mp4v codec for video compression for broad compatibility
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter('temp.mp4', fourcc, 30.0, (screen_width, screen_height))

        with mss() as sct:
            # Correcting monitor index for mss library as it starts from 1
            monitor = sct.monitors[self.monitor_index + 1]  
            while self.is_running:
                img = sct.grab(monitor)
                # Convert captured image to a numpy array and then to BGR for OpenCV processing
                img_np = np.array(img)
                frame = cv2.cvtColor(img_np, cv2.COLOR_BGRA2BGR)
                out.write(frame)

        # Release the video writer to free resources
        out.release()
        # Emit signal to indicate recording has stopped and the file is ready to be saved
        self.update.emit()

    def start_recording(self):
        # Prevent multiple instances of the recording thread from starting
        if not self.isRunning():
            self.start()

    def stop_recording(self):
        # Signal the run loop to stop recording
        self.is_running = False

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SS Record")
        self.setFixedSize(250, 175)  # Fixed size window to simplify UI design
        # Set window icon, ensure the path is correct
        self.setWindowIcon(QIcon('./components/icon.ico'))

        self.selected_monitor_index = None
        self.recording_thread = None

        # UI elements setup
        self.pick_monitor_button = QPushButton("Pick Monitor", self)
        self.pick_monitor_button.setGeometry(50, 10, 150, 40)
        self.pick_monitor_button.clicked.connect(self.pick_monitor)

        self.start_button = QPushButton("Start Recording", self)
        self.start_button.setGeometry(50, 60, 150, 40)
        self.start_button.clicked.connect(self.start_recording)
        self.start_button.setEnabled(False)  # Disabled until a monitor is selected

        self.stop_button = QPushButton("Stop Recording", self)
        self.stop_button.setGeometry(50, 110, 150, 40)
        self.stop_button.clicked.connect(self.stop_recording)
        self.stop_button.setEnabled(False)  # Initially disabled

    def pick_monitor(self):
        # List available monitors for the user to choose from
        monitors = get_monitors()
        monitor_names = [f"Monitor {i}: {monitor.width}x{monitor.height}" for i, monitor in enumerate(monitors)]
        choice, ok = QInputDialog.getItem(self, "Pick Monitor", "Select a monitor:", monitor_names, 0, False)
        if ok:
            self.selected_monitor_index = monitor_names.index(choice)
            # Enable the start button now that a monitor has been selected
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)

    def start_recording(self):
        if self.selected_monitor_index is not None:
            # Initialize and start the recording thread
            self.recording_thread = ScreenRecordThread(monitor_index=self.selected_monitor_index)
            # Connect the update signal to save_file method to prompt user for file location
            self.recording_thread.update.connect(self.save_file)
            self.recording_thread.start_recording()
        if self.recording_thread:
            # Update UI state to reflect recording status
            self.stop_button.setEnabled(True)
            self.start_button.setEnabled(False)
            self.pick_monitor_button.setEnabled(False)

    def stop_recording(self):
        if self.recording_thread:
            # Signal the recording thread to stop and update UI accordingly
            self.recording_thread.stop_recording()
            self.pick_monitor_button.setEnabled(True)
            self.stop_button.setEnabled(False)

    # File dialog method
    def save_file(self):
        fileName, _ = QFileDialog.getSaveFileName(self, "Save Video", "", "Video Files (*.mp4);;All Files (*)")
        if fileName:
            import shutil
            shutil.move('temp.mp4', fileName)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
