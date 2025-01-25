"""
memory_monitor.py

This module handles memory monitoring functionality through the MemoryMonitor class.
It provides both RAM and swap usage information in percentage and visual format.
"""

import psutil

class MemoryMonitor:
    def __init__(self, bars=50):
        self.bars = bars

    def get_memory_percentage(self):
        return psutil.virtual_memory().percent

    def get_swap_percentage(self):
        return psutil.swap_memory().percent

    def get_memory_usage(self):
        memory = self.get_memory_percentage()
        return self._format_usage(memory)

    def get_swap_usage(self):
        swap = self.get_swap_percentage()
        return self._format_usage_swap(swap)

    def _format_usage(self, memory):
        memory_percent = memory / 100.0
        memory_visual = '#' * int(memory_percent * self.bars) + '-' * (self.bars - int(memory_percent * self.bars))
        return f"Memory: [{memory_visual}] {memory:.2f}%"

    def _format_usage_swap(self, swap):
        swap_percent = swap / 100.0
        swap_visual = '#' * int(swap_percent * self.bars) + '-' * (self.bars - int(swap_percent * self.bars))
        return f"Swap: [{swap_visual}] {swap:.2f}%"