import sys
import serial
import serial.tools.list_ports
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QComboBox, QPushButton, QTextEdit,
                               QFileDialog)
from PySide6.QtCore import QThread, Signal

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

    def stop(self):
        self.is_running = False
        self.wait() 
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()

# --- MAIN GUI WINDOW ---
class UartReaderApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simple UART Reader")
        self.resize(700, 450)

        # Main Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Top Controls Layout
        controls_layout = QHBoxLayout()
        
        # 1. Port Selector
        self.port_combo = QComboBox()
        self.refresh_ports() 
        
        # 2. Expanded Baudrate Selector
        self.baud_combo = QComboBox()
        standard_baudrates = [
            "1200", "2400", "4800", "9600", "19200", "38400", 
            "57600", "115200", "230400", "460800", "921600"
        ]
        self.baud_combo.addItems(standard_baudrates)
        self.baud_combo.setCurrentText("115200") # Default

        # 3. Connect Button
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.toggle_connection)

        # 4. Save to File Button
        self.save_btn = QPushButton("Save to File")
        self.save_btn.clicked.connect(self.save_to_file)

        # Add controls to the horizontal layout
        controls_layout.addWidget(self.port_combo)
        controls_layout.addWidget(self.baud_combo)
        controls_layout.addWidget(self.connect_btn)
        controls_layout.addWidget(self.save_btn)

        # Output Text Area
        self.text_output = QTextEdit()
        self.text_output.setReadOnly(True)

        layout.addLayout(controls_layout)
        layout.addWidget(self.text_output)

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
            
            self.connect_btn.setText("Disconnect")
            self.port_combo.setEnabled(False)
            self.baud_combo.setEnabled(False)
            self.text_output.append(f"[System] Connected to {port} at {baud} baud.\n")
        else:
            self.reader_thread.stop()
            self.connect_btn.setText("Connect")
            self.port_combo.setEnabled(True)
            self.baud_combo.setEnabled(True)
            self.text_output.append("\n[System] Disconnected.\n")

    def append_data(self, text):
        cursor = self.text_output.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText(text)
        self.text_output.setTextCursor(cursor)

    def save_to_file(self):
        # Open a native Ubuntu file dialog
        file_name, _ = QFileDialog.getSaveFileName(
            self, 
            "Save UART Output", 
            "", 
            "Text Files (*.txt);;Log Files (*.log);;All Files (*)"
        )
        
        if file_name:
            try:
                # Read all text from the UI and write it to the chosen file
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
