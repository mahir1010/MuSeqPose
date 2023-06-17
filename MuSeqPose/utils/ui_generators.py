import os

from PySide2.QtCore import QRegExp, Signal, Qt
from PySide2.QtGui import QIntValidator, QDoubleValidator, QRegExpValidator, QValidator
from PySide2.QtWidgets import QCheckBox, QRadioButton, QWidget, QLineEdit, QHBoxLayout, QLabel, QComboBox, \
    QDoubleSpinBox, QFileDialog, QPushButton, QMessageBox

from MuSeqPose.config import MuSeqPoseConfig
from MuSeqPose.utils.FlowLayout import FlowLayout
from MuSeqPose.utils.session_manager import SessionManager
from cvkit.pose_estimation.data_readers import datastore_readers, initialize_datastore_reader
from cvkit.pose_estimation.processors.processor_interface import ProcessorMetaData


def generate_radio_buttons(names: list):
    buttons = []
    for name in names:
        buttons.append(QRadioButton(name))
    buttons[0].setChecked(True)
    return buttons


def generate_checkboxes(names: list, checked=True):
    buttons = []
    for name in names:
        buttons.append(QCheckBox(name))
        buttons[-1].setChecked(checked)
    return buttons


class SessionFileLoader(QWidget):
    file_loaded = Signal()

    def __init__(self, parent, config: MuSeqPoseConfig, dialog=True, pre_load=True):
        super(SessionFileLoader, self).__init__(parent)
        self.is_dialog = dialog
        if dialog:
            self.setWindowFlag(Qt.Dialog, True)
            self.resize(300, 100)
        self.file = None
        self.is_dialog = dialog
        layout = QHBoxLayout()
        layout.setMargin(0)
        self.setWindowTitle("Load New File")
        self.flavors = QComboBox()
        self.flavors.addItems(list(datastore_readers.keys()))

        self.flavors.setCurrentIndex(0)
        layout.addWidget(self.flavors)
        file_btn = QPushButton('Load File')
        file_btn.clicked.connect(self.load_file)
        layout.addWidget(file_btn)
        self.config = config
        self.pre_load = pre_load
        self.setLayout(layout)

    def load_file(self, event=None):
        self.file = QFileDialog.getOpenFileName(self, f"Load {self.flavors.currentText()} File",
                                                self.config.output_folder, 'CSV (*.csv)')[0]
        if not self.is_dialog:
            self.file_loaded.emit()
        if self.file and self.pre_load:
            try:
                self.file = initialize_datastore_reader(self.config.body_parts, self.file,
                                                        self.flavors.currentText())
                if self.is_dialog:
                    self.close()
            except Exception as ex:
                print(ex)
                self.file = None
                QMessageBox.warning(self, "Error", str(ex))

    def closeEvent(self, event):
        if self.is_dialog:
            self.file_loaded.emit()
        event.accept()


class BaseInputWidget(QWidget):
    value_changed = Signal()
    ERROR_CSS = "QPushButton,QCheckBox,QComboBox,QLineEdit,QDoubleSpinBox{border: 1px solid #CC0000}"

    def __init__(self, metadata: ProcessorMetaData, session_manager: SessionManager):
        super().__init__()
        self.metadata = metadata
        self.config = session_manager.config
        self.session_manager = session_manager
        self._layout = QHBoxLayout()
        self.title = QLabel(metadata.display_name)
        self.title.setAlignment(Qt.AlignLeading)
        self.title.setFixedWidth(200)
        self._layout.addWidget(self.title)
        self._layout.setAlignment(Qt.AlignVCenter | Qt.AlignLeading)
        self.setLayout(self._layout)
        self._backup_stylesheet = self.styleSheet()

    def is_valid(self):
        return False

    def get_output(self):
        pass

    def set_data(self, data):
        pass

    def set_stylesheet(self, style=''):
        self.setStyleSheet(self._backup_stylesheet + style)

    def reset_ui(self):
        pass


class IntField(BaseInputWidget):

    def __init__(self, metadata: ProcessorMetaData, session_manager: SessionManager):
        assert metadata.param_type == ProcessorMetaData.INT
        super().__init__(metadata, session_manager)

        self.input_field = QLineEdit()
        validator = QIntValidator()
        if metadata.min_val is not None:
            validator.setBottom(metadata.min_val)
        if metadata.max_val is not None:
            validator.setTop(metadata.max_val)
        self.input_field.setValidator(validator)
        if metadata.default is not None:
            self.input_field.setText(str(metadata.default))
        self.setToolTip(metadata.tooltip)
        self._layout.addWidget(self.input_field)
        self.input_field.editingFinished.connect(lambda x: self.value_changed.emit())

    def reset_ui(self):
        if self.metadata.default is not None:
            self.input_field.setText(str(self.metadata.default))
        else:
            self.input_field.setText('')

    def is_valid(self):
        return self.input_field.text() != ''

    def get_output(self):
        return int(self.input_field.text())

    def set_data(self, data):
        self.input_field.setText(str(data))


class FloatField(BaseInputWidget):
    def __init__(self, metadata: ProcessorMetaData, session_manager: SessionManager):
        assert metadata.param_type == ProcessorMetaData.FLOAT
        super().__init__(metadata, session_manager)

        self.input_field = QLineEdit()
        validator = QDoubleValidator()
        if metadata.min_val is not None:
            validator.setBottom(metadata.min_val)
        if metadata.max_val is not None:
            validator.setTop(metadata.max_val)
        self.input_field.setValidator(validator)
        if metadata.default is not None:
            self.input_field.setText(str(metadata.default))
        self.setToolTip(metadata.tooltip)
        self._layout.addWidget(self.input_field)
        self.setLayout(self._layout)
        self.input_field.editingFinished.connect(lambda: self.value_changed.emit())

    def reset_ui(self):
        if self.metadata.default is not None:
            self.input_field.setText(str(self.metadata.default))
        else:
            self.input_field.setText('')

    def is_valid(self):
        return self.input_field.text() != ''

    def get_output(self):
        return float(self.input_field.text())

    def set_data(self, data):
        self.input_field.setText(str(data))


class TextField(BaseInputWidget):
    def __init__(self, metadata: ProcessorMetaData, session_manager: SessionManager):
        assert metadata.param_type == ProcessorMetaData.TEXT
        super().__init__(metadata, session_manager)

        self.input_field = QLineEdit()
        if metadata.max_val is not None:
            self.input_field.setMaxLength(metadata.max_val)
        if metadata.default is not None:
            self.input_field.setText(str(metadata.default))
        if metadata.regex != '':
            self.input_field.setValidator(QRegExpValidator(QRegExp(metadata.regex)))
        self.setToolTip(metadata.tooltip)
        self._layout.addWidget(self.input_field)
        self.setLayout(self._layout)
        self.input_field.editingFinished.connect(lambda: self.value_changed.emit())

    def reset_ui(self):
        if self.metadata.default is not None:
            self.input_field.setText(str(self.metadata.default))
        else:
            self.input_field.setText('')

    def is_valid(self):
        return self.input_field.text() != ''

    def get_output(self):
        return self.input_field.text()

    def set_data(self, data):
        self.input_field.setText(str(data))


class BooleanField(BaseInputWidget):
    def __init__(self, metadata: ProcessorMetaData, session_manager: SessionManager):
        assert metadata.param_type == ProcessorMetaData.BOOLEAN
        super().__init__(metadata, session_manager)

        self.input_field = QCheckBox()
        if metadata.default is not None:
            self.input_field.setChecked(metadata.default)
        self.setToolTip(metadata.tooltip)
        self._layout.addWidget(self.input_field)
        self.setLayout(self._layout)
        self.input_field.stateChanged.connect(lambda x: self.value_changed.emit())

    def reset_ui(self):
        if self.metadata.default is not None:
            self.input_field.setChecked(self.metadata.default)
        else:
            self.input_field.setChecked(False)

    def is_valid(self):
        return True

    def get_output(self):
        return self.input_field.isChecked()

    def set_data(self, data):
        self.input_field.setChecked(data)


class BodyPartValidator(QValidator):
    def __init__(self, body_parts):
        super().__init__()
        self.body_parts = body_parts

    def validate(self, target_text, text_pos: int):
        if target_text in self.body_parts:
            return QValidator.Acceptable
        else:
            return QValidator.Intermediate


class BodyPartField(BaseInputWidget):
    def __init__(self, metadata: ProcessorMetaData, session_manager: SessionManager):
        assert metadata.param_type == ProcessorMetaData.BODY_PART
        super().__init__(metadata, session_manager)
        if self.metadata.min_val is None:
            self.metadata.min_val = 1
        if self.metadata.max_val is None:
            self.metadata.max_val = 1

        self.flow_layout = FlowLayout()
        self.flow_layout.setAlignment(Qt.AlignBottom)
        self._layout.addLayout(self.flow_layout, 1)
        self.input_fields = []
        for i in range(self.metadata.max_val):
            self.input_fields.append(QComboBox())
            self.input_fields[-1].addItem('')
            self.input_fields[-1].addItems(self.config.body_parts)
            self.input_fields[-1].currentIndexChanged.connect(lambda x: self.value_changed.emit())
            self.flow_layout.addWidget(self.input_fields[-1])
        self.setToolTip(metadata.tooltip)
        self.setLayout(self._layout)

    def reset_ui(self):
        for cb in self.input_fields:
            cb.setCurrentIndex(-1)

    def is_valid(self):
        output = self.get_output()
        if type(output) == list:
            return self.metadata.min_val <= len(output) <= self.metadata.max_val
        else:
            return self.metadata.min_val <= 1 <= self.metadata.max_val

    def get_output(self):
        results = [cb.currentText() for cb in self.input_fields if cb.currentText() != '']
        if len(results) == 1:
            return results[0]
        return results

    def set_data(self, data: list):
        if type(data) != list:
            data = [data]
        for combobox, data_field in zip(self.input_fields, data):
            combobox.setCurrentIndex(combobox.findText(data_field))


class RangeField(BaseInputWidget):
    def __init__(self, metadata: ProcessorMetaData, session_manager: SessionManager):
        assert metadata.param_type == ProcessorMetaData.FIXED_RANGE
        super().__init__(metadata, session_manager)

        self.input_field = QDoubleSpinBox()

        if metadata.min_val is not None:
            self.input_field.setMinimum(metadata.min_val)
        if metadata.max_val is not None:
            self.input_field.setMaximum(metadata.max_val)
        if metadata.default is not None:
            self.input_field.setValue(float(metadata.default))
        self.input_field.valueChanged.connect(lambda x: self.value_changed.emit())
        self.setToolTip(metadata.tooltip)
        self._layout.addWidget(self.input_field)
        self.setLayout(self._layout)

    def reset_ui(self):
        if self.metadata.default is not None:
            self.input_field.setValue(float(self.metadata.default))
        else:
            self.input_field.setValue(0)

    def is_valid(self):
        return True

    def get_output(self):
        return self.input_field.value()

    def set_data(self, data):
        self.input_field.setValue(float(data))


class NumpyField(BaseInputWidget):

    def __init__(self, metadata: ProcessorMetaData, session_manager: SessionManager):
        assert metadata.param_type == ProcessorMetaData.NUMPY_ARRAY
        super().__init__(metadata, session_manager)

        self.file_path = None
        self.file_btn = QPushButton('Load File')
        self.file_btn.clicked.connect(self.load_file)
        self.file_btn.setMaximumWidth(200)
        self._layout.addWidget(self.file_btn)
        self.setToolTip(metadata.tooltip)

        self.setLayout(self._layout)

    def load_file(self, event):
        self.file_path = QFileDialog.getOpenFileName(self, f"Load Numpy File",
                                                     self.config.output_folder, 'Numpy (*.npy,*.npz)')[0]
        self.value_changed.emit()
        if self.file_path:
            self.file_btn.setText(self.file_path)

    def reset_ui(self):
        self.file_path = None

    def is_valid(self):
        return self.file_path is not None and os.path.exists(self.file_path)

    def get_output(self):
        return self.file_path

    def set_data(self, data):
        self.file_path = data
        self.file_btn.setText(data)


class DatastoreField(BaseInputWidget):

    def __init__(self, metadata: ProcessorMetaData, session_manager: SessionManager):
        assert metadata.param_type == ProcessorMetaData.DATA_STORE
        super().__init__(metadata, session_manager)

        self.file_loader = SessionFileLoader(None, self.config, False, False)
        self.file_loader.file_loaded.connect(lambda: self.value_changed.emit())
        self._layout.addWidget(self.file_loader)
        self.setToolTip(metadata.tooltip)
        self.setLayout(self._layout)

    def reset_ui(self):
        self.file_loader.file = None

    def is_valid(self):
        return self.file_loader.file is not None and os.path.exists(self.file_loader.file)

    def get_output(self):
        return {'path': self.file_loader.file, 'type': self.file_loader.flavors.currentText()}

    def set_data(self, data):
        self.file_loader.file = data['path']
        self.file_loader.flavors.setCurrentIndex(self.file_loader.flavors.findText(data['type']))


class ViewsField(BaseInputWidget):

    def __init__(self, metadata: ProcessorMetaData, session_manager: SessionManager):
        assert metadata.param_type == ProcessorMetaData.VIEWS
        super().__init__(metadata, session_manager)
        if self.metadata.min_val is None:
            self.metadata.min_val = 1
        if self.metadata.max_val is None:
            self.metadata.max_val = 1

        self.flow_layout = FlowLayout()
        self._layout.addLayout(self.flow_layout, 1)
        self.input_fields = generate_checkboxes(self.config.views, False)
        for field in self.input_fields:
            field.stateChanged.connect(lambda: self.value_changed.emit())
            self.flow_layout.addWidget(field)
        self.setToolTip(metadata.tooltip)
        self.setLayout(self._layout)

    def reset_ui(self):
        for field in self.input_fields:
            field.setChecked(False)

    def is_valid(self):
        return self.metadata.min_val <= len(self.get_output()) <= self.metadata.max_val

    def get_output(self):
        return [cb.text() for cb in self.input_fields if cb.isChecked()]

    def set_data(self, data: list):
        for checkbox in self.input_fields:
            if checkbox.text() in data:
                checkbox.setChecked(True)


class FilePathField(BaseInputWidget):

    def __init__(self, metadata: ProcessorMetaData, session_manager: SessionManager):
        assert metadata.param_type == ProcessorMetaData.FILE_PATH
        super().__init__(metadata, session_manager)
        self.file_path = None
        self.file_btn = QPushButton('Select File')
        self.file_btn.clicked.connect(self.load_file)
        self.file_btn.setMaximumWidth(200)
        self._layout.addWidget(self.file_btn)
        self.setToolTip(metadata.tooltip)

        self.setLayout(self._layout)

    def load_file(self, event):
        self.file_path = QFileDialog.getSaveFileName(self, f"File Path",
                                                     self.config.output_folder, self.metadata.regex)[0]
        self.value_changed.emit()
        if self.file_path:
            self.file_btn.setText(self.file_path)

    def reset_ui(self):
        self.file_path = None

    def is_valid(self):
        return self.file_path is not None

    def get_output(self):
        return self.file_path

    def set_data(self, data):
        self.file_path = data


class DirPathField(BaseInputWidget):

    def __init__(self, metadata: ProcessorMetaData, session_manager: SessionManager):
        assert metadata.param_type == ProcessorMetaData.DIR_PATH
        super().__init__(metadata, session_manager)

        self.file_path = None
        self.file_btn = QPushButton('Select Directory')
        self.file_btn.clicked.connect(self.load_file)
        self.file_btn.setMaximumWidth(200)
        self._layout.addWidget(self.file_btn)
        self.setToolTip(metadata.tooltip)

        self.setLayout(self._layout)

    def load_file(self, event):
        self.file_path = QFileDialog.getExistingDirectory(self, f"Directory Path",
                                                          self.config.output_folder)[0]
        self.value_changed.emit()
        if self.file_path:
            self.file_btn.setText(self.file_path)

    def reset_ui(self):
        self.file_path = None

    def is_valid(self):
        return self.file_path is not None

    def get_output(self):
        return self.file_path

    def set_data(self, data):
        self.file_path = data
