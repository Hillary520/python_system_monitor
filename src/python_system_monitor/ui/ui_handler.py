"""
ui_handler.py - Handles UI rendering and layout management
"""

import curses
import time
import math
from collections import defaultdict

import psutil

class UIHandler:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.selected_process = 0
        self.sort_by = 'memory_percent'
        self.sort_reverse = True
        self.search_term = ''
        self.show_details = False
        self.selected_pid = None
        self.graph_data = defaultdict(list)
        self.max_history = 60  # 1 minute of history at 1s intervals

        # Add content size tracking BEFORE get_layout is called
        self.content_sizes = {
            'system': {'min_h': 10, 'min_w': 40},  # Increased min height from 6 to 10
            'cpu': {'min_h': 8, 'min_w': 45},
            'memory': {'min_h': 5, 'min_w': 30}, 
            'network': {'min_h': 5, 'min_w': 35},  
            'processes': {'min_h': 10, 'min_w': 50}
        }
        
        # Minimal dimensions
        self.layout = {
            'min_width': 80,
            'min_height': 24,
            'padding': 1,
            'margin': 1
        }
        
        # Initialize color pairs
        curses.use_default_colors()
        self.init_colors()
        self.last_layout = None
        self.buffer = None

        # Create a new window for buffering
        self.window = curses.newwin(curses.LINES, curses.COLS)
        self.window.keypad(1)
        self.window.nodelay(1)
        
        # Initialize colors
        self.init_colors()

        # Add box drawing characters
        self.box_chars = {
            'ascii': {
                'tl': '+', 'tr': '+',
                'bl': '+', 'br': '+',
                'h': '-', 'v': '|'
            },
            'unicode': {
                'tl': '╭', 'tr': '╮',
                'bl': '╰', 'br': '╯',
                'h': '─', 'v': '│'
            }
        }
        
        # Try to detect if unicode is supported
        try:
            self.stdscr.addstr(0, 0, '─')
            self.use_unicode = True
        except:
            self.use_unicode = False
        finally:
            self.stdscr.clear()

        # Initialize color gradients
        self.GRADIENT_PAIRS = [
            curses.color_pair(1),  # Green for low usage
            curses.color_pair(3),  # Yellow for medium usage
            curses.color_pair(4)   # Red for high usage
        ]

        # Add modern styling configurations
        self.styles = {
            'borders': {
                'thin': {'h': '─', 'v': '│', 'tl': '╭', 'tr': '╮', 'bl': '╰', 'br': '╯'},
                'thick': {'h': '━', 'v': '┃', 'tl': '┏', 'tr': '┓', 'bl': '┗', 'br': '┛'},
                'double': {'h': '═', 'v': '║', 'tl': '╔', 'tr': '╗', 'bl': '╚', 'br': '╝'},
            },
            'bars': {
                'fill': '█',
                'half': '▄',
                'empty': '░'
            },
            'indicators': {
                'up': '↑',
                'down': '↓',
                'warning': '⚠',
                'error': '✗',
                'ok': '✓'
            }
        }
        
        # Track window dimensions
        self.last_width = curses.COLS
        self.last_height = curses.LINES

        # Initialize layout with current dimensions
        self.last_height, self.last_width = curses.LINES, curses.COLS
        self.last_layout = self.get_layout(self.last_height, self.last_width)

        # Color thresholds for usage indicators
        self.color_thresholds = {
            'normal': 60,    # Below this is green
            'warning': 85,   # Below this is yellow, above is red
        }

        self.process_scroll_offset = 0  # Add scroll offset for processes
        self.show_help = False  # Add help view toggle
        
        # Add instructions content (replace help_content)
        self.instructions = [
            "CONTROLS:",
            "↑/↓: Navigate   s: Sort   r: Reverse sort",
            "k: Kill process   /: Search   q: Quit"
        ]

    def init_colors(self):
        """Initialize color pairs"""
        # Define basic colors with transparent background (-1)
        curses.init_pair(1, curses.COLOR_GREEN, -1)    # Low usage
        curses.init_pair(2, curses.COLOR_CYAN, -1)     # Headers
        curses.init_pair(3, curses.COLOR_YELLOW, -1)   # Medium usage
        curses.init_pair(4, curses.COLOR_RED, -1)      # High usage
        curses.init_pair(5, curses.COLOR_WHITE, -1)    # Normal text
        curses.init_pair(6, curses.COLOR_BLACK, curses.COLOR_WHITE)  # Selected

        # Store color pairs for usage levels
        self.usage_colors = {
            'low': curses.color_pair(1),      # Green
            'medium': curses.color_pair(3),    # Yellow
            'high': curses.color_pair(4)       # Red
        }

    def get_layout(self, h, w):
        """Improved responsive layout with content-aware sizing"""
        margin = self.layout['margin']
        
        # Calculate available space
        available_height = h - (margin * 2)
        available_width = w - (margin * 2)
        
        # Calculate minimum widths for columns
        left_min_width = max(
            self.content_sizes['system']['min_w'],
            self.content_sizes['cpu']['min_w'],
            self.content_sizes['processes']['min_w']
        )
        right_min_width = max(
            self.content_sizes['memory']['min_w'],
            self.content_sizes['network']['min_w']
        )
        
        # Calculate column widths with minimums
        left_col_width = max(left_min_width, int(available_width * 0.65))
        right_col_width = max(right_min_width, available_width - left_col_width - margin)
        
        # Calculate dynamic heights based on content and available space
        system_height = max(
            self.content_sizes['system']['min_h'],
            min(12, int(available_height * 0.3))  # Increased from 0.2 to 0.3
        )
        
        cpu_height = max(
            self.content_sizes['cpu']['min_h'],
            min(int(available_height * 0.3),
                # Adjust based on number of CPU cores
                4 + (psutil.cpu_count() + 1) // 2)  # +1 for overall CPU
        )
        
        # Remaining height for processes
        process_height = max(
            self.content_sizes['processes']['min_h'],
            available_height - system_height - cpu_height - (margin * 3)
        )
        
        # Right column heights
        memory_height = self.content_sizes['memory']['min_h']
        network_height = self.content_sizes['network']['min_h']
        
        # Instructions height (fixed)
        instructions_height = 4
        
        # Calculate remaining space if needed
        remaining_height = available_height - network_height - memory_height - instructions_height - (margin * 4)
        
        # Add remaining space to instructions if we have extra
        if remaining_height > 0:
            instructions_height += remaining_height
        
        layout = {
            'system': {
                'x': margin,
                'y': margin,
                'w': left_col_width,
                'h': system_height,
                'inner_w': left_col_width - 2,  # Account for borders
                'inner_h': system_height - 2
            },
            'cpu': {
                'x': margin,
                'y': system_height + (margin * 2),
                'w': left_col_width,
                'h': cpu_height,
                'inner_w': left_col_width - 2,
                'inner_h': cpu_height - 2
            },
            'processes': {
                'x': margin,
                'y': system_height + cpu_height + (margin * 3),
                'w': left_col_width,
                'h': process_height,
                'inner_w': left_col_width - 2,
                'inner_h': process_height - 2
            },
            'memory': {
                'x': left_col_width + (margin * 2),
                'y': network_height + (margin * 2),
                'w': right_col_width,
                'h': memory_height,
                'inner_w': right_col_width - 2,
                'inner_h': memory_height - 2
            },
            'network': {
                'x': left_col_width + (margin * 2),
                'y': margin,
                'w': right_col_width,
                'h': network_height,
                'inner_w': right_col_width - 2,
                'inner_h': network_height - 2
            },
            'instructions': {
                'x': left_col_width + (margin * 2),
                'y': network_height + memory_height + (margin * 3),
                'w': right_col_width,
                'h': instructions_height,
                'inner_w': right_col_width - 2,
                'inner_h': instructions_height - 2
            }
        }
        return layout

    def draw_box(self, y, x, h, w, title=''):
        """Draw a box with proper error handling and fallback to ASCII"""
        try:
            chars = self.box_chars['unicode' if self.use_unicode else 'ascii']
            
            # Draw title
            self.stdscr.attron(curses.color_pair(2))
            self.stdscr.addstr(y, x + 2, f" {title} ")
            self.stdscr.attroff(curses.color_pair(2))
            
            # Draw corners
            self.stdscr.addch(y, x, chars['tl'])
            self.stdscr.addch(y, x + w - 1, chars['tr'])
            self.stdscr.addch(y + h - 1, x, chars['bl'])
            self.stdscr.addch(y + h - 1, x + w - 1, chars['br'])
            
            # Draw horizontal lines
            for i in range(x + 1, x + w - 1):
                self.stdscr.addch(y, i, chars['h'])
                self.stdscr.addch(y + h - 1, i, chars['h'])
            
            # Draw vertical lines
            for i in range(y + 1, y + h - 1):
                self.stdscr.addch(i, x, chars['v'])
                self.stdscr.addch(i, x + w - 1, chars['v'])
                
        except curses.error:
            # Silently handle curses errors
            pass

    def draw_size_warning(self, h, w):
        """Draw terminal size warning"""
        msg = f"Terminal too small. Min size: {self.layout['min_width']}x{self.layout['min_height']}"
        self.stdscr.clear()
        self.stdscr.addstr(h//2, (w-len(msg))//2, msg)

    def update_process_section(self, y, x, width, processes, selected_idx):
        """Update process list with sorting, searching, and scrolling"""
        if not processes:
            return

        # Filter processes based on search
        if self.search_term:
            processes = [p for p in processes if self.search_term.lower() in p['name'].lower()]

        # Sort processes
        processes.sort(key=lambda p: p[self.sort_by], reverse=self.sort_reverse)

        # Bound selection and scroll offset
        max_idx = len(processes) - 1
        self.selected_process = min(max_idx, self.selected_process)
        visible_height = self.last_layout['processes']['inner_h'] - 1  # -1 for header
        max_scroll = max(0, len(processes) - visible_height)
        self.process_scroll_offset = min(max_scroll, self.process_scroll_offset)

        # Draw header
        headers = [
            ('PID', 7), ('NAME', 20), ('USER', 10), 
            ('MEM%', 6), ('CPU%', 6), ('STATUS', 8)
        ]
        header_str = ''
        for name, size in headers:
            header_str += f'{name:<{size}}'
        self.stdscr.attron(curses.A_BOLD)
        self.stdscr.addstr(y, x, header_str)
        self.stdscr.attroff(curses.A_BOLD)

        # Draw scrollbar if needed
        if len(processes) > visible_height:
            scrollbar_height = visible_height
            scroll_pos = int((self.process_scroll_offset / max_scroll) * (scrollbar_height - 1))
            for i in range(scrollbar_height):
                char = '█' if i == scroll_pos else '│'
                try:
                    self.stdscr.addstr(y + 1 + i, x + width - 1, char)
                except curses.error:
                    pass

        # Draw visible processes
        visible_processes = processes[self.process_scroll_offset:self.process_scroll_offset + visible_height]
        for idx, proc in enumerate(visible_processes):
            if y + idx + 1 >= curses.LINES - 1:
                break

            # Highlight selected process
            is_selected = idx + self.process_scroll_offset == self.selected_process
            if is_selected:
                self.stdscr.attron(curses.A_REVERSE)

            # Format and draw process line
            line = (f"{proc['pid']:<7}{proc['name']:<20}{proc['username']:<10}"
                   f"{proc['memory_percent']:>6.1f}{proc['cpu_percent']:>6.1f}"
                   f"{proc['status']:<8}")
            self.stdscr.addstr(y + idx + 1, x, line[:width-1])  # -1 for scrollbar

            if is_selected:
                self.stdscr.attroff(curses.A_REVERSE)

        # Draw scroll indicators if needed
        if self.process_scroll_offset > 0:
            self.stdscr.addstr(y, x + width - 3, "↑")
        if self.process_scroll_offset + visible_height < len(processes):
            self.stdscr.addstr(y + visible_height, x + width - 3, "↓")

        # Draw search bar if active
        if self.search_term:
            self.stdscr.addstr(y-1, x, f"Search: {self.search_term}")

    def handle_input(self, key):
        """Handle keyboard input with scrolling"""
        if key == ord('q'):
            return 'quit'
        elif key == ord('k'):
            return 'kill'
        elif key == curses.KEY_UP:
            if self.selected_process > 0:
                self.selected_process -= 1
                if self.selected_process < self.process_scroll_offset:
                    self.process_scroll_offset = self.selected_process
        elif key == curses.KEY_DOWN:
            self.selected_process += 1
            visible_height = self.last_layout['processes']['inner_h']
            if self.selected_process >= self.process_scroll_offset + visible_height:
                self.process_scroll_offset += 1
        elif key == ord('g'):  # Go to top
            self.selected_process = 0
            self.process_scroll_offset = 0
        elif key == ord('G'):  # Go to bottom
            self.selected_process = 99999  # Will be bounded by actual process count
            self.process_scroll_offset = max(0, self.selected_process - visible_height + 1)
        elif key == ord('/'):
            self.search_term = ''
            curses.echo()
            self.search_term = self.stdscr.getstr(0, 0).decode('utf-8')
            curses.noecho()
        elif key == ord('s'):
            sort_options = ['memory_percent', 'cpu_percent', 'pid', 'name']
            current = sort_options.index(self.sort_by)
            self.sort_by = sort_options[(current + 1) % len(sort_options)]
        elif key == ord('r'):
            self.sort_reverse = not self.sort_reverse
        elif key == ord('d'):
            self.show_details = not self.show_details
        
    def update_graphs(self, cpu_percent, memory_percent, load_avg):
        """Update historical data for graphs"""
        timestamp = time.time()
        self.graph_data['cpu'].append((timestamp, cpu_percent))
        self.graph_data['memory'].append((timestamp, memory_percent))
        self.graph_data['load'].append((timestamp, load_avg[0]))

        # Keep only last minute of data
        cutoff = timestamp - 60
        for metric in self.graph_data:
            self.graph_data[metric] = [(t, v) for t, v in self.graph_data[metric] 
                                     if t > cutoff]

    def draw_graph(self, y, x, width, height, data, title):
        """Draw a simple ASCII graph"""
        if not data:
            return

        max_val = max(v for _, v in data)
        min_val = min(v for _, v in data)
        range_val = max(max_val - min_val, 1)

        for i, (_, val) in enumerate(data):
            if i >= width:
                break
            bar_height = int((val - min_val) / range_val * (height - 1))
            for h in range(bar_height):
                self.stdscr.addch(y + height - h - 1, x + i, '|')

    def draw_modern_bar(self, y, x, width, percentage, label="", color_pair=None):
        """Draw a modern-looking progress bar with boundary checking"""
        try:
            # Get color based on percentage if none provided
            if color_pair is None:
                color_pair = self._get_usage_color(percentage)
                
            # Calculate available space
            label_width = len(label) + 2 if label else 0
            percent_width = 7  # Space for percentage display
            available_width = max(0, width - label_width - percent_width)
            
            if available_width <= 0:
                return
            
            # Draw label if we have space
            if label and label_width < width:
                self.stdscr.addstr(y, x, f"{label}: ")
                x += label_width
            
            # Calculate bar width
            filled_width = int(available_width * (percentage / 100))
            empty_width = available_width - filled_width
            
            # Draw bar with color
            if color_pair:
                self.stdscr.attron(color_pair)
            
            # Draw filled portion
            if filled_width > 0:
                self.stdscr.addstr(y, x, self.styles['bars']['fill'] * filled_width)
            
            # Draw empty portion
            if empty_width > 0:
                self.stdscr.addstr(y, x + filled_width, 
                                 self.styles['bars']['empty'] * empty_width)
            
            if color_pair:
                self.stdscr.attroff(color_pair)
            
            # Draw percentage if we have space
            if width >= label_width + available_width + percent_width:
                self.stdscr.addstr(y, x + available_width + 1, 
                                 f"{percentage:3.0f}%")
                
        except curses.error:
            pass

    def update_cpu_section(self, y, x, width, stats):
        """Modernized CPU display with proper layout management"""
        try:
            section = self.last_layout['cpu']
            inner_width = section['inner_w']
            inner_height = section['inner_h']
            
            # Track content size
            content_height = 3 + (len(stats['cores']) + 1) // 2  # Basic height + cores
            content_width = max(35, width)  # Minimum width for core display
            self.update_section_content_size('cpu', content_height, content_width)
            
            # Use inner dimensions for drawing
            self.draw_modern_bar(y, x, inner_width, stats['usage'], "CPU",
                               self._get_usage_color(stats['usage']))
            
            # Get section height from current layout or fallback
            section_height = (self.last_layout['cpu']['h'] if self.last_layout 
                            else self.last_height // 3) - 2  # Account for borders
            
            # Overall CPU usage with color gradient
            color = self._get_usage_color(stats['usage'])
            self.draw_modern_bar(y, x, width, stats['usage'], "CPU", color)
            
            # Calculate core display layout
            cores = stats['cores']
            num_cores = len(cores)
            cores_per_row = max(1, width // 35)  # Dynamically calculate cores per row
            num_rows = (num_cores + cores_per_row - 1) // cores_per_row
            
            # Check if we have enough vertical space
            if num_rows + 2 > section_height:  # +2 for CPU bar and padding
                cores_per_row = max(1, num_cores // (section_height - 2))
                num_rows = (num_cores + cores_per_row - 1) // cores_per_row
            
            # Draw core usage bars
            for idx, core in enumerate(cores):
                row = idx // cores_per_row
                col = idx % cores_per_row
                
                if row < section_height - 1:  # Ensure we don't exceed section height
                    core_x = x + (col * (width // cores_per_row))
                    core_y = y + row + 2  # +2 to leave space for CPU bar
                    
                    core_width = (width // cores_per_row) - 1
                    self.draw_modern_bar(
                        core_y, core_x, core_width,
                        core, f"C{idx}", 
                        self._get_usage_color(core)
                    )

            # Draw additional info if space permits
            info_y = y + num_rows + 2
            if info_y < y + section_height - 1:
                # CPU frequency
                if stats.get('freq_current'):
                    freq_line = f"Freq: {stats['freq_current']:4.1f} MHz"
                    self.stdscr.addstr(info_y, x, freq_line[:width])

                # Load average
                if stats.get('load_avg'):
                    load_y = info_y + 1
                    if load_y < y + section_height:
                        load_line = (f"Load: {stats['load_avg'][0]:.2f} "
                                   f"{stats['load_avg'][1]:.2f} "
                                   f"{stats['load_avg'][2]:.2f}")
                        self.stdscr.addstr(load_y, x, load_line[:width])
                    
        except curses.error:
            pass

    def update_memory_section(self, y, x, width, mem_percent, swap_percent):
        """Update memory section with usage bars"""
        try:
            section = self.last_layout['memory']
            inner_width = section['inner_w']
            
            # Track content size
            content_height = 4  # Two bars plus padding
            content_width = max(30, width)  # Minimum width for memory bars
            self.update_section_content_size('memory', content_height, content_width)
            
            # Use inner dimensions for drawing
            self.draw_modern_bar(y, x, inner_width, mem_percent, "RAM",
                               self._get_usage_color(mem_percent))
            self.draw_modern_bar(y + 1, x, inner_width, swap_percent, "Swap",
                               self._get_usage_color(swap_percent))
        except curses.error:
            pass

    def update_system_info(self, y, x, width, info):
        """Update system information section"""
        try:
            lines = info.split('\n')
            for idx, line in enumerate(lines):
                if y + idx >= curses.LINES - 1:
                    break
                self.stdscr.addstr(y + idx, x, line[:width])
        except curses.error:
            pass

    def update_network_section(self, y, x, width, data):
        """Update network bandwidth information"""
        try:
            bandwidth_data, interfaces = data
            
            # Show current bandwidth
            self.stdscr.addstr(y, x, f"Bandwidth(KB/s): {bandwidth_data}")
            
            # Show only first interface (or most important one)
            primary_interface = next(iter(interfaces.items()))
            self.stdscr.addstr(y + 1, x, f"{primary_interface[0]}: {primary_interface[1]}")
            
        except curses.error:
            pass

    def _get_scaled_dimension(self, base_size, available_space, min_size=1):
        """Scale dimensions based on available space"""
        return max(min_size, int(base_size * (available_space / 100)))

    def handle_resize(self):
        """Improved resize handling with layout updates"""
        curses.update_lines_cols()
        new_h, new_w = self.stdscr.getmaxyx()
        
        # Only recalculate if dimensions actually changed
        if new_h != self.last_height or new_w != self.last_width:
            self.stdscr.clear()
            self.last_height, self.last_width = new_h, new_w
            
            # Recreate buffer with new dimensions
            if self.buffer:
                del self.buffer
            self.buffer = curses.newpad(new_h, new_w)
            
            # Calculate and store new layout
            self.last_layout = self.get_layout(new_h, new_w)
            return self.last_layout
        return None

    def refresh(self):
        """Explicit refresh of the screen"""
        try:
            self.stdscr.noutrefresh()
            curses.doupdate()
        except curses.error:
            pass

    def _get_usage_color(self, percentage):
        """Get appropriate color based on usage percentage"""
        try:
            if percentage < self.color_thresholds['normal']:
                return self.usage_colors['low']
            elif percentage < self.color_thresholds['warning']:
                return self.usage_colors['medium']
            return self.usage_colors['high']
        except (TypeError, ValueError):
            return self.usage_colors['low']  # Default to green on error

    def update_section_content_size(self, section, content_h, content_w):
        """Update the minimum size requirements for a section based on its content"""
        if section in self.content_sizes:
            self.content_sizes[section]['min_h'] = max(
                self.content_sizes[section]['min_h'],
                content_h + 2  # Add padding
            )
            self.content_sizes[section]['min_w'] = max(
                self.content_sizes[section]['min_w'],
                content_w + 2  # Add padding
            )

    def draw_instructions(self):
        """Draw instructions panel"""
        try:
            section = self.last_layout['instructions']
            start_y = section['y'] + 1
            start_x = section['x'] + 1
            
            for idx, line in enumerate(self.instructions):
                if idx == 0:
                    self.stdscr.attron(curses.A_BOLD | curses.color_pair(2))
                self.stdscr.addstr(start_y + idx, start_x, line)
                if idx == 0:
                    self.stdscr.attroff(curses.A_BOLD | curses.color_pair(2))
                    
        except curses.error:
            pass