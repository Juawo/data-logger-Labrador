import time
import datetime
from periphery import I2C

# --- CONFIGURAÇÕES GERAIS ---
# Usando o barramento I2C que sabemos que funciona
I2C_BUS_PATH = "/dev/i2c-2"

# Caminho do arquivo de log no cartão SD, conforme solicitado
LOG_FILE = "/media/sdcard/dados_sensores.txt"

# --- CONFIGURAÇÕES DO SENSOR MAX30102 (Oxímetro e Batimentos) ---
MAX30102_I2C_ADDRESS = 0x57

# Registradores do MAX30102
MAX30102_REG_MODE_CONFIG = 0x09
MAX30102_REG_SPO2_CONFIG = 0x0A
MAX30102_REG_LED_PULSE_AMP1 = 0x0C # IR
MAX30102_REG_LED_PULSE_AMP2 = 0x0D # Vermelho
MAX30102_REG_FIFO_DATA = 0x07

# --- FUNÇÕES PARA O SENSOR MAX30102 ---
def max30102_init(i2c):
    """Inicializa e configura o sensor MAX30102."""
    try:
        # Reset
        i2c.transfer(MAX30102_I2C_ADDRESS, [I2C.Message([MAX30102_REG_MODE_CONFIG, 0x40])])
        time.sleep(0.1)
        # Configura o modo para SpO2 (Red e IR ativos)
        i2c.transfer(MAX30102_I2C_ADDRESS, [I2C.Message([MAX30102_REG_MODE_CONFIG, 0x03])])
        # Configuração do SpO2 (ADC Range, Sample Rate, LED Pulse Width)
        i2c.transfer(MAX30102_I2C_ADDRESS, [I2C.Message([MAX30102_REG_SPO2_CONFIG, 0x67])])
        # Configura a amplitude do pulso dos LEDs (brilho médio)
        i2c.transfer(MAX30102_I2C_ADDRESS, [I2C.Message([MAX30102_REG_LED_PULSE_AMP1, 0x3F])]) # IR
        i2c.transfer(MAX30102_I2C_ADDRESS, [I2C.Message([MAX30102_REG_LED_PULSE_AMP2, 0x3F])]) # Red
        print("Sensor MAX30102 inicializado com sucesso.")
        return True
    except Exception as e:
        print(f"Erro ao inicializar MAX30102: {e}")
        return False

def max30102_read_raw(i2c):
    """Lê um conjunto de dados brutos (IR e Red) do FIFO do sensor."""
    try:
        read_buf = [0] * 6
        write_msg = I2C.Message([MAX30102_REG_FIFO_DATA])
        read_msg = I2C.Message(read_buf, read=True)
        i2c.transfer(MAX30102_I2C_ADDRESS, [write_msg, read_msg])
        data = read_msg.data

        # Os dados no FIFO do MAX30102 vêm em 6 bytes: 3 para Red, 3 para IR
        red_raw = (data[0] << 16) | (data[1] << 8) | data[2]
        ir_raw = (data[3] << 16) | (data[4] << 8) | data[5]
        return ir_raw, red_raw
    except Exception:
        return None

# --- EXECUÇÃO PRINCIPAL ---
if __name__ == "__main__":
    i2c = None
    try:
        i2c = I2C(I2C_BUS_PATH)
        print(f"Barramento I2C em '{I2C_BUS_PATH}' aberto.")

        max30102_ok = max30102_init(i2c)

        if not max30102_ok:
            print("Não foi possível inicializar o sensor. Encerrando.")
        else:
            print("Iniciando leitura de dados. Pressione Ctrl+C para parar.")
            while True:
                max_data = max30102_read_raw(i2c)
                
                if max_data:
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    ir_value, red_value = max_data
                    
                    log_line = f"[{timestamp}] Raw IR: {ir_value}, Raw Red: {red_value}"
                    
                    print(log_line)
                    
                    # Salva a linha no arquivo de log, adicionando no final (modo 'a')
                    try:
                        with open(LOG_FILE, "a") as f:
                            f.write(log_line + "\n")
                    except Exception as e:
                        print(f"!!! ERRO AO ESCREVER NO ARQUIVO {LOG_FILE}: {e}")
                else:
                    print("Falha na leitura do MAX30102.")

                time.sleep(1)

    except KeyboardInterrupt:
        print("\nPrograma encerrado pelo usuário.")
    except Exception as e:
        print(f"Ocorreu um erro geral: {e}")
    finally:
        if i2c:
            i2c.close()
            print("Conexão I2C fechada.")