import os

from PySide2.QtCore import QFile, Qt, QRegExp
from PySide2.QtGui import QRegExpValidator
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QCheckBox, QWidget, QHBoxLayout, QMessageBox

import OptiPose.pipeline
from OptiPose.post_processor_interface import ClusterAnalysisProcess
from OptiPose.post_processor_interface.FileLoadProcessor import FileLoadProcess
from OptiPose.post_processor_interface.FileSaveProcessor import FileSaveProcess
from OptiPose.post_processor_interface.KalmanFilterProcessor import KalmanFilterProcess
from OptiPose.post_processor_interface.LinearInterpolationProcessor import LinearInterpolationProcess
from OptiPose.post_processor_interface.MedianDistanceFilterProcessor import MedianDistanceFilterProcess
from OptiPose.post_processor_interface.MovingAverageProcessor import MovingAverageProcess
from OptiPose.post_processor_interface.ReconstructionProcessor import ReconstructionProcess
from config import MuSeqPoseConfig
from utils.PostProcessorThread import Thread
from utils.SessionFileLoader import SessionFileLoader
from utils.SessionFileManager import SessionFileManager
from widgets.AlignmentWidget import AlignmentDialog
from widgets.HeadingAnalysisWidget import HeadingAnalysisWidget
from widgets.OptiPoseCard import OptiPoseCard


class OptiPoseWidget(QWidget):
    def __init__(self, config: MuSeqPoseConfig, session_manager: SessionFileManager):
        super(OptiPoseWidget, self).__init__(parent=None)
        file = QFile('Resources/OptiPosePipeline.ui')
        file.open(QFile.ReadOnly)
        self.ui = QUiLoader().load(file)
        self.config = config
        self.session_manager = session_manager
        self.view_checkboxes = []
        self.alignment_view_checkbox = []
        for view in self.config.views:
            alignment_checkbox = QCheckBox(view)
            alignment_checkbox.setChecked(True)
            self.alignment_view_checkbox.append(alignment_checkbox)
            self.ui.alignment_view_list.addWidget(alignment_checkbox)

            view_checkbox = QCheckBox(view)
            view_checkbox.setChecked(True)
            self.view_checkboxes.append(view_checkbox)
            self.ui.view_selection_list.addWidget(view_checkbox)

        self.ui.file_loader_container.setMargin(0)
        self.file_loader = SessionFileLoader(None, self.config, False)
        self.ui.file_loader_container.addWidget(self.file_loader)
        self.ui.recon_algorithm.addItems(['default', 'auto_subset'])
        self.ui.recon_algorithm.setCurrentIndex(1)
        layout = QHBoxLayout()
        layout.setMargin(0)
        layout.addWidget(self.ui)
        self.setLayout(layout)
        self.ui.axes_annotation_btn.clicked.connect(lambda x: AlignmentDialog(self, config, session_manager))
        self.ui.alignment_matrix_btn.clicked.connect(self.update_alignment_data)
        self.ui.recon_scale.setText(str(self.config.scale))
        self.ui.recon_threshold.setValue(self.config.threshold)
        self.ui.median_threshold.setValue(self.config.threshold)
        self.ui.interp_threshold.setValue(self.config.threshold)
        self.ui.kalman_threshold.setValue(self.config.threshold)
        self.ui.moving_avg_threshold.setValue(self.config.threshold)
        self.ui.add_input_file.clicked.connect(self.insert_input_file)
        self.ui.pipeline_container.setAlignment(Qt.AlignTop)
        self.operation_list = []
        self.operation_index = 0
        self.ui.execute_btn.clicked.connect(self.start_pipeline)
        self.ui.output_file_name.setValidator(QRegExpValidator(QRegExp("[a-zA-Z0-9]{1}[a-zA-Z0-9_]*")))
        self.ui.add_median_btn.clicked.connect(self.insert_median_distance_culling_process)
        self.ui.add_interp_btn.clicked.connect(self.insert_interpolation_process)
        self.ui.add_kalman_btn.clicked.connect(self.insert_kalman_filter_process)
        self.ui.add_moving_avg.clicked.connect(self.insert_moving_avg_process)
        self.ui.analysis_widget.addTab(HeadingAnalysisWidget(config).ui,"Heading")
        self.show()

    def start_pipeline(self, event=None):
        if not self.ui.output_file_name.hasAcceptableInput():
            QMessageBox.warning(self.ui, 'Error', 'Invalid Output File Name')
            return
        output_file = self.ui.output_file_name.text()
        path = f'{os.path.join(self.config.output_folder, output_file)}.csv'
        if os.path.exists(path):
            btn = QMessageBox.information(self.ui, "File Exists!", "File Exists; Do you want to overwrite?",
                                          QMessageBox.Yes, QMessageBox.No)
            if btn == QMessageBox.No:
                return
        post_processor = FileSaveProcess(path)
        self.generate_process_card([post_processor])
        self.execute_pipeline()

    def update_alignment_data(self, event=None):
        alignment_source = [checkbox.text() for checkbox in self.alignment_view_checkbox if checkbox.isChecked()]
        if len(alignment_source) < 2:
            QMessageBox.warning(self.ui, "Error", "Need at least 2 views for alignment")
            return
        ret = OptiPose.pipeline.update_alignment_matrices(self.config, alignment_source)
        if ret:
            QMessageBox.information(self.ui, "Success", "Alignment matrices generated")
        else:
            QMessageBox.warning(self.ui, "Error", "Error while generating alignment matrices")

    def insert_input_file(self, event=None):
        if len(self.operation_list) != 0:
            QMessageBox.warning(self.ui, "Error", "File can only be inserted at the top")
            return
        if self.ui.custom_file_btn.isChecked():
            if self.file_loader.file is None:
                QMessageBox.warning(self.ui, "Error", 'Custom File not Loaded.\n' +
                                    'You can select reconstruction option to generate new file')
                return
            post_processor = FileLoadProcess(self.file_loader.file)

        else:
            candidate_views = [cb.text() for cb in self.view_checkboxes if cb.isChecked()]
            if len(candidate_views) < 2:
                QMessageBox.warning(self.ui, "Error", "Need at least 2 views for reconstruction")
                return
            source_views = []
            data_readers = []
            for candidate in candidate_views:
                data_readers.append(self.session_manager.session_data_readers[candidate])
                source_views.append(candidate)
            post_processor = ReconstructionProcess(self.config, source_views, data_readers,
                                                   self.ui.recon_threshold.value(),
                                                   scale=float(self.ui.recon_scale.text()),
                                                   reconstruction_algorithm=self.ui.recon_algorithm.currentText())
            file_name = f"{self.ui.recon_file_prefix.text()}_{self.ui.recon_threshold.value()}_{'_'.join([view for view in source_views]) if self.ui.recon_algorithm.currentText() != 'auto_subset' else 'auto_subset'}"
            self.ui.output_file_name.setText(file_name)
        self.generate_process_card([post_processor])

    def execute_pipeline(self):
        args = None
        if self.operation_index > 0:
            if self.operation_list[self.operation_index - 1].exception_occurred:
                QMessageBox.warning(self.ui, "Error", self.operation_list[self.operation_index - 1].exception_message)
                # TODO Clear Pipeline
                return
            args = self.operation_list[self.operation_index - 1].get_output()
        if self.operation_index >= len(self.operation_list):
            return
        self.operation_list[self.operation_index].set_args(args)
        self.operation_list[self.operation_index].execute()
        self.operation_index += 1

    def insert_median_distance_culling_process(self, event):
        try:
            distance_threshold = float(self.ui.median_distance_threshold.text())
        except:
            QMessageBox.warning(self.ui, "Error", "Invalid median distance")
            return
        threshold = self.ui.median_threshold.value()
        post_processor = MedianDistanceFilterProcess(threshold, distance_threshold)
        self.generate_process_card([post_processor])

    def insert_interpolation_process(self, event):
        try:
            max_cluster_size = float(self.ui.interp_max_cluster.text())
            if max_cluster_size > 10:
                # TODO set project level framerate key in yaml
                btn = QMessageBox.warning(self.ui, "Warning!", "Interpolating over large frames is not advised.\n" +
                                          "Are you sure you want to continue?", QMessageBox.Yes, QMessageBox.No)
                if btn == QMessageBox.No:
                    return
        except:
            QMessageBox.warning(self.ui, "Error", "Invalid cluster size")
            return
        threshold = self.ui.interp_threshold.value()
        cluster_post_processor = ClusterAnalysisProcess(threshold)
        self.generate_process_card([cluster_post_processor])
        post_processors = []
        for column in self.config.body_parts:
            post_processors.append(LinearInterpolationProcess(column, threshold, max_cluster_size))
        self.generate_process_card(post_processors)

    def insert_moving_avg_process(self, event):
        try:
            window_size = float(self.ui.moving_avg_window.text())
            if window_size > 10:
                # TODO set project level framerate key in yaml
                btn = QMessageBox.warning(self.ui, "Warning!", "Smoothing over large window is not advised.\n" +
                                          "Are you sure you want to continue?", QMessageBox.Yes, QMessageBox.No)
                if btn == QMessageBox.No:
                    return
        except:
            QMessageBox.warning(self.ui, "Error", "Invalid Window size")
            return
        threshold = self.ui.moving_avg_threshold.value()
        post_processors = []
        for column in self.config.body_parts:
            post_processors.append(MovingAverageProcess(column, window_size, threshold))
        self.generate_process_card(post_processors)

    def insert_kalman_filter_process(self, event):
        threshold = self.ui.kalman_threshold.value()
        skip_invalid = self.ui.kalman_skip_invalids.isChecked()
        post_processors = []
        for column in self.config.body_parts:
            post_processors.append(
                KalmanFilterProcess(column, self.config.framerate, skip_invalid, threshold))
        self.generate_process_card(post_processors)

    def generate_process_card(self, post_processors: list):
        threads = []
        for idx, post_processor in enumerate(post_processors):
            threads.append(Thread(idx, post_processor))
        card = OptiPoseCard(threads)
        card.execution_completed.connect(self.execute_pipeline)
        self.operation_list.append(card)
        self.ui.pipeline_container.insertWidget(len(self.operation_list), card)