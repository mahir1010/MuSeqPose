from datetime import timedelta

from PySide2.QtCore import QTimer, Signal
from PySide2.QtWidgets import QVBoxLayout, QButtonGroup, QCheckBox, QMessageBox

from MuSeqPose.player_interface import VideoPlayer
from MuSeqPose.ui_Skeleton import SkeletonController
from MuSeqPose.utils.session_manager import SessionManager
from MuSeqPose.widgets.ImageViewer import AnnotationImageViewer
from MuSeqPose.widgets.PlayControlWidget import PlayControlWidget
from MuSeqPose.widgets.ui_KeyPoint import KeyPointController


class AnnotationWidget(PlayControlWidget):
    reproject = Signal(str, int, list, list)

    def update_frame_number(self):
        self.frame_number = self.video_player.frame_number

    def __init__(self, view_name: str, session_manager: SessionManager, ui_file, video_player: VideoPlayer,
                 threshold=0.6,
                 parent=None):
        super(AnnotationWidget, self).__init__(session_manager, ui_file, threshold, parent)
        self.view_name = view_name
        self.video_player = video_player
        layout = QVBoxLayout()
        layout.addWidget(self.ui)
        self.ui.reprojectionToolBox.setVisible(self.config.reprojection_toolbox_enabled)
        self.setLayout(layout)
        self.annotation_button_group = QButtonGroup()
        self.visibility_button_group = QButtonGroup()
        self.visibility_button_group.setExclusive(False)
        self.behaviour_button_group = QButtonGroup()
        self.behaviour_button_group.setExclusive(False)
        self.interp_button_group = QButtonGroup()
        self.interp_button_group.setExclusive(False)
        self.reprojection_parts_button_group = QButtonGroup()
        self.reprojection_parts_button_group.setExclusive(False)
        self.reprojection_views_button_group = QButtonGroup()
        self.reprojection_views_button_group.setExclusive(False)
        self.keypoint_list = []
        self.current_keypoint = None
        self.image_viewer = AnnotationImageViewer()
        self.image_viewer.scroll_keypoint.connect(self.scroll_keypoint)
        self.image_viewer.select_keypoint.connect(
            lambda id, state: self.annotation_button_group.button(id).setChecked(state))
        self.image_viewer.modify_keypoint.connect(self.modify_selected_keypoint)
        self.image_viewer.delete_keypoint.connect(self.set_keypoint_likelihood)
        self.ui.view_container.addWidget(self.image_viewer)

        self.interp_initial_index_set = set(self.config.body_parts)
        self.interp_candidate_set = set()
        self.interp_initial_index_frame = 0
        self.ui.interpSetCurrentIndex.clicked.connect(self.interp_update_initial_index_set)
        for idx, (name, color) in enumerate(zip(self.config.body_parts, self.config.colors)):
            kp_ui = KeyPointController(idx, name, color)
            self.keypoint_list.append(kp_ui)
            self.ui.keypoint_container.addWidget(kp_ui)
            self.visibility_button_group.addButton(kp_ui.visibility_checkbox, id=kp_ui.id)
            self.annotation_button_group.addButton(kp_ui.annotation_radio_button, id=kp_ui.id)
            btn = QCheckBox(name)
            self.interp_button_group.addButton(btn, idx)
            self.ui.interpolationList.addWidget(btn)
            if self.config.reprojection_toolbox_enabled:
                reprojection_btn = QCheckBox(name)
                self.reprojection_parts_button_group.addButton(reprojection_btn, idx)
                self.ui.reprojKeypointList.addWidget(reprojection_btn)
        if self.config.reprojection_toolbox_enabled:
            self.ui.reprojectButton.clicked.connect(self.reproject_parts)
            for idx, view in enumerate(self.config.annotation_views):
                reprojection_btn = QCheckBox(view)
                self.reprojection_views_button_group.addButton(reprojection_btn, idx)
                self.ui.viewList.addWidget(reprojection_btn)
        for idx, behaviour in enumerate(self.config.behaviours):
            btn = QCheckBox(behaviour)
            self.behaviour_button_group.addButton(btn, id=idx)
            self.ui.behaviourList.addWidget(btn)
        self.behaviour_button_group.idToggled.connect(self.set_behaviour)
        self.interp_button_group.idToggled.connect(self.interp_set_candidate)
        self.current_keypoint = self.keypoint_list[0]
        self.video_player.data_point_drawer = SkeletonController(self.session_manager, threshold)
        self.annotation_button_group.idToggled.connect(self.change_keypoint)
        self.visibility_button_group.idToggled.connect(self.set_keypoint_likelihood)
        self.current_keypoint.annotation_radio_button.setChecked(True)
        self.ui.toolBox.setCurrentIndex(0)
        self.render_next_frame()
        self.timer = QTimer()
        self.timer.timeout.connect(self.render_next_frame)
        self.ui.seekBar.setMaximum(self.video_player.get_number_of_frames())
        self.ui.seekBar.valueChanged.connect(lambda: self.seek_ui_input(self.ui.seekBar.value()))
        self.ui.seekBar.setTracking(False)
        self.ui.interpSeekIndex.clicked.connect(lambda event: self.seek(self.interp_initial_index_frame))
        self.ui.interpSelectAllButton.clicked.connect(self.interp_select_all)
        self.ui.interpClearAllButton.clicked.connect(self.interp_clear_all)
        self.ui.interpolateButton.clicked.connect(self.interpolate)

    def scroll_keypoint(self, offset):
        current_id = self.keypoint_list.index(self.current_keypoint)
        new_id = current_id + offset
        new_id = 0 if new_id < 0 else len(self.keypoint_list) - 1 if new_id >= len(self.keypoint_list) else new_id
        self.annotation_button_group.button(new_id).setChecked(True)

    def reproject_parts(self, event):
        view_candidates = [btn.text() for btn in self.reprojection_views_button_group.buttons() if btn.isChecked()]
        part_candidates = [btn.text() for btn in self.reprojection_parts_button_group.buttons() if btn.isChecked()]
        if len(view_candidates) > 1 and len(part_candidates) > 0:
            self.reproject.emit(self.view_name, self.frame_number, view_candidates, part_candidates)

    def change_keypoint(self, id, state):
        if state:
            self.current_keypoint = self.keypoint_list[id]
            self.ui.scrollArea_2.ensureWidgetVisible(self.current_keypoint)
        self.video_player.data_point_drawer.mark_selected(self.config.body_parts[id], state)

    def get_timestamp(self, frame_number):
        return str(timedelta(seconds=round(frame_number / self.video_player.video_reader.fps, 3)))

    def render_next_frame(self, redraw=None):
        if type(redraw) == bool and redraw:
            self.image_viewer.draw_frame(self.video_player.current_frame)
        else:
            self.frame_number = self.video_player.render_next_frame(self.image_viewer)
        self.ui.frameNumber.setText(
            f'<html style="font-weight:600">Frame-Number: {self.frame_number}/{self.video_player.get_number_of_frames()}</html>')
        self.ui.timestamp.setText(f'<html style="font-weight:600">{self.get_timestamp(self.frame_number)}</html>')
        self.update_annotation_ui(self.video_player.data_point)
        self.draw_markers()
        self.ui.seekBar.blockSignals(True)
        self.ui.seekBar.setValue(self.frame_number)
        self.ui.seekBar.blockSignals(False)

    def update_annotation_ui(self, skeleton):
        for idx, part in enumerate(self.config.body_parts):
            self.keypoint_list[idx].visibility_checkbox.blockSignals(True)
            if skeleton[part] >= self.threshold:
                self.keypoint_list[idx].visibility_checkbox.setChecked(True)
            else:
                self.keypoint_list[idx].visibility_checkbox.setChecked(False)
            self.keypoint_list[idx].visibility_checkbox.blockSignals(False)
            self.keypoint_list[idx].first_click = True
        self.behaviour_button_group.blockSignals(True)
        for i, btn in enumerate(self.behaviour_button_group.buttons()):
            if self.ui.overwrite_btn.isChecked():
                self.set_behaviour(i, btn.isChecked())
            elif self.config.behaviours[i] in self.video_player.data_point.behaviour:
                btn.setChecked(True)
                self.set_behaviour(i, True)
            else:
                btn.setChecked(False)
                self.set_behaviour(i, False)
        self.behaviour_button_group.blockSignals(False)
        self.interp_update_candidates()

    def modify_selected_keypoint(self, point):
        name = self.current_keypoint.name
        if self.current_keypoint.visibility_checkbox.isChecked() or self.current_keypoint.first_click:
            self.current_keypoint.first_click = False
            self.visibility_button_group.blockSignals(True)
            self.current_keypoint.visibility_checkbox.setChecked(True)
            self.visibility_button_group.blockSignals(False)
            self.video_player.data_point[name][:2] = point.x(), point.y()
            self.video_player.data_point[name].likelihood = 1.0
            self.video_player.data_store.set_part(self.frame_number, self.video_player.data_point[name])
            self.draw_markers()

    def set_keypoint_likelihood(self, id, state):
        keypoint = self.keypoint_list[id] if id >= 0 else self.current_keypoint
        name = keypoint.name
        if state:
            keypoint.annotation_radio_button.setChecked(True)
        self.video_player.data_point[name].likelihood = 0.0 if not state else self.threshold
        self.video_player.data_store.set_part(self.frame_number, self.video_player.data_point[name])
        self.draw_markers()

    def draw_markers(self):
        self.video_player.data_point_drawer.update_skeleton(self.video_player.data_point)
        self.update_annotation_ui(self.video_player.data_point)
        # self.image_viewer.draw_skeleton(self.video_player.data_point_drawer.itemGroup)
        self.image_viewer.draw_skeleton(self.video_player.data_point_drawer)

    def set_behaviour(self, id, checked):
        if checked:
            if self.config.behaviours[id] not in self.video_player.data_point.behaviour:
                self.video_player.data_point.behaviour.append(self.config.behaviours[id])
        else:
            if self.config.behaviours[id] in self.video_player.data_point.behaviour:
                self.video_player.data_point.behaviour.remove(self.config.behaviours[id])
        self.video_player.data_store.set_behaviour(self.frame_number, self.video_player.data_point.behaviour)

    def interp_update_candidates(self):
        for idx, name in enumerate(self.config.body_parts):
            if name in self.interp_initial_index_set and self.keypoint_list[idx].visibility_checkbox.isChecked():
                self.interp_button_group.button(idx).setChecked(True)
            else:
                self.interp_button_group.button(idx).setChecked(False)

    def interp_set_candidate(self, id, state):
        name = self.config.body_parts[id]
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
            if state and name in self.interp_initial_index_set and self.keypoint_list[
                id].visibility_checkbox.isChecked():
                self.interp_candidate_set.add(name)
            else:
                if name in self.interp_candidate_set:
                    self.interp_candidate_set.remove(name)
                self.interp_button_group.button(id).setChecked(False)
        self.interp_button_group.blockSignals(False)

    def interp_update_initial_index_set(self, event=None):
        self.interp_initial_index_set = set([self.keypoint_list[i].name for i in range(len(self.keypoint_list)) if
                                             self.keypoint_list[i].visibility_checkbox.isChecked() and
                                             self.keypoint_list[i].name in self.interp_candidate_set])
        self.interp_initial_index_frame = self.frame_number
        self.ui.interpInitialIndex.setText(str(self.frame_number))

    def interp_select_all(self, event):
        for btn in self.interp_button_group.buttons():
            btn.setChecked(True)

    def interp_clear_all(self, event):
        for btn in self.interp_button_group.buttons():
            btn.setChecked(False)

    def interpolate(self, event):
        total_frames = self.frame_number - self.interp_initial_index_frame
        if total_frames > 10:
            test = QMessageBox.question(self, "Interpolation Warning",
                                        f"Interpolating over {total_frames} frames; Are you sure?", QMessageBox.Yes,
                                        QMessageBox.No)
            if test == QMessageBox.No:
                return
        if total_frames < 2:
            return
        for name in self.interp_candidate_set:
            part_initial = self.video_player.data_store.get_part(self.interp_initial_index_frame, name)
            part_current = self.video_player.data_store.get_part(self.frame_number, name)
            additive_coordinates = (part_current - part_initial) / total_frames
            for i in range(self.interp_initial_index_frame, self.frame_number):
                self.video_player.data_store.set_part(i, part_initial)
                part_initial += additive_coordinates

    def seek(self, frame_number):
        if self.frame_number != frame_number and frame_number < self.video_player.get_number_of_frames():
            self.video_player.seek(max(0, frame_number))
            self.render_next_frame()
        else:
            self.render_next_frame(True)

    def reset_view(self, event=None):
        self.image_viewer.fitInView()

    def play_video(self, event):
        if self.is_video_playing:
            self.fps_timer.stop()
            self.timer.stop()
            self.is_video_playing = False
            self.ui.nextFrameButton.setEnabled(True)
            self.ui.speedFactor.setEnabled(True)
            self.ui.prevFrameButton.setEnabled(True)
            self.ui.playPauseButton.setText('Play')

        else:
            factor = self.ui.speedFactor.value()
            self.timer.start(int((1000 / self.video_player.video_reader.fps) / factor))
            self.fps_timer.start(1000)
            self.ui.playPauseButton.setText('Pause')
            self.is_video_playing = True
            self.ui.speedFactor.setEnabled(False)
            self.ui.nextFrameButton.setEnabled(False)
            self.ui.prevFrameButton.setEnabled(False)
