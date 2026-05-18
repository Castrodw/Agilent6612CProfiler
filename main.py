import os
import sys
import time
from collections import deque
from datetime import datetime

import numpy as np
import pyqtgraph as pg

from PyQt5 import QtWidgets, QtCore, QtGui

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
# RESET / SAVE BUTTONS
# -----------------------------
btn_reset            = QtWidgets.QPushButton("Reset Graph")
btn_save             = QtWidgets.QPushButton("Save Graph")
btn_load_comparison  = QtWidgets.QPushButton("Load Comparison")
btn_clear_comparison = QtWidgets.QPushButton("Clear Comparison")
btn_clear_comparison.hide()

btn_row = QtWidgets.QWidget()
btn_layout = QtWidgets.QHBoxLayout()
btn_layout.setContentsMargins(0, 0, 0, 0)
btn_layout.addWidget(btn_reset)
btn_layout.addWidget(btn_save)
btn_layout.addWidget(btn_load_comparison)
btn_layout.addWidget(btn_clear_comparison)
btn_layout.addStretch()
btn_row.setLayout(btn_layout)

comparison_container = QtWidgets.QWidget()
comparison_layout    = QtWidgets.QVBoxLayout()
comparison_layout.setContentsMargins(0, 0, 0, 0)
comparison_container.setLayout(comparison_layout)
comparison_container.hide()

def reset_graph():
    global start_time
    times.clear()
    voltages.clear()
    currents.clear()
    start_time = time.time()
    curve_v.setData([], [])
    curve_c.setData([], [])
    status.setText("Graph reset.")

def save_graph():
    filename = f"graph_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    save_path = f"C:\\Agilent6612CProfiler\\{filename}"
    graphics.grab().save(save_path)
    status.setText(f"Saved: {filename}")

btn_reset.clicked.connect(reset_graph)
btn_save.clicked.connect(save_graph)

# -----------------------------
# LAYOUT
# -----------------------------
layout.addWidget(graphics)
layout.addWidget(controls)
layout.addWidget(btn_row)
layout.addWidget(comparison_container)
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