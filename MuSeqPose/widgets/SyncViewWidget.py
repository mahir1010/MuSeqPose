import math

from PySide2.QtCore import QTimer
from PySide2.QtWidgets import QVBoxLayout

from MuSeqPose.player_interface.PlotPlayer import PlotPlayer
from MuSeqPose.utils.session_manager import SessionManager
from MuSeqPose.widgets.ImageViewer import ImageViewer
from MuSeqPose.widgets.PlayControlWidget import PlayControlWidget


class SyncViewWidget(PlayControlWidget):

    def update_frame_number(self):
        pass

    def render_next_frame(self, event=None):
        for player, viewer in zip(self.video_players, self.image_viewers):
            # if viewer is None:
            player.render_next_frame(viewer)
        self.frame_number = self.video_players[-1].frame_number
        self.ui.seekBar.blockSignals(True)
        self.ui.seekBar.setValue(self.frame_number)
        self.ui.seekBar.blockSignals(False)
        self.ui.frameNumber.setText(
            f'<html style="font-weight:600">{self.frame_number}/{self.video_players[0].get_number_of_frames()}</html>')

    def reset_view(self, event=None):
        for viewer in self.image_viewers:
            if viewer is not None:
                viewer.fitInView()

    def seek(self, frame_number):
        if self.frame_number != frame_number and frame_number < self.video_players[0].get_number_of_frames():
            for player in self.video_players:
                player.seek(max(0, frame_number))
            self.render_next_frame()

    def play_video(self, event):
        if self.is_video_playing:
            self.fps_timer.stop()
            self.timer.stop()
            self.is_video_playing = False
            self.ui.nextFrameButton.setEnabled(True)
            self.ui.prevFrameButton.setEnabled(True)
            self.ui.playPauseButton.setText('Play')
        else:
            self.render_next_frame()
            self.fps_timer.start(1000)
            self.timer.start(int(1000 / self.video_players[0].video_reader.fps))
            self.ui.playPauseButton.setText('Pause')
            self.is_video_playing = True
            self.ui.nextFrameButton.setEnabled(False)
            self.ui.prevFrameButton.setEnabled(False)

    def __init__(self, session_manager: SessionManager, ui_file, video_players, threshold=0.6, parent=None):
        super(SyncViewWidget, self).__init__(session_manager, ui_file, threshold, parent)
        self.video_players = video_players
        self.image_viewers = []
        self.frame_number = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.render_next_frame)
        self.is_video_playing = False
        if len(video_players) > 2:
            rows = math.ceil(len(video_players) / 3)
            cols = 3
        else:
            rows = 1
            cols = len(video_players)
        idx = 0
        for r in range(rows):
            self.ui.gridlayout.setRowStretch(r, 1)
            for c in range(cols):
                self.ui.gridlayout.setColumnStretch(c, 1)
                if idx >= len(video_players):
                    break
                if not isinstance(video_players[idx], (PlotPlayer,)):
                    self.image_viewers.append(ImageViewer())
                    self.ui.gridlayout.addWidget(self.image_viewers[idx], r, c)
                else:
                    self.image_viewers.append(None)
                    self.ui.gridlayout.addWidget(self.video_players[idx].get_widget(), r, c)
                idx += 1
        layout = QVBoxLayout()
        layout.addWidget(self.ui)
        self.setLayout(layout)
        self.ui.seekBar.setMaximum(self.video_players[0].get_number_of_frames())
        self.ui.seekBar.valueChanged.connect(lambda: self.seek_ui_input(self.ui.seekBar.value()))
