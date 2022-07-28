
from PySide2.QtCore import Signal

from PySide2.QtGui import QPixmap, Qt, QColor
from PySide2.QtWidgets import QWidget, QVBoxLayout, QGraphicsItemGroup, QButtonGroup

from io_interface.DataStoreInterface import DataStoreInterface
from Skeleton import Skeleton
from io_interface.VideoReaderInterface import VideoReaderInterface
from ImageViewer import ImageViewer
from ui_KeyPoint import KeyPointController
from ui_Skeleton import SkeletonController


class CameraController(QWidget):

    def __init__(self,main_ui,config,video_reader: VideoReaderInterface, data_store: DataStoreInterface,threshold=0.6):
        super().__init__()
        self.main_ui = main_ui
        self.config = config
        self.data_store = data_store
        self.video_reader = video_reader
        v_layout = QVBoxLayout()
        self.image_viewer = ImageViewer(self,SkeletonController(config,threshold,))
        v_layout.addWidget(self.image_viewer)
        self.setLayout(v_layout)
        self.frame_number = -1
        self.is_initialized = False
        self.skeleton = None
        self.keypoint_list = []
        self.annotation_button_group = QButtonGroup()
        for idx, (name, color) in enumerate(zip(self.config['body_parts'], self.config['colors'])):
            q_color = QColor.fromRgb(*color)
            kp_ui = KeyPointController(idx, name, q_color)
            self.keypoint_list.append(kp_ui)
            self.annotation_button_group.addButton(kp_ui.annotation_radio_button)



    def render_next_frame(self, event=None):
        if self.video_reader.state == -1:
            return
        if self.video_reader.state == 0:
            self.video_reader.start()
        frame = self.video_reader.next_frame()
        if frame is not None:
            self.frame_number = self.video_reader.get_current_index()
            self.main_ui.frameNumber.setText(
                f'<html style="font-weight:600">Frame-Number: {self.frame_number}/{self.video_reader.get_number_of_frames()}</html>')
            self.skeleton=self.data_store.get_skeleton(self.frame_number)
            self.image_viewer.draw_frame(frame,self.skeleton,self.skeleton)

    def render_previous_frame(self):
        if self.frame_number != 0:
            self.seek(self.frame_number - 1)

    def seek(self, frame_number):
        if self.frame_number != frame_number and frame_number < self.video_reader.get_number_of_frames():
            self.video_reader.seek_pos(max(0, frame_number))
            self.render_next_frame(None)
        else:
            self.update_keypoints()

    def reset_view(self, event=None):
        if self.image_viewer.zoom_times > 0:
            self.image_viewer.scale(ImageViewer.ZOOM_OUT_FACTOR * self.image_viewer.zoom_times,
                                    ImageViewer.ZOOM_OUT_FACTOR * self.image_viewer.zoom_times)
        self.image_viewer.fitInView()
