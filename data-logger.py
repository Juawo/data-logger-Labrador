# Código adaptado para dois barramentos I2C
from periphery import I2C
import time

# --- CONFIGURAÇÕES DOS BARRAMENTOS ---
# Barramento para o AHT10 (Pinos 3 e 5)
I2C_BUS_AHT10_PATH = "/dev/i2c-2"
# Barramento para o MAX30102 (Pinos 8 e 10)
I2C_BUS_MAX_PATH = "/dev/i2c-0"

# --- CONFIGURAÇÕES DO SENSOR AHT10 ---
AHT10_I2C_ADDRESS = 0x38

# --- CONFIGURAÇÕES DO SENSOR MAX30102 ---
MAX30102_I2C_ADDRESS = 0x57

# --- (O restante das constantes e funções permanecem as mesmas) ---
AHT10_CMD_INIT = [0xE1, 0x08, 0x00]
AHT10_CMD_MEASURE = [0xAC, 0x33, 0x00]
MAX30102_REG_MODE_CONFIG = 0x09
MAX30102_REG_SPO2_CONFIG = 0x0A
MAX30102_REG_LED_PULSE_AMP1 = 0x0C
MAX30102_REG_LED_PULSE_AMP2 = 0x0D
MAX30102_REG_FIFO_DATA = 0x07

def aht10_init(i2c):
    try:
        i2c.transfer(AHT10_I2C_ADDRESS, [I2C.Message(AHT10_CMD_INIT)])
        time.sleep(0.02)
        print("Sensor AHT10 inicializado com sucesso.")
        return True
    except Exception as e:
        print(f"Erro ao inicializar AHT10: {e}")
        return False

def aht10_read(i2c):
    i2c.transfer(AHT10_I2C_ADDRESS, [I2C.Message(AHT10_CMD_MEASURE)])
    time.sleep(0.08)
    read_buf = [0] * 6
    read_msg = I2C.Message(read_buf, read=True)
    i2c.transfer(AHT10_I2C_ADDRESS, [read_msg])
    data = read_msg.data
    humidity_raw = ((data[1] << 16) | (data[2] << 8) | data[3]) >> 4
    temperature_raw = ((data[3] & 0x0F) << 16) | (data[4] << 8) | data[5]
    humidity = (humidity_raw / 1048576) * 100
    temperature = (temperature_raw / 1048576) * 200 - 50
    return temperature, humidity

def max30102_init(i2c):
    try:
        i2c.transfer(MAX30102_I2C_ADDRESS, [I2C.Message([MAX30102_REG_MODE_CONFIG, 0x40])])
        time.sleep(0.1)
        i2c.transfer(MAX30102_I2C_ADDRESS, [I2C.Message([MAX30102_REG_MODE_CONFIG, 0x03])])
        i2c.transfer(MAX30102_I2C_ADDRESS, [I2C.Message([MAX30102_REG_SPO2_CONFIG, 0x67])])
        i2c.transfer(MAX30102_I2C_ADDRESS, [I2C.Message([MAX30102_REG_LED_PULSE_AMP1, 0x1F])])
        i2c.transfer(MAX30102_I2C_ADDRESS, [I2C.Message([MAX30102_REG_LED_PULSE_AMP2, 0x1F])])
        print("Sensor MAX30102 inicializado com sucesso.")
        return True
    except Exception as e:
        print(f"Erro ao inicializar MAX30102: {e}")
        return False

def max30102_read_raw(i2c):
    read_buf = [0] * 6
    write_msg = I2C.Message([MAX30102_REG_FIFO_DATA])
    read_msg = I2C.Message(read_buf, read=True)
    i2c.transfer(MAX30102_I2C_ADDRESS, [write_msg, read_msg])
    data = read_msg.data
    red_raw = (data[0] << 16) | (data[1] << 8) | data[2]
    ir_raw = (data[3] << 16) | (data[4] << 8) | data[5]
    return ir_raw, red_raw

# --- EXECUÇÃO PRINCIPAL ---
if __name__ == "__main__":
    i2c_aht10 = None
    i2c_max = None
    try:
        # Abre os dois barramentos I2C separadamente
        i2c_aht10 = I2C(I2C_BUS_AHT10_PATH)
        i2c_max = I2C(I2C_BUS_MAX_PATH)
        print(f"Barramento AHT10 em '{I2C_BUS_AHT10_PATH}' aberto.")
        print(f"Barramento MAX30102 em '{I2C_BUS_MAX_PATH}' aberto.")

        # Inicializa cada sensor em seu respectivo barramento
        aht10_ok = aht10_init(i2c_aht10)
        max30102_ok = max30102_init(i2c_max)

        while True:
            # Lê cada sensor usando seu próprio objeto i2c
            if aht10_ok:
                temp, hum = aht10_read(i2c_aht10)
                print(f"AHT10 -> Temperatura: {temp:.2f} C, Umidade: {hum:.2f} %")

            if max30102_ok:
                ir, red = max30102_read_raw(i2c_max)
                print(f"MAX30102 -> Raw IR: {ir}, Raw Red: {red}")
            
            print("-" * 30)
            time.sleep(1)

    except Exception as e:
        print(f"Ocorreu um erro geral: {e}")
    finally:
        # Fecha ambas as conexões
        if i2c_aht10:
            i2c_aht10.close()
            print("Conexão I2C AHT10 fechada.")
        if i2c_max:
            i2c_max.close()
            print("Conexão I2C MAX30102 fechada.")