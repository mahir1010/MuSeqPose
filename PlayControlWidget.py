from PySide2.QtGui import QPixmap, Qt, QColor
from PySide2.QtCore import QFile, QTimer
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QWidget, QVBoxLayout, QGraphicsItemGroup, QButtonGroup, QCheckBox
from ImageViewer import ImageViewer


class PlayControlWidget(QWidget):

    def __init__(self,config, view_name,ui_file,video_reader,data_store, threshold=0.6, parent=None):
        super(PlayControlWidget, self).__init__(parent)
        self.config = config
        self.view_name = view_name
        self.threshold = 0.6
        self.video_reader = video_reader
        self.data_store = data_store
        self.image_viewer = ImageViewer()
        self.frame_number = 0
        self.skeleton = None
        self.is_video_playing = False
        ui_file = QFile(ui_file)
        ui_file.open(QFile.ReadOnly)
        self.ui = QUiLoader().load(ui_file)
        self.ui.resetViewButton.clicked.connect(self.reset_view)
        self.ui.nextFrameButton.clicked.connect(self.next_button_pressed)
        self.ui.prevFrameButton.clicked.connect(self.prev_button_pressed)
        self.ui.playPauseButton.clicked.connect(self.play_video)
        self.ui.seekButton.clicked.connect(self.seek_ui_input)
        self.ui.seekBar.setMinimum(0)
        self.ui.seekBar.setMaximum(self.video_reader.get_number_of_frames())
        self.ui.seekBar.valueChanged.connect(lambda: self.seek_ui_input(self.ui.seekBar.value()))
        self.ui.view_container.addWidget(self.image_viewer)

    def render_next_frame(self, event=None):
        if self.video_reader.state == -1:
            return
        if self.video_reader.state == 0:
            self.video_reader.start()
        frame = self.video_reader.next_frame()
        if frame is not None:
            if self.skeleton is not None:
                self.data_store.set_skeleton(self.frame_number, self.skeleton)
            self.frame_number = self.video_reader.get_current_index()
            self.ui.frameNumber.setText(
                f'<html style="font-weight:600">Frame-Number: {self.frame_number}/{self.video_reader.get_number_of_frames()}</html>')
            self.skeleton = self.data_store.get_skeleton(self.frame_number)
            if self.skeleton.behaviour == "":
                self.set_behaviour(self.behaviour_button_group.checkedId())
                self.image_viewer.draw_frame(frame)

    def render_previous_frame(self):
        if self.frame_number != 0:
            self.seek(self.frame_number - 1)

    def seek(self, frame_number):
        if self.frame_number != frame_number and frame_number < self.video_reader.get_number_of_frames():
            self.video_reader.seek_pos(max(0, frame_number))
            self.render_next_frame(None)

    def reset_view(self, event=None):
        if self.image_viewer.zoom_times > 0:
            self.image_viewer.scale(ImageViewer.ZOOM_OUT_FACTOR * self.image_viewer.zoom_times,
                                    ImageViewer.ZOOM_OUT_FACTOR * self.image_viewer.zoom_times)
        self.image_viewer.fitInView()

    def seek_ui_input(self, event=None):
        if type(event) != int:
            try:
                frame_number = int(self.ui.seekValue.text())
            except ValueError:
                pass
        else:
            frame_number = event
        self.seek(frame_number)

    def play_video(self, event):
        if self.is_video_playing:
            self.timer.stop()
            self.is_video_playing = False
            self.ui.nextFrameButton.setEnabled(True)
            self.ui.prevFrameButton.setEnabled(True)
            self.ui.playPauseButton.setText('Play')
        else:
            self.timer.start(int(1000 / self.video_reader.fps))
            self.ui.playPauseButton.setText('Pause')
            self.is_video_playing = True
            self.ui.nextFrameButton.setEnabled(False)
            self.ui.prevFrameButton.setEnabled(False)

    def next_button_pressed(self, event):
        self.render_next_frame()

    def prev_button_pressed(self, event):
        self.render_previous_frame()

    def reset_current_view(self, event):
        self.reset_view()
