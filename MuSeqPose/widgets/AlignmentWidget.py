from PySide2.QtCore import QFile
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QDialog, QMessageBox

from MuSeqPose import get_resource
from MuSeqPose.ui_Skeleton import Marker
from MuSeqPose.utils.session_manager import SessionManager
from MuSeqPose.utils.ui_generators import generate_checkboxes
from MuSeqPose.widgets.ImageViewer import AnnotationImageViewer
from cvkit.pose_estimation.reconstruction.EasyWand_tools import update_alignment_matrices


class AlignmentDialog(QDialog):
    COLORS = [
        [0, 170, 0],
        [0, 170, 170],
        [170, 0, 0]
    ]
    KEYS = ['origin', 'x_max', 'y_max']

    def __init__(self, parent, session_manager: SessionManager,target_views=None):
        super(AlignmentDialog, self).__init__(parent)
        self.frame_number = 0
        self.config = session_manager.config
        self.session_manager = session_manager
        file = QFile(get_resource('AlignmentDialog.ui'))
        file.open(QFile.ReadOnly)
        self.ui = QUiLoader().load(file)
        self.radio_map = {0: self.ui.origin, 1: self.ui.x_axis, 2: self.ui.y_axis}
        self.markers = {}
        self.views = []
        self.widgets = []
        self.ui.clear_btn.clicked.connect(self.clear_data)
        self.ui.exit_btn.clicked.connect(self.close)
        self.max_frames = 0
        max_init = False
        if session_manager.config.x_len>0:
            self.ui.x_len_edit.setText(str(session_manager.config.x_len))
        if session_manager.config.y_len>0:
            self.ui.y_len_edit.setText(str(session_manager.config.y_len))
        if target_views is None:
            target_views = self.config.views
        self.checkboxes = generate_checkboxes(target_views,True)
        for index, view in enumerate(target_views):
            if view not in self.config.annotation_views:
                continue
            self.ui.select_views.layout().addWidget(self.checkboxes[index])
            widget = AnnotationImageViewer()
            widget.draw_frame(session_manager.session_video_readers[view].random_access_image(self.frame_number))
            if not max_init:
                self.max_frames = len(session_manager.session_video_readers[view])
                max_init = True
            else:
                self.max_frames = min(self.max_frames, len(session_manager.session_video_readers[view]))
            self.markers[view] = []
            self.views.append(view)
            for i in range(3):
                x, y = self.config.views[view].axes.get(self.KEYS[i], [-4, -4])
                self.markers[view].append(Marker(i, 0, 0, 4, 4, color=self.COLORS[i]))
                self.markers[view][-1].setVisible(True)
                widget.scene.addItem(self.markers[view][-1])
                self.markers[view][-1].setX(x - 2)
                self.markers[view][-1].setY(y - 2)
            widget.select_keypoint.connect(self.change_keypoint)
            widget.modify_keypoint.connect(self.annotate)
            self.ui.view_container.addTab(widget, view)
            self.widgets.append(widget)
            # widget.fitInView()
        self.setLayout(self.ui.layout())
        self.ui.frame_slider.setMinimum(0)
        self.ui.frame_slider.setMaximum(self.max_frames)
        self.ui.frame_slider.valueChanged.connect(self.change_frame)
        self.ui.reset_btn.clicked.connect(self.reset_view)
        self.ui.align_btn.clicked.connect(self.align_axes)
        self.show()

    def align_axes(self,event):
        alignment_source = [checkbox.text() for checkbox in self.checkboxes if checkbox.isChecked()]
        try:
            self.config.x_len = float(self.ui.x_len_edit.text())
            self.config.y_len = float(self.ui.y_len_edit.text())
        except:
            self.config.x_len = 0
            self.config.y_len = 0
        if len(alignment_source) < 2:
            QMessageBox.warning(self, "Error", "Need at least 2 views for alignment")
            return
        ret = update_alignment_matrices(self.config, alignment_source)
        if ret:
            QMessageBox.information(self, "Success", f"Alignment matrices generated\nComputed Scale:{round(self.config.computed_scale,2)}")
        else:
            QMessageBox.warning(self, "Error", "Error while generating alignment matrices")
    def reset_view(self,event):
        index = self.ui.view_container.currentIndex()
        self.widgets[index].fitInView()

    def annotate(self, pos):
        index = self.ui.view_container.currentIndex()
        selected = [k for k in self.radio_map if self.radio_map[k].isChecked()][0]
        marker = self.markers[self.views[index]][selected]
        marker.setX(pos.x() - 2)
        marker.setY(pos.y() - 2)
        marker.update()
        self.config.views[self.views[index]].axes[self.KEYS[selected]] = [int(pos.x()), int(pos.y())]

    def change_keypoint(self, pos, _):
        self.radio_map[pos].setChecked(True)

    def clear_data(self, event=None):
        index = self.ui.view_container.currentIndex()
        self.config.views[self.views[index]].axes = {}

    def change_frame(self, frame_number):
        self.frame_number = min(max(frame_number, 0), self.max_frames)
        for i, view in enumerate(self.views):
            self.widgets[i].draw_frame(
                self.session_manager.session_video_readers[view].random_access_image(self.frame_number))
