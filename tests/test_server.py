def test_emit_no_resp(server, client):
    assert client.emit('/id', None) is None
    assert client.call('/id', None) is not None
