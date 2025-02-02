"""CPU monitoring and analysis module.

Features:
- Overall CPU utilization tracking
- Per-core usage statistics
- Frequency monitoring
- Temperature sensors (Linux)
- Load average calculation

Performance considerations:
- Uses non-blocking operations
- Implements rate limiting
- Caches frequent measurements
- Smooths rapid fluctuations
"""

import psutil
import platform
import os
import time

class CPUMonitor:
    """Monitors CPU activity and provides usage statistics.

    Args:
        bars (int): Number of characters to use in the visual progress bars

    Features:
    - Per-core and overall CPU usage tracking
    - Frequency monitoring
    - Temperature sensors reading on Linux
    - Visual representation of CPU load
    """

    def __init__(self, bars=50):
        self.temp_sensors = self._init_temp_sensors()
        self.prev_cpu_times = psutil.cpu_times()
        self.bars = bars
        self.last_cpu_percent = psutil.cpu_percent(interval=None)
        self.last_per_cpu_percent = psutil.cpu_percent(interval=None, percpu=True)
        self.last_check_time = time.time()
        self.update_threshold = 0.05 
    def _init_temp_sensors(self):
        if platform.system() == 'Linux':
            sensors = {}
            try:
                for sensor in psutil.sensors_temperatures().values():
                    for entry in sensor:
                        if 'core' in entry.label.lower():
                            sensors[entry.label] = entry
                return sensors
            except:
                return None
        return None

    def get_detailed_stats(self):
        current_time = time.time()
        if current_time - self.last_check_time >= self.update_threshold: 
            self.last_cpu_percent = psutil.cpu_percent(interval=None)
            self.last_per_cpu_percent = psutil.cpu_percent(interval=None, percpu=True)
            self.last_check_time = current_time

        cpu_freq = psutil.cpu_freq()
        stats = {
            'usage': self.last_cpu_percent,
            'freq_current': cpu_freq.current if cpu_freq else 0,
            'freq_max': cpu_freq.max if cpu_freq else 0,
            'cores': self.last_per_cpu_percent,
            'temps': self._get_temps(),
            'load_avg': psutil.getloadavg()
        }
        return stats

    def _get_temps(self):
        if not self.temp_sensors:
            return None
        return {label: sensor.current for label, sensor in self.temp_sensors.items()}

    def get_cpu_usage(self):
        return self._format_usage(self.last_cpu_percent)

    def get_cpu_cores_usage(self):
        return [self._format_core_usage(idx, core) for idx, core in enumerate(self.last_per_cpu_percent)]

    def _format_usage(self, cpu):
        cpu_percent = cpu / 100.0
        cpu_visual = '#' * int(cpu_percent * self.bars) + '-' * (self.bars - int(cpu_percent * self.bars))
        return f"CPU: [{cpu_visual}] {cpu:.2f}%"

    def _format_core_usage(self, core_idx, core):
        core_percent = core / 100.0
        core_visual = '#' * int(core_percent * self.bars) + '-' * (self.bars - int(core_percent * self.bars))
        return f"Core {core_idx}: [{core_visual}] {core:.2f}%"