# Comparison Panel — Design Spec
**Date:** 2026-05-17
**Status:** Approved

## Overview

Add a replaceable comparison panel below the live voltage/current plots. The user can load a previously saved CSV or image file and view it alongside the active live graph. The panel can be swapped or cleared at any time without restarting the app.

---

## UI Changes

Two buttons are added to the existing button row in `main.py`:

- **"Load Comparison"** — opens a `QFileDialog` filtered to `.csv` and common image types (`.png`, `.jpg`, `.bmp`, `.gif`). Always visible.
- **"Clear Comparison"** — destroys the current comparison widget and hides the container. Only shown when a comparison is loaded.

A comparison container `QWidget` with a `QVBoxLayout` is inserted into the main `QVBoxLayout` below the existing `GraphicsLayoutWidget`. It is hidden by default and shown when a file is loaded.

---

## File Format Detection

Detection is by file extension (case-insensitive):

| Extension | Handler |
|---|---|
| `.csv` | CSV data path → `pg.GraphicsLayoutWidget` |
| `.png` `.jpg` `.bmp` `.gif` | Image path → `QLabel` + `QPixmap` |

Unsupported extensions show an error in the status label; no panel is opened.

---

## CSV Rendering

Columns read: `elapsed_seconds`, `voltage`, `current` (matches `logger.py` output).

A `pg.GraphicsLayoutWidget` is built with:
- Row 1: Voltage plot — magenta pen, width 2, label "Voltage (V)", grid on
- Row 2: Current plot — orange pen, width 2, label "Current (A)", grid on
- X-axis: `elapsed_seconds` from the CSV, starting at 0
- A `QLabel` filename header is placed above the `GraphicsLayoutWidget`

Colors (magenta / orange) are chosen to be visually distinct from the live traces (cyan / yellow).

---

## Image Rendering

A `QLabel` is created with the image loaded via `QPixmap`. It is scaled to fit the available width while preserving aspect ratio using `Qt.KeepAspectRatio`. A filename label is placed above the image.

---

## Swap / Clear Behavior

- **Swap:** Clicking "Load Comparison" while a panel is already loaded destroys the existing child widget(s) inside the container and rebuilds from the new file. The container stays visible.
- **Clear:** Clicking "Clear Comparison" destroys the child widget(s), hides the container, and hides the "Clear Comparison" button.

---

## Scope

All changes are confined to `main.py`. No new files are created. No changes to `logger.py`, `serial_worker.py`, `controls.py`, or `config.py`.
