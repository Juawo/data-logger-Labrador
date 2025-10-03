from periphery import I2C
import time
from datetime import datetime

LOG_PATH = "/media/sdcard/datalog_oxibat.txt"
MAX30102_ADDR = 0x57

i2c = I2C("/dev/i2c-2")  # ajuste se for i2c-1

def write_reg(addr, reg, value):
    msgs = [I2C.Message([reg, value])]
    i2c.transfer(addr, msgs)

def read_reg(addr, reg):
    msgs = [I2C.Message([reg], read=False), I2C.Message([0x00], read=True)]
    i2c.transfer(addr, msgs)
    return msgs[1].data[0]

def init_max30102():
    part_id = read_reg(MAX30102_ADDR, 0xFF)
    print(f"MAX30102 PART ID: {part_id:#x}")

    # Reset
    write_reg(MAX30102_ADDR, 0x09, 0x40)
    time.sleep(0.1)

    # Config SPO2
    write_reg(MAX30102_ADDR, 0x0A, 0x27)  # SPO2 config: 100Hz, 411us, 18-bit
    write_reg(MAX30102_ADDR, 0x09, 0x03)  # Mode: Red + IR

def read_fifo():
    # Lê 6 bytes da FIFO (Red e IR)
    msgs = [I2C.Message([0x07], read=False), I2C.Message([0x00]*6, read=True)]
    i2c.transfer(MAX30102_ADDR, msgs)
    data = msgs[1].data
    red = (data[0] << 16) | (data[1] << 8) | data[2]
    ir = (data[3] << 16) | (data[4] << 8) | data[5]
    return red & 0x3FFFF, ir & 0x3FFFF

def log_data():
    red, ir = read_fifo()
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    log_line = (
        f"--- Registro {timestamp} ---\n"
        f"RED: {red}\n"
        f"IR : {ir}\n"
        f"-----------------------------\n\n"
    )

    with open(LOG_PATH, "a") as f:
        f.write(log_line)

    print(log_line)

if __name__ == "__main__":
    try:
        init_max30102()
        while True:
            log_data()
            time.sleep(1)
    except KeyboardInterrupt:
        i2c.close()
