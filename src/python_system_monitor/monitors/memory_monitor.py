"""
Memory utilization monitoring module.

Features:
- RAM usage tracking
- Swap space monitoring
- Visual progress bars
- Percentage-based metrics
- Real-time updates

Example usage:
    monitor = MemoryMonitor(bars=50)
    ram_usage = monitor.get_memory_usage()
    swap_usage = monitor.get_swap_usage()
"""

import psutil

class MemoryMonitor:
    """Tracks and visualizes system memory usage.

    Args:
        bars (int): Number of characters to use in the visual progress bar

    The monitor provides both numerical percentages and visual representations
    of memory usage for both RAM and swap space.
    """

    def __init__(self, bars=50):
        self.bars = bars

    def get_memory_percentage(self) -> float:
        """Returns current RAM usage as percentage."""
        return psutil.virtual_memory().percent

    def get_swap_percentage(self) -> float:
        """Returns current swap usage as percentage."""
        return psutil.swap_memory().percent

    def get_memory_usage(self) -> str:
        """Returns formatted string showing RAM usage with visual bar."""
        memory = self.get_memory_percentage()
        return self._format_usage(memory)

    def get_swap_usage(self) -> str:
        """Returns formatted string showing swap usage with visual bar."""
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