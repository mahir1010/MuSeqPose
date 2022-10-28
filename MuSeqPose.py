import os
import sys
from random import randint

from PySide2.QtCore import QFile, QCoreApplication, Qt
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QApplication, QFileDialog

import OptiPose.DLT as DLT
from OptiPose import save_config
from config import MuSeqPoseConfig
from player_interface import VideoPlayer
from player_interface.PlotPlayer import ReconstructionPlayer, LinePlotPlayer
from utils.SessionFileManager import SessionFileManager
from widgets.AnnotationWidget import AnnotationWidget
from widgets.OptiPosePipeline import OptiPoseWidget
from widgets.PlayControlWidget import PlayControlWidget
from widgets.SyncViewWidget import SyncViewWidget


class MuSeqAnnotator(QApplication):
    def __init__(self, argv):
        super(MuSeqAnnotator, self).__init__(argv)
        ui_file = QFile(os.path.join('Resources', 'main.ui'))
        ui_file.open(QFile.ReadOnly)
        loader = QUiLoader()
        self.ui = loader.load(ui_file)
        self.ui.show()
        self.ui.actionLoad.triggered.connect(self.open_project)
        self.ui.setWindowTitle('MuSeq Pose Kit')
        self.ui.actionSave.triggered.connect(self.save_files)
        self.views = []
        self.file_name = None
        self.config = None
        self.current_view_index = 0
        self.players = {}
        self.ui.actionSave_Config.triggered.connect(save_config)
        self.session_manager = None
        self.global_frame_number = 0

    def reset_app(self):
        for idx, view in enumerate(self.views):
            self.ui.viewTabWidget.removeTab(idx)
            view.destroy()
        for player in self.players.values():
            player.release()
            del player
        self.players.clear()
        self.views.clear()
        self.file_name = None
        self.config = None
        self.current_view_index = 0
        self.players = {}
        self.session_manager = None
        self.global_frame_number = 0

    def save_files(self, event=None):
        for player in self.players.values():
            player.data_store.save_file()

    def open_project(self, event=None):
        file_name = QFileDialog.getOpenFileName(self.ui, "Open Yaml File", None, "config (*.yaml *.yml)")[0]
        if file_name:
            self.reset_app()
            self.file_name = file_name
            self.load_data()

    def load_data(self):
        self.config = MuSeqPoseConfig(self.file_name)
        self.session_manager = SessionFileManager(self.config)
        self.ui.setWindowTitle(f'MuSeq Pose Kit : {self.config.project_name}')
        while len(self.config.colors) < self.config.num_parts:
            self.config.colors.append([randint(0, 255) for i in range(3)])
        for view in self.config.annotation_views:
            video_player = VideoPlayer(self.config, self.config.annotation_views[view])
            self.session_manager.register_data_reader(view, video_player.data_store)
            self.session_manager.register_video_reader(view, video_player.video_reader)
            self.players[view] = video_player
            ui_file = os.path.join('Resources', 'AnnotationWidget.ui')
            play_controller = AnnotationWidget(view, self.config, ui_file, video_player,
                                               threshold=self.config.threshold)
            play_controller.update_status.connect(self.update_status_bar)
            self.views.append(play_controller)
            play_controller.reproject.connect(self.reproject)
            self.ui.viewTabWidget.addTab(play_controller, view)
        for plot in self.config.plots:
            if self.config.plots[plot].type == "Reconstruction":
                self.players[plot] = ReconstructionPlayer(self.config, self.config.plots[plot])
            else:
                self.players[plot] = LinePlotPlayer(self.config, self.config.plots[plot])
        if len(self.config.sync_views)>0:
            sync_controller = SyncViewWidget(self.config, os.path.join('Resources', 'SyncViewPlayer.ui'),
                                             [player for view, player in self.players.items() if
                                              view in self.config.sync_views])
            sync_controller.update_status.connect(self.update_status_bar)
            self.views.append(sync_controller)
            self.ui.viewTabWidget.addTab(sync_controller, "sync")
        widget = OptiPoseWidget(self.config, self.session_manager)
        self.views.append(widget)
        self.ui.viewTabWidget.addTab(widget, "OptiPose")
        self.current_view_index = 0
        self.ui.viewTabWidget.currentChanged.connect(self.change_view)

    def change_view(self, i):
        if self.current_view_index != i:
            current_view = self.views[self.current_view_index]
            new_view = self.views[i]
            self.current_view_index = i
            if isinstance(current_view, PlayControlWidget):
                if current_view.is_video_playing:
                    current_view.ui.playPauseButton.clicked.emit()
                self.global_frame_number = current_view.frame_number

            if isinstance(new_view, PlayControlWidget):
                new_view.seek_ui_input(self.global_frame_number)
                new_view.update_frame_number()

    def reproject(self, view_name, frame_number, view_candidates, part_candidates):
        list_of_views = list(self.config.views.keys())
        view_indices = [list_of_views.index(view) for view in view_candidates]
        dlt_coefficients = self.dlt_coefficients[view_indices, :]
        num_views = len(view_candidates)
        skeletons = [self.views[idx].video_player.data_store.get_skeleton(frame_number) for idx in view_indices]
        for part in part_candidates:
            _2d_parts = [sk[part] for sk in skeletons]
            _3d_part = DLT.DLTrecon(3, num_views, dlt_coefficients, _2d_parts)
            reprojected_parts = DLT.DLTdecon(self.dlt_coefficients, _3d_part, 3, self.dlt_coefficients.shape[0])
            for i in range(len(list_of_views)):
                original_part = self.views[i].video_player.data_store.get_marker(frame_number, part)
                original_part[:2] = reprojected_parts[0][i * 2:i * 2 + 2]
                original_part.likelihood = self.config.threshold
                self.views[i].video_player.data_point[part] = original_part
                self.views[i].video_player.data_store.set_marker(frame_number, original_part)
        self.views[list_of_views.index(view_name)].render_next_frame(redraw=True)
        pass

    def update_status_bar(self, status):
        self.ui.status.setText(f'<html><p style="font-weight:500">{status}</p></html>')


if __name__ == "__main__":
    QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    app = MuSeqAnnotator(sys.argv)
    sys.exit(app.exec_())
