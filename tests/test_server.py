import threading
import time
from time import sleep


def test_emit_endpoint(server, client):
    client.emit('/inc', None)
    assert client.call('/getinc', None) == 1


def test_call_endpoint(server, client):
    assert client.call('/echo', {'blop': 56}) == {'blop': 56}


def test_call_async(server, client):
    event = threading.Event()

    def _cb(result):
        assert result == 5
        event.set()

    client.call_async('/echo', 5, _cb)
    sleep(1)

    assert event.is_set()


def test_concurrent(server, client, client1, client2):
    lock = threading.Lock()
    counter = {'value': 0}

    def _cb(result):
        with lock:
            counter['value'] += 1

    t = time.time()
    client.call_async('/3sec', 5, _cb)
    client1.call_async('/3sec', 5, _cb)
    client2.call_async('/3sec', 5, _cb)
    assert time.time() - t < 1  # Ensure previous calls were not blocking

    sleep(3.1)  # If concurrent if should take a bit more than 3 secs instead of 3*client for non-concurrent
    assert(counter['value'] == 3)
