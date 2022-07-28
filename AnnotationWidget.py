import os

from PySide2.QtCore import QFile, QTimer
from PySide2.QtUiTools import QUiLoader

from ImageViewer import ImageViewer, AnnotationImageViewer
from PlayControlWidget import PlayControlWidget
from io_interface.DeeplabcutDataStore import DeeplabcutDataStore
from io_interface.CV2VideoReader import CV2VideoReader
from Skeleton import Skeleton
from PySide2.QtGui import QPixmap, Qt, QColor
from PySide2.QtWidgets import QWidget, QVBoxLayout, QGraphicsItemGroup, QButtonGroup, QCheckBox
from ui_KeyPoint import KeyPointController
from ui_Skeleton import SkeletonController


class AnnotationWidget(PlayControlWidget):
    def __init__(self, config, view_name,ui_file,video_reader,data_store, threshold=0.6, parent=None):
        super(AnnotationWidget, self).__init__(config, view_name,ui_file,video_reader,data_store, threshold, parent)
        layout = QVBoxLayout()
        layout.addWidget(self.ui)
        self.setLayout(layout)
        self.annotation_button_group = QButtonGroup()
        self.visibility_button_group = QButtonGroup()
        self.visibility_button_group.setExclusive(False)
        self.behaviour_button_group = QButtonGroup()
        self.interp_button_group = QButtonGroup()
        self.interp_button_group.setExclusive(False)
        self.keypoint_list = []
        self.current_keypoint = None

        self.ui.view_container.removeWidget(self.image_viewer)
        self.image_viewer.deleteLater()
        
        self.image_viewer = AnnotationImageViewer()
        self.image_viewer.scroll_keypoint.connect(self.scroll_keypoint)
        self.image_viewer.select_keypoint.connect(lambda id,state:self.annotation_button_group.button(id).setChecked(state))
        self.image_viewer.modify_keypoint.connect(self.modify_selected_keypoint)
        self.image_viewer.delete_keypoint.connect(self.set_keypoint_likelihood)
        self.ui.view_container.addWidget(self.image_viewer)

        self.interp_initial_index_set=set(self.config['body_parts'])
        self.interp_candidate_set=set()
        self.interp_initial_index_frame=0
        self.ui.interpSetCurrentIndex.clicked.connect(self.interp_update_initial_index_set)
        for idx, (name, color) in enumerate(zip(self.config['body_parts'], self.config['colors'])):
            kp_ui = KeyPointController(idx, name, color)
            self.keypoint_list.append(kp_ui)
            self.ui.keypoint_container.addWidget(kp_ui)
            self.visibility_button_group.addButton(kp_ui.visibility_checkbox, id=kp_ui.id)
            self.annotation_button_group.addButton(kp_ui.annotation_radio_button, id=kp_ui.id)
            btn = QCheckBox(name)
            self.interp_button_group.addButton(btn,idx)
            self.ui.interpolationList.addWidget(btn)
        for idx, behaviour in enumerate(self.config['behaviours']):
            btn = QCheckBox(behaviour)
            self.behaviour_button_group.addButton(btn, id=idx)
            self.ui.behaviourList.addWidget(btn)
        self.behaviour_button_group.buttons()[0].setChecked(True)
        self.behaviour_button_group.idClicked.connect(self.set_behaviour)
        self.interp_button_group.idToggled.connect(self.interp_set_candidate)
        self.current_keypoint = self.keypoint_list[0]
        self.skeleton_drawer = SkeletonController(self.config)
        self.annotation_button_group.idToggled.connect(self.change_keypoint)
        self.visibility_button_group.idToggled.connect(self.set_keypoint_likelihood)
        self.current_keypoint.annotation_radio_button.setChecked(True)
        self.ui.toolBox.setCurrentIndex(0)
        self.render_next_frame()
        self.timer = QTimer()
        self.timer.timeout.connect(self.render_next_frame)

        self.ui.interpSeekIndex.clicked.connect(lambda event:self.seek(self.interp_initial_index_frame))
        self.ui.interpSelectAllButton.clicked.connect(self.interp_select_all)
        self.ui.interpClearAllButton.clicked.connect(self.interp_clear_all)
        self.ui.interpolateButton.clicked.connect(self.interpolate)

    def scroll_keypoint(self, offset):
        current_id = self.keypoint_list.index(self.current_keypoint)
        new_id = current_id + offset
        new_id = 0 if new_id < 0 else len(self.keypoint_list) - 1 if new_id >= len(self.keypoint_list) else new_id
        self.annotation_button_group.button(new_id).setChecked(True)

    def change_keypoint(self, id, state):
        if state:
            self.current_keypoint = self.keypoint_list[id]
            self.ui.scrollArea_2.ensureWidgetVisible(self.current_keypoint)
        self.skeleton_drawer.mark_selected(self.config['body_parts'][id], state)

    def render_next_frame(self, event=None):
        super().render_next_frame(event)
        self.update_annotation_ui(self.skeleton)
        self.draw_markers()
        self.ui.seekBar.setValue(self.frame_number)

    def update_annotation_ui(self, skeleton):
        for idx, part in enumerate(self.config['body_parts']):
            self.keypoint_list[idx].visibility_checkbox.blockSignals(True)
            if skeleton[part] >= self.threshold:
                self.keypoint_list[idx].visibility_checkbox.setChecked(True)
            else:
                self.keypoint_list[idx].visibility_checkbox.setChecked(False)
            self.keypoint_list[idx].visibility_checkbox.blockSignals(False)
        self.behaviour_button_group.blockSignals(True)
        self.behaviour_button_group.buttons()[self.config['behaviours'].index(skeleton.behaviour)].setChecked(True)
        self.behaviour_button_group.blockSignals(False)
        self.interp_update_candidates()

    def modify_selected_keypoint(self, point):
        name = self.current_keypoint.name
        self.skeleton[name][:2] = point.x(), point.y()
        self.skeleton[name].liklihood = 1.0
        self.data_store.set_marker(self.frame_number, self.skeleton[name])
        self.draw_markers()

    def set_keypoint_likelihood(self, id, state):
        keypoint = self.keypoint_list[id] if id >= 0 else self.current_keypoint
        name = keypoint.name
        self.skeleton[name].likelihood = 0.0 if not state else self.threshold
        self.data_store.set_marker(self.frame_number, self.skeleton[name])
        self.draw_markers()

    def draw_markers(self):
        self.skeleton_drawer.update_skeleton(self.skeleton)
        self.update_annotation_ui(self.skeleton)
        self.image_viewer.draw_skeleton(self.skeleton_drawer.itemGroup)

    def set_behaviour(self, id):
        self.skeleton.behaviour = self.config['behaviours'][id]

    def interp_update_candidates(self):
        for idx,name in enumerate(self.config['body_parts']):
            if name in self.interp_initial_index_set and self.keypoint_list[idx].visibility_checkbox.isChecked():
                self.interp_button_group.button(idx).setChecked(True)
            else:
                self.interp_button_group.button(idx).setChecked(False)

    def interp_set_candidate(self, id, state):
        name = self.config['body_parts'][id]
        self.interp_button_group.blockSignals(True)
        if self.frame_number == self.interp_initial_index_frame:
            if state and self.keypoint_list[id].visibility_checkbox.isChecked():
                self.interp_initial_index_set.add(name)
                self.interp_candidate_set.add(name)
            else:
                if name in self.interp_initial_index_set:
                    self.interp_initial_index_set.remove(name)
                if name in self.interp_candidate_set:
                    self.interp_candidate_set.remove(name)
                self.interp_button_group.button(id).setChecked(False)
        else:
            if state and name in self.interp_initial_index_set and self.keypoint_list[id].visibility_checkbox.isChecked():
                self.interp_candidate_set.add(name)
            else:
                if name in self.interp_candidate_set:
                    self.interp_candidate_set.remove(name)
                self.interp_button_group.button(id).setChecked(False)
        self.interp_button_group.blockSignals(False)

    def interp_update_initial_index_set(self,event=None):
        self.interp_initial_index_set = set([self.keypoint_list[i].name for i in range(len(self.keypoint_list)) if
                                             self.keypoint_list[i].visibility_checkbox.isChecked() and self.keypoint_list[i].name in self.interp_candidate_set])
        self.interp_initial_index_frame=self.frame_number
        self.ui.interpInitialIndex.setText(str(self.frame_number))

    def interp_select_all(self,event):
        for btn in self.interp_button_group.buttons():
            btn.setChecked(True)

    def interp_clear_all(self,event):
        for btn in self.interp_button_group.buttons():
            btn.setChecked(False)

    def interpolate(self,event):
        total_frames = self.frame_number-self.interp_initial_index_frame
        if total_frames<2:
            return
        for name in self.interp_candidate_set:
            part_initial = self.data_store.get_marker(self.interp_initial_index_frame,name)
            part_current = self.data_store.get_marker(self.frame_number, name)
            additive_coordinates = (part_current-part_initial)/total_frames
            for i in range(self.interp_initial_index_frame,self.frame_number):
                self.data_store.set_marker(i,part_initial)
                part_initial+=additive_coordinates
