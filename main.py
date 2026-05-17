import sys
import time
from collections import deque

import numpy as np
import pyqtgraph as pg

from PyQt5 import QtWidgets, QtCore

from serial_worker import SerialWorker
from logger import CSVLogger
from controls import ControlPanel

import config

# -----------------------------
# DATA BUFFERS
# -----------------------------
times = deque(maxlen=config.MAX_POINTS)
voltages = deque(maxlen=config.MAX_POINTS)
currents = deque(maxlen=config.MAX_POINTS)

start_time = time.time()

# -----------------------------
# LOGGER
# -----------------------------
logger = None

if config.CSV_LOGGING:
    logger = CSVLogger(config.CSV_FILENAME)

# -----------------------------
# DATA CALLBACK
# -----------------------------
def add_measurement(voltage, current):

    elapsed = time.time() - start_time

    times.append(elapsed)
    voltages.append(voltage)
    currents.append(current)

    if logger:
        logger.log(voltage, current)

# -----------------------------
# SERIAL WORKER
# -----------------------------
worker = SerialWorker(
    config.SERIAL_PORT,
    config.BAUDRATE,
    config.POLL_INTERVAL,
    add_measurement
)

worker.start()

# -----------------------------
# QT APP
# -----------------------------
app = QtWidgets.QApplication([])

pg.setConfigOptions(
    antialias=True,
    background='k',
    foreground='w'
)

window = QtWidgets.QMainWindow()

central = QtWidgets.QWidget()
layout = QtWidgets.QVBoxLayout()

graphics = pg.GraphicsLayoutWidget()

# -----------------------------
# VOLTAGE PLOT
# -----------------------------
plot_v = graphics.addPlot(title="Voltage")
plot_v.showGrid(x=True, y=True)
plot_v.setLabel('left', 'Voltage', units='V')
plot_v.getViewBox().setDefaultPadding(0.02)

curve_v = plot_v.plot(
    pen=pg.mkPen('c', width=2)
)

graphics.nextRow()

# -----------------------------
# CURRENT PLOT
# -----------------------------
plot_c = graphics.addPlot(title="Current")
plot_c.showGrid(x=True, y=True)
plot_c.setLabel('left', 'Current', units='A')
plot_c.getViewBox().setDefaultPadding(0.02)

curve_c = plot_c.plot(
    pen=pg.mkPen('y', width=2)
)

# -----------------------------
# CONTROL PANEL
# -----------------------------
controls = ControlPanel(worker)

# -----------------------------
# STATUS LABEL
# -----------------------------
status = QtWidgets.QLabel()

# -----------------------------
# LAYOUT
# -----------------------------
layout.addWidget(graphics)
layout.addWidget(controls)
layout.addWidget(status)

central.setLayout(layout)

window.setCentralWidget(central)

window.resize(1400, 900)
window.setWindowTitle(
    "Agilent 6612C Power Profiler"
)

window.show()

# -----------------------------
# UPDATE GUI
# -----------------------------
def update():

    if len(times) == 0:
        return

    t = np.array(times)

    curve_v.setData(t, np.array(voltages))
    curve_c.setData(t, np.array(currents))

    # rolling window
    xmin = max(0, t[-1] - 30)
    xmax = t[-1]

    plot_v.setXRange(xmin, xmax, padding=0)
    plot_c.setXRange(xmin, xmax, padding=0)

    status.setText(
        f"Voltage: {voltages[-1]:.3f} V  "
        f"Current: {currents[-1]:.3f} A"
    )

timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(20)

# -----------------------------
# CLEAN EXIT
# -----------------------------
def cleanup():

    worker.stop()

    if logger:
        logger.close()

app.aboutToQuit.connect(cleanup)

sys.exit(app.exec_())