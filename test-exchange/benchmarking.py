import server
import time

def timer(func):
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        print(f"Function '{func.__name__}' executed in {end_time - start_time:.6f} seconds")
        return result
    return wrapper

@timer
def run_benchmark(test_server):
    msg = (
        "8=FIX.4.2\x019=65\x0135=A\x0134=1\x0149=CLIENT1\x0156=EXCHANGE\x01"
        "52=20251001-18:30:00.000\x0198=0\x01108=30\x0110=128\x01"
    )
    for _ in range(1000):
        test_server.send_data(msg)
        test_server.receive_data()

if __name__ == "__main__":
    test_server = server.Server()

    run_benchmark(test_server)