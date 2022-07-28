import sys

import yaml as yml
from PySide2.QtCore import QTimer, QFile, QCoreApplication, Qt
from PySide2.QtWidgets import QApplication, QFileDialog, QMainWindow, QButtonGroup, QRadioButton, QCheckBox, \
    QGraphicsItemGroup
from PySide2.QtUiTools import QUiLoader

from AnnotationWidget import AnnotationWidget
from io_interface.CV2VideoReader import CV2VideoReader
from io_interface.DeeplabcutDataStore import DeeplabcutDataStore
from ui_KeyPoint import KeyPointController
from Keypoint import Keypoint
from ui_CameraController import CameraController
from ui_Skeleton import SkeletonController
from ui_main import Ui_MainWindow
import os


class MuSeqAnnotator(QApplication):
    def __init__(self,argv):
        super(MuSeqAnnotator, self).__init__(argv)
        ui_file = QFile(os.path.join('Resources','main.ui'))
        ui_file.open(QFile.ReadOnly)
        loader = QUiLoader()
        self.ui = loader.load(ui_file)
        self.ui.show()
        self.ui.actionLoad.triggered.connect(self.open_project)
        self.ui.setWindowTitle('Pose Annotator')
        self.views = []
        self.file_name = None
        self.config=None
        self.current_view_index=0


    def open_project(self):
        file_name = QFileDialog.getOpenFileName(self.ui, "Open Yaml File", None, "config (*.yaml)")[0]
        if file_name:
            self.file_name = file_name
            self.load_data()

    def load_data(self):
        self.config = yml.safe_load(open(self.file_name, 'r'))
        self.ui.setWindowTitle(f'MuSeq Annotator : {self.config["name"]}')
        for view in self.config['views']:
            view_data = self.config['views'][view]
            video_reader = CV2VideoReader(view, view_data['video_file'], int(view_data['framerate']))
            data_store=DeeplabcutDataStore(self.config['body_parts'], view_data['annotation_file'])
            ui_file = os.path.join('Resources','AnnotationWidget.ui')
            play_controller=AnnotationWidget(self.config, view, ui_file,video_reader, data_store,threshold=self.config['threshold'])
            self.views.append(play_controller)
            self.ui.viewTabWidget.addTab(play_controller, view)
        self.current_view_index = 0
        self.ui.viewTabWidget.currentChanged.connect(self.change_view)

    def change_view(self, i):
        if self.current_view_index != i:
            current_view = self.views[self.current_view_index]
            new_view = self.views[i]
            if current_view.is_video_playing:
                current_view.ui.playPauseButton.clicked.emit()
            frame_number = current_view.frame_number
            self.current_view_index = i
            new_view.seek(frame_number)

if __name__ == "__main__":
    QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    app = MuSeqAnnotator(sys.argv)
    sys.exit(app.exec_())
