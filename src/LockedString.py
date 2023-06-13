import threading

class LockedString:

    lock : threading.Lock
    string : str

    def __init__(self, string : str = None):

        self.lock = threading.Condition()
        self.string = string

    def set_string(self, string : str):

        try:

            self.lock.acquire()

            self.string = string

            self.lock.notifyAll()

        finally:

            self.lock.release()

    def get_string(self) -> str:

        try:

            self.lock.acquire()

            while not self.string:

                self.lock.wait()

            return self.string

        finally:

            self.string = None

            self.lock.release()

