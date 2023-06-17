from PySide2.QtWidgets import QMessageBox

from MuSeqPose.utils.session_manager import SessionManager
from MuSeqPose.widgets.OperationCardWidget import OperationCard
from MuSeqPose.widgets.ProcessorCardWidget import ProcessorConfigurator
from cvkit import get_processor_class, verify_installed_processor


def verify_import(imported_data: dict):
    try:
        assert 'pipeline' in imported_data
        for data in imported_data['pipeline']:
            for configurator_data in data:
                assert verify_installed_processor(configurator_data['id'])
                assert 'parameters' in configurator_data
    except:
        return False
    return True


class PipelineExecutionManager:

    def __init__(self, session_manager: SessionManager):
        self.session_manager = session_manager
        self.pipeline: list[OperationCard] = []
        self.current_index = 0

    def add_processor(self, card: OperationCard):
        self.pipeline.append(card)
        card.execution_completed.connect(self.execute_next)

    def remove_processor(self, card: OperationCard):
        self.pipeline.remove(card)

    def import_pipeline(self, parent, imported_data: dict):
        new_pipeline = []
        for card in imported_data.get('pipeline', []):
            processor_configurators = []
            for configurator_data in card:
                configurator = ProcessorConfigurator(parent, self.session_manager,
                                                     get_processor_class(configurator_data['id']))
                for key, input_ui in configurator.ui_map.items():
                    data = configurator_data['parameters'].get(key, None)
                    if data is not None:
                        input_ui.set_data(data)
                processor_configurators.append(configurator)
            new_pipeline.append(OperationCard(self.session_manager, processor_configurators))
        if len(new_pipeline) > 0:
            self.delete_pipeline()
            for card in new_pipeline:
                self.add_processor(card)
            return self.pipeline
        return None

    def export_pipeline(self):
        out_dict = {'pipeline': []}
        for card in self.pipeline:
            processors = []
            for configurator in card.processor_configurators:
                id = configurator.target_processor.PROCESSOR_ID
                processor = {'id': id, 'parameters': {}}
                for key in configurator.ui_map:
                    serialize = configurator.target_processor.META_DATA[key].serialize
                    processor['parameters'][key] = configurator.ui_map[key].get_output() if serialize else None
                processors.append(processor)
            out_dict['pipeline'].append(processors)
        return out_dict

    def execute_next(self):
        if self.current_index < len(self.pipeline):
            if self.current_index != 0 and self.pipeline[self.current_index - 1].exception_occurred:
                QMessageBox.warning(self.pipeline[self.current_index - 1], "Error",
                                    self.pipeline[self.current_index - 1].exception_message)
                return
            args = self.pipeline[self.current_index - 1].get_output()
            self.pipeline[self.current_index].execute(args)
            self.current_index += 1
        else:
            for card in self.pipeline:
                card.configurable = True

    def start_execution(self):
        execution_condition = True
        for card in self.pipeline:
            if not card.verify_configurators():
                execution_condition = False
        if execution_condition:
            self.current_index = 0
            self.execute_next()
        return execution_condition

    def reset_pipeline(self):
        for card in self.pipeline:
            card.reset_operation()

    def delete_pipeline(self):
        for card in self.pipeline:
            try:
                card.deleteLater()
            except:
                pass
        self.pipeline.clear()
