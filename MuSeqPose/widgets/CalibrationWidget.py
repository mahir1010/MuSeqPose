import os

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
        self.show()

    def annotate(self, pos):
        index = self.ui.view_container.currentIndex()
        selected = [k for k in range(len(self.radio_btns)) if self.radio_btns[k].isChecked()][0]
        marker = self.markers[self.views[index]][selected]
        marker.setX(pos.x() - 2)
        marker.setY(pos.y() - 2)
        if self.radio_btns[marker.idx].text() in self.config.body_parts:
            part = Part([pos.x(), pos.y()], self.radio_btns[marker.idx].text(), 1.0)
            self.session_manager.session_data_readers[self.views[index]].set_part(
                self.frame_indices[self.frame_number], part)
        else:
            self.config.calibration_static_point_locations[self.views[index]][
                self.config.calibration_static_points[selected - self.config.num_parts]] = [pos.x(), pos.y()]
        marker.update()

    def delete_frame(self, event):
        delete_frame_number = self.frame_number
        if len(self.frame_indices) <= 10:
            QMessageBox.warning(self.ui, 'Error', 'Need at least 10 images to generate calibration data')
            return
        self.frame_number = min(0, self.frame_number - 1)
        self.frame_indices.pop(delete_frame_number)
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
            self.widgets[i].draw_frame(self.video_readers[view].random_access_image(self.frame_number))
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
