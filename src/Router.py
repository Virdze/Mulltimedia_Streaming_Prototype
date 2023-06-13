import sys
import os
import threading
import sys
import socket
import time

from Constants import *



class Router:

    neighbours : list[str]

    delays : dict[str, int]
    delays_lock : threading.Lock

    min_hops : dict[str,int]
    min_hops_lock : threading.Lock

    has_stream : bool
    has_stream_lock : threading.Lock

    interested : set[str]
    interested_lock : threading.Lock

    monitoring_socket : socket.socket
    streaming_socket  : socket.socket
    join_socket : socket.socket

    def __init__(self, neighbours : list[str]):

        self.neighbours = neighbours

        self.delays_lock = threading.Lock()
        self.delays = {}

        self.min_hops = {}
        self.min_hops_lock = threading.Lock()

        self.has_stream = False
        self.has_stream_lock = threading.Lock()

        self.interested = set()
        self.interested_lock = threading.Lock()

        self.monitoring_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.monitoring_socket.bind(('', FLOOD_PORT))

        self.streaming_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.streaming_socket.bind(('', RTP_PORT))

        self.join_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.join_socket.bind(('', JOIN_PORT))

    ## Methods for class manipulation
    # --------------------------------------------------------------------------------------------------------------------------------------

    def add_timestamp(self, addr : str, time : int):

        try:
            self.delays_lock.acquire()
            self.delays[addr] = time

        finally:
            self.delays_lock.release()

    def update_min_num_of_hops(self, addr : str, value : int) -> bool:

        try:
            self.min_hops_lock.acquire()
            min_hops = self.min_hops.get(addr)

            if not min_hops or min_hops < HOP_THRESHOLD:
                self.min_hops[addr] = value
                return True

            else:
                return False

        finally:
            self.min_hops_lock.release()


    def get_min_num_of_hops(self, addr : str) -> int:

        try:
            self.min_hops_lock.acquire()

            return self.min_hops[addr]

        finally:
            self.min_hops_lock.release()

    def get_streaming_state(self) -> bool:

        try:
            self.has_stream_lock.acquire()

            return self.has_stream

        finally:
            self.has_stream_lock.release()

    def add_interested(self, addr : str):

        try:
            self.interested_lock.acquire()
            self.interested.add(addr)

        finally:
            self.interested_lock.release()

    def remove_interested(self, addr : str):

        try:
            self.interested_lock.acquire()
            if addr in self.interested:
                self.interested.remove(addr)

        finally:
            self.interested_lock.release()

    def get_next_hop(self):

        try:
            self.delays_lock.acquire()
            return list(
                    sorted(
                        self.delays,
                        key = lambda entry: entry[1]
                    )
                )[0]

        except IndexError:
            return None

        finally:
            self.delays_lock.release()



    ## Methods for the services on the class
    # --------------------------------------------------------------------------------------------------------------------------------------


    def transmit_to_neighbour_nodes(self, addr : str, msg : bytes):

        self.monitoring_socket.sendto(msg, (addr, FLOOD_PORT))


    # store the info in the local node info
    # and flood neighbours with the same message
    def update_router_info(self,
        msg : bytes,
        recv_addr : tuple[str, int],
        timestamp : int,
    ):

        msg_as_str_tuple = from_bytes(msg).split(';')

        hops = int(msg_as_str_tuple[0])
        server_time = int(msg_as_str_tuple[1])

        delay = timestamp - server_time
        self.add_timestamp(recv_addr[0], delay)

        # wait for some more flooding from other nodes
        time.sleep(1)

        # use number of hops as criteria
        # as to which nodes to flood
        flag : bool = self.update_min_num_of_hops(recv_addr[0], hops)
        hops += 1

        if flag:
            for n in self.neighbours:

                if n == recv_addr[0]:
                    continue

                threading.Thread(
                    target = self.transmit_to_neighbour_nodes,
                    args = (n, as_bytes(f'{str(hops)};{str(server_time)}'))
                ).start()

                self.update_min_num_of_hops(n, hops)


    def router_monitoring_service(self):

        while True:

            try:
                (msg, recv_addr) = self.monitoring_socket.recvfrom(1024)

                #print(from_bytes(msg))

                threading.Thread(
                    target = self.update_router_info,
                    args = (msg, recv_addr, int(time.time()))
                ).start()

            except Exception as e:
                print(e)
                break


    def replicate(self, msg : bytes):

        for n in self.neighbours:

            try:
                self.interested_lock.acquire()

                if n in self.interested:

                    try:
                        self.streaming_socket.sendto(msg, (n, RTP_PORT))
                    except:
                        #TODO treat errors
                        pass

            finally:
                self.interested_lock.release()

    def router_streaming_service(self):

        self.streaming_socket.settimeout(FLOOD_TIMEOUT * 2)

        while True:

            try:
                (msg, _) = self.streaming_socket.recvfrom(20480)
                print("Recebi Stream")

                try:
                    self.has_stream_lock.acquire()
                    self.has_stream = True
                finally:
                    self.has_stream_lock.release()

                threading.Thread(
                    target = self.replicate,
                    args = (msg,)
                ).start()

            except TimeoutError:
                try:
                    self.has_stream_lock.acquire()
                    self.has_stream = False
                finally:
                    self.has_stream_lock.release()


    def router_join_service(self):

        while True:

            (msg, rcv_addr) = self.join_socket.recvfrom(1024)
            print(f'Recebi: {from_bytes(msg)}')

            match from_bytes(msg):
                case 'join':
                    self.add_interested(rcv_addr[0])
                    print(self.interested)
                case 'leave':
                    self.remove_interested(rcv_addr[0])
                case _:
                    pass

            if not self.get_streaming_state():
                if addr := self.get_next_hop():
                    print(addr)
                    print("Nao tenho stream, enviei para o proximo.")
                    self.join_socket.sendto(msg, (addr,JOIN_PORT))


    def run(self):

        #Router precisa
        #       serviço para o streaming
        #       serviço para monotorização
        #       serviço para receber pedidos de streaming


        monitoring_thread : threading.Thread = threading.Thread(target=self.router_monitoring_service, args=())
        monitoring_thread.start()

        join_thread : threading.Thread = threading.Thread(target=self.router_join_service, args=())
        join_thread.start()

        streaming_thread  : threading.Thread = threading.Thread(target=self.router_streaming_service, args=())
        streaming_thread.start()


        monitoring_thread.join()
        join_thread.join()
        streaming_thread.join()
