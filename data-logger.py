import smbus2
import time
import datetime

# ==========================================================
# CONFIGURAÇÕES GERAIS
# ==========================================================
I2C_BUS_NUMBER = 2  # Apenas o número do barramento I2C (/dev/i2c-2)
bus = smbus2.SMBus(I2C_BUS_NUMBER)

# ATENÇÃO: Verifique e corrija o caminho para o seu cartão SD!
# O nome 'CARTAO M' pode precisar ser ajustado. Use 'ls /media/caninos/' para ver o nome correto.
LOG_FILE = "/media/sdcard/dados_sensores.txt"

# ==========================================================
# SEÇÃO: SENSOR AHT10 (Temperatura e Umidade)
# ==========================================================
AHT10_ADDRESS = 0x38
AHT10_CMD_INIT = [0xE1, 0x08, 0x00]
AHT10_CMD_MEASURE = [0xAC, 0x33, 0x00]

def init_aht10():
    """Inicializa o AHT10 (calibração)."""
    try:
        # A biblioteca smbus2 não tem um comando de escrita simples, então usamos um truque
        # enviando o comando como se estivéssemos escrevendo no 'registro' 0xE1
        bus.write_i2c_block_data(AHT10_ADDRESS, AHT10_CMD_INIT[0], AHT10_CMD_INIT[1:])
        time.sleep(0.02)
        print("Sensor AHT10 inicializado.")
        return True
    except Exception as e:
        print(f"Erro ao inicializar AHT10: {e}")
        return False

def read_aht10():
    """Lê temperatura (°C) e umidade (%) do AHT10."""
    try:
        # Envia o comando de medição
        bus.write_i2c_block_data(AHT10_ADDRESS, AHT10_CMD_MEASURE[0], AHT10_CMD_MEASURE[1:])
        time.sleep(0.08)

        # Lê os 6 bytes de dados
        data = bus.read_i2c_block_data(AHT10_ADDRESS, 0x00, 6) # O 0x00 é um placeholder

        hum_raw = ((data[1] << 16) | (data[2] << 8) | data[3]) >> 4
        temp_raw = ((data[3] & 0x0F) << 16) | (data[4] << 8) | data[5]

        humidity = (hum_raw / 1048576) * 100
        temperature = (temp_raw / 1048576) * 200 - 50
        return temperature, humidity
    except Exception as e:
        # print(f"Erro na leitura do AHT10: {e}") # Descomente para depurar
        return None

# ==========================================================
# SEÇÃO: SENSOR MAX30102 (Oxímetro e Batimentos)
# ==========================================================
MAX30102_ADDRESS = 0x57
MAX30102_REG_MODE_CONFIG = 0x09
MAX30102_REG_SPO2_CONFIG = 0x0A
MAX30102_REG_LED_PULSE_AMP1 = 0x0C # IR
MAX30102_REG_LED_PULSE_AMP2 = 0x0D # Vermelho
MAX30102_REG_FIFO_DATA = 0x07

def init_max30102():
    """Inicializa e configura o MAX30102."""
    try:
        # Reset
        bus.write_byte_data(MAX30102_ADDRESS, MAX30102_REG_MODE_CONFIG, 0x40)
        time.sleep(0.1)
        # Modo SpO2
        bus.write_byte_data(MAX30102_ADDRESS, MAX30102_REG_MODE_CONFIG, 0x03)
        # Config SpO2 (ADC Range, Sample Rate, etc)
        bus.write_byte_data(MAX30102_ADDRESS, MAX30102_REG_SPO2_CONFIG, 0x67)
        # Brilho dos LEDs
        bus.write_byte_data(MAX30102_ADDRESS, MAX30102_REG_LED_PULSE_AMP1, 0x1F) # IR
        bus.write_byte_data(MAX30102_ADDRESS, MAX30102_REG_LED_PULSE_AMP2, 0x1F) # Vermelho
        print("Sensor MAX30102 inicializado.")
        return True
    except Exception as e:
        print(f"Erro ao inicializar MAX30102: {e}")
        return False

def read_max30102_raw():
    """Lê dados brutos (IR e Red) do MAX30102."""
    try:
        # Lê 6 bytes a partir do registrador de dados do FIFO (0x07)
        data = bus.read_i2c_block_data(MAX30102_ADDRESS, MAX30102_REG_FIFO_DATA, 6)
        
        red_raw = (data[0] << 16) | (data[1] << 8) | data[2]
        ir_raw = (data[3] << 16) | (data[4] << 8) | data[5]
        return ir_raw, red_raw
    except Exception as e:
        # print(f"Erro na leitura do MAX30102: {e}") # Descomente para depurar
        return None

# ==========================================================
# FUNÇÃO MAIN
# ==========================================================
def main():
    """Loop principal de leitura dos sensores."""
    # Inicializa os sensores
    aht10_ok = init_aht10()
    max30102_ok = init_max30102()

    try:
        while True:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Faz a leitura de cada sensor
            aht_data = read_aht10()
            max_data = read_max30102_raw()
            
            # Formata a string de log para o AHT10
            if aht_data:
                aht_str = f"Temp: {aht_data[0]:.1f} C, Umid: {aht_data[1]:.1f}%"
            else:
                aht_str = "AHT10: Falha na leitura"

            # Formata a string de log para o MAX30102
            if max_data:
                max_str = f"IR: {max_data[0]}, Red: {max_data[1]}"
            else:
                max_str = "MAX30102: Falha na leitura"
           
            log_line = f"[{timestamp}] {aht_str} | {max_str}"

            print(log_line)
            try:
                with open(LOG_FILE, "a") as f:
                    f.write(log_line + "\n")
            except Exception as e:
                print(f"ERRO AO ESCREVER NO ARQUIVO: {e}")

            time.sleep(1)
    except KeyboardInterrupt:
        print("\nLeitura encerrada pelo usuário.")
    finally:
        bus.close()
        print("Barramento I2C fechado.")

# ==========================================================
# PONTO DE ENTRADA
# ==========================================================
if __name__ == "__main__":
    main()