from periphery import I2C
import time
import os
from datetime import datetime

# Caminho do log
LOG_PATH = "/media/sdcard/datalog_sensores.txt"

# Endereços I2C (dependem do sensor)
AHT10_ADDR = 0x38
MAX30102_ADDR = 0x57

# Inicializa I2C no /dev/i2c-0 (confirmar com "ls /dev/i2c-*")
i2c = I2C("/dev/i2c-0")

def read_aht10():
    """Leitura de temperatura e umidade do AHT10"""
    # Inicia medição
    msgs = [I2C.Message([0xAC, 0x33, 0x00])]
    i2c.transfer(AHT10_ADDR, msgs)
    time.sleep(0.08)  # tempo de conversão típico ~75ms

    # Lê 6 bytes
    msgs = [I2C.Message([0x00], read=False), I2C.Message([0x00]*6, read=True)]
    i2c.transfer(AHT10_ADDR, msgs)
    data = msgs[1].data

    raw_humi = ((data[1] << 12) | (data[2] << 4) | (data[3] >> 4))
    raw_temp = (((data[3] & 0x0F) << 16) | (data[4] << 8) | data[5])

    humi = (raw_humi / (1 << 20)) * 100.0
    temp = (raw_temp / (1 << 20)) * 200.0 - 50
    return round(temp, 2), round(humi, 2)

def read_max30102():
    """Leitura simplificada do MAX30102 (apenas exemplo)"""
    # Configuração mínima pode ser feita escrevendo nos registradores
    # Aqui apenas lemos o ID do chip como teste
    msgs = [I2C.Message([0xFF], read=False), I2C.Message([0x00], read=True)]
    i2c.transfer(MAX30102_ADDR, msgs)
    part_id = msgs[1].data[0]
    return part_id  # no real: ler FIFO, calcular BPM/SpO2

def log_data():
    temp, humi = read_aht10()
    bpm = 0
    spo2 = 0
    try:
        bpm = read_max30102()  # placeholder (usar algoritmo real depois)
    except Exception:
        pass

    timestamp = datetime.utcnow().isoformat()
    log_line = f"{timestamp},{temp},{humi},{bpm},{spo2}\n"

    with open(LOG_PATH, "a") as f:
        f.write(log_line)

    print("Log:", log_line.strip())

if __name__ == "__main__":
    try:
        while True:
            log_data()
            time.sleep(5)  # intervalo de 5 segundos
    except KeyboardInterrupt:
        i2c.close()
        print("Encerrado.")
