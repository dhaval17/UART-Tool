# Simple UART Reader

A lightweight, GUI-based serial port reader built with Python and PySide6 (Qt). Designed specifically for Linux (tested on Ubuntu 26.04), this application allows you to connect to serial devices, monitor data in real-time, and save logs to file.

## Prerequisites

Before installing the application, ensure your system has the required dependencies and permissions.

1. **Python 3 & Virtual Environments:**
   Ubuntu 26.04 restricts system-wide `pip` installations. You will need the Python 3 virtual environment package:
   ```bash
   sudo apt update
   sudo apt install python3-venv
   ```

2. **Hardware Permissions (Important):**
   By default, Linux does not allow standard users to read from serial ports (like `/dev/ttyUSB0`). You must add your user to the `dialout` group to use this application without `sudo`.
   ```bash
   sudo usermod -a -G dialout $USER
   ```

   *Note: You **must** log out and log back in (or reboot) for this permission change to take effect.*

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/dhaval17/UART-Tool.git
   cd UART-Tool
   ```

2. **Create a virtual environment:**
   ```bash
   python3 -m venv uart_env
   ```

3. **Activate the virtual environment:**
   ```bash
   source uart_env/bin/activate
   ```

4. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

Whenever you want to run the application, ensure your virtual environment is active.

1. Open your terminal in the project directory.
2. Activate the environment (if it isn't already):
   ```bash
   source uart_env/bin/activate
   ```

3. Run the main script:
   ```bash
   python main.py
   ```

## Features

* **Auto-Detection:** Automatically populates a dropdown with available serial ports.
* **Expanded Baudrates:** Supports standard baudrates from 1200 up to 921600.
* **Non-Blocking UI:** Utilizes `QThread` to ensure the graphical interface remains responsive while reading high-speed serial data.
* **Save to File:** Export your serial monitor logs to a `.txt` or `.log` file natively.
* **Port and Baudrate Selection:** Easy-to-use combo boxes to select your desired port and communication speed.
* **Connect/Disconnect Toggle:** Simple button to establish or terminate serial connections.
* **Write Ability:** Send data to the serial device with support for repeat functionality and special character sequences.
* **Special Character Support:** Handle repeated characters and escape sequences (e.g., `\n`, `\r`, `\t`) for flexible message transmission.

## How to Use

1. **Select a Serial Port:** Use the top-left dropdown to select your serial device (e.g., `/dev/ttyUSB0`).
2. **Choose Baudrate:** Select your desired baudrate from the dropdown (default: 115200).
3. **Connect:** Click the "Connect" button to start reading data. The button will change to "Disconnect".
4. **Monitor Data:** View incoming serial data in the text area in real-time.
5. **Write Messages:** Send custom messages to the device with support for:
   - Repeating messages multiple times
   - Special character sequences (\n for newline, \r for carriage return, \t for tab, etc.)
   - Raw character transmission
6. **Save Output:** Click "Save to File" to export the current output to a `.txt` or `.log` file.
7. **Disconnect:** Click "Disconnect" when finished to close the serial connection.

## Troubleshooting

* **Error: `[Errno 13] Permission denied: '/dev/ttyUSB0'`**
  You forgot to add your user to the `dialout` group, or you haven't rebooted/logged out since doing so. Refer to the Prerequisites section.

* **No ports showing up?**
  Ensure your USB-to-Serial adapter or microcontroller is properly plugged in. You can verify the system sees it by running `ls /dev/tty*` in your terminal and looking for `ttyUSB` or `ttyACM` devices.

* **Application is freezing or unresponsive?**
  The application uses background threads to keep the UI responsive. If issues persist, try restarting the application.

* **Data not displaying correctly?**
  Verify that you've selected the correct baudrate. Mismatched baudrates will result in garbled output.

* **Special characters not being transmitted correctly?**
  Ensure that your message format is correct. Use proper escape sequences (e.g., `\n` for newline) and check that the receiving device expects the same character encoding.

## License

This project is open source. Feel free to fork, modify, and use as needed.

## Contributing

Bug reports and feature requests are welcome! Please open an issue on GitHub if you encounter any problems or have suggestions for improvements.
