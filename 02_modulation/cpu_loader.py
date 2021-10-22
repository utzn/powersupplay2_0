import multiprocessing as mp
import time
import psutil


class CpuLoader:
    def __init__(self):
        self.cpu_count = mp.cpu_count()

    @staticmethod
    def busy_wait(end_time: time) -> None:
        """Make CPU busy with random variable assignments until provided datetime"""
        while time.time() < end_time:
            pass

    def spawn_child(self, worker: int, end_time: time) -> None:
        """Spawn child with proper affinity"""
        p = psutil.Process()
        p.cpu_affinity([worker])
        self.busy_wait(end_time)

    def load_cpu(self, duration: float, num_cpu=None) -> None:
        """Load the CPU (all cores) for a specified duration"""
        if num_cpu is None:
            num_cpu = self.cpu_count
        end_time = time.time() + duration
        with mp.Pool() as pool:
            # Populate CPU
            for w in range(0, num_cpu):
                pool.apply_async(self.spawn_child, (w, end_time))

            # Wait for children to finish
            pool.close()
            pool.join()

    def load_core(self, duration: float, core: int) -> None:
        """Loads a specific core of the CPU for a specified duration"""
        end_time = time.time() + duration
        with mp.Pool() as pool:
            pool.apply(self.spawn_child, (core % self.cpu_count, end_time))
        pool.close()
        pool.join()
