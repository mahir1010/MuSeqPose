import json
import os
import pathlib
import shutil
from copy import copy
from os.path import exists, join

from PySide2.QtCore import QFile, QSortFilterProxyModel, QRegExp
from PySide2.QtGui import QStandardItem, QStandardItemModel, QRegExpValidator, QIcon
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QWidget, QMessageBox, QFileDialog

from MuSeqPose import get_resource
from MuSeqPose.utils.pipeline_execution_manager import PipelineExecutionManager, verify_import
from MuSeqPose.utils.session_manager import SessionManager
from MuSeqPose.widgets.OperationCardWidget import OperationCard
from MuSeqPose.widgets.ProcessorCardWidget import ProcessorConfigurator
from cvkit import discovered_pe_processors, pose_estimation_plugin


class ProcessorItem(QStandardItem):
    def __init__(self, processor_name, processor_id, widget_id):
        super().__init__(processor_name)
        self.processor_id = processor_id
        self.widget_id = widget_id


class PipelineWidget(QWidget):

    def __init__(self, session_manager: SessionManager):
        super(PipelineWidget, self).__init__(parent=None)
        file = QFile(get_resource('PipelineWidget.ui'))
        file.open(QFile.ReadOnly)
        self.config = session_manager.config
        self.session_manager = session_manager
        self.ui = QUiLoader().load(file)

        source_model = QStandardItemModel()
        source_model.setHorizontalHeaderLabels(['Processor', 'Summary'])
        # Populate Data Model from discovered processors
        data_model = {}
        for plugin in pose_estimation_plugin:
            data_model[plugin] = {}
        for processor_id, processor in discovered_pe_processors.items():
            data_model[processor.plugin_name].setdefault(processor.processor_type, []).append(processor_id)
        # Generate Tree Items from the Data Model
        idx = 0
        for plugin in data_model:
            base_row = QStandardItem(plugin)
            base_row.setEditable(False)
            for type in data_model[plugin]:
                type_row = QStandardItem(type)
                type_row.setEditable(False)
                base_row.appendRow(type_row)
                for processor in data_model[plugin][type]:
                    processor_row = ProcessorItem(discovered_pe_processors[processor].processor_class.PROCESSOR_NAME,
                                                  processor, idx)
                    idx += 1
                    self.ui.stacked_widget.addWidget(ProcessorConfigurator(None, session_manager,
                                                                           discovered_pe_processors[
                                                                               processor].processor_class, True))
                    processor_row.setEditable(False)
                    type_row.appendRow([processor_row, QStandardItem(
                        discovered_pe_processors[processor].processor_class.PROCESSOR_SUMMARY)])
            source_model.appendRow(base_row)
        self.ui.stacked_widget.setCurrentIndex(0)

        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(source_model)
        self.ui.treeview.setModel(self.proxy_model)
        self.ui.treeview.setColumnWidth(0, 300)
        self.ui.treeview.expandAll()
        self.ui.treeview.doubleClicked.connect(self.load_processor_widget)

        self.setLayout(self.ui.layout())
        self.pipeline_chain_layout = self.ui.pipeline_container.layout()
        self.ui.add_processor_btn.clicked.connect(self.register_processor)
        self.ui.pipeline_execute_btn.clicked.connect(self.execute_pipeline)
        self.pipeline_manager = PipelineExecutionManager(self.session_manager)
        self.ui.export_pipeline_btn.clicked.connect(self.export_pipeline)
        self.ui.pipeline_name_edit.setValidator(QRegExpValidator(QRegExp("[a-zA-Z0-9]{1}[a-zA-Z0-9_.]*")))
        icon = QIcon.fromTheme("document-new")
        self.ui.pipeline_cb.addItem("-- New Pipeline --")
        self.ui.pipeline_cb.setItemIcon(0, icon)
        self.ui.pipeline_cb.addItems(list(self.config.loaded_pipelines.keys()))
        self.ui.import_pipeline_btn.clicked.connect(self.import_pipeline)
        self.ui.pipeline_cb.currentTextChanged.connect(self.load_pipeline)

    def load_processor_widget(self, index):
        source_index = self.proxy_model.mapToSource(index)
        item = source_index.model().itemFromIndex(source_index)
        if isinstance(item, ProcessorItem):
            self.current_processor_id = item.processor_id
            self.ui.stacked_widget.setCurrentIndex(item.widget_id)

    def add_operation_card(self, card: OperationCard):
        card.delete_card.connect(self.remove_operation_card)
        self.pipeline_chain_layout.insertWidget(self.pipeline_chain_layout.count() - 2, card)

    def register_processor(self, event):
        current_widget = self.ui.stacked_widget.currentWidget()
        processor = current_widget.get_instance()
        if processor is not None:
            card = None
            if processor.DISTRIBUTED:
                btn = QMessageBox.question(self, "Distributed Processor", "Do you want to process all parts?")
                if btn == QMessageBox.Yes:
                    configurators = []
                    for i, part in enumerate(self.config.body_parts):
                        new_processor = copy(processor)
                        new_processor.target_column = part
                        configurators.append(
                            ProcessorConfigurator(self, self.session_manager, new_processor))
                    card = OperationCard(self.session_manager, configurators)
            if card is None:
                card = OperationCard(self.session_manager,
                                     [ProcessorConfigurator(self, self.session_manager, processor)])
            self.add_operation_card(card)
            self.pipeline_manager.add_processor(card)

    def remove_operation_card(self):
        card = self.sender()
        self.pipeline_manager.remove_processor(card)
        card.deleteLater()

    def execute_pipeline(self):
        self.pipeline_manager.reset_pipeline()
        if not self.pipeline_manager.start_execution():
            QMessageBox.warning(self, "Execution Failed",
                                "Error while verifying Processors.\nPlease check the pipeline.")
            return

    def export_pipeline(self):
        if not self.ui.pipeline_name_edit.hasAcceptableInput() or self.ui.pipeline_name_edit.text() == '':
            self.ui.pipeline_name_edit.setFocus()
            return
        pipeline_name = self.ui.pipeline_name_edit.text()
        path = os.path.join(self.config.pipeline_directory, f'{pipeline_name}.pipeline')
        if os.path.exists(path):
            btn = QMessageBox.information(self, "File Exists!", "Do you want to overwrite?",
                                          QMessageBox.Yes, QMessageBox.No)
            if btn == QMessageBox.No:
                return
        data_dict = self.pipeline_manager.export_pipeline()
        json.dump(data_dict, open(path, 'w'))
        QMessageBox.information(self, 'Success', 'File Exported Successfully!')

    def load_pipeline(self, pipeline_name):
        if pipeline_name in self.config.loaded_pipelines:
            new_pipeline = self.pipeline_manager.import_pipeline(self, self.config.loaded_pipelines[pipeline_name])
            if new_pipeline is not None:
                for card in new_pipeline:
                    self.add_operation_card(card)
        else:
            self.pipeline_manager.delete_pipeline()

    def import_pipeline(self):
        file_path = QFileDialog.getOpenFileName(self, f"Select Pipeline File",
                                                self.config.pipeline_directory, "*.pipeline")[0]
        if file_path:
            file_name = pathlib.Path(file_path).stem
            new_path = join(self.config.pipeline_directory, f'{file_name}.pipeline')
            try:
                pipeline_data = json.load(open(file_path, 'r'))
            except:
                QMessageBox.warning(self, 'Import Pipeline', 'Pipeline files require valid JSON format!')
                return
            if not verify_import(pipeline_data):
                QMessageBox.warning(self, 'Import Pipeline',
                                    'Invalid Pipeline data found.\nPlease ensure you have all required plugins installed.')
                return
            if exists(new_path):
                btn = QMessageBox.information(self, "Import Pipeline", "Do you want to overwrite?",
                                              QMessageBox.Yes, QMessageBox.No)
                if btn == QMessageBox.No:
                    return
            shutil.copy(file_path, new_path)
            self.config.loaded_pipelines[file_name] = pipeline_data
            QMessageBox.information(self, 'Import Pipeline', f'{file_name} imported successfully!')
            if self.ui.pipeline_cb.findText(file_name) < 0:
                self.ui.pipeline_cb.addItem(file_name)
