"""
Main system monitor coordination module.

Architecture:
- Asynchronous task scheduling
- Non-blocking UI updates
- Event-driven monitoring
- Resource-efficient polling
- Responsive user interface

Components:
- CPU monitoring
- Memory tracking
- Network statistics
- Process management
- System information
"""

import curses
import asyncio
import signal
import time
from python_system_monitor.monitors.system_info import SystemInfo
from python_system_monitor.monitors.cpu_monitor import CPUMonitor
from python_system_monitor.monitors.memory_monitor import MemoryMonitor
from python_system_monitor.monitors.network_monitor import NetworkMonitor
from python_system_monitor.monitors.process_monitor import ProcessMonitor
from python_system_monitor.ui.ui_handler import UIHandler

async def monitor_cpu(cpu_monitor, ui, y, x, width):
    """CPU monitoring with minimal latency"""
    while True:
        stats = cpu_monitor.get_detailed_stats()
        ui.update_cpu_section(y, x, width, stats)
        await asyncio.sleep(0.05) 

async def monitor_memory(memory_monitor, ui, y, x, width):
    """Memory monitoring with higher frequency"""
    while True:
        try:
            mem = memory_monitor.get_memory_percentage()
            swap = memory_monitor.get_swap_percentage()
            ui.update_memory_section(y, x, width, mem, swap)
            await asyncio.sleep(0.1) 
        except Exception as e:
            await asyncio.sleep(0.1)

async def monitor_system_info(system_info, ui, y, x, width):
    """System info with staggered updates"""
    while True:
        try:
            data = await system_info.get_system_info()
            ui.update_system_info(y, x, width, data)
            await asyncio.sleep(10) 
        except Exception as e:
            await asyncio.sleep(5)

async def monitor_network(network_monitor, ui, y, x, width):
    """Network monitoring with minimal delay"""
    while True:
        try:
            data = network_monitor.get_bandwidth_usage()
            ui.update_network_section(y, x, width, data)
            await asyncio.sleep(0.05) 
        except Exception as e:
            await asyncio.sleep(0.05)

async def monitor_processes(process_monitor, ui, y, x, width):
    """Process monitoring with higher frequency"""
    while True:
        try:
            processes = process_monitor.get_running_processes()
            ui.update_process_section(y, x, width, processes, ui.selected_process)
            await asyncio.sleep(0.2)
        except Exception as e:
            await asyncio.sleep(0.1)

async def handle_process_control(process_monitor, ui):
    """Responsive process control"""
    while True:
        try:
            key = ui.stdscr.getch()
            if key != -1:
                action = ui.handle_input(key)
                if action == 'kill':
                    processes = process_monitor.get_running_processes()
                    if processes and 0 <= ui.selected_process < len(processes):
                        pid = processes[ui.selected_process]['pid']
                        process_monitor.kill_process(pid)
                elif action == 'refresh':
                    ui.stdscr.clear()
                    ui.stdscr.refresh()
            await asyncio.sleep(0.016)
        except Exception as e:
            await asyncio.sleep(0.016)

async def ui_refresher(ui):
    """Higher frequency UI refresh"""
    while True:
        await asyncio.sleep(0.016)
        ui.stdscr.refresh()

async def handle_resize(ui, stdscr):
    """Enhanced resize handler with debouncing and smooth transitions"""
    resize_timeout = 0.1
    last_resize = 0
    
    while True:
        try:
            current_time = time.time()
            if current_time - last_resize > resize_timeout:
                new_layout = ui.handle_resize()
                if new_layout:
                    last_resize = current_time
                    return new_layout
            await asyncio.sleep(0.05)
        except curses.error:
            pass
        
async def main(stdscr):
    """Enhanced main function with smooth updates"""
    # Initialize curses
    curses.start_color()
    curses.use_default_colors()
    curses.curs_set(0)
    stdscr.nodelay(1)
    stdscr.clear()
    
    ui = UIHandler(stdscr)
    
    # Initial layout calculation
    h, w = stdscr.getmaxyx()
    layout = ui.get_layout(h, w)
    ui.last_layout = layout 
    
    # Monitor instances and their corresponding monitoring functions
    monitors = {
        'system': (SystemInfo(), monitor_system_info),
        'cpu': (CPUMonitor(), monitor_cpu),
        'memory': (MemoryMonitor(), monitor_memory),
        'network': (NetworkMonitor(), monitor_network),
        'processes': (ProcessMonitor(), monitor_processes)
    }

    while True:
        try:
            h, w = stdscr.getmaxyx()
            if h < ui.layout['min_height'] or w < ui.layout['min_width']:
                ui.draw_size_warning(h, w)
                ui.refresh()
                await asyncio.sleep(0.5)
                continue

            # Clear screen and draw layout
            stdscr.clear()
            layout = ui.get_layout(h, w)
            
            # Draw boxes first
            for section, dims in layout.items():
                ui.draw_box(dims['y'], dims['x'], dims['h'], dims['w'], section.upper())
            
            # Draw instructions (add this before creating tasks)
            ui.draw_instructions()
            
            # Create monitoring tasks
            tasks = []
            for section, dims in layout.items():
                if section in monitors:
                    monitor_instance, monitor_func = monitors[section]
                    task = asyncio.create_task(monitor_func(
                        monitor_instance, ui, 
                        dims['y']+1, dims['x']+1, 
                        dims['w']-2
                    ))
                    tasks.append(task)

            # Add control tasks
            tasks.extend([
                asyncio.create_task(handle_process_control(monitors['processes'][0], ui)),
                asyncio.create_task(ui_refresher(ui))
            ])

            await asyncio.gather(*tasks)

        except KeyboardInterrupt:
            break
        except curses.error:
            stdscr.refresh()
            await asyncio.sleep(0.1)

def run():
    """Entry point for curses wrapper"""
    curses.wrapper(lambda stdscr: asyncio.run(main(stdscr)))

if __name__ == "__main__":
    import sys
    import os
    # Add the project root directory to Python path
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    sys.path.insert(0, project_root)
    run()