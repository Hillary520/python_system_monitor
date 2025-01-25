"""
Asynchronous system information collection module.

Key features:
- Non-blocking OS information retrieval
- Hardware specifications gathering
- Network information collection
- Resource availability tracking
- Cached data management for static information
"""

import platform
import psutil
import socket
import asyncio
from concurrent.futures import ThreadPoolExecutor

class SystemInfo:
    """Asynchronous system information collector.

    Uses ThreadPoolExecutor for potentially blocking operations and
    implements caching for relatively static information.
    """
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.cached_ip = None
        self.cached_hostname = None

    async def get_system_info(self):
        """Collect system info without blocking the event loop"""
        loop = asyncio.get_running_loop()
        
        try:
            results = await asyncio.gather(
                self._get_os_info(loop),
                self._get_cpu_info(),
                self._get_ram_info(),
                self._get_disk_info(loop),
                self._get_battery_status(loop),
                return_exceptions=True
            )
        except Exception as e:
            return f"System Info Error: {str(e)}"

        info = []
        for result in results:
            if isinstance(result, dict):
                info.extend([f"{k}: {v}" for k, v in result.items()])
            elif not isinstance(result, Exception):
                info.append(str(result))

        return "\n".join(info[:7])  
    async def _get_os_info(self, loop):
        """Async OS/Host info with caching"""
        if not self.cached_hostname:
            self.cached_hostname = await loop.run_in_executor(
                self.executor, socket.gethostname
            )
        if not self.cached_ip:
            self.cached_ip = await loop.run_in_executor(
                self.executor, socket.gethostbyname, self.cached_hostname
            )
        
        return {
            "OS": f"{platform.system()} {platform.release()}",
            "Host": self.cached_hostname,
            "IP": self.cached_ip
        }

    async def _get_cpu_info(self):
        """Non-blocking CPU info"""
        return {
            "CPU": f"{platform.processor()}",
            "Cores": f"{psutil.cpu_count(logical=True)}"
        }

    async def _get_ram_info(self):
        """Memory info using psutil"""
        mem = psutil.virtual_memory()
        return {
            "RAM": f"{mem.total / (1024**3):.1f}GB",
            "Available": f"{mem.available / (1024**3):.1f}GB"
        }

    async def _get_disk_info(self, loop):
        """Async disk info"""
        usage = await loop.run_in_executor(
            self.executor, psutil.disk_usage, '/'
        )
        return {
            "Disk": f"{usage.percent}% ({usage.free / (1024**3):.1f}GB free)"
        }

    async def _get_battery_status(self, loop):
        """Safe battery status check"""
        try:
            battery = await loop.run_in_executor(
                self.executor, getattr, psutil, "sensors_battery"
            )
            if battery:
                return {"Battery": f"{battery.percent}%"}
            return {"Battery": "N/A"}
        except AttributeError:
            return {"Battery": "N/A"}

    def _format_uptime(self, seconds):
        """Format uptime duration"""
        days, remainder = divmod(seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, _ = divmod(remainder, 60)
        return f"{int(days)}d {int(hours)}h {int(minutes)}m"