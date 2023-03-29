import sys
import os
import re
import subprocess
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QFileDialog, QMessageBox, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QProgressBar, QSpacerItem, QSizePolicy
from PyQt5.QtCore import Qt, QThread, pyqtSignal


class VideoConverterWorker(QThread):
    progress = pyqtSignal(int)

    def __init__(self, input_file, output_dir, speed):
        super().__init__()
        self.input_file = input_file
        self.output_dir = output_dir
        self.speed = speed

    def run(self):
        output_file = os.path.join(self.output_dir, os.path.splitext(
            os.path.basename(self.input_file))[0] + ".mp4")
        cmd = [
            "ffmpeg", "-i", self.input_file, "-c:v", "hevc_nvenc",
            "-preset", self.speed, "-c:a", "copy", output_file
        ]

        process = subprocess.Popen(
            cmd, stderr=subprocess.PIPE, universal_newlines=True)
        duration = None
        time_pattern = re.compile(r"time=(\d{2}:\d{2}:\d{2}\.\d{2})")

        for line in process.stderr:
            if "Duration" in line:
                time_parts = line.split(",")[0].split(" ")[-1].split(":")
                duration = int(time_parts[0]) * 3600 + \
                    int(time_parts[1]) * 60 + float(time_parts[2])

            match = time_pattern.search(line)
            if match:
                current_time = match.group(1)
                current_time_parts = current_time.split(":")
                current_time_sec = int(current_time_parts[0]) * 3600 + int(
                    current_time_parts[1]) * 60 + float(current_time_parts[2])

                if duration:
                    progress = int(current_time_sec / duration * 100)
                    self.progress.emit(progress)


class VideoConverter(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Video Converter")
        self.setGeometry(100, 100, 800, 300)
        self.initUI()

    def initUI(self):
        central_widget = QWidget()
        layout = QVBoxLayout()

        hbox1 = QHBoxLayout()
        label1 = QLabel("Video file:")
        self.input_file_label = QLabel("No file selected.")
        select_file_button = QPushButton("Select file")
        select_file_button.clicked.connect(self.select_file)
        hbox1.addWidget(label1)
        hbox1.addWidget(self.input_file_label)
        hbox1.addWidget(select_file_button)

        hbox2 = QHBoxLayout()
        label2 = QLabel("Output folder:")
        self.output_dir_label = QLabel("No folder selected.")
        select_output_dir_button = QPushButton("Select folder")
        select_output_dir_button.clicked.connect(self.select_output_dir)
        hbox2.addWidget(label2)
        hbox2.addWidget(self.output_dir_label)
        hbox2.addWidget(select_output_dir_button)

        hbox3 = QHBoxLayout()
        label3 = QLabel("Conversion speed:")
        self.speed_combobox = QComboBox()
        self.speed_combobox.addItems(["fast", "medium", "slow"])
        hbox3.addWidget(label3)
        hbox3.addWidget(self.speed_combobox)

        self.start_button = QPushButton("Start conversion")
        self.start_button.clicked.connect(self.start_conversion)
        self.progress_bar = QProgressBar()

        spacer = QSpacerItem(
            40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        layout.addLayout(hbox1)
        layout.addLayout(hbox2)
        layout.addLayout(hbox3)
        layout.addWidget(self.start_button)
        layout.addWidget(self.progress_bar)
        layout.addItem(spacer)

        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def select_file(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        self.input_file, _ = QFileDialog.getOpenFileName(
            self, "Select video file", "", "All Files (*)", options=options)
        if self.input_file:
            self.input_file_label.setText(self.input_file)

    def select_output_dir(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ShowDirsOnly
        self.output_dir = QFileDialog.getExistingDirectory(
            self, "Select output folder", "", options=options)
        if self.output_dir:
            self.output_dir_label.setText(self.output_dir)

    def start_conversion(self):
        if not hasattr(self, 'input_file') or not hasattr(self, 'output_dir'):
            QMessageBox.warning(
                self, "Warning", "Please select a video file and an output folder.")
            return

        speed = self.speed_combobox.currentText()

        self.start_button.setEnabled(False)
        self.progress_bar.setValue(0)

        self.worker = VideoConverterWorker(
            self.input_file, self.output_dir, speed)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.conversion_finished)
        self.worker.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def conversion_finished(self):
        self.start_button.setEnabled(True)
        self.progress_bar.setValue(100)
        QMessageBox.information(
            self, "Conversion complete", "Video conversion completed successfully!")


def main():
    app = QApplication(sys.argv)
    main_window = VideoConverter()
    main_window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
