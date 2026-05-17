import threading
import time
import serial

class SerialWorker(threading.Thread):

    def __init__(
        self,
        port,
        baudrate,
        poll_interval,
        callback
    ):
        super().__init__(daemon=True)

        self.callback = callback
        self.poll_interval = poll_interval
        self.running = True
        self._lock = threading.Lock()

        self.ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            xonxoff=True,
            timeout=1
        )

    def query(self, cmd):
        with self._lock:
            self.ser.reset_input_buffer()
            self.ser.write((cmd + '\r\n').encode())
            return self.ser.readline().decode().strip()

    def write(self, cmd):
        with self._lock:
            self.ser.write((cmd + '\r\n').encode())

    def run(self):

        try:
            print(self.query("*IDN?"))
        except Exception as e:
            print("Connection Error:", e)

        while self.running:

            try:
                v_str = self.query("MEAS:VOLT?")
                c_str = self.query("MEAS:CURR?")

                if not v_str or not c_str:
                    print("No response from instrument (timeout)")
                    continue

                self.callback(float(v_str), float(c_str))

            except ValueError as e:
                print("Parse Error:", e)
            except Exception as e:
                print("Read Error:", e)

            time.sleep(self.poll_interval)

    def output_on(self):
        self.write("OUTP ON")

    def output_off(self):
        self.write("OUTP OFF")

    def set_voltage(self, value):
        self.write(f"VOLT {value}")

    def set_current(self, value):
        self.write(f"CURR {value}")

    def stop(self):
        self.running = False
        self.ser.close()