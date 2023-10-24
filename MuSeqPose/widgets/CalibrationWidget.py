import os

import cv2
import numpy as np
from PySide2.QtCore import QFile
from PySide2.QtGui import QKeySequence
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QDialog, QRadioButton, QMessageBox, QShortcut

from MuSeqPose import get_resource
from MuSeqPose.ui_Skeleton import Marker
from MuSeqPose.utils.session_manager import SessionManager
from MuSeqPose.widgets.ImageViewer import AnnotationImageViewer
from cvkit.pose_estimation import Part
from cvkit.pose_estimation.reconstruction.EasyWand_tools import generate_EasyWand_data
from cvkit.video_readers.image_sequence_reader import generate_image_sequence_reader


class CalibrationDialog(QDialog):

    def __init__(self, parent, session_manager: SessionManager, frame_indices):
        super().__init__(parent)
        self.frame_number = 0
        self.frame_indices = frame_indices
        self.config = session_manager.config
        self.session_manager = session_manager
        file = QFile(get_resource('CalibrationWidget.ui'))
        file.open(QFile.ReadOnly)
        self.ui = QUiLoader().load(file)
        self.setWindowTitle("MuSeqPose - Wand Calibration Widget")
        self.video_readers = {}
        self.views = []
        self.widgets = []
        self.radio_btns = []
        self.ui.cancel.clicked.connect(self.close)
        self.ui.frameNumber.setText(f'{self.frame_number}/{len(self.frame_indices) - 1}')
        self.markers = {}
        for part in self.config.body_parts:
            self.radio_btns.append(QRadioButton(part))
            self.ui.keypointContainer.addWidget(self.radio_btns[-1])
        for part in self.config.calibration_static_points:
            self.radio_btns.append(QRadioButton(part))
            self.ui.keypointContainer.addWidget(self.radio_btns[-1])
        self.radio_btns[0].setChecked(True)
        for index, view in enumerate(self.config.views):
            widget = AnnotationImageViewer()
            source_reader = session_manager.session_video_readers[view]
            self.video_readers[view] = generate_image_sequence_reader(source_reader.video_path,
                                                                      source_reader.fps, frame_indices,
                                                                      os.path.join(self.config.output_folder,
                                                                                   'calibration', 'candidates', view))
            widget.draw_frame(self.video_readers[view].random_access_image(self.frame_number))
            self.views.append(view)
            widget.select_keypoint.connect(self.change_keypoint)
            widget.modify_keypoint.connect(self.annotate)
            self.ui.view_container.addTab(widget, view)
            self.widgets.append(widget)
            self.markers[view] = []
            for i in range(len(self.radio_btns)):
                self.markers[view].append(Marker(i, 0, 0, 4, 4, color=self.config.colors[i]))
                widget.scene.addItem(self.markers[view][-1])
                self.markers[view][-1].setVisible(True)
            for i in range(self.config.num_parts, len(self.radio_btns)):
                pos = self.config.calibration_static_point_locations[view][
                    self.config.calibration_static_points[i - self.config.num_parts]]
                self.markers[view][i].setX(pos[0] - 2)
                self.markers[view][i].setY(pos[1] - 2)
        self.frame_indices = [int(os.path.basename(path).split('.')[0]) for path in self.video_readers[view].images]
        self.setLayout(self.ui.layout())
        self.ui.frame_slider.setMinimum(0)
        self.ui.frame_slider.setMaximum(len(self.frame_indices) - 1)
        self.ui.frame_slider.valueChanged.connect(self.change_frame)
        QShortcut(QKeySequence.MoveToNextChar, self.ui.frame_slider, lambda: self.change_frame(self.frame_number + 1))
        QShortcut(QKeySequence.MoveToPreviousChar, self.ui.frame_slider,
                  lambda: self.change_frame(self.frame_number - 1))
        self.ui.generateData.clicked.connect(self.generate_data)
        self.ui.deleteFrame.clicked.connect(self.delete_frame)
        self.change_frame(0)
        self.ui.detect_corner_btn.clicked.connect(self.detect_corner)
        self.show()

    def annotate(self, pos):
        if type(pos) == np.ndarray:
            x = pos[0]
            y = pos[1]
        else:
            x = pos.x()
            y = pos.y()
        index = self.ui.view_container.currentIndex()
        selected = [k for k in range(len(self.radio_btns)) if self.radio_btns[k].isChecked()][0]
        marker = self.markers[self.views[index]][selected]
        marker.setX(x - 2)
        marker.setY(y - 2)
        if self.radio_btns[marker.idx].text() in self.config.body_parts:
            part = Part([x, y], self.radio_btns[marker.idx].text(), 1.0)
            self.session_manager.session_data_readers[self.views[index]].set_part(
                self.frame_indices[self.frame_number], part)
        else:
            self.config.calibration_static_point_locations[self.views[index]][
                self.config.calibration_static_points[selected - self.config.num_parts]] = [x, y]
        marker.update()

    def delete_frame(self, event):
        delete_frame_number = self.frame_number
        if len(self.frame_indices) <= 7:
            QMessageBox.warning(self.ui, 'Error', 'Need at least 7 images to generate calibration data')
            return
        self.frame_number = min(0, self.frame_number - 1)
        self.frame_indices.pop(delete_frame_number)
        # Only ImageSequenceReader supports frame deletion.
        for reader in self.video_readers.values():
            reader.delete_frame(delete_frame_number)
        self.ui.frame_slider.setMaximum(len(self.frame_indices) - 1)
        self.change_frame(self.frame_number)

    def generate_data(self, event):
        csv_maps = {camera: self.session_manager.session_data_readers[camera] for camera in self.config.views}
        static_points_map = {}
        for camera in self.config.views:
            static_points_map[camera] = []
            for marker in self.markers[camera][len(self.config.body_parts):]:
                static_points_map[camera].append([marker.x() + 2, marker.y() + 2])
        try:
            generate_EasyWand_data(self.config, csv_maps, self.frame_indices, static_points_map)
            QMessageBox.information(self.ui, 'Info', 'EasyWand data generated')
            self.close()
        except Exception as ex:
            print(ex)
            QMessageBox.warning(self.ui, 'Error', f'Error occurred while generating EasyWand data.\n{ex}')

    def change_keypoint(self, pos, _):
        self.radio_btns[pos].setChecked(True)

    def change_frame(self, frame_number):
        self.frame_number = min(max(frame_number, 0), len(self.frame_indices) - 1)
        self.ui.frameNumber.setText(
            f'{self.frame_number}/{len(self.frame_indices)} :{self.frame_indices[self.frame_number]} ')
        for i, view in enumerate(self.views):
            image = self.video_readers[view].random_access_image(self.frame_number)
            self.widgets[i].draw_frame(image)
            self.widgets[i].fitInView()
            for index, part in enumerate(self.config.body_parts):
                pos = self.session_manager.session_data_readers[view].get_part(self.frame_indices[self.frame_number],
                                                                               part)
                self.markers[view][index].setX(int(pos[0] - 2))
                self.markers[view][index].setY(int(pos[1] - 2))
                self.markers[view][index].update()

    def close(self):
        for reader in self.video_readers.values():
            reader.release()
        super().close()

    def detect_corner(self, event):
        index = self.ui.view_container.currentIndex()
        selected = [k for k in range(len(self.radio_btns)) if self.radio_btns[k].isChecked()][0]
        marker = self.markers[self.views[index]][selected]
        image = self.video_readers[self.views[index]].random_access_image(self.frame_number)
        pos = self.compute_corner(image, np.array([marker.x() + 2, marker.y() + 2]))
        self.annotate(pos)

    def compute_corner(self, image, point, pixel_padding=15):
        # Repurposed from https://docs.opencv.org/3.4/dc/d0d/tutorial_py_features_harris.html
        roi = np.array([[max(0, point[1] - pixel_padding), min(image.shape[0] - 1, point[1] + pixel_padding)],
                        [max(0, point[0] - pixel_padding), min(image.shape[1] - 1, point[0] + pixel_padding)]]).astype(
            np.intc)

        gray = cv2.cvtColor(image[roi[0][0]:roi[0][1], roi[1][0]:roi[1][1], :], cv2.COLOR_RGB2GRAY)
        sharpen_kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
        gray = cv2.filter2D(gray, -1, sharpen_kernel)
        gray = np.float32(gray)
        dst = cv2.cornerHarris(gray, 2, 3, 0.04)
        dst = cv2.dilate(dst, None)
        ret, dst = cv2.threshold(dst, 0.01 * dst.max(), 255, 0)
        dst = np.uint8(dst)
        # find centroids
        ret, labels, stats, centroids = cv2.connectedComponentsWithStats(dst)
        # define the criteria to stop and refine the corners
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.001)
        corners = cv2.cornerSubPix(gray, np.float32(centroids), (5, 5), (-1, -1), criteria)
        corners[:, 1] += roi[0][0]
        corners[:, 0] += roi[1][0]
        index = np.argmin(np.sum(np.abs(corners - point), axis=1))
        return corners[index]
