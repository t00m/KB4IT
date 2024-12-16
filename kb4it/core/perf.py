import time
from functools import wraps

from kb4it.core.log import get_logger

log = get_logger('perf')

def timeit(func):
    @wraps(func)
    def timeit_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        total_time = end_time - start_time
        # ~ if total_time > 1:
            # ~ log.perf(f"[PERFORMANCE] {total_time:.4f}s => Stage {func.__name__}")
        # ~ else:
            # ~ log.trace(f"[PERFORMANCE] {total_time:.4f}s => Stage {func.__name__}")
        log.trace(f"[PERFORMANCE] {total_time:.4f}s => Stage {func.__name__}")
        return result
    return timeit_wrapper
