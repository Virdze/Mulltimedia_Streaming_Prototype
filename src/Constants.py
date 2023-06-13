SERVER_TYPE : int = 0
CLIENT_TYPE : int = 1
ROUTER_TYPE : int = 2

RTP_PORT      : int = 25000
FLOOD_PORT    : int = 3000
JOIN_PORT     : int = 1345

FLOOD_TIMEOUT : float = 10

HOP_THRESHOLD : int = 10


def as_bytes(s : str) -> bytes:
    return s.encode('utf-8')

def from_bytes(b : bytes) -> str:
    return b.decode('utf-8')
