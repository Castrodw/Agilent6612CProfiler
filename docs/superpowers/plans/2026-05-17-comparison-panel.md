# Comparison Panel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a replaceable comparison panel below the live plots that loads a CSV (data overlay) or image (scaled preview) for side-by-side review with the active graph.

**Architecture:** All changes are in `main.py`. A hidden `QWidget` container sits below the existing `GraphicsLayoutWidget` in the main layout. "Load Comparison" opens a file dialog, detects format by extension, builds the appropriate widget (pyqtgraph plots for CSV, QLabel for images), and inserts it into the container. "Clear Comparison" destroys the child widget and hides the container. Swap is handled by clearing before each new load.

**Tech Stack:** PyQt5, pyqtgraph, Python stdlib `csv` and `os` modules.

---

## File Map

| File | Change |
|---|---|
| `main.py` | Add imports, buttons, container widget, 4 helper functions, button wiring |

---

### Task 1: Add imports and extend button row

**Files:**
- Modify: `main.py:1-9` (imports)
- Modify: `main.py:117-145` (button row)

- [ ] **Step 1: Add `os` and `QtGui` imports**

At the top of `main.py`, the current imports block ends at line 16. Replace:

```python
import sys
import time
from collections import deque
from datetime import datetime

import numpy as np
import pyqtgraph as pg

from PyQt5 import QtWidgets, QtCore
```

with:

```python
import os
import sys
import time
from collections import deque
from datetime import datetime

import numpy as np
import pyqtgraph as pg

from PyQt5 import QtWidgets, QtCore, QtGui
```

- [ ] **Step 2: Add "Load Comparison" and "Clear Comparison" buttons to the button row**

Find the button row block (currently around lines 117–126). Replace it with:

```python
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
```

- [ ] **Step 3: Add comparison container below the graphics widget**

After the `btn_row` block and before the `def reset_graph():` function, add:

```python
comparison_container = QtWidgets.QWidget()
comparison_layout    = QtWidgets.QVBoxLayout()
comparison_layout.setContentsMargins(0, 0, 0, 0)
comparison_container.setLayout(comparison_layout)
comparison_container.hide()
```

- [ ] **Step 4: Add comparison_container to the main layout**

Find the layout assembly block (currently around lines 150–153):

```python
layout.addWidget(graphics)
layout.addWidget(controls)
layout.addWidget(btn_row)
layout.addWidget(status)
```

Replace with:

```python
layout.addWidget(graphics)
layout.addWidget(controls)
layout.addWidget(btn_row)
layout.addWidget(comparison_container)
layout.addWidget(status)
```

- [ ] **Step 5: Run the app and verify**

```
python main.py
```

Expected: app launches, "Load Comparison" and "Reset Graph" / "Save Graph" buttons are all visible in the button row. "Clear Comparison" is NOT visible. The live graphs still update normally. No errors in the console.

- [ ] **Step 6: Commit**

```bash
git add main.py
git commit -m "feat: add comparison panel buttons and hidden container"
```

---

### Task 2: Implement format detection

**Files:**
- Modify: `main.py` — add `_detect_format` function

- [ ] **Step 1: Add `_detect_format` after the `comparison_container` block and before `def reset_graph():`**

```python
def _detect_format(filepath):
    ext = filepath.rsplit('.', 1)[-1].lower() if '.' in filepath else ''
    if ext == 'csv':
        return 'csv'
    if ext in ('png', 'jpg', 'jpeg', 'bmp', 'gif'):
        return 'image'
    return None
```

- [ ] **Step 2: Verify manually in a Python shell**

```
python -c "
def _detect_format(filepath):
    ext = filepath.rsplit('.', 1)[-1].lower() if '.' in filepath else ''
    if ext == 'csv': return 'csv'
    if ext in ('png', 'jpg', 'jpeg', 'bmp', 'gif'): return 'image'
    return None

assert _detect_format('power_profile.csv') == 'csv'
assert _detect_format('DATA.CSV') == 'csv'
assert _detect_format('graph.png') == 'image'
assert _detect_format('photo.jpg') == 'image'
assert _detect_format('shot.bmp') == 'image'
assert _detect_format('data.xlsx') is None
assert _detect_format('noextension') is None
print('All assertions passed.')
"
```

Expected output: `All assertions passed.`

- [ ] **Step 3: Commit**

```bash
git add main.py
git commit -m "feat: add _detect_format"
```

---

### Task 3: Implement CSV comparison builder

**Files:**
- Modify: `main.py` — add `_build_csv_comparison` function

- [ ] **Step 1: Add `_build_csv_comparison` after `_detect_format`**

```python
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
```

- [ ] **Step 2: Manual smoke test**

Run the app and verify it starts without errors. (The function is not yet wired to a button — that comes in Task 5.)

```
python main.py
```

Expected: no ImportError or SyntaxError. App launches normally.

- [ ] **Step 3: Commit**

```bash
git add main.py
git commit -m "feat: add _build_csv_comparison"
```

---

### Task 4: Implement image comparison builder

**Files:**
- Modify: `main.py` — add `_build_image_comparison` function

- [ ] **Step 1: Add `_build_image_comparison` after `_build_csv_comparison`**

```python
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
```

- [ ] **Step 2: Manual smoke test**

```
python main.py
```

Expected: no errors, app launches normally.

- [ ] **Step 3: Commit**

```bash
git add main.py
git commit -m "feat: add _build_image_comparison"
```

---

### Task 5: Wire up Load and Clear buttons

**Files:**
- Modify: `main.py` — add `_clear_comparison_widgets`, `load_comparison`, `clear_comparison` functions and connect buttons

- [ ] **Step 1: Add `_clear_comparison_widgets` helper**

Add after `_build_image_comparison`:

```python
def _clear_comparison_widgets():
    while comparison_layout.count():
        item = comparison_layout.takeAt(0)
        w = item.widget()
        if w:
            w.deleteLater()
```

- [ ] **Step 2: Add `load_comparison` function**

```python
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
```

- [ ] **Step 3: Add `clear_comparison` function**

```python
def clear_comparison():
    _clear_comparison_widgets()
    comparison_container.hide()
    btn_clear_comparison.hide()
    status.setText("Comparison cleared.")
```

- [ ] **Step 4: Connect the buttons**

Find the existing button connections block:

```python
btn_reset.clicked.connect(reset_graph)
btn_save.clicked.connect(save_graph)
```

Replace with:

```python
btn_reset.clicked.connect(reset_graph)
btn_save.clicked.connect(save_graph)
btn_load_comparison.clicked.connect(load_comparison)
btn_clear_comparison.clicked.connect(clear_comparison)
```

- [ ] **Step 5: Run the app and do a full manual test**

```
python main.py
```

**CSV test:**
1. Click "Load Comparison"
2. Select an existing `power_profile.csv` (or any CSV with the right columns)
3. Verify a new panel appears below the controls with magenta voltage plot and orange current plot
4. Verify "Clear Comparison" button is now visible
5. Click "Load Comparison" again with a different file — verify the old panel is replaced
6. Click "Clear Comparison" — verify the panel disappears and the button hides

**Image test:**
1. Click "Load Comparison"
2. Select an existing `.png` (e.g., a saved graph PNG)
3. Verify the image appears below the controls, scaled to fit
4. Click "Clear Comparison" — panel disappears

**Error cases:**
1. Click "Load Comparison", cancel the dialog — nothing happens
2. (Optional) Rename a file to `.xlsx` and try loading it — status bar shows "Unsupported file type."

- [ ] **Step 6: Commit**

```bash
git add main.py
git commit -m "feat: wire up load and clear comparison panel"
```

---

### Task 6: Final integration verification and memory update

**Files:**
- No code changes

- [ ] **Step 1: Re-run the format detection shell check**

```
python -c "
def _detect_format(filepath):
    ext = filepath.rsplit('.', 1)[-1].lower() if '.' in filepath else ''
    if ext == 'csv': return 'csv'
    if ext in ('png', 'jpg', 'jpeg', 'bmp', 'gif'): return 'image'
    return None

assert _detect_format('power_profile.csv') == 'csv'
assert _detect_format('graph.png') == 'image'
assert _detect_format('data.xlsx') is None
print('All assertions passed.')
"
```

Expected: `All assertions passed.`

- [ ] **Step 2: Verify live graph still updates normally**

Run the app connected to the instrument (or with the serial port disconnected — the app tolerates a missing port). Confirm the rolling voltage/current graphs still update at ~50fps and the status bar shows live readings. The comparison panel below does not affect live plot performance.

- [ ] **Step 3: Final commit**

```bash
git add .
git commit -m "chore: finalize comparison panel integration"
```
