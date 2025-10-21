import server

if __name__ == "__main__":
    test_server = server.Server()

    msg = (
        "8=FIX.4.2\x019=65\x0135=A\x0134=1\x0149=CLIENT1\x0156=EXCHANGE\x01"
        "52=20251001-18:30:00.000\x0198=0\x01108=30\x0110=128\x01"
    )

    test_server.send_data(msg)