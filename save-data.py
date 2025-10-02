def save_data(path, data):
    file = open(path, "w")

    for i in range(3):
        data = input("Digite um valor")
        file.write(data)
        file.write("\n")

    file.close()
