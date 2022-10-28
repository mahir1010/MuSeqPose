from PySide2.QtWidgets import QCheckBox, QRadioButton


def generate_radio_buttons(names: list):
    buttons = []
    for name in names:
        buttons.append(QRadioButton(name))
    buttons[0].setChecked(True)
    return buttons


def generate_checkboxes(names: list,checked=True):
    buttons = []
    for name in names:
        buttons.append(QCheckBox(name))
        buttons[-1].setChecked(checked)
    return buttons
