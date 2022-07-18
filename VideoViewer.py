from PySide2.QtWidgets import QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,QFrame
from PySide2.QtGui import QPixmap,Qt
from PySide2.QtCore import QRectF, Signal

from DataStoreInterface import DataStoreInterface
from VideoReaderInterface import VideoReaderInterface
from PIL import Image
from PIL.ImageQt import ImageQt


class ImageViewer(QGraphicsView):
    ZOOM_IN_FACTOR=1.25
    ZOOM_OUT_FACTOR=0.8

    delete_keypoint = Signal()

    def __init__(self,parent):
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.pixmap_item=QGraphicsPixmapItem()
        self._scene.addItem(self.pixmap_item)
        self.setScene(self._scene)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setFrameShape(QFrame.NoFrame)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setCursor(Qt.CrossCursor)
        self.zoom_flag=False
        self.zoom_times=0

    def fitInView(self) -> None:
        rect = QRectF(self.pixmap_item.pixmap().rect())
        if not rect.isNull():
            self.setSceneRect(rect)
            unity = self.transform().mapRect(QRectF(0, 0, 1, 1))
            self.scale(1 / unity.width(), 1 / unity.height())
            viewrect = self.viewport().rect()
            scenerect = self.transform().mapRect(rect)
            factor = min(viewrect.width() / scenerect.width(),
                         viewrect.height() / scenerect.height())
            self.scale(factor, factor)

    def wheelEvent(self, event):
        if self.zoom_flag:
            if event.angleDelta().y() > 0:
                factor = 1.25
                self.zoom_times+=1
            else:
                factor = 0.8
                self.zoom_times=max(0,self.zoom_times-1)
            if self.zoom_times>0:
                self.scale(factor, factor)

    def mouseMoveEvent(self, event):
        point = event.localPos()
        self.setFocus()
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        if event.button()==Qt.MidButton:
            self.delete_keypoint.emit()
        super().mousePressEvent(event)

    def keyPressEvent(self, event) -> None:
        if event.key()==Qt.Key_Control:
            self.zoom_flag=True
            self.setDragMode(QGraphicsView.ScrollHandDrag)
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event) -> None:
        if event.key() == Qt.Key_Control:
            self.zoom_flag = False
            self.setDragMode(QGraphicsView.NoDrag)
        super().keyReleaseEvent(event)

class VideoViewer(QWidget):

    def __init__(self,main_ui,video_reader:VideoReaderInterface,data_store:DataStoreInterface,keypoints):
        super().__init__()
        self.main_ui=main_ui
        self.keypoints=keypoints
        self.data_store=data_store
        self.video_reader= video_reader
        v_layout=QVBoxLayout()
        self.image_viewer=ImageViewer(self)
        v_layout.addWidget(self.image_viewer)
        self.setLayout(v_layout)
        self.current_frame_number=-1
        self.is_initialized=False

    def update_keypoints(self):
        for keypoint in self.keypoints:
            self.data_store.get_keypoint_location(keypoint.data_point, self.current_frame_number)
            keypoint.marker.setRect(*keypoint.data_point.get_location(), 5, 5)
            keypoint.marker.setToolTip(f'{int(keypoint.data_point.x_loc)},{int(keypoint.data_point.y_loc)}')
            if keypoint.data_point > 0.6:
                keypoint.visibility_checkbox.setChecked(True)
            else:
                keypoint.visibility_checkbox.setChecked(False)
        self.draw_keypoints()

    def draw_keypoints(self):
        for keypoint in self.keypoints:
            keypoint.marker.setVisible(keypoint.visibility_checkbox.isChecked())
            if keypoint.marker in self.image_viewer.scene().items():
                self.image_viewer.scene().removeItem(keypoint.marker)
            self.image_viewer.scene().addItem(keypoint.marker)

    def render_next_frame(self, event=None):
        if self.video_reader.state==0:
            self.video_reader.start()
        frame=self.video_reader.next_frame()
        self.current_frame_number=self.video_reader.get_current_index()
        self.main_ui.frameNumber.setText(f'<html style="font-weight:600">Frame-Number: {self.current_frame_number}/{self.video_reader.get_number_of_frames()}</html>')
        self.update_keypoints()
        if frame is not None:
            pixmap=QPixmap.fromImage(ImageQt(Image.fromarray(frame)))
            self.image_viewer.pixmap_item.setPixmap(pixmap)
            # self.image_viewer.fitInView()

    def render_previous_frame(self):
        if self.current_frame_number!=0:
            self.seek(self.current_frame_number-1)

    def seek(self,frame_number):
        if self.current_frame_number != frame_number and frame_number<self.video_reader.get_number_of_frames():
            self.video_reader.seek_pos(max(0,frame_number-1))
            self.render_next_frame(None)
        else:
            self.update_keypoints()

    def reset_view(self,event=None):
        if self.image_viewer.zoom_times>0:
            self.image_viewer.scale(ImageViewer.ZOOM_OUT_FACTOR*self.image_viewer.zoom_times,ImageViewer.ZOOM_OUT_FACTOR*self.image_viewer.zoom_times)
        self.image_viewer.fitInView()
