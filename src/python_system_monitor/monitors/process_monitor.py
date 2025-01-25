"""
Process monitoring and management module.

Key features:
- Real-time process statistics tracking
- Resource usage monitoring per process
- Process control capabilities
- I/O and network connection tracking
- Memory and CPU utilization measurement
"""

import psutil
import signal
import os
import time

class ProcessMonitor:
    """Monitors and manages system processes with resource tracking capabilities.
    
    Maintains running statistics for:
    - CPU usage over time
    - I/O operations tracking
    - Memory usage
    - Network connections
    - Thread counts
    """
    def __init__(self):
        self.cpu_percent_dict = {}
        self.io_counters = {}
        self.last_io_update = {}
        self.last_update = time.time()

    def get_running_processes(self, num_processes=15):
        current_time = time.time()
        processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'username', 'status']):
            try:
                with proc.oneshot():
                    # Basic info
                    info = proc.info
                    info['memory_percent'] = proc.memory_percent()
                    
                    # CPU usage
                    cpu_percent = proc.cpu_percent()
                    self.cpu_percent_dict[proc.pid] = cpu_percent
                    info['cpu_percent'] = cpu_percent

                    # IO counters
                    try:
                        io = proc.io_counters()
                        if proc.pid in self.io_counters:
                            last_io = self.io_counters[proc.pid]
                            last_time = self.last_io_update[proc.pid]
                            time_delta = current_time - last_time
                            
                            info['io_read_speed'] = (io.read_bytes - last_io.read_bytes) / time_delta
                            info['io_write_speed'] = (io.write_bytes - last_io.write_bytes) / time_delta
                        else:
                            info['io_read_speed'] = 0
                            info['io_write_speed'] = 0
                        
                        self.io_counters[proc.pid] = io
                        self.last_io_update[proc.pid] = current_time
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        info['io_read_speed'] = 0
                        info['io_write_speed'] = 0

                    # Network connections
                    try:
                        info['connections'] = len(proc.connections())
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        info['connections'] = 0

                    # Thread count
                    try:
                        info['num_threads'] = proc.num_threads()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        info['num_threads'] = 0

                    processes.append(info)

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        self.last_update = current_time
        return sorted(processes, 
                     key=lambda p: p.get('memory_percent', 0), 
                     reverse=True)[:num_processes]

    def get_process_details(self, pid):
        """Get detailed information for a specific process"""
        if not isinstance(pid, int) or pid <= 0:
            return None
            
        try:
            proc = psutil.Process(pid)
            try:
                with proc.oneshot():
                    return {
                        'name': proc.name(),
                        'cmdline': ' '.join(proc.cmdline() or []),
                        'exe': proc.exe(),
                        'cwd': proc.cwd(),
                        'cpu_times': proc.cpu_times(),
                        'memory_maps': proc.memory_maps(),
                        'memory_info': proc.memory_info(),
                        'connections': proc.connections(),
                        'open_files': proc.open_files(),
                        'threads': proc.threads(),
                        'environ': proc.environ()
                    }
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                return None
        except (psutil.NoSuchProcess, psutil.AccessDenied, ValueError):
            return None

    def kill_process(self, pid):
        """Safely terminate a process"""
        if not isinstance(pid, int) or pid <= 0:
            return False
            
        try:
            process = psutil.Process(pid)
            try:
                process.terminate()
                process.wait(timeout=3)
                return True
            except psutil.TimeoutExpired:
                process.kill()
                return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                return False
        except (psutil.NoSuchProcess, psutil.AccessDenied, ValueError):
            return False