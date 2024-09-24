from ib_insync import *

'''
This class is aiming at interact with Interactive Brokers TWS server
'''


class IBConnection:
    def __init__(self, host: str = '127.0.0.1', port: int = 7497, client_id: int = 1):
        """
        Set default input as local connection to tws server and only allows local connections

        :param host: str
        :param port: int
        :param client_id: int
        """
        self.ib = IB()
        self.host = host
        self.port = port
        self.client_id = client_id

    def connect(self):
        self.ib.connect(self.host, self.port, clientId=self.client_id)

    def disconnect(self):
        self.ib.disconnect()

    def get_ib(self):
        return self.ib
