def save_data(path,data):
    file = open(path, "a")
    file.write(str(data))
    file.write("\n")
    file.close()