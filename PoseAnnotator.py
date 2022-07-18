import sys

import yaml as yml
from PySide2.QtWidgets import QApplication, QFileDialog, QMainWindow, QListWidgetItem, QButtonGroup, QRadioButton
from PySide2.QtCore import QTimer
from CV2VideoReader import CV2VideoReader
from DeeplabcutDataStore import DeeplabcutDataStore
from KeyPointUI import KeyPointUI
from Keypoint import Keypoint
from VideoViewer import VideoViewer
from ui_main import Ui_MainWindow


class MuSeqAnnotator(QMainWindow):
    def __init__(self):
        super(MuSeqAnnotator, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.actionLoad.triggered.connect(self.open_project)
        self.setWindowTitle('Pose Annotator')
        self.views=[]
        self.initialized=False
        self.file_name=None
        self.config={}
        self.current_view_index=0
        self.keypoint_list=[]
        self.annotation_button_group=QButtonGroup()
        self.activity_button_group=QButtonGroup()
        self.ui.viewTabWidget.currentChanged.connect(self.change_view)
        self.timer = QTimer()
        self.ui.playPauseButton.clicked.connect(self.play_video)
        self.is_video_playing=False
        self.ui.seekButton.clicked.connect(self.seek_frame)
        self.ui.nextFrameButton.clicked.connect(self.next_button_pressed)
        self.ui.prevFrameButton.clicked.connect(self.prev_button_pressed)
        self.ui.resetViewButton.clicked.connect(self.reset_current_view)
        self.current_keypoint = None


    def open_project(self):
        file_name = QFileDialog.getOpenFileName(self, "Open Yaml File", None, "config (*.yaml)")[0]
        if file_name:
            self.file_name = file_name
            self.load_data()
            self.initialized = True

    def load_data(self):
        self.config = yml.safe_load(open(self.file_name, 'r'))
        self.setWindowTitle(f'MuSeq Annotator : {self.config["name"]}')

        for idx,(name,color) in enumerate(zip(self.config['bodyparts'],self.config['colors'])):
            keypoint=Keypoint(name,color)
            kp_ui=KeyPointUI(idx,keypoint)
            self.keypoint_list.append(kp_ui)
            self.ui.keyPointList.addWidget(kp_ui)
            kp_ui.keypoint_deleted.connect(self.redraw_kp)
            kp_ui.keypoint_selected.connect(self.change_keypoint)
            kp_ui.visibility_checkbox.clicked.connect(self.redraw_kp)
            self.annotation_button_group.addButton(kp_ui.annotation_radio_button, id=kp_ui.id)
        self.keypoint_list[0].annotation_radio_button.setChecked(True)
        self.current_keypoint=self.keypoint_list[0]
        self.annotation_button_group.idClicked.connect(self.change_keypoint)

        for activity in self.config['activities']:
            radio=QRadioButton()
            radio.setText(activity)
            self.activity_button_group.addButton(radio)
            self.ui.activityList.addWidget(radio)

        for view in self.config['views']:
            view_data=self.config['views'][view]
            video_reader=CV2VideoReader(view,view_data['video_file'],int(view_data['framerate']))
            data_store=DeeplabcutDataStore(view_data['annotation_file'])
            video_viewer=VideoViewer(self.ui, video_reader, data_store, self.keypoint_list)
            video_viewer.image_viewer.delete_keypoint.connect(self.delete_selected_keypoint)
            self.views.append(video_viewer)
            self.ui.viewTabWidget.addTab(video_viewer,view)
        self.views[0].render_next_frame(None)
        self.ui.nextFrameButton.setEnabled(True)
        self.ui.playPauseButton.setEnabled(True)
        self.ui.prevFrameButton.setEnabled(True)
        self.ui.resetViewButton.setEnabled(True)
        self.ui.seekButton.setEnabled(True)

    def delete_selected_keypoint(self):
        self.current_keypoint.visibility_checkbox.setChecked(False)
        self.redraw_kp(None)

    def change_keypoint(self,id):
        self.current_keypoint=self.keypoint_list[id]


    def seek_frame(self,event):
        frame_number=int(self.ui.seekValue.text())
        self.views[self.current_view_index].seek(frame_number)

    def redraw_kp(self,event):
        self.views[self.current_view_index].draw_keypoints()

    def play_video(self,event):
        if self.is_video_playing:
            self.timer.stop()
            self.is_video_playing=False
            self.ui.nextFrameButton.setEnabled(True)
            self.ui.prevFrameButton.setEnabled(True)
            self.ui.playPauseButton.setText('Play')
        else:
            try:
                self.timer.timeout.disconnect()
            except:
                pass
            self.timer.timeout.connect(self.views[self.current_view_index].render_next_frame)
            self.timer.start(int(1000/self.views[self.current_view_index].video_reader.fps))
            self.ui.playPauseButton.setText('Pause')
            self.is_video_playing = True
            self.ui.nextFrameButton.setEnabled(False)
            self.ui.prevFrameButton.setEnabled(False)

    def next_button_pressed(self,event):
        self.views[self.current_view_index].render_next_frame()

    def prev_button_pressed(self,event):
        self.views[self.current_view_index].render_previous_frame()

    def reset_current_view(self,event):
        self.views[self.current_view_index].reset_view()

    def change_view(self,i):
        if self.current_view_index!=i:
            if self.is_video_playing:
                self.ui.playPauseButton.clicked.emit()
            frame_number=self.views[self.current_view_index].video_reader.get_current_index()
            self.current_view_index=i
            self.views[i].seek(frame_number)
            if not self.views[self.current_view_index].is_initialized:
                self.views[self.current_view_index].is_initialized=True
                self.reset_current_view(None)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MuSeqAnnotator()
    window.show()

    sys.exit(app.exec_())
