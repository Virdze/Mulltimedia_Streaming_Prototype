import sys
import os
import threading
import socket
import time

from Constants import *
from TkContextManager import TkContextManager
from LockedString import LockedString



class Client:

    neighbours : list[str]
    join_socket : socket.socket
    join_message : LockedString

    def __init__(self, neighbours : list[str]):

        self.neighbours = neighbours

        self.join_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.join_message = LockedString()


    def client_streaming_service(self):

        os.environ['DISPLAY'] = ':0.0'

        tkmanager = TkContextManager('', RTP_PORT, self.join_message)
        tkmanager.run()


    def client_join_service(self):

        while True:

            # assuming that for clients there's only one neighbour
            n = self.neighbours[0]
            print(n)

            msg = self.join_message.get_string()
            self.join_socket.sendto(as_bytes(msg), (n, JOIN_PORT))


    def run(self):

        #Router precisa
        #       serviço para o streaming
        #       serviço para receber pedidos de streaming

        #iniciar serviço de monotorização


        streaming_thread : threading.Thread = threading.Thread(target=self.client_streaming_service, args=())
        streaming_thread.start()

        join_thread : threading.Thread = threading.Thread(target=self.client_join_service, args=())
        join_thread.start()


        streaming_thread.join()
        join_thread.join()
