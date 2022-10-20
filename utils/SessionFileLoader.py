from PySide2.QtCore import Signal, Qt
from PySide2.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QComboBox, QLabel, QPushButton, QFileDialog, \
    QMessageBox

from OptiPose.data_store_interface import datastore_readers, initialize_datastore_reader
from config import MuSeqPoseConfig


class SessionFileLoader(QWidget):
    file_loaded = Signal()

    def __init__(self, parent, config:MuSeqPoseConfig,dialog=True):
        super(SessionFileLoader, self).__init__(parent)
        self.is_dialog = dialog
        if dialog:
            self.setWindowFlag(Qt.Dialog,True)
            self.resize(300,100)
        self.file = None
        layout = QHBoxLayout()
        layout.setMargin(0)
        self.setWindowTitle("Load New File")
        self.flavors = QComboBox()
        self.flavors.addItems(list(datastore_readers.keys()))
        self.flavors.setCurrentIndex(0)
        layout.addWidget(self.flavors)
        file_btn = QPushButton('Load File')
        file_btn.clicked.connect(self.load_file)
        layout.addWidget(file_btn)
        self.config = config
        self.setLayout(layout)

    def load_file(self, event=None):
        self.file = QFileDialog.getOpenFileName(self, f"Load {self.flavors.currentText()} File",
                                                self.config.output_folder, 'CSV (*.csv)')[0]
        if self.file:
            try:
                self.file = initialize_datastore_reader(self.config.body_parts, self.file,
                                                        self.flavors.currentText())
                if self.is_dialog:
                    self.close()
            except Exception as ex:
                print(ex)
                self.file = None
                QMessageBox.warning(self, "Error", str(ex))

    def closeEvent(self, event):
        self.file_loaded.emit()
        event.accept()