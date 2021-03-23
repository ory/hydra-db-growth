import concurrent.futures
import logging

utils_logger = logging.getLogger('utils')


class Concurrent:

    def __init__(self, max_workers=100):
        self.max_workers = max_workers
        self.futures = []
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers)

    def add_future(self, function, *args, **kwargs):
        self.futures.append(self.executor.submit(function, *args, **kwargs))

    def run(self):
        results = []
        for future in concurrent.futures.as_completed(self.futures):
            try:
                results.append(future.result())
            except Exception as e:
                utils_logger.error(e)
                pass
        return results
