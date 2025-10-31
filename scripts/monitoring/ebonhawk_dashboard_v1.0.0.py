#!/usr/bin/env python3
"""
Ebonhawk Monitoring Dashboard
Real-time system monitoring dashboard for ebonhawk
"""

import os
import sys
import json
import time
import curses
from datetime import datetime
from pathlib import Path
from typing import Dict, List

try:
    import psutil
except ImportError:
    print("Error: psutil required. Install with: pip3 install psutil")
    sys.exit(1)

class EbonhawkDashboard:
    """Terminal dashboard for ebonhawk monitoring"""
    
    def __init__(self):
        self.data_path = Path.home() / ".ebonhawk-maintenance" / "data"
        self.running = True
        
    def get_system_stats(self) -> Dict:
        """Get current system statistics"""
        stats = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'hostname': 'ebonhawk',
            'cpu_percent': psutil.cpu_percent(interval=1),
            'cpu_freq': psutil.cpu_freq().current if psutil.cpu_freq() else 0,
            'memory': psutil.virtual_memory(),
            'disk': psutil.disk_usage('/'),
            'network': psutil.net_io_counters(),
            'load_avg': os.getloadavg(),
            'processes': len(psutil.pids()),
            'boot_time': datetime.fromtimestamp(psutil.boot_time())
        }
        
        # Get temperatures if available
        try:
            temps = psutil.sensors_temperatures()
            if temps:
                for name, entries in temps.items():
                    for entry in entries:
                        if entry.label in ['Core 0', 'CPU', 'Package']:
                            stats['temperature'] = entry.current
                            break
        except:
            stats['temperature'] = None
            
        return stats
    
    def get_top_processes(self, n=5) -> List[Dict]:
        """Get top N processes by CPU usage"""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                pinfo = proc.info
                if pinfo['cpu_percent'] > 0:
                    processes.append(pinfo)
            except:
                pass
        
        return sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)[:n]
    
    def draw_dashboard(self, stdscr):
        """Draw the dashboard interface"""
        curses.curs_set(0)  # Hide cursor
        stdscr.nodelay(1)    # Non-blocking input
        
        # Colors
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_CYAN, curses.COLOR_BLACK)
        
        while self.running:
            try:
                stdscr.clear()
                height, width = stdscr.getmaxyx()
                
                # Get stats
                stats = self.get_system_stats()
                top_procs = self.get_top_processes()
                
                # Title
                title = "EBONHAWK SYSTEM MONITOR"
                stdscr.addstr(0, (width - len(title)) // 2, title, curses.A_BOLD | curses.color_pair(4))
                stdscr.addstr(1, (width - len(stats['timestamp'])) // 2, stats['timestamp'])
                
                # System Info
                row = 3
                stdscr.addstr(row, 2, "SYSTEM INFORMATION", curses.A_BOLD)
                row += 1
                stdscr.addstr(row, 2, "-" * 40)
                row += 1
                
                uptime = datetime.now() - stats['boot_time']
                days = uptime.days
                hours = uptime.seconds // 3600
                minutes = (uptime.seconds % 3600) // 60
                
                stdscr.addstr(row, 2, f"Hostname: {stats['hostname']}")
                row += 1
                stdscr.addstr(row, 2, f"Uptime: {days}d {hours}h {minutes}m")
                row += 1
                stdscr.addstr(row, 2, f"Processes: {stats['processes']}")
                row += 2
                
                # CPU
                stdscr.addstr(row, 2, "CPU", curses.A_BOLD)
                row += 1
                cpu_bar = self.make_bar(stats['cpu_percent'], 30)
                cpu_color = self.get_color(stats['cpu_percent'], 75, 90)
                stdscr.addstr(row, 2, f"Usage: {cpu_bar} {stats['cpu_percent']:5.1f}%", curses.color_pair(cpu_color))
                row += 1
                stdscr.addstr(row, 2, f"Frequency: {stats['cpu_freq']:.0f} MHz")
                row += 1
                stdscr.addstr(row, 2, f"Load Average: {stats['load_avg'][0]:.2f}, {stats['load_avg'][1]:.2f}, {stats['load_avg'][2]:.2f}")
                row += 1
                if stats['temperature']:
                    temp_color = self.get_color(stats['temperature'], 65, 75)
                    stdscr.addstr(row, 2, f"Temperature: {stats['temperature']:.1f}°C", curses.color_pair(temp_color))
                    row += 1
                row += 1
                
                # Memory
                stdscr.addstr(row, 2, "MEMORY", curses.A_BOLD)
                row += 1
                mem = stats['memory']
                mem_percent = mem.percent
                mem_bar = self.make_bar(mem_percent, 30)
                mem_color = self.get_color(mem_percent, 80, 90)
                stdscr.addstr(row, 2, f"Usage: {mem_bar} {mem_percent:5.1f}%", curses.color_pair(mem_color))
                row += 1
                stdscr.addstr(row, 2, f"Used: {mem.used / (1024**3):.1f} GB / {mem.total / (1024**3):.1f} GB")
                row += 2
                
                # Disk
                stdscr.addstr(row, 2, "DISK", curses.A_BOLD)
                row += 1
                disk = stats['disk']
                disk_bar = self.make_bar(disk.percent, 30)
                disk_color = self.get_color(disk.percent, 80, 90)
                stdscr.addstr(row, 2, f"Usage: {disk_bar} {disk.percent:5.1f}%", curses.color_pair(disk_color))
                row += 1
                stdscr.addstr(row, 2, f"Used: {disk.used / (1024**3):.1f} GB / {disk.total / (1024**3):.1f} GB")
                row += 2
                
                # Network
                stdscr.addstr(row, 2, "NETWORK", curses.A_BOLD)
                row += 1
                net = stats['network']
                stdscr.addstr(row, 2, f"Sent: {net.bytes_sent / (1024**3):.2f} GB")
                row += 1
                stdscr.addstr(row, 2, f"Recv: {net.bytes_recv / (1024**3):.2f} GB")
                row += 2
                
                # Top Processes
                if row < height - 8:
                    stdscr.addstr(row, 2, "TOP PROCESSES", curses.A_BOLD)
                    row += 1
                    stdscr.addstr(row, 2, "-" * 60)
                    row += 1
                    stdscr.addstr(row, 2, "PID     CPU%   MEM%   NAME")
                    row += 1
                    
                    for proc in top_procs:
                        if row < height - 2:
                            proc_str = f"{proc['pid']:<7} {proc['cpu_percent']:5.1f}  {proc['memory_percent']:5.1f}  {proc['name'][:30]}"
                            stdscr.addstr(row, 2, proc_str)
                            row += 1
                
                # Footer
                footer = "Press 'q' to quit | Refreshes every 2 seconds"
                stdscr.addstr(height - 1, (width - len(footer)) // 2, footer, curses.A_DIM)
                
                stdscr.refresh()
                
                # Check for quit
                key = stdscr.getch()
                if key == ord('q'):
                    self.running = False
                    break
                
                time.sleep(2)
                
            except curses.error:
                pass
            except KeyboardInterrupt:
                self.running = False
                break
    
    def make_bar(self, percent, width) -> str:
        """Create a progress bar"""
        filled = int(width * percent / 100)
        bar = '█' * filled + '░' * (width - filled)
        return f"[{bar}]"
    
    def get_color(self, value, warning, critical) -> int:
        """Get color based on thresholds"""
        if value >= critical:
            return 3  # Red
        elif value >= warning:
            return 2  # Yellow
        else:
            return 1  # Green
    
    def run(self):
        """Run the dashboard"""
        try:
            curses.wrapper(self.draw_dashboard)
        except KeyboardInterrupt:
            pass
        finally:
            print("\nDashboard closed.")

def main():
    """Main entry point"""
    dashboard = EbonhawkDashboard()
    dashboard.run()

if __name__ == "__main__":
    main()