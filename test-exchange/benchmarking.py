import server
import time

from test_input import messages

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
    for _ in range(1000):  # Number of iterations for benchmarking
        for msg in messages:
            test_server.send_data(msg)
            test_server.receive_data()

if __name__ == "__main__":
    test_server = server.Server()

    run_benchmark(test_server)