from PyQt5 import QtWidgets

class ControlPanel(QtWidgets.QWidget):

    def __init__(self, worker):
        super().__init__()

        self.worker = worker

        layout = QtWidgets.QGridLayout()

        self.btn_on = QtWidgets.QPushButton("Output ON")
        self.btn_off = QtWidgets.QPushButton("Output OFF")

        self.voltage_box = QtWidgets.QDoubleSpinBox()
        self.voltage_box.setRange(0, 20)
        self.voltage_box.setSuffix(" V")

        self.current_box = QtWidgets.QDoubleSpinBox()
        self.current_box.setRange(0, 50)
        self.current_box.setSuffix(" A")

        self.btn_set_voltage = QtWidgets.QPushButton("Set Voltage")
        self.btn_set_current = QtWidgets.QPushButton("Set Current")

        layout.addWidget(self.btn_on, 0, 0)
        layout.addWidget(self.btn_off, 0, 1)

        layout.addWidget(self.voltage_box, 1, 0)
        layout.addWidget(self.btn_set_voltage, 1, 1)

        layout.addWidget(self.current_box, 2, 0)
        layout.addWidget(self.btn_set_current, 2, 1)

        self.setLayout(layout)

        self.btn_on.clicked.connect(self.worker.output_on)
        self.btn_off.clicked.connect(self.worker.output_off)

        self.btn_set_voltage.clicked.connect(
            lambda: self.worker.set_voltage(
                self.voltage_box.value()
            )
        )

        self.btn_set_current.clicked.connect(
            lambda: self.worker.set_current(
                self.current_box.value()
            )
        )