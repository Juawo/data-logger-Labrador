from periphery import I2C
import time
from datetime import datetime

LOG_PATH = "/media/sdcard/datalog_temp_umd.txt"
AHT10_ADDR = 0x38

i2c = I2C("/dev/i2c-2")  # ajuste se for i2c-1 na Labrador

def read_aht10():
    # Inicializa leitura
    msgs = [I2C.Message([0xAC, 0x33, 0x00])]
    i2c.transfer(AHT10_ADDR, msgs)
    time.sleep(0.08)

    # Lê 6 bytes
    msgs = [I2C.Message([0x00], read=False), I2C.Message([0x00]*6, read=True)]
    i2c.transfer(AHT10_ADDR, msgs)
    data = msgs[1].data

    raw_humi = ((data[1] << 12) | (data[2] << 4) | (data[3] >> 4))
    raw_temp = (((data[3] & 0x0F) << 16) | (data[4] << 8) | data[5])

    humi = (raw_humi / (1 << 20)) * 100.0
    temp = (raw_temp / (1 << 20)) * 200.0 - 50
    return round(temp, 2), round(humi, 2)

def log_data():
    temp, humi = read_aht10()
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    log_line = (
        f"--- Registro {timestamp} ---\n"
        f"Temperatura : {temp:.2f} °C\n"
        f"Umidade     : {humi:.2f} %\n"
        f"-----------------------------\n\n"
    )

    with open(LOG_PATH, "a") as f:
        f.write(log_line)

    print(log_line)

if __name__ == "__main__":
    try:
        while True:
            log_data()
            time.sleep(5)
    except KeyboardInterrupt:
        i2c.close()
