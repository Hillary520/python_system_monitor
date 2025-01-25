"""Module for network bandwidth monitoring with rate smoothing.

Tracks network interface bandwidth usage with:
- Download/upload rate calculation
- Rate smoothing for stable readings
- Interface enumeration
"""

import psutil
import time
import socket
from collections import deque

class NetworkMonitor:
    """Monitors network bandwidth with smoothed rate calculations.

    Args:
        smoothing_window (int): Number of samples to use for rate smoothing

    Tracks bandwidth usage across all network interfaces and provides
    smoothed rate calculations to prevent erratic readings.
    """
    def __init__(self, smoothing_window=3):
        self.last_received = psutil.net_io_counters().bytes_recv
        self.last_sent = psutil.net_io_counters().bytes_sent
        self.last_check_time = time.time()
        self.recv_rates = deque(maxlen=smoothing_window)
        self.sent_rates = deque(maxlen=smoothing_window)
        self._update_interfaces()

    def _update_interfaces(self):
        self.interfaces = {}
        for name, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if addr.family == socket.AF_INET:
                    self.interfaces[name] = addr.address
                    break

    def get_bandwidth_usage(self):
        current_time = time.time()
        current = psutil.net_io_counters()
        
        # Reduce minimum time delta
        time_delta = current_time - self.last_check_time
        if time_delta < 0.05: 
            if self.recv_rates and self.sent_rates:
                recv_rate = self.recv_rates[-1]
                sent_rate = self.sent_rates[-1]
            else:
                return "▼ 0.0KB/s ▲ 0.0KB/s", self.interfaces
        else:
            # Convert to KB/s
            recv_rate = (current.bytes_recv - self.last_received) / time_delta / 1024
            sent_rate = (current.bytes_sent - self.last_sent) / time_delta / 1024
            
            # Add to smoothing window
            self.recv_rates.append(recv_rate)
            self.sent_rates.append(sent_rate)
            
            # Update last values
            self.last_received = current.bytes_recv
            self.last_sent = current.bytes_sent
            self.last_check_time = current_time

        # Calculate smoothed rates
        avg_recv = sum(self.recv_rates) / len(self.recv_rates) if self.recv_rates else 0
        avg_sent = sum(self.sent_rates) / len(self.sent_rates) if self.sent_rates else 0

        # Format with standard arrows
        bandwidth_data = f"▼ {avg_recv:.1f}KB/s ▲ {avg_sent:.1f}KB/s"
        return bandwidth_data, self.interfaces