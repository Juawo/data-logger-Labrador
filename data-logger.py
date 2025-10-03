# Importando as bibliotecas necessárias
from periphery import I2C
import time

# --- CONFIGURAÇÕES GERAIS ---
# O barramento I2C da Labrador, conforme os exemplos do seu slide
I2C_BUS_PATH = "/dev/i2c-2"

# --- CONFIGURAÇÕES DO SENSOR AHT10 (Temperatura e Umidade) ---
AHT10_I2C_ADDRESS = 0x38 # Endereço padrão do AHT10

# Comandos baseados no datasheet e no seu slide
AHT10_CMD_INIT = [0xE1, 0x08, 0x00]
AHT10_CMD_MEASURE = [0xAC, 0x33, 0x00]

# --- CONFIGURAÇÕES DO SENSOR MAX30102 (Oxímetro e Batimentos) ---
MAX30102_I2C_ADDRESS = 0x57 # Endereço I2C de 7 bits do MAX30102

# Registradores do MAX30102
MAX30102_REG_MODE_CONFIG = 0x09
MAX30102_REG_SPO2_CONFIG = 0x0A
MAX30102_REG_LED_PULSE_AMP1 = 0x0C # IR
MAX30102_REG_LED_PULSE_AMP2 = 0x0D # Vermelho
MAX30102_REG_FIFO_DATA = 0x07

# --- FUNÇÕES PARA O SENSOR AHT10 ---

def aht10_init(i2c):
    """Inicializa o sensor AHT10."""
    try:
        init_msg = I2C.Message(AHT10_CMD_INIT)
        i2c.transfer(AHT10_I2C_ADDRESS, [init_msg])
        time.sleep(0.02)
        print("Sensor AHT10 inicializado com sucesso.")
        return True
    except Exception as e:
        print(f"Erro ao inicializar AHT10: {e}")
        return False

def aht10_read(i2c):
    """Lê temperatura e umidade do sensor AHT10."""
    measure_msg = I2C.Message(AHT10_CMD_MEASURE)
    i2c.transfer(AHT10_I2C_ADDRESS, [measure_msg])
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

# --- FUNÇÕES PARA O SENSOR MAX30102 ---

def max30102_init(i2c):
    """Inicializa e configura o sensor MAX30102."""
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
    """Lê um conjunto de dados brutos (IR e Red) do FIFO do sensor."""
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
    try:
        i2c = I2C(I2C_BUS_PATH)
        print(f"Barramento I2C em '{I2C_BUS_PATH}' aberto.")

        aht10_ok = aht10_init(i2c)
        max30102_ok = max30102_init(i2c)

        while True:
            if aht10_ok:
                temp, hum = aht10_read(i2c)
                print(f"AHT10 -> Temperatura: {temp:.2f} C, Umidade: {hum:.2f} %")

            if max30102_ok:
                ir, red = max30102_read_raw(i2c)
                print(f"MAX30102 -> Raw IR: {ir}, Raw Red: {red}")
            
            print("-" * 30)
            time.sleep(1)

    except Exception as e:
        print(f"Ocorreu um erro geral: {e}")
    finally:
        if 'i2c' in locals():
            i2c.close()
            print("Conexão I2C fechada.")