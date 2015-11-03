import newrelic.agent

import os
import psutil
import time
import functools

class CustomMemoryUsageNode(object):
    def __init__(self, name):
        self.name = name
        self.start_memory_physical = None
        self.end_memory_physical = None

    def __enter__(self):
        m = get_memory()
        self.start_memory_physical = float(m.rss)/(1024*1024)
        return self

    def __exit__(self):
        m = p.get_memory()
        self.end_memory_physical = float(m.rss)/(1024*1024)

        physical_delta = self.end_memory_physical - self.start_memory_physical

        newrelic.agent.record_custom_metric(self.name, physical_delta)


    def get_memory(self):
        pid = os.getpid()
        p = psutil.Process(pid)
        return p.get_memory_info

def custom_memory_usage_node(name):
    def _decorator(f):
        @functools.wraps(f)
        def _wrapper(*args, **kwargs):
            with CustomMemoryUsageNode(name):
                return f(*args, **kwargs)
        return _wrapper
    return _decorator