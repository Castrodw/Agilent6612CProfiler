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

# -----------------------------
# FORMAT DETECTION
# -----------------------------
def _detect_format(filepath):
    ext = filepath.rsplit('.', 1)[-1].lower() if '.' in filepath else ''
    if ext == 'csv':
        return 'csv'
    if ext in ('png', 'jpg', 'jpeg', 'bmp', 'gif'):
        return 'image'
    return None

def _build_csv_comparison(filepath):
    import csv as _csv

    elapsed, v_data, c_data = [], [], []
    with open(filepath, newline='') as f:
        for row in _csv.DictReader(f):
            elapsed.append(float(row['elapsed_seconds']))
            v_data.append(float(row['voltage']))
            c_data.append(float(row['current']))

    container = QtWidgets.QWidget()
    vbox = QtWidgets.QVBoxLayout()
    vbox.setContentsMargins(0, 4, 0, 0)

    header = QtWidgets.QLabel(f"Comparison: {os.path.basename(filepath)}")
    vbox.addWidget(header)

    gw = pg.GraphicsLayoutWidget()
    gw.setFixedHeight(400)

    pv = gw.addPlot(title="Voltage (saved)")
    pv.showGrid(x=True, y=True)
    pv.setLabel('left', 'Voltage', units='V')
    pv.getViewBox().setDefaultPadding(0.02)
    pv.plot(elapsed, v_data, pen=pg.mkPen('m', width=2))

    gw.nextRow()

    pc = gw.addPlot(title="Current (saved)")
    pc.showGrid(x=True, y=True)
    pc.setLabel('left', 'Current', units='A')
    pc.getViewBox().setDefaultPadding(0.02)
    pc.plot(elapsed, c_data, pen=pg.mkPen(color=(255, 165, 0), width=2))

    vbox.addWidget(gw)
    container.setLayout(vbox)
    return container

def _build_image_comparison(filepath):
    container = QtWidgets.QWidget()
    vbox = QtWidgets.QVBoxLayout()
    vbox.setContentsMargins(0, 4, 0, 0)

    header = QtWidgets.QLabel(f"Comparison: {os.path.basename(filepath)}")
    vbox.addWidget(header)

    pixmap = QtGui.QPixmap(filepath)
    img_label = QtWidgets.QLabel()
    img_label.setPixmap(
        pixmap.scaledToWidth(1200, QtCore.Qt.SmoothTransformation)
    )
    img_label.setAlignment(QtCore.Qt.AlignCenter)
    vbox.addWidget(img_label)

    container.setLayout(vbox)
    return container

def _clear_comparison_widgets():
    while comparison_layout.count():
        item = comparison_layout.takeAt(0)
        w = item.widget()
        if w:
            w.deleteLater()

def load_comparison():
    filepath, _ = QtWidgets.QFileDialog.getOpenFileName(
        window,
        "Load Comparison File",
        "",
        "Data & Images (*.csv *.png *.jpg *.bmp *.gif);;"
        "CSV Files (*.csv);;"
        "Images (*.png *.jpg *.bmp *.gif)"
    )
    if not filepath:
        return

    fmt = _detect_format(filepath)
    if fmt is None:
        status.setText("Unsupported file type.")
        return

    _clear_comparison_widgets()

    try:
        if fmt == 'csv':
            widget = _build_csv_comparison(filepath)
        else:
            widget = _build_image_comparison(filepath)
    except Exception as e:
        status.setText(f"Error loading file: {e}")
        return

    comparison_layout.addWidget(widget)
    comparison_container.show()
    btn_clear_comparison.show()
    status.setText(f"Loaded: {os.path.basename(filepath)}")

def clear_comparison():
    _clear_comparison_widgets()
    comparison_container.hide()
    btn_clear_comparison.hide()
    status.setText("Comparison cleared.")

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
btn_load_comparison.clicked.connect(load_comparison)
btn_clear_comparison.clicked.connect(clear_comparison)

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