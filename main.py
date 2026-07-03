import sys
import serial
import serial.tools.list_ports
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QComboBox, QPushButton, QTextEdit,
                               QFileDialog, QLineEdit, QSpinBox, QLabel)
from PySide6.QtCore import QThread, Signal, QTimer

# --- BACKGROUND THREAD FOR UART ---
class SerialReaderThread(QThread):
    data_received = Signal(str)

    def __init__(self, port, baudrate):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.serial_port = None
        self.is_running = False

    def run(self):
        try:
            self.serial_port = serial.Serial(self.port, self.baudrate, timeout=1)
            self.is_running = True
            
            while self.is_running:
                if self.serial_port.in_waiting > 0:
                    raw_data = self.serial_port.read(self.serial_port.in_waiting)
                    text_data = raw_data.decode('utf-8', errors='ignore')
                    self.data_received.emit(text_data)
                    
        except Exception as e:
            self.data_received.emit(f"\n[Error] {str(e)}\n")

    def write_data(self, data_bytes):
        if self.serial_port and self.serial_port.is_open:
            try:
                self.serial_port.write(data_bytes)
            except Exception as e:
                self.data_received.emit(f"\n[Write Error] {str(e)}\n")

    def stop(self):
        self.is_running = False
        self.wait() 
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()

# --- MAIN GUI WINDOW ---
class UartReaderApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simple UART Reader & Sender")
        self.resize(800, 600) 

        # Main Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # --- QTimer for Repeat Functionality ---
        self.repeat_timer = QTimer(self)
        self.repeat_timer.timeout.connect(self.execute_repeat_action)
        self.repeat_mode = None # Tracks if we are repeating "TEXT" or "SPECIAL"

        # -------------------------
        # TOP CONTROLS (Connection)
        # -------------------------
        top_controls = QHBoxLayout()
        
        self.port_combo = QComboBox()
        self.refresh_ports() 
        
        self.baud_combo = QComboBox()
        standard_baudrates = ["1200", "2400", "4800", "9600", "19200", "38400", 
                              "57600", "115200", "230400", "460800", "921600"]
        self.baud_combo.addItems(standard_baudrates)
        self.baud_combo.setCurrentText("115200")

        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.toggle_connection)

        self.save_btn = QPushButton("Save to File")
        self.save_btn.clicked.connect(self.save_to_file)

        self.clear_btn = QPushButton("Clear Output")
        self.clear_btn.clicked.connect(lambda: self.text_output.clear())

        top_controls.addWidget(self.port_combo)
        top_controls.addWidget(self.baud_combo)
        top_controls.addWidget(self.connect_btn)
        top_controls.addWidget(self.save_btn)
        top_controls.addWidget(self.clear_btn)

        # -------------------------
        # MIDDLE (Text Output)
        # -------------------------
        self.text_output = QTextEdit()
        self.text_output.setReadOnly(True)

        # -------------------------
        # BOTTOM CONTROLS (Standard Command)
        # -------------------------
        bottom_controls = QHBoxLayout()
        
        self.cmd_input = QLineEdit()
        self.cmd_input.setPlaceholderText("Type command here...")
        self.cmd_input.returnPressed.connect(self.send_command)
        self.cmd_input.setEnabled(False) 

        self.line_ending_combo = QComboBox()
        self.line_ending_combo.addItems(["No line ending", "Newline (\\n)", 
                                         "Carriage Return (\\r)", "Both (\\r\\n)"])
        self.line_ending_combo.setCurrentText("Newline (\\n)")
        self.line_ending_combo.setEnabled(False)

        self.send_btn = QPushButton("Send Text")
        self.send_btn.clicked.connect(self.send_command)
        self.send_btn.setEnabled(False)

        self.repeat_text_btn = QPushButton("Repeat Message")
        self.repeat_text_btn.clicked.connect(self.start_repeat_text)
        self.repeat_text_btn.setEnabled(False)

        bottom_controls.addWidget(self.cmd_input)
        bottom_controls.addWidget(self.line_ending_combo)
        bottom_controls.addWidget(self.send_btn)
        bottom_controls.addWidget(self.repeat_text_btn)

        # -------------------------
        # SPECIAL CHARACTERS ROW
        # -------------------------
        special_controls = QHBoxLayout()
        
        self.special_chars = {
            "Ctrl+C (Interrupt)": b'\x03',
            "Ctrl+D (EOF)": b'\x04',
            "Ctrl+Z (Suspend)": b'\x1A',
            "Escape (ESC)": b'\x1B',
            "Tab (TAB)": b'\x09'
        }
        
        self.special_combo = QComboBox()
        self.special_combo.addItems(self.special_chars.keys())
        self.special_combo.setEnabled(False)
        
        self.send_special_btn = QPushButton("Send Special Character")
        self.send_special_btn.clicked.connect(self.send_special_command)
        self.send_special_btn.setEnabled(False)

        self.repeat_special_btn = QPushButton("Repeat Special Char")
        self.repeat_special_btn.clicked.connect(self.start_repeat_special)
        self.repeat_special_btn.setEnabled(False)

        special_controls.addWidget(self.special_combo)
        special_controls.addWidget(self.send_special_btn)
        special_controls.addWidget(self.repeat_special_btn)
        special_controls.addStretch() 

        # -------------------------
        # REPEATER SETTINGS ROW
        # -------------------------
        repeater_settings = QHBoxLayout()
        
        self.interval_label = QLabel("Repeat Interval:")
        
        # QSpinBox allows safe integer input for milliseconds
        self.interval_spinbox = QSpinBox()
        self.interval_spinbox.setRange(10, 3600000) # From 10ms to 1 hour
        self.interval_spinbox.setValue(1000) # Default to 1 second (1000ms)
        self.interval_spinbox.setSuffix(" ms")
        self.interval_spinbox.setEnabled(False)

        self.stop_repeat_btn = QPushButton("Stop Repeat")
        self.stop_repeat_btn.setStyleSheet("background-color: #aa0000; color: white;") # Make it obvious
        self.stop_repeat_btn.clicked.connect(self.stop_repeater)
        self.stop_repeat_btn.setEnabled(False)

        repeater_settings.addWidget(self.interval_label)
        repeater_settings.addWidget(self.interval_spinbox)
        repeater_settings.addWidget(self.stop_repeat_btn)
        repeater_settings.addStretch()

        # Assemble the Main Layout
        layout.addLayout(top_controls)
        layout.addWidget(self.text_output)
        layout.addLayout(bottom_controls)
        layout.addLayout(special_controls) 
        layout.addLayout(repeater_settings)

        self.reader_thread = None

    def refresh_ports(self):
        self.port_combo.clear()
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.port_combo.addItem(port.device)

    def toggle_connection(self):
        if self.reader_thread is None or not self.reader_thread.isRunning():
            port = self.port_combo.currentText()
            baud = int(self.baud_combo.currentText())
            
            if not port:
                self.text_output.append("[System] No port selected.")
                return

            self.reader_thread = SerialReaderThread(port, baud)
            self.reader_thread.data_received.connect(self.append_data)
            self.reader_thread.start()
            
            # UI State updates
            self.connect_btn.setText("Disconnect")
            self.port_combo.setEnabled(False)
            self.baud_combo.setEnabled(False)
            self.set_interaction_enabled(True)
            self.cmd_input.setFocus() 
            
            self.text_output.append(f"[System] Connected to {port} at {baud} baud.\n")
        else:
            self.stop_repeater() # Ensure timer stops if we disconnect!
            self.reader_thread.stop()
            
            # UI State updates
            self.connect_btn.setText("Connect")
            self.port_combo.setEnabled(True)
            self.baud_combo.setEnabled(True)
            self.set_interaction_enabled(False)
            
            self.text_output.append("\n[System] Disconnected.\n")

    def set_interaction_enabled(self, state):
        """Helper to bulk enable/disable UI elements."""
        self.cmd_input.setEnabled(state)
        self.line_ending_combo.setEnabled(state)
        self.send_btn.setEnabled(state)
        self.repeat_text_btn.setEnabled(state)
        self.special_combo.setEnabled(state)
        self.send_special_btn.setEnabled(state)
        self.repeat_special_btn.setEnabled(state)
        self.interval_spinbox.setEnabled(state)

    def send_command(self):
        if self.reader_thread and self.reader_thread.isRunning():
            cmd = self.cmd_input.text()
            ending = self.line_ending_combo.currentText()
            
            if ending == "Newline (\\n)":
                cmd += "\n"
            elif ending == "Carriage Return (\\r)":
                cmd += "\r"
            elif ending == "Both (\\r\\n)":
                cmd += "\r\n"
                
            self.reader_thread.write_data(cmd.encode('utf-8'))
            self.append_data(f"--> [TX]: {cmd}")
            
            # Only clear the input box if we aren't in repeat mode
            if not self.repeat_timer.isActive():
                self.cmd_input.clear()
        else:
            self.text_output.append("[System] Cannot send. Not connected.")

    def send_special_command(self):
        if self.reader_thread and self.reader_thread.isRunning():
            char_name = self.special_combo.currentText()
            char_bytes = self.special_chars[char_name]
            
            self.reader_thread.write_data(char_bytes)
            self.append_data(f"\n--> [TX Special]: Sent {char_name}\n")
        else:
            self.text_output.append("[System] Cannot send. Not connected.")

    # --- REPEATER LOGIC ---
    def start_repeat_text(self):
        self.repeat_mode = "TEXT"
        self.send_command() # Send immediately once
        self.start_timer()

    def start_repeat_special(self):
        self.repeat_mode = "SPECIAL"
        self.send_special_command() # Send immediately once
        self.start_timer()

    def start_timer(self):
        interval_ms = self.interval_spinbox.value()
        self.repeat_timer.start(interval_ms)
        
        # Disable inputs so user doesn't conflict with repeating action
        self.set_interaction_enabled(False)
        self.stop_repeat_btn.setEnabled(True)
        self.text_output.append(f"[System] Started repeating every {interval_ms}ms...\n")

    def stop_repeater(self):
        if self.repeat_timer.isActive():
            self.repeat_timer.stop()
            self.set_interaction_enabled(True)
            self.stop_repeat_btn.setEnabled(False)
            self.text_output.append("\n[System] Repeating stopped.\n")

    def execute_repeat_action(self):
        """Triggered automatically by the QTimer."""
        if self.repeat_mode == "TEXT":
            self.send_command()
        elif self.repeat_mode == "SPECIAL":
            self.send_special_command()

    def append_data(self, text):
        cursor = self.text_output.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText(text)
        self.text_output.setTextCursor(cursor)

    def save_to_file(self):
        file_name, _ = QFileDialog.getSaveFileName(
            self, 
            "Save UART Output", 
            "", 
            "Text Files (*.txt);;Log Files (*.log);;All Files (*)"
        )
        if file_name:
            try:
                content = self.text_output.toPlainText()
                with open(file_name, 'w', encoding='utf-8') as file:
                    file.write(content)
                self.text_output.append(f"\n[System] Output successfully saved to: {file_name}\n")
            except Exception as e:
                self.text_output.append(f"\n[System Error] Failed to save file: {str(e)}\n")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = UartReaderApp()
    window.show()
    sys.exit(app.exec())
