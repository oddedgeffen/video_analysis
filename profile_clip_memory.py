import tracemalloc
import psutil
import os
import time
from document_processor.logo_replace.utils.clip_utils import get_clip_model


def get_rss_mb():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)


if __name__ == "__main__":
    tracemalloc.start()
    print(f"Initial: traced current={tracemalloc.get_traced_memory()[0]/1024/1024:.2f}MB, peak={tracemalloc.get_traced_memory()[1]/1024/1024:.2f}MB, RSS={get_rss_mb():.2f}MB")

    # Load CLIP model
    model, preprocess = get_clip_model()
    time.sleep(1)

    current, peak = tracemalloc.get_traced_memory()
    print(f"After get_clip_model(): current={current/1024/1024:.2f}MB, peak={peak/1024/1024:.2f}MB, RSS={get_rss_mb():.2f}MB")

    tracemalloc.stop() 