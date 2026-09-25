class Address:
    """
    Object representing a network address (IP and Port)
    """
    def __init__(self, ip: str, port: int):
        self.ip = ip
        self.port = port
