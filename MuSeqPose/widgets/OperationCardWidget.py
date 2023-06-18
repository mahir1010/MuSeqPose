from PySide2.QtCore import Signal, QFile, QThreadPool, Qt
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QHBoxLayout, QLabel, QProgressBar, QWidget, QVBoxLayout, QStyle, QPushButton, QMessageBox

from MuSeqPose import get_resource
from MuSeqPose.utils.processor_thread import ProcessorThread
from MuSeqPose.utils.session_manager import SessionManager
from MuSeqPose.widgets.ProcessorCardWidget import ProcessorConfigurator


class OperationStatusWidget(QWidget):
    CONFIG_ERROR_CSS = "QPushButton{border: 2px solid #CC0000;}"

    def __init__(self, configurator: ProcessorConfigurator):
        super().__init__()
        self.configurator = configurator
        edit_icon = self.style().standardIcon(QStyle.SP_FileDialogDetailedView)
        close_icon = self.style().standardIcon(QStyle.SP_DockWidgetCloseButton)
        layout = QHBoxLayout()
        layout.setMargin(5)
        layout.setSpacing(10)
        self.configurator_btn = QPushButton()
        self.configurator_btn.setIcon(edit_icon)
        # self.configurator_btn.clicked.connect(lambda x: self.edit_processor_card(configurator))
        if not configurator.verify_data()[0]:
            self.configurator_btn.setStyleSheet(configurator.styleSheet() + self.CONFIG_ERROR_CSS)
        # configurator.accepted.connect(lambda: self.update_processor(configurator))
        self.remove_btn = QPushButton()
        self.remove_btn.setIcon(close_icon)
        # self.remove_btn.clicked.connect(lambda x: self.remove_configurator(configurator))
        self.remove_btn.setStyleSheet("QPushButton{border:none;}")
        self.label = None
        if 'target_column' in configurator.ui_map:
            self.label = QLabel(configurator.ui_map['target_column'].get_output())
            layout.addWidget(self.label, 1)
            self.label.setFixedHeight(30)
        self.bar = QProgressBar()
        self.bar.setFixedHeight(30)
        self.bar.setValue(0)
        self.bar.setAlignment(Qt.AlignCenter)
        self.bar.setMaximum(100)
        # self.progress.append(False)
        layout.addWidget(self.bar, 2)
        layout.addWidget(self.configurator_btn, 0)
        layout.addWidget(self.remove_btn, 0)
        # self.ui.scrollArea.setMinimumWidth(layout.geometry().width())
        # self.ui.progress_container.layout().addLayout(layout)
        self.setLayout(layout)

    def update_label(self,configurator):
        if self.label is not None:
            self.label.setText(configurator.ui_map['target_column'].get_output())

class OperationCard(QWidget):
    delete_card = Signal()
    execution_completed = Signal()

    ACTIVE_CSS = "QWidget#card{border: 2px solid rgb(51,149,211);}"
    COMPLETED_CSS = "QWidget#card{border: 2px solid #18b221;}"
    ERROR_CSS = "QWidget#card{border: 2px solid #CC0000;}"
    CONFIG_ERROR_CSS = "QPushButton{border: 2px solid #CC0000;}"

    def __init__(self, session_manager: SessionManager, processor_configurators: list[ProcessorConfigurator]):
        super(OperationCard, self).__init__()
        self.session_manager = session_manager
        self.processor_configurators = processor_configurators
        assert all([p.target_processor.PROCESSOR_ID == processor_configurators[0].target_processor.PROCESSOR_ID for p in
                    self.processor_configurators])
        file = QFile(get_resource('OperationCard.ui'))
        self.close_icon = self.style().standardIcon(QStyle.SP_DockWidgetCloseButton)
        file.open(QFile.ReadOnly)
        base_layout = QVBoxLayout()
        base_layout.setMargin(0)
        self.ui = QUiLoader().load(file)
        base_layout.addWidget(self.ui)
        self.ui.delete_op.setIcon(self.close_icon)
        self.ui.delete_op.clicked.connect(self.delete_operation_clicked)
        self.progress = []
        self.exception_occurred = False
        self.exception_message = ''
        self.ui.title.setText(self.processor_configurators[0].target_processor.PROCESSOR_NAME)
        self.operation_status_widgets = []
        self.adjustSize()
        for processor in self.processor_configurators:
            self.generate_processor_thread_ui(processor)
        if self.processor_configurators[0].target_processor.DISTRIBUTED:
            self.add_thread_btn = QPushButton("Add Body Part")
            self.add_thread_btn.setContentsMargins(5, 5, 5, 5)
            self.add_thread_btn.clicked.connect(self.configure_new_processor)
            self.add_thread_btn.setFixedHeight(30)
            self.ui.layout().addWidget(self.add_thread_btn)
        self.processor_threads = []
        self.threadpool = QThreadPool.globalInstance()
        self.setLayout(base_layout)
        self.adjustSize()
        self.configurable = True
        self._backup_stylesheet = self.styleSheet()
        # self.show()

    def set_configurable(self, value):
        self.configurable = value

    def configure_new_processor(self, event):
        if not self.configurable:
            return
        processor_dialog = ProcessorConfigurator(self, self.session_manager,
                                                 self.processor_configurators[0].target_processor)
        processor_dialog.accepted.disconnect()
        processor_dialog.accepted.connect(lambda: self.add_new_processor(processor_dialog))
        processor_dialog.open()

    def add_new_processor(self, dialog):
        dialog.accepted.disconnect()
        dialog.accepted.connect(lambda: self.update_processor(dialog))
        if dialog in self.processor_configurators:
            QMessageBox.warning(self.ui, 'Error', 'Processor already exists!')
            return
        is_valid, error = dialog.verify_data()
        if not is_valid:
            QMessageBox.warning(self.ui, 'Error', error)
            return
        self.processor_configurators.append(dialog)
        self.generate_processor_thread_ui(self.processor_configurators[-1])
        dialog.close()

    def generate_processor_thread_ui(self, configurator: ProcessorConfigurator):
        status_widget = OperationStatusWidget(configurator)

        status_widget.configurator_btn.clicked.connect(lambda x: self.edit_processor_card(configurator))
        configurator.accepted.connect(lambda: self.update_processor(configurator))
        self.progress.append(False)
        self.operation_status_widgets.append(status_widget)
        self.ui.scrollArea.setMinimumWidth(status_widget.geometry().width()/2)
        self.ui.progress_container.layout().addWidget(status_widget)

    def execute(self, processor_args):
        self.configurable = False
        self.set_css(self.ACTIVE_CSS)
        for index, configurator in enumerate(self.processor_configurators):
            processor_thread = ProcessorThread(index, configurator.get_instance())
            self.processor_threads.append(processor_thread)
            processor_thread.set_args(processor_args)
            processor_thread.signals.progress_update.connect(self.operation_status_widgets[index].bar.setValue)
            processor_thread.signals.process_complete.connect(self.sub_process_completed)
            self.threadpool.start(processor_thread)

    def sub_process_completed(self, index, status):
        if status != '' and not self.exception_occurred:
            self.exception_occurred = True
            self.exception_message = status
            self.set_css(self.ERROR_CSS)
            self.progress[index] = False
        else:
            self.progress[index] = True
            self.operation_status_widgets[index].bar.setValue(100)

        self.processor_threads[index].signals.timer.stop()
        if all(self.progress):
            self.execution_completed.emit()
            self.set_css(self.COMPLETED_CSS)

    def get_output(self):
        if len(self.processor_threads) > 0:
            return self.processor_threads[0].get_output()

    def delete_operation_clicked(self, event):
        if not self.configurable:
            return
        self.delete_card.emit()

    def remove_configurator(self, configurator: ProcessorConfigurator):
        index = self.processor_configurators.index(configurator)
        if len(self.processor_configurators) == 1:
            self.delete_operation_clicked(None)
            return
        container_layout = self.ui.progress_container.layout()
        remove_item = container_layout.itemAt(index + 1)
        # for i in reversed(range(remove_item.count())):
        #     remove_item.itemAt(i).widget().deleteLater()
        remove_item.deleteLater()
        container_layout.removeItem(remove_item)
        del self.processor_configurators[index]
        del self.operation_status_widgets[index]
        del self.progress[index]
        container_layout.update()

    def edit_processor_card(self, configurator):
        if not self.configurable:
            return
        configurator.open()

    #
    def update_processor(self, configurator):
        is_valid, error = configurator.verify_data()
        c = configurator == self.processor_configurators[0]
        if not is_valid:
            QMessageBox.warning(self.ui, 'Error', error)
            return
        if sum([configurator==conf for conf in self.processor_configurators])!=1:
            QMessageBox.warning(self,'Error',"Processor already exists!")
            return
        index = self.processor_configurators.index(configurator)
        self.operation_status_widgets[index].update_label(configurator)
        self.operation_status_widgets[index].configurator_btn.setStyleSheet(configurator.styleSheet().replace(self.CONFIG_ERROR_CSS, ''))
        configurator.close()

    def set_css(self, css):
        self.setStyleSheet(self._backup_stylesheet + css)

    def reset_operation(self):
        self.set_css('')
        self.exception_occurred = False
        self.exception_message = ''
        for widget in self.operation_status_widgets:
            widget.bar.setValue(0)
        self.progress = [False] * len(self.progress)

    def verify_configurators(self):
        return_flag = True
        for idx, configurator in enumerate(self.processor_configurators):
            if not configurator.verify_data()[0]:
                self.operation_status_widgets[idx].configurator_btn.setStyleSheet(configurator.styleSheet() + self.CONFIG_ERROR_CSS)
                return_flag = False
        return return_flag
