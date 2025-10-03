
from periphery import I2C
import time

I2C_BUS_PATH = "/dev/i2c-2"
AHT10_I2C_ADDRESS = 0x38
AHT10_CMD_SOFT_RESET = 0xBA

print("--- Iniciando Teste Mínimo para o AHT10 ---")
i2c = None  # Inicializa a variável fora do try

try:
    i2c = I2C(I2C_BUS_PATH)
    print(f"Barramento I2C em '{I2C_BUS_PATH}' aberto.")

    # Tentativa de enviar o comando mais simples possível: um soft reset
    print(f"Tentando enviar comando de Soft Reset (0x{AHT10_CMD_SOFT_RESET:X}) para o endereço 0x{AHT10_I2C_ADDRESS:X}...")
    
    reset_msg = I2C.Message([AHT10_CMD_SOFT_RESET])
    i2c.transfer(AHT10_I2C_ADDRESS, [reset_msg])

    print("\n>>> SUCESSO! O comando foi enviado sem erros.")
    print("Isso confirma que a comunicação básica com o AHT10 é possível.")

except Exception as e:
    print(f"\n>>> FALHA! O erro ocorreu mesmo com o comando simples: {e}")

finally:
    if i2c:
        i2c.close()
        print("Conexão I2C fechada.")