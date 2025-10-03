# Importando as bibliotecas necessárias
from periphery import I2C
import time

# --- CONFIGURAÇÕES GERAIS ---
# O barramento I2C da Labrador, conforme os exemplos do seu slide [cite: 245]
# Verifique no pinout (página 2 do slide) se está usando os pinos corretos para i2c-2
I2C_BUS_PATH = "/dev/i2c-2"

# --- CONFIGURAÇÕES DO SENSOR AHT10 (Temperatura e Umidade) ---
AHT10_I2C_ADDRESS = 0x38 # Endereço padrão do AHT10 [cite: 246]

# Comandos baseados no datasheet e no seu slide [cite: 255, 278]
AHT10_CMD_INIT = [0xE1, 0x08, 0x00]
AHT10_CMD_MEASURE = [0xAC, 0x33, 0x00]

# --- CONFIGURAÇÕES DO SENSOR MAX30102 (Oxímetro e Batimentos) ---
# O endereço do MAX30102 é composto por um ID de 7 bits (0b1010111) e um bit de leitura/escrita. [cite: 1435]
# O endereço para escrita (R/W bit = 0) é 0xAE. No entanto, a biblioteca python-periphery usa o endereço de 7 bits, que é 0x57.
MAX30102_I2C_ADDRESS = 0x57

# Registradores do MAX30102 (baseado na datasheet, página 10) [cite: 965]
MAX30102_REG_MODE_CONFIG = 0x09
MAX30102_REG_SPO2_CONFIG = 0x0A
MAX30102_REG_LED_PULSE_AMP1 = 0x0C # IR
MAX30102_REG_LED_PULSE_AMP2 = 0x0D # Vermelho
MAX30102_REG_FIFO_DATA = 0x07
MAX30102_REG_FIFO_WR_PTR = 0x04
MAX30102_REG_FIFO_RD_PTR = 0x06

# --- FUNÇÕES PARA O SENSOR AHT10 ---

def aht10_init(i2c):
    """Inicializa o sensor AHT10, como no slide.""" [cite: 253]
    try:
        # Envia comando de inicialização [cite: 257]
        init_msg = I2C.Message(AHT10_CMD_INIT)
        i2c.transfer(AHT10_I2C_ADDRESS, [init_msg])
        time.sleep(0.02) # Aguarda 20ms para estabilização [cite: 258]
        print("Sensor AHT10 inicializado com sucesso.")
        return True
    except Exception as e:
        print(f"Erro ao inicializar AHT10: {e}")
        return False

def aht10_read(i2c):
    """Lê temperatura e umidade do sensor AHT10.""" [cite: 274]
    # Envia comando para iniciar medição [cite: 279]
    measure_msg = I2C.Message(AHT10_CMD_MEASURE)
    i2c.transfer(AHT10_I2C_ADDRESS, [measure_msg])
    time.sleep(0.08) # Aguarda 80ms para a conversão [cite: 280]

    # Lê os 6 bytes de dados do sensor [cite: 282]
    read_buf = [0] * 6
    read_msg = I2C.Message(read_buf, read=True)
    i2c.transfer(AHT10_I2C_ADDRESS, [read_msg])
    data = read_msg.data

    # Extrai os dados brutos de umidade e temperatura [cite: 287, 288]
    humidity_raw = ((data[1] << 16) | (data[2] << 8) | data[3]) >> 4
    temperature_raw = ((data[3] & 0x0F) << 16) | (data[4] << 8) | data[5]

    # Calcula umidade e temperatura reais usando as fórmulas do datasheet/slide [cite: 272, 289, 290]
    humidity = (humidity_raw / 1048576) * 100
    temperature = (temperature_raw / 1048576) * 200 - 50

    return temperature, humidity

# --- FUNÇÕES PARA O SENSOR MAX30102 ---

def max30102_init(i2c):
    """Inicializa e configura o sensor MAX30102."""
    try:
        # RESET (bit 6 = 1 no registro 0x09) [cite: 1165, 1166]
        i2c.transfer(MAX30102_I2C_ADDRESS, [I2C.Message([MAX30102_REG_MODE_CONFIG, 0x40])])
        time.sleep(0.1)

        # Configura o modo para SpO2 (Red e IR ativos, valor 0x03) 
        i2c.transfer(MAX30102_I2C_ADDRESS, [I2C.Message([MAX30102_REG_MODE_CONFIG, 0x03])])
        
        # Configuração do SpO2: ADC Range=16384nA, Sample Rate=100sps, LED Pulse Width=411us (ADC 18-bit) [cite: 1173, 1177, 1187, 1193]
        # SPO2_ADC_RGE=11, SPO2_SR=001, LED_PW=11 -> 0b01100111 = 0x67
        i2c.transfer(MAX30102_I2C_ADDRESS, [I2C.Message([MAX30102_REG_SPO2_CONFIG, 0x67])])
        
        # Configura a amplitude do pulso dos LEDs (brilho, 0x1F = 6.4mA) [cite: 1199, 1202]
        i2c.transfer(MAX30102_I2C_ADDRESS, [I2C.Message([MAX30102_REG_LED_PULSE_AMP1, 0x1F])]) # IR
        i2c.transfer(MAX30102_I2C_ADDRESS, [I2C.Message([MAX30102_REG_LED_PULSE_AMP2, 0x1F])]) # Red
        
        print("Sensor MAX30102 inicializado com sucesso.")
        return True
    except Exception as e:
        print(f"Erro ao inicializar MAX30102: {e}")
        return False

def max30102_read_raw(i2c):
    """Lê um conjunto de dados brutos (IR e Red) do FIFO do sensor."""
    # O sensor armazena amostras em um buffer (FIFO)[cite: 936]. Cada amostra tem 6 bytes (3 para IR, 3 para Red)[cite: 1054].
    # Vamos ler uma única amostra (6 bytes).
    read_buf = [0] * 6
    
    # Mensagens para apontar para o registrador de dados do FIFO (0x07) e depois ler 6 bytes
    write_msg = I2C.Message([MAX30102_REG_FIFO_DATA])
    read_msg = I2C.Message(read_buf, read=True)
    
    i2c.transfer(MAX30102_I2C_ADDRESS, [write_msg, read_msg])
    data = read_msg.data

    # Combina os 3 bytes para cada canal para obter os valores de 18 bits [cite: 1068, 1080]
    red_raw = (data[0] << 16) | (data[1] << 8) | data[2]
    ir_raw = (data[3] << 16) | (data[4] << 8) | data[5]

    return ir_raw, red_raw

# --- EXECUÇÃO PRINCIPAL ---
if __name__ == "__main__":
    try:
        # Inicializa o barramento I2C
        i2c = I2C(I2C_BUS_PATH)
        print(f"Barramento I2C em '{I2C_BUS_PATH}' aberto.")

        # Tenta inicializar os sensores
        aht10_ok = aht10_init(i2c)
        max30102_ok = max30102_init(i2c)

        # Loop principal para leitura contínua
        while True:
            if aht10_ok:
                temp, hum = aht10_read(i2c)
                print(f"AHT10 -> Temperatura: {temp:.2f} C, Umidade: {hum:.2f} %")

            if max30102_ok:
                ir, red = max30102_read_raw(i2c)
                print(f"MAX30102 -> Raw IR: {ir}, Raw Red: {red}")
                # AVISO: Calcular BPM e SpO2 a partir dos dados brutos é um processo complexo
                # que envolve algoritmos de processamento de sinal.
            
            print("-" * 30)
            time.sleep(1)

    except Exception as e:
        print(f"Ocorreu um erro geral: {e}")
    finally:
        # Fecha a conexão I2C ao sair
        if 'i2c' in locals():
            i2c.close()
            print("Conexão I2C fechada.")