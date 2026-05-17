import csv
import time

class CSVLogger:
    def __init__(self, filename):
        self.file = open(filename, "w", newline="")
        self.writer = csv.writer(self.file)

        self.writer.writerow([
            "timestamp",
            "elapsed_seconds",
            "voltage",
            "current"
        ])

        self.start_time = time.time()

    def log(self, voltage, current):
        elapsed = time.time() - self.start_time

        self.writer.writerow([
            time.strftime("%Y-%m-%d %H:%M:%S"),
            f"{elapsed:.3f}",
            f"{voltage:.6f}",
            f"{current:.6f}"
        ])

        self.file.flush()

    def close(self):
        self.file.close()