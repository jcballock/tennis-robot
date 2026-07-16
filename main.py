#!/usr/bin/env python3
import socket
import serial
import time

TEENSY_PORT = '/dev/ttyACM0'
BAUD_RATE = 115200
TEENSY_RECONNECT_DELAY = 5  # How often (in seconds) to retry Teensy connection if offline

def main():
    teensy = None
    
    # 1. Try to connect to Teensy with a 10-second timeout
    print(f"Connecting to Teensy on {TEENSY_PORT} (10-second timeout)...")
    start_time = time.time()
    
    while time.time() - start_time < 10:
        try:
            teensy = serial.Serial(TEENSY_PORT, BAUD_RATE, timeout=1)
            print("Connected to Teensy successfully!")
            break
        except serial.SerialException:
            time.sleep(1)
            
    if teensy is None:
        print("⚠️ Teensy connection timed out after 10 seconds. Continuing to Bluetooth setup...")

    # 2. Setup Native Bluetooth RFCOMM Socket
    server_sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
    server_sock.bind(("00:00:00:00:00:00", 1))  # Binds to any local adapter on channel 1
    server_sock.listen(1)

    print("Bluetooth server started. Ready for phone pairing/connection.")

    last_reconnect_attempt = 0

    while True:
        try:
            # Blocks until phone connects
            phone_sock, client_info = server_sock.accept()
            print(f"Phone connected from: {client_info}")
            phone_sock.setblocking(False)  # Non-blocking for smooth loop execution

            while True:
                current_time = time.time()

                # 3. Background Reconnection to Teensy (if it's offline)
                if teensy is None:
                    if current_time - last_reconnect_attempt > TEENSY_RECONNECT_DELAY:
                        last_reconnect_attempt = current_time
                        try:
                            teensy = serial.Serial(TEENSY_PORT, BAUD_RATE, timeout=1)
                            print("🔌 Teensy successfully connected/reconnected!")
                        except serial.SerialException:
                            pass  # Quietly fail and try again in 5 seconds

                # 4. Handle incoming data from phone (if Teensy is available)
                try:
                    data = phone_sock.recv(1024)
                    if len(data) == 0:
                        raise ConnectionResetError
                    
                    print(f"Received from Phone: {data.decode('utf-8', errors='ignore').strip()}")
                    
                    if teensy is not None:
                        teensy.write(data)
                        teensy.flush()
                    else:
                        print("⚠️ Cannot forward command: Teensy is currently offline.")
                        phone_sock.send(b"Error: Teensy offline\r\n")
                        
                except BlockingIOError:
                    pass  # No data from phone right now, proceed

                # 5. Handle incoming data from Teensy to forward back to phone
                if teensy is not None:
                    try:
                        if teensy.in_waiting > 0:
                            reply = teensy.readline()
                            phone_sock.send(reply)
                    except serial.SerialException:
                        print("⚠️ Teensy connection lost!")
                        teensy.close()
                        teensy = None  # Flag for reconnection loop

                time.sleep(0.01)  # Limit CPU usage

        except (ConnectionResetError, OSError):
            print("Phone disconnected. Waiting for a new connection...")
            try:
                phone_sock.close()
            except NameError:
                pass

if __name__ == '__main__':
    main()
