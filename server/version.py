def get_version():
    try:
        with open("./VERSION") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None
