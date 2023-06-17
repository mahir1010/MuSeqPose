import inspect
from copy import deepcopy

from PySide2.QtCore import QFile
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QDialog

from MuSeqPose import get_resource
from MuSeqPose.utils.ui_generators import *


def generate_input_ui(session_manager: SessionManager, metadata: ProcessorMetaData):
    ui_class = None
    ui_class = IntField if not ui_class and metadata.param_type == ProcessorMetaData.INT else ui_class
    ui_class = FloatField if not ui_class and metadata.param_type == ProcessorMetaData.FLOAT else ui_class
    ui_class = BooleanField if not ui_class and metadata.param_type == ProcessorMetaData.BOOLEAN else ui_class
    ui_class = TextField if not ui_class and metadata.param_type == ProcessorMetaData.TEXT else ui_class
    ui_class = BodyPartField if not ui_class and metadata.param_type == ProcessorMetaData.BODY_PART else ui_class
    ui_class = RangeField if not ui_class and metadata.param_type == ProcessorMetaData.FIXED_RANGE else ui_class
    ui_class = NumpyField if not ui_class and metadata.param_type == ProcessorMetaData.NUMPY_ARRAY else ui_class
    ui_class = DatastoreField if not ui_class and metadata.param_type == ProcessorMetaData.DATA_STORE else ui_class
    ui_class = ViewsField if not ui_class and metadata.param_type == ProcessorMetaData.VIEWS else ui_class
    ui_class = DirPathField if not ui_class and metadata.param_type == ProcessorMetaData.DIR_PATH else ui_class
    ui_class = FilePathField if not ui_class and metadata.param_type == ProcessorMetaData.FILE_PATH else ui_class
    if ui_class:
        return ui_class(metadata, session_manager)


class ProcessorConfigurator(QDialog):
    invalid_data_signal = Signal(bool)

    def __init__(self, parent, session_manager: SessionManager,
                 target_processor, is_widget=False):
        super().__init__(parent)
        self.target_processor = target_processor
        self.config = session_manager.config
        self.session_manager = session_manager
        self.is_widget = is_widget
        file = QFile(get_resource('ProcessorConfigurator.ui'))
        file.open(QFile.ReadOnly)
        self.ui = QUiLoader().load(file)

        if is_widget:
            self.setWindowFlag(Qt.Widget)
        else:
            self.setWindowTitle("Processor Configurator")
            self.setMinimumSize(400, 300)
            self.setMaximumHeight(400)
            self.setMaximumWidth(500)
            layout = QHBoxLayout()
            accept_btn = QPushButton("Confirm")
            accept_btn.clicked.connect(lambda x: self.accepted.emit())
            layout.addWidget(accept_btn)
            self.ui.base_layout.addLayout(layout)

        self.ui.processor_title.setText(target_processor.PROCESSOR_NAME)
        self.ui_map = {}
        for key, value in self.target_processor.META_DATA.items():
            if value.param_type != ProcessorMetaData.GLOBAL_CONFIG and value.param_type != ProcessorMetaData.FILE_MAP:
                input_ui = generate_input_ui(self.session_manager, value)
                self.ui_map[key] = input_ui
                self.ui.container.addWidget(input_ui)
        self.set_ui_data()
        self.ui.container.addStretch(1)
        self.setLayout(self.ui.layout())

    def get_instance(self):
        is_valid, error = self.verify_data()
        if not is_valid:
            QMessageBox.warning(self, 'Error', error)
            return None
        if inspect.isclass(self.target_processor):
            attrs = {}
            for attr, value in self.target_processor.META_DATA.items():
                if value.param_type == ProcessorMetaData.GLOBAL_CONFIG:
                    attrs[attr] = self.config
                elif value.param_type == ProcessorMetaData.FILE_MAP:
                    attrs[attr] = self.session_manager.session_data_readers
                else:
                    attrs[attr] = self.ui_map[attr].get_output()
            return self.target_processor(**attrs)
        else:
            copy = deepcopy(self.target_processor)
            for attr, value in self.target_processor.META_DATA.items():
                if value.param_type == ProcessorMetaData.GLOBAL_CONFIG:
                    setattr(copy, attr, self.config)
                elif value.param_type == ProcessorMetaData.FILE_MAP:
                    setattr(copy, attr, self.session_manager.session_data_readers)
                else:
                    setattr(copy, attr, self.ui_map[attr].get_output())
            return copy

    def verify_data(self):
        for input_ui in self.ui_map.values():
            if not input_ui.is_valid():
                return False, f"{input_ui.metadata.display_name} Data Invalid!"
        return True, ''

    def __eq__(self, other):
        if type(other) == type(self):
            for key in self.ui_map:
                if self.ui_map[key].get_output() != other.ui_map[key].get_output():
                    return False
            return True
        return False

    def showEvent(self, event):
        if not self.is_widget:
            for input_ui in self.ui_map.values():
                if not input_ui.is_valid():
                    input_ui.set_stylesheet(input_ui.ERROR_CSS)
                else:
                    input_ui.set_stylesheet()
        else:
            for input_ui in self.ui_map.values():
                input_ui.reset_ui()
        super().showEvent(event)

    def set_ui_data(self):
        if not inspect.isclass(self.target_processor):
            for attr, value in self.target_processor.META_DATA.items():
                if value.param_type not in [ProcessorMetaData.GLOBAL_CONFIG, ProcessorMetaData.FILE_MAP]:
                    data = self.target_processor.__getattribute__(attr)
                    if data is not None:
                        self.ui_map[attr].set_data(data)
