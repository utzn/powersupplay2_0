from cpu_loader import CpuLoader
import time


def generate_signal(duration, freq: int) -> None:
    """
    Generating different frequencies is achieved by changing the frequency of CPU load switching.
    """

    # print info
    print("---Generating Signal---")
    print("Duration: " + str(duration) + " s")
    print("# Cores: " + str(cl.cpu_count) + " ")

    start_time = time.time()
    while start_time + duration > time.time():
        cl.load_cpu(1 / (0.5 * freq))
        time.sleep(1 / (0.5 * freq))


def generate_sweep_signal(duration: float) -> None:
    """Sweep signal"""
    print("Broadcasting sweep signal for " + str(duration) + " seconds.")
    start = time.time()
    generate_signal(duration)
    print("Success! Sweep signal lasted for " + str(time.time() - start) + " seconds.")


def generate_bfsk(data: str, bfsk_freq=1.0, high_freq=20000, low_freq=10000) -> None:
    """
    Generate a BFSK signal for the parsed data, consisting of 1s and 0s.
    Adjustable parameters are the speed at which the signal transmits data (bfsk_freq) and
    the frequencies used to code 1s and 0s.
    """

    print("Broadcasting BFSK signal for data: " + data)
    print("Approximate duration: " + str(len(data) / bfsk_freq) + " seconds")
    start = time.time()
    for elem in data:
        if elem == "0":
            generate_signal(1 / bfsk_freq, low_freq)
        elif elem == "1":
            generate_signal(1 / bfsk_freq, high_freq)
        else:
            print("Data wasn't in binary format!")
            return
    print("Success! BFSK signal lasted for " + str(time.time() - start) + " seconds.")


def ofdm_test():
    pass


if __name__ == "__main__":
    cl = CpuLoader()
    print("Number of available cores: " + str(cl.cpu_count))
    generate_bfsk("10101010", low_freq=1000, high_freq=2000)
