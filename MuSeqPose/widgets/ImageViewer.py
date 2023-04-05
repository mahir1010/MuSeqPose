from PIL import Image
from PIL.ImageQt import ImageQt
from PySide2.QtCore import Signal, QRectF, QPointF
from PySide2.QtGui import Qt, QPixmap
from PySide2.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QFrame

from MuSeqPose.ui_Skeleton import Marker, SkeletonController


class ImageViewer(QGraphicsView):
    ZOOM_IN_FACTOR = 1.25
    ZOOM_OUT_FACTOR = 0.8

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.pixmap_item = QGraphicsPixmapItem()
        self.scene.addItem(self.pixmap_item)
        self.setScene(self.scene)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setFrameShape(QFrame.NoFrame)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setCursor(Qt.CrossCursor)
        self.zoom_flag = False
        self.zoom_times = 0

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
            self.zoom_times = 0

    def wheelEvent(self, event):
        if self.zoom_flag:
            if event.angleDelta().y() > 0:
                factor = 1.25
                self.zoom_times += 1
            else:
                factor = 0.8
                self.zoom_times = max(0, self.zoom_times - 1)
            if self.zoom_times > 0:
                self.scale(factor, factor)

    def mouseMoveEvent(self, event):
        point = event.localPos()
        self.setFocus()
        super().mouseMoveEvent(event)

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key_Control:
            self.zoom_flag = True
            self.setDragMode(QGraphicsView.ScrollHandDrag)
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event) -> None:
        if event.key() == Qt.Key_Control:
            self.zoom_flag = False
            self.setDragMode(QGraphicsView.NoDrag)
        super().keyReleaseEvent(event)

    def draw_frame(self, frame):
        pixmap = QPixmap.fromImage(ImageQt(Image.fromarray(frame)))
        self.pixmap_item.setPixmap(pixmap)
        self.update()

    def draw_skeleton(self, skeleton: SkeletonController):
        # TODO Redesign drawing, no need to remove and add graphics items on every update.
        for line in skeleton.lines:
            if line in self.scene.items():
                pass  # self.scene.removeItem(line)
            else:
                self.scene.addItem(line)
        for marker in skeleton.markers.values():
            if marker in self.scene.items():
                pass  # self.scene.removeItem(marker)
            else:
                self.scene.addItem(marker)
        self.update()


class AnnotationImageViewer(ImageViewer):
    delete_keypoint = Signal(int, bool)
    modify_keypoint = Signal(QPointF)
    scroll_keypoint = Signal(int)
    select_keypoint = Signal(int, bool)

    def __init__(self, parent=None):
        super(AnnotationImageViewer, self).__init__(parent)
        self.selected_marker = None

    def mousePressEvent(self, event):
        if event.button() == Qt.MidButton and not self.zoom_flag:
            self.delete_keypoint.emit(-1, False)
        if event.button() == Qt.LeftButton and not self.zoom_flag:
            new_position = self.pixmap_item.mapFromScene(self.mapToScene(event.pos()))
            clicked_item = self.scene.itemAt(new_position, self.transform())
            if type(clicked_item) == Marker:
                self.select_keypoint.emit(clicked_item.idx, True)
                self.selected_marker = clicked_item
        if event.button() == Qt.RightButton and not self.zoom_flag:
            new_position = self.pixmap_item.mapFromScene(self.mapToScene(event.pos()))
            self.modify_keypoint.emit(new_position)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.selected_marker is not None:
            new_position = self.pixmap_item.mapFromScene(self.mapToScene(event.pos()))
            self.select_keypoint.emit(self.selected_marker.idx, True)
            self.modify_keypoint.emit(new_position)
            self.selected_marker = None
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event):
        if not self.zoom_flag:
            if event.angleDelta().y() > 0:
                self.scroll_keypoint.emit(-1)
            else:
                self.scroll_keypoint.emit(1)
        super(AnnotationImageViewer, self).wheelEvent(event)
