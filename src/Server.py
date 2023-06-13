import socket
import sys
import threading
import socket
import time
import os

from VideoStream import VideoStream
from RtpPacket   import RtpPacket
from Constants   import *



class Server:

    #Server Info
    neighbours : list[str]

    interested : set[str]
    interested_lock : threading.Lock

    # Streaming related
    filename : str
    monitoring_socket : socket.socket
    join_socket : socket.socket
    streaming_socket  : socket.socket
    event : threading.Event


    def __init__(self, neighbours : list[str]):

        self.neighbours = neighbours


        #Streaming related
        self.monitoring_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.streaming_socket  = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.join_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.join_socket.bind(('', JOIN_PORT))

        self.event = threading.Event()

        self.interested = set()
        self.interested_lock = threading.Lock()

        while True:
            print("Enter video filename: ", end='', flush = True)
            filename = sys.stdin.readline().rstrip()

            if os.path.isfile(filename):
                self.filename = filename
                break

            else:
                print(f"{sys.argv[0]}: error while trying to read '{filename}'", file=sys.stderr)

    ## Methods for class manipulation
    # --------------------------------------------------------------------------------------------------------------------------------------


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

    ## Methods for the services on the class
    # --------------------------------------------------------------------------------------------------------------------------------------

    # function common to both clients and servers
    def message_node(self, addr : str, msg : bytes):

        self.monitoring_socket.settimeout(FLOOD_TIMEOUT * 2)
        self.monitoring_socket.sendto(msg, (addr, FLOOD_PORT))

    def server_monitoring_service(self):

        while True:

            # hops; timestamp
            msg = as_bytes(f"1;{int(time.time())}")

            #print(from_bytes(msg))

            for n in self.neighbours:

                threading.Thread(
                    target = self.message_node,
                    args = (n, msg)
                ).start()


            time.sleep(FLOOD_TIMEOUT)


    def broadcast_to_all_interested(self, n : str, data : bytes, frame_num : int):

        try:
            self.interested_lock.acquire()

            if n in self.interested:
                packet = self.make_rtp(data, frame_num)
                self.streaming_socket.sendto(packet, (n, RTP_PORT))

        except socket.error:
            print(f'{sys.argv[1]} error: {socket.error}', file=sys.stderr)

        finally:
            self.interested_lock.release()

    def server_streaming_service(self):

        video_stream = VideoStream(self.filename)
        frame_num = 0

        while True:

            self.event.wait(0.05)

            if self.event.is_set():
                break

            if data := video_stream.next_frame():

                frame_num = video_stream.frame_num

                for n in self.neighbours:

                    self.broadcast_to_all_interested(n, data, frame_num)

            else:
                video_stream = VideoStream(self.filename, frame_num+1)

    def make_rtp(self, payload : bytes, frame_num : int) -> bytes:

        version = 2
        padding = 0
        extension = 0
        cc = 0
        marker = 0
        pt = 26  # MJPEG type
        seqnum = frame_num
        ssrc = 0

        rtp_packet = RtpPacket()
        rtp_packet.encode(
            version, padding,
            extension, cc,
            seqnum, marker,
            pt, ssrc,
            payload
        )

        print(f"Enconding RTP packet: {str(seqnum)}")

        return rtp_packet.get_packet()


    def server_join_service(self):

        while True:

            (msg, rcv_addr) = self.join_socket.recvfrom(1024)

            match from_bytes(msg):
                case 'join':
                    self.add_interested(rcv_addr[0])
                    print(self.interested)
                case 'leave':
                    self.remove_interested(rcv_addr[0])
                case _:
                    pass

    def run(self):

        #Server precisa
        #       serviço para o streaming
        #       serviço para monotorização
        #       serviço para receber pedidos de streaming


        #iniciar serviço de monotorização
        monitoring_thread : threading.Thread = threading.Thread(target=self.server_monitoring_service, args=())
        monitoring_thread.start()

        join_thread : threading.Thread = threading.Thread(target= self.server_join_service, args=())
        join_thread.start()

        streaming_thread  : threading.Thread = threading.Thread(target=self.server_streaming_service, args=())
        streaming_thread.start()


        monitoring_thread.join()
        join_thread.join()
        streaming_thread.join()
