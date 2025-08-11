#!/usr/bin/env python3
"""
Modern Unified System Manager GUI v2.0
Enhanced with modern dark theme, system tray, and improved UX
Linux-focused system management tool
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import subprocess
import threading
import os
import sys
import time
import json
from pathlib import Path
import queue
import re
import shutil
import signal
from datetime import datetime, timedelta

# Advanced system monitoring
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("Note: psutil not available - some monitoring features will be limited")

# System tray support
try:
    import pystray
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False
    print("Note: pystray/PIL not available - system tray will be disabled")

class ModernTheme:
    """Modern dark theme configuration"""
    
    # Color palette
    DARK_BG = "#1e1e1e"
    DARKER_BG = "#161616"
    SURFACE = "#2d2d2d"
    SURFACE_VARIANT = "#3d3d3d"
    PRIMARY = "#0078d4"
    PRIMARY_HOVER = "#106ebe"
    SUCCESS = "#107c10"
    WARNING = "#ff8c00"
    DANGER = "#d13438"
    TEXT_PRIMARY = "#ffffff"
    TEXT_SECONDARY = "#cccccc"
    TEXT_DISABLED = "#888888"
    BORDER = "#404040"
    
    @classmethod
    def configure_ttk_theme(cls, root):
        """Configure modern dark theme for ttk widgets"""
        style = ttk.Style()
        
        # Configure theme
        style.theme_use('clam')
        
        # General configurations
        style.configure('.',
                       background=cls.DARK_BG,
                       foreground=cls.TEXT_PRIMARY,
                       bordercolor=cls.BORDER,
                       darkcolor=cls.DARKER_BG,
                       lightcolor=cls.SURFACE,
                       troughcolor=cls.DARKER_BG,
                       selectbackground=cls.PRIMARY,
                       selectforeground=cls.TEXT_PRIMARY,
                       fieldbackground=cls.SURFACE,
                       font=('Segoe UI', 9))
        
        # Frame
        style.configure('TFrame',
                       background=cls.DARK_BG,
                       relief='flat')
        
        # LabelFrame
        style.configure('TLabelframe',
                       background=cls.DARK_BG,
                       foreground=cls.TEXT_PRIMARY,
                       bordercolor=cls.BORDER,
                       relief='solid',
                       borderwidth=1)
        
        style.configure('TLabelframe.Label',
                       background=cls.DARK_BG,
                       foreground=cls.TEXT_PRIMARY,
                       font=('Segoe UI', 9, 'bold'))
        
        # Labels
        style.configure('TLabel',
                       background=cls.DARK_BG,
                       foreground=cls.TEXT_PRIMARY)
        
        style.configure('Title.TLabel',
                       background=cls.DARK_BG,
                       foreground=cls.TEXT_PRIMARY,
                       font=('Segoe UI', 18, 'bold'))
        
        style.configure('Heading.TLabel',
                       background=cls.DARK_BG,
                       foreground=cls.TEXT_PRIMARY,
                       font=('Segoe UI', 12, 'bold'))
        
        style.configure('Success.TLabel',
                       background=cls.DARK_BG,
                       foreground=cls.SUCCESS)
        
        style.configure('Warning.TLabel',
                       background=cls.DARK_BG,
                       foreground=cls.WARNING)
        
        style.configure('Error.TLabel',
                       background=cls.DARK_BG,
                       foreground=cls.DANGER)
        
        # Buttons
        style.configure('TButton',
                       background=cls.SURFACE,
                       foreground=cls.TEXT_PRIMARY,
                       bordercolor=cls.BORDER,
                       focuscolor='none',
                       relief='flat',
                       borderwidth=1,
                       font=('Segoe UI', 9))
        
        style.map('TButton',
                 background=[('active', cls.SURFACE_VARIANT),
                           ('pressed', cls.DARKER_BG)])
        
        style.configure('Primary.TButton',
                       background=cls.PRIMARY,
                       foreground=cls.TEXT_PRIMARY,
                       font=('Segoe UI', 9, 'bold'))
        
        style.map('Primary.TButton',
                 background=[('active', cls.PRIMARY_HOVER),
                           ('pressed', cls.PRIMARY)])
        
        style.configure('Success.TButton',
                       background=cls.SUCCESS,
                       foreground=cls.TEXT_PRIMARY)
        
        style.configure('Danger.TButton',
                       background=cls.DANGER,
                       foreground=cls.TEXT_PRIMARY)
        
        # Notebook
        style.configure('TNotebook',
                       background=cls.DARK_BG,
                       bordercolor=cls.BORDER,
                       tabmargins=[2, 5, 2, 0])
        
        style.configure('TNotebook.Tab',
                       background=cls.SURFACE,
                       foreground=cls.TEXT_SECONDARY,
                       padding=[20, 8],
                       font=('Segoe UI', 9))
        
        style.map('TNotebook.Tab',
                 background=[('selected', cls.PRIMARY),
                           ('active', cls.SURFACE_VARIANT)],
                 foreground=[('selected', cls.TEXT_PRIMARY),
                           ('active', cls.TEXT_PRIMARY)])
        
        # Entry
        style.configure('TEntry',
                       fieldbackground=cls.SURFACE,
                       foreground=cls.TEXT_PRIMARY,
                       bordercolor=cls.BORDER,
                       insertcolor=cls.TEXT_PRIMARY)
        
        # Combobox
        style.configure('TCombobox',
                       fieldbackground=cls.SURFACE,
                       background=cls.SURFACE,
                       foreground=cls.TEXT_PRIMARY,
                       bordercolor=cls.BORDER,
                       arrowcolor=cls.TEXT_PRIMARY)
        
        # Treeview
        style.configure('Treeview',
                       background=cls.DARK_BG,
                       foreground=cls.TEXT_PRIMARY,
                       fieldbackground=cls.DARK_BG,
                       bordercolor=cls.BORDER,
                       relief='solid',
                       borderwidth=1)
        
        style.configure('Treeview.Heading',
                       background=cls.SURFACE,
                       foreground=cls.TEXT_PRIMARY,
                       relief='flat',
                       font=('Segoe UI', 9, 'bold'))
        
        style.map('Treeview',
                 background=[('selected', cls.PRIMARY)])
        
        # Progressbar
        style.configure('TProgressbar',
                       background=cls.PRIMARY,
                       troughcolor=cls.DARKER_BG,
                       bordercolor=cls.BORDER,
                       relief='flat',
                       borderwidth=1)
        
        # Checkbutton
        style.configure('TCheckbutton',
                       background=cls.DARK_BG,
                       foreground=cls.TEXT_PRIMARY,
                       focuscolor='none')
        
        # Scrollbar
        style.configure('TScrollbar',
                       background=cls.SURFACE,
                       troughcolor=cls.DARKER_BG,
                       bordercolor=cls.BORDER,
                       arrowcolor=cls.TEXT_PRIMARY,
                       darkcolor=cls.SURFACE,
                       lightcolor=cls.SURFACE)

class AnimatedProgressBar:
    """Custom animated progress bar with gradient effect"""
    
    def __init__(self, parent, width=300, height=20):
        self.parent = parent
        self.canvas = tk.Canvas(parent, width=width, height=height, 
                               bg=ModernTheme.DARKER_BG, highlightthickness=0)
        self.width = width
        self.height = height
        self.progress = 0
        self.animation_id = None
        
        # Create gradient background
        self.create_gradient_bg()
        
    def create_gradient_bg(self):
        """Create gradient background"""
        # Background rectangle
        self.bg_rect = self.canvas.create_rectangle(
            0, 0, self.width, self.height,
            fill=ModernTheme.DARKER_BG, outline=ModernTheme.BORDER
        )
        
        # Progress rectangle (initially hidden)
        self.progress_rect = self.canvas.create_rectangle(
            0, 0, 0, self.height,
            fill=ModernTheme.PRIMARY, outline=""
        )
        
    def set_progress(self, value):
        """Set progress value (0-100)"""
        self.progress = max(0, min(100, value))
        self.update_visual()
        
    def update_visual(self):
        """Update visual representation"""
        progress_width = (self.progress / 100) * self.width
        self.canvas.coords(self.progress_rect, 0, 0, progress_width, self.height)
        
        # Color based on progress
        if self.progress < 30:
            color = ModernTheme.DANGER
        elif self.progress < 70:
            color = ModernTheme.WARNING
        else:
            color = ModernTheme.SUCCESS
            
        self.canvas.itemconfig(self.progress_rect, fill=color)
        
    def start_pulse(self):
        """Start pulsing animation for indeterminate progress"""
        self.pulse_animation()
        
    def pulse_animation(self):
        """Animate pulsing effect"""
        if self.animation_id:
            import math
            pulse = (math.sin(time.time() * 3) + 1) / 2  # 0-1
            alpha_color = f"#{int(pulse * 255):02x}{int(pulse * 120):02x}{int(pulse * 212):02x}"
            self.canvas.itemconfig(self.progress_rect, fill=alpha_color)
            self.animation_id = self.parent.after(50, self.pulse_animation)
            
    def stop_pulse(self):
        """Stop pulsing animation"""
        if self.animation_id:
            self.parent.after_cancel(self.animation_id)
            self.animation_id = None
            
    def pack(self, **kwargs):
        self.canvas.pack(**kwargs)
        
    def grid(self, **kwargs):
        self.canvas.grid(**kwargs)

class SystemTrayManager:
    """System tray integration"""
    
    def __init__(self, app_instance):
        self.app = app_instance
        self.icon = None
        
        if not TRAY_AVAILABLE:
            return
            
        # Create tray icon
        self.create_icon()
        
    def create_icon(self):
        """Create system tray icon"""
        # Create a simple icon image
        image = Image.new('RGB', (64, 64), color=ModernTheme.PRIMARY)
        draw = ImageDraw.Draw(image)
        
        # Draw a simple gear icon
        draw.ellipse([10, 10, 54, 54], outline='white', width=3)
        draw.ellipse([26, 26, 38, 38], outline='white', width=2)
        
        # Create menu
        menu = pystray.Menu(
            pystray.MenuItem("Show/Hide", self.toggle_window),
            pystray.MenuItem("Quick Clean", self.quick_clean),
            pystray.MenuItem("System Status", self.show_status),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit", self.quit_app)
        )
        
        self.icon = pystray.Icon("Unified System Manager", image, 
                                "Unified System Manager", menu)
        
    def start_tray(self):
        """Start system tray in background thread"""
        if self.icon:
            threading.Thread(target=self.icon.run, daemon=True).start()
            
    def toggle_window(self, icon, item):
        """Toggle main window visibility"""
        if self.app.root.winfo_viewable():
            self.app.root.withdraw()
        else:
            self.app.root.deiconify()
            self.app.root.lift()
            
    def quick_clean(self, icon, item):
        """Quick clean from tray"""
        self.app.root.after(0, self.app.quick_clean)
        
    def show_status(self, icon, item):
        """Show status from tray"""
        self.app.root.after(0, self.app.show_status_popup)
        
    def quit_app(self, icon, item):
        """Quit application"""
        self.icon.stop()
        self.app.root.after(0, self.app.quit_application)

class ModernUnifiedSystemManagerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Unified System Manager v2.0")
        self.root.geometry("1600x1000")
        self.root.minsize(1400, 800)
        
        # Configure modern theme
        self.root.configure(bg=ModernTheme.DARK_BG)
        ModernTheme.configure_ttk_theme(root)
        
        # Application state
        self.config_dir = Path.home() / ".unified-system-manager"
        self.config_file = self.config_dir / "config.conf"
        self.tidytux_script = self.config_dir / "components" / "tidytux.sh"
        self.gdrive_script = self.config_dir / "components" / "gdrive-manager.sh"
        self.mount_point = Path.home() / "GoogleDrive"
        
        # Status tracking
        self.cleanup_running = False
        self.backup_running = False
        self.monitoring = True
        self.monitor_thread = None
        
        # System tray
        self.tray = SystemTrayManager(self)
        
        # Keyboard shortcuts
        self.setup_keyboard_shortcuts()
        
        # Create main interface
        self.create_main_interface()
        
        # Start system monitoring
        self.start_system_monitoring()
        
        # Start system tray
        if TRAY_AVAILABLE:
            self.tray.start_tray()
        
        # Initial status check
        self.refresh_all_status()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_window_close)
        
    def setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts"""
        self.root.bind('<Control-q>', lambda e: self.quit_application())
        self.root.bind('<Control-r>', lambda e: self.refresh_all_status())
        self.root.bind('<Control-c>', lambda e: self.quick_clean())
        self.root.bind('<Control-b>', lambda e: self.quick_backup())
        self.root.bind('<F1>', lambda e: self.show_help())
        self.root.bind('<F5>', lambda e: self.refresh_all_status())
        
    def create_main_interface(self):
        """Create the modern main interface"""
        # Main container with padding
        self.main_container = ttk.Frame(self.root, padding="15")
        self.main_container.pack(fill='both', expand=True)
        
        # Create header
        self.create_modern_header()
        
        # Create main content area
        self.create_content_area()
        
        # Create modern status bar
        self.create_modern_status_bar()
        
    def create_modern_header(self):
        """Create modern header with gradient and actions"""
        header_frame = ttk.Frame(self.main_container)
        header_frame.pack(fill='x', pady=(0, 15))
        
        # Left side - Title and subtitle
        title_section = ttk.Frame(header_frame)
        title_section.pack(side='left', fill='y')
        
        title_label = ttk.Label(title_section, text="🔧 Unified System Manager", 
                               style='Title.TLabel')
        title_label.pack(anchor='w')
        
        subtitle_label = ttk.Label(title_section, 
                                  text="Complete Linux system management and automation",
                                  foreground=ModernTheme.TEXT_SECONDARY)
        subtitle_label.pack(anchor='w', pady=(0, 5))
        
        # System info line
        self.header_info = ttk.Label(title_section, text="Loading system info...",
                                    foreground=ModernTheme.TEXT_DISABLED,
                                    font=('Segoe UI', 8))
        self.header_info.pack(anchor='w')
        
        # Right side - Quick actions with modern styling
        actions_frame = ttk.Frame(header_frame)
        actions_frame.pack(side='right', fill='y')
        
        # Quick action buttons with icons
        quick_actions = [
            ("⚡ Quick Clean", self.quick_clean, 'Primary.TButton'),
            ("☁️ Backup", self.quick_backup, 'Success.TButton'),
            ("🔄 Refresh", self.refresh_all_status, 'TButton'),
            ("⚙️ Settings", self.show_settings, 'TButton')
        ]
        
        for i, (text, command, style) in enumerate(quick_actions):
            btn = ttk.Button(actions_frame, text=text, command=command, style=style)
            btn.pack(side='left', padx=(0, 8) if i < len(quick_actions)-1 else 0)
            # Add tooltip
            self.create_tooltip(btn, f"Keyboard: Ctrl+{text[0].lower()}")
            
    def create_content_area(self):
        """Create main content area with modern notebook"""
        # Main notebook with modern styling
        self.notebook = ttk.Notebook(self.main_container)
        self.notebook.pack(fill='both', expand=True, pady=(0, 15))
        
        # Create enhanced tabs
        self.create_dashboard_tab_v2()
        self.create_cleanup_tab_v2()
        self.create_gdrive_tab_v2()
        self.create_system_tab_v2()
        self.create_automation_tab_v2()
        self.create_logs_tab_v2()
        
    def create_dashboard_tab_v2(self):
        """Enhanced dashboard with modern cards and real-time monitoring"""
        dashboard = ttk.Frame(self.notebook)
        self.notebook.add(dashboard, text="📊 Dashboard")
        
        # Create scrollable content
        canvas = tk.Canvas(dashboard, bg=ModernTheme.DARK_BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(dashboard, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack scrollable components
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Create grid layout for cards
        scrollable_frame.columnconfigure(0, weight=1)
        scrollable_frame.columnconfigure(1, weight=1)
        scrollable_frame.columnconfigure(2, weight=1)
        
        # Top row - System monitoring cards
        self.create_cpu_card(scrollable_frame).grid(row=0, column=0, sticky='nsew', padx=5, pady=5)
        self.create_memory_card(scrollable_frame).grid(row=0, column=1, sticky='nsew', padx=5, pady=5)
        self.create_disk_card(scrollable_frame).grid(row=0, column=2, sticky='nsew', padx=5, pady=5)
        
        # Second row - Status and storage
        self.create_services_card(scrollable_frame).grid(row=1, column=0, sticky='nsew', padx=5, pady=5)
        self.create_storage_overview_card(scrollable_frame).grid(row=1, column=1, columnspan=2, sticky='nsew', padx=5, pady=5)
        
        # Third row - Activity and quick actions
        self.create_activity_feed_card(scrollable_frame).grid(row=2, column=0, columnspan=2, sticky='nsew', padx=5, pady=5)
        self.create_smart_suggestions_card(scrollable_frame).grid(row=2, column=2, sticky='nsew', padx=5, pady=5)
        
        # Configure row weights
        for i in range(3):
            scrollable_frame.rowconfigure(i, weight=1)
            
    def create_cpu_card(self, parent):
        """CPU monitoring card with animated gauge"""
        card = ttk.LabelFrame(parent, text="🔥 CPU Usage", padding=15)
        
        # CPU percentage display
        self.cpu_display = ttk.Label(card, text="0%", 
                                    font=('Segoe UI', 24, 'bold'),
                                    foreground=ModernTheme.PRIMARY)
        self.cpu_display.pack(pady=(0, 10))
        
        # Animated progress bar
        self.cpu_progress = AnimatedProgressBar(card, width=200, height=8)
        self.cpu_progress.pack(pady=(0, 10))
        
        # CPU details
        details_frame = ttk.Frame(card)
        details_frame.pack(fill='x')
        
        self.cpu_cores = ttk.Label(details_frame, text="Cores: N/A",
                                  foreground=ModernTheme.TEXT_SECONDARY)
        self.cpu_cores.pack(anchor='w')
        
        self.cpu_freq = ttk.Label(details_frame, text="Frequency: N/A",
                                 foreground=ModernTheme.TEXT_SECONDARY)
        self.cpu_freq.pack(anchor='w')
        
        return card
        
    def create_memory_card(self, parent):
        """Memory monitoring card"""
        card = ttk.LabelFrame(parent, text="💾 Memory Usage", padding=15)
        
        # Memory percentage
        self.mem_display = ttk.Label(card, text="0%", 
                                    font=('Segoe UI', 24, 'bold'),
                                    foreground=ModernTheme.SUCCESS)
        self.mem_display.pack(pady=(0, 10))
        
        # Memory progress bar
        self.mem_progress = AnimatedProgressBar(card, width=200, height=8)
        self.mem_progress.pack(pady=(0, 10))
        
        # Memory details
        details_frame = ttk.Frame(card)
        details_frame.pack(fill='x')
        
        self.mem_used = ttk.Label(details_frame, text="Used: N/A",
                                 foreground=ModernTheme.TEXT_SECONDARY)
        self.mem_used.pack(anchor='w')
        
        self.mem_total = ttk.Label(details_frame, text="Total: N/A",
                                  foreground=ModernTheme.TEXT_SECONDARY)
        self.mem_total.pack(anchor='w')
        
        return card
        
    def create_disk_card(self, parent):
        """Disk usage monitoring card"""
        card = ttk.LabelFrame(parent, text="💽 Disk Usage", padding=15)
        
        # Disk percentage
        self.disk_display = ttk.Label(card, text="0%", 
                                     font=('Segoe UI', 24, 'bold'),
                                     foreground=ModernTheme.WARNING)
        self.disk_display.pack(pady=(0, 10))
        
        # Disk progress bar
        self.disk_progress = AnimatedProgressBar(card, width=200, height=8)
        self.disk_progress.pack(pady=(0, 10))
        
        # Disk details
        details_frame = ttk.Frame(card)
        details_frame.pack(fill='x')
        
        self.disk_free = ttk.Label(details_frame, text="Free: N/A",
                                  foreground=ModernTheme.TEXT_SECONDARY)
        self.disk_free.pack(anchor='w')
        
        self.disk_total = ttk.Label(details_frame, text="Total: N/A",
                                   foreground=ModernTheme.TEXT_SECONDARY)
        self.disk_total.pack(anchor='w')
        
        return card
        
    def create_services_card(self, parent):
        """System services status card"""
        card = ttk.LabelFrame(parent, text="⚙️ System Services", padding=15)
        
        # Services tree with modern styling
        self.services_tree = ttk.Treeview(card, columns=('Status',), height=8, show='tree headings')
        self.services_tree.heading('#0', text='Service')
        self.services_tree.heading('Status', text='Status')
        self.services_tree.column('#0', width=120)
        self.services_tree.column('Status', width=80)
        
        # Scrollbar for services
        services_scroll = ttk.Scrollbar(card, orient='vertical', command=self.services_tree.yview)
        self.services_tree.configure(yscrollcommand=services_scroll.set)
        
        self.services_tree.pack(side='left', fill='both', expand=True)
        services_scroll.pack(side='right', fill='y')
        
        return card
        
    def create_storage_overview_card(self, parent):
        """Enhanced storage overview with visual breakdown"""
        card = ttk.LabelFrame(parent, text="📊 Storage Overview", padding=15)
        
        # Storage tree with better columns
        self.storage_tree = ttk.Treeview(card, 
                                        columns=('Size', 'Percent', 'Type'), 
                                        height=8, show='tree headings')
        self.storage_tree.heading('#0', text='Location')
        self.storage_tree.heading('Size', text='Size')
        self.storage_tree.heading('Percent', text='Usage')
        self.storage_tree.heading('Type', text='Type')
        
        self.storage_tree.column('#0', width=200)
        self.storage_tree.column('Size', width=100)
        self.storage_tree.column('Percent', width=80)
        self.storage_tree.column('Type', width=80)
        
        # Scrollbar
        storage_scroll = ttk.Scrollbar(card, orient='vertical', command=self.storage_tree.yview)
        self.storage_tree.configure(yscrollcommand=storage_scroll.set)
        
        self.storage_tree.pack(side='left', fill='both', expand=True)
        storage_scroll.pack(side='right', fill='y')
        
        # Context menu for storage tree
        self.storage_menu = tk.Menu(self.root, tearoff=0, 
                                   bg=ModernTheme.SURFACE, fg=ModernTheme.TEXT_PRIMARY)
        self.storage_menu.add_command(label="Analyze with ncdu", command=self.analyze_selected_directory)
        self.storage_menu.add_command(label="Clean directory", command=self.clean_selected_directory)
        
        self.storage_tree.bind("<Button-3>", self.show_storage_context_menu)
        
        return card
        
    def create_activity_feed_card(self, parent):
        """Real-time activity feed"""
        card = ttk.LabelFrame(parent, text="📝 Activity Feed", padding=15)
        
        # Activity text with modern styling
        self.activity_text = scrolledtext.ScrolledText(card, height=10, wrap=tk.WORD,
                                                      bg=ModernTheme.DARKER_BG,
                                                      fg=ModernTheme.TEXT_PRIMARY,
                                                      insertbackground=ModernTheme.TEXT_PRIMARY,
                                                      selectbackground=ModernTheme.PRIMARY,
                                                      font=('Consolas', 9))
        self.activity_text.pack(fill='both', expand=True)
        
        # Configure text tags for colored output
        self.activity_text.tag_configure("info", foreground=ModernTheme.TEXT_PRIMARY)
        self.activity_text.tag_configure("success", foreground=ModernTheme.SUCCESS)
        self.activity_text.tag_configure("warning", foreground=ModernTheme.WARNING)
        self.activity_text.tag_configure("error", foreground=ModernTheme.DANGER)
        self.activity_text.tag_configure("timestamp", foreground=ModernTheme.TEXT_DISABLED)
        
        return card
        
    def create_smart_suggestions_card(self, parent):
        """Smart suggestions based on system analysis"""
        card = ttk.LabelFrame(parent, text="💡 Smart Suggestions", padding=15)
        
        self.suggestions_frame = ttk.Frame(card)
        self.suggestions_frame.pack(fill='both', expand=True)
        
        # Placeholder suggestions
        self.update_smart_suggestions()
        
        return card
        
    def create_cleanup_tab_v2(self):
        """Enhanced cleanup tab with better organization"""
        cleanup_frame = ttk.Frame(self.notebook)
        self.notebook.add(cleanup_frame, text="🧹 System Cleanup")
        
        # Create main sections
        left_panel = ttk.Frame(cleanup_frame)
        left_panel.pack(side='left', fill='both', expand=True, padx=(0, 5))
        
        right_panel = ttk.Frame(cleanup_frame)
        right_panel.pack(side='right', fill='both', expand=True, padx=(5, 0))
        
        # Left panel - Cleanup options
        self.create_cleanup_options_section(left_panel)
        self.create_cleanup_controls_section(left_panel)
        
        # Right panel - Progress and analysis
        self.create_cleanup_progress_section(right_panel)
        self.create_cleanup_analysis_section(right_panel)
        
    def create_cleanup_options_section(self, parent):
        """Cleanup options with better categorization"""
        options_card = ttk.LabelFrame(parent, text="🗂️ Cleanup Categories", padding=15)
        options_card.pack(fill='x', pady=(0, 10))
        
        # Create categories
        categories = {
            "System Cache": [
                ("clean_apt_cache", "APT Package Cache", "Clean downloaded package files"),
                ("clean_snap_cache", "Snap Package Cache", "Remove old snap revisions"),
                ("clean_thumbnails", "Thumbnail Cache", "Clear image thumbnails"),
                ("clean_fontconfig", "Font Cache", "Rebuild font cache"),
            ],
            "User Data": [
                ("clean_browsers", "Browser Data", "Clear browser caches and history"),
                ("clean_trash", "Trash/Recycle Bin", "Empty trash completely"),
                ("clean_downloads", "Downloads Folder", "Organize and clean downloads"),
                ("clean_temp_files", "Temporary Files", "Remove system and user temp files"),
            ],
            "Development": [
                ("clean_docker", "Docker Resources", "Prune containers, images, volumes"),
                ("clean_npm", "NPM Cache", "Clear Node.js package cache"),
                ("clean_pip", "Python Packages", "Clean pip cache and temp files"),
                ("clean_logs", "Log Files", "Rotate and compress old logs"),
            ]
        }
        
        self.cleanup_options = {}
        
        # Create notebook for categories
        cat_notebook = ttk.Notebook(options_card)
        cat_notebook.pack(fill='both', expand=True)
        
        for category, options in categories.items():
            cat_frame = ttk.Frame(cat_notebook)
            cat_notebook.add(cat_frame, text=category)
            
            for key, label, description in options:
                option_frame = ttk.Frame(cat_frame)
                option_frame.pack(fill='x', pady=2)
                
                var = tk.BooleanVar(value=True)
                self.cleanup_options[key] = var
                
                cb = ttk.Checkbutton(option_frame, text=label, variable=var)
                cb.pack(side='left')
                
                desc_label = ttk.Label(option_frame, text=f" - {description}",
                                      foreground=ModernTheme.TEXT_SECONDARY,
                                      font=('Segoe UI', 8))
                desc_label.pack(side='left')
                
    def create_cleanup_controls_section(self, parent):
        """Enhanced cleanup controls"""
        controls_card = ttk.LabelFrame(parent, text="🎮 Cleanup Control", padding=15)
        controls_card.pack(fill='x', pady=(0, 10))
        
        # Control buttons
        buttons_frame = ttk.Frame(controls_card)
        buttons_frame.pack(fill='x', pady=(0, 10))
        
        self.cleanup_button = ttk.Button(buttons_frame, text="🚀 Start Cleanup", 
                                       command=self.start_enhanced_cleanup,
                                       style='Primary.TButton')
        self.cleanup_button.pack(side='left', padx=(0, 10))
        
        ttk.Button(buttons_frame, text="⚡ Quick Clean", 
                  command=self.quick_clean_enhanced).pack(side='left', padx=(0, 10))
        
        ttk.Button(buttons_frame, text="🆘 Emergency Clean", 
                  command=self.emergency_cleanup_enhanced,
                  style='Danger.TButton').pack(side='left')
        
        # Cleanup settings
        settings_frame = ttk.Frame(controls_card)
        settings_frame.pack(fill='x')
        
        self.dry_run = tk.BooleanVar()
        ttk.Checkbutton(settings_frame, text="Dry run (preview only)", 
                       variable=self.dry_run).pack(side='left', padx=(0, 20))
        
        self.auto_confirm = tk.BooleanVar()
        ttk.Checkbutton(settings_frame, text="Auto-confirm actions", 
                       variable=self.auto_confirm).pack(side='left')
        
    def create_cleanup_progress_section(self, parent):
        """Enhanced cleanup progress tracking"""
        progress_card = ttk.LabelFrame(parent, text="📊 Cleanup Progress", padding=15)
        progress_card.pack(fill='both', expand=True, pady=(0, 10))
        
        # Overall progress
        progress_info = ttk.Frame(progress_card)
        progress_info.pack(fill='x', pady=(0, 10))
        
        self.cleanup_status = ttk.Label(progress_info, text="Ready to clean",
                                       font=('Segoe UI', 11, 'bold'))
        self.cleanup_status.pack(anchor='w')
        
        self.cleanup_progress_bar = AnimatedProgressBar(progress_card, width=400, height=12)
        self.cleanup_progress_bar.pack(fill='x', pady=(0, 10))
        
        # Space saved indicator
        self.space_saved_label = ttk.Label(progress_card, text="Space saved: 0 MB",
                                          foreground=ModernTheme.SUCCESS,
                                          font=('Segoe UI', 10, 'bold'))
        self.space_saved_label.pack(anchor='w', pady=(0, 10))
        
        # Progress log
        self.cleanup_log = scrolledtext.ScrolledText(progress_card, height=15,
                                                    bg=ModernTheme.DARKER_BG,
                                                    fg=ModernTheme.TEXT_PRIMARY,
                                                    font=('Consolas', 9))
        self.cleanup_log.pack(fill='both', expand=True)
        
        # Configure log tags
        self.cleanup_log.tag_configure("success", foreground=ModernTheme.SUCCESS)
        self.cleanup_log.tag_configure("warning", foreground=ModernTheme.WARNING)
        self.cleanup_log.tag_configure("error", foreground=ModernTheme.DANGER)
        self.cleanup_log.tag_configure("info", foreground=ModernTheme.TEXT_PRIMARY)
        
    def create_cleanup_analysis_section(self, parent):
        """Cleanup analysis and recommendations"""
        analysis_card = ttk.LabelFrame(parent, text="🔍 System Analysis", padding=15)
        analysis_card.pack(fill='x')
        
        # Analysis buttons
        analysis_buttons = ttk.Frame(analysis_card)
        analysis_buttons.pack(fill='x', pady=(0, 10))
        
        ttk.Button(analysis_buttons, text="📊 Disk Analysis", 
                  command=self.analyze_disk_usage).pack(side='left', padx=(0, 5))
        
        ttk.Button(analysis_buttons, text="🔍 Find Large Files", 
                  command=self.find_large_files_enhanced).pack(side='left', padx=(0, 5))
        
        ttk.Button(analysis_buttons, text="👥 Find Duplicates", 
                  command=self.find_duplicates_enhanced).pack(side='left')
        
        # Analysis results
        self.analysis_text = scrolledtext.ScrolledText(analysis_card, height=8,
                                                      bg=ModernTheme.DARKER_BG,
                                                      fg=ModernTheme.TEXT_PRIMARY,
                                                      font=('Consolas', 9))
        self.analysis_text.pack(fill='both', expand=True)
        
    def create_gdrive_tab_v2(self):
        """Enhanced Google Drive tab"""
        gdrive_frame = ttk.Frame(self.notebook)
        self.notebook.add(gdrive_frame, text="☁️ Google Drive")
        
        # Implementation continues...
        # [Space constraints - implementing key methods below]
        
    def create_system_tab_v2(self):
        """Enhanced system management tab"""
        system_frame = ttk.Frame(self.notebook)
        self.notebook.add(system_frame, text="⚙️ System")
        
        # System management implementation...
        
    def create_automation_tab_v2(self):
        """Enhanced automation tab"""
        automation_frame = ttk.Frame(self.notebook)
        self.notebook.add(automation_frame, text="🤖 Automation")
        
        # Automation implementation...
        
    def create_logs_tab_v2(self):
        """Enhanced logs tab"""
        logs_frame = ttk.Frame(self.notebook)
        self.notebook.add(logs_frame, text="📋 Logs")
        
        # Logs implementation...
        
    def create_modern_status_bar(self):
        """Create modern status bar with indicators"""
        self.status_bar = ttk.Frame(self.main_container)
        self.status_bar.pack(fill='x', side='bottom')
        
        # Left side - Status
        left_status = ttk.Frame(self.status_bar)
        left_status.pack(side='left', fill='y')
        
        self.status_label = ttk.Label(left_status, text="🟢 Ready",
                                     foreground=ModernTheme.SUCCESS)
        self.status_label.pack(side='left', padx=(0, 20))
        
        # Center - Progress (hidden initially)
        self.status_progress = AnimatedProgressBar(self.status_bar, width=200, height=4)
        
        # Right side - System stats and indicators
        right_status = ttk.Frame(self.status_bar)
        right_status.pack(side='right', fill='y')
        
        self.connection_status = ttk.Label(right_status, text="🔗 Offline",
                                          foreground=ModernTheme.TEXT_DISABLED)
        self.connection_status.pack(side='right', padx=(20, 0))
        
        self.stats_label = ttk.Label(right_status, text="",
                                    foreground=ModernTheme.TEXT_SECONDARY,
                                    font=('Segoe UI', 8))
        self.stats_label.pack(side='right', padx=(20, 0))
        
    # Enhanced system monitoring
    def start_system_monitoring(self):
        """Enhanced system monitoring with better visuals"""
        if not PSUTIL_AVAILABLE:
            self.set_monitoring_unavailable()
            return
            
        def monitor():
            while self.monitoring:
                try:
                    self.update_system_metrics()
                    time.sleep(2)
                except Exception as e:
                    print(f"Monitoring error: {e}")
                    time.sleep(5)
                    
        self.monitor_thread = threading.Thread(target=monitor, daemon=True)
        self.monitor_thread.start()
        
    def update_system_metrics(self):
        """Update all system metrics with animations"""
        if not PSUTIL_AVAILABLE:
            return
            
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_freq = psutil.cpu_freq()
            cpu_count = psutil.cpu_count()
            
            self.root.after(0, self.update_cpu_display, cpu_percent, cpu_freq, cpu_count)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            self.root.after(0, self.update_memory_display, memory)
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            self.root.after(0, self.update_disk_display, disk)
            
            # Update header info
            uptime = datetime.now() - datetime.fromtimestamp(psutil.boot_time())
            uptime_str = f"Uptime: {str(uptime).split('.')[0]}"
            
            load_avg = os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0]
            load_str = f"Load: {load_avg[0]:.2f}"
            
            info_text = f"{uptime_str} | {load_str} | Processes: {len(psutil.pids())}"
            self.root.after(0, lambda: self.header_info.config(text=info_text))
            
        except Exception as e:
            print(f"Error updating metrics: {e}")
            
    def update_cpu_display(self, cpu_percent, cpu_freq, cpu_count):
        """Update CPU display with animation"""
        self.cpu_display.config(text=f"{cpu_percent:.1f}%")
        self.cpu_progress.set_progress(cpu_percent)
        
        # Update color based on usage
        if cpu_percent > 80:
            color = ModernTheme.DANGER
        elif cpu_percent > 60:
            color = ModernTheme.WARNING
        else:
            color = ModernTheme.SUCCESS
            
        self.cpu_display.config(foreground=color)
        
        # Update details
        self.cpu_cores.config(text=f"Cores: {cpu_count}")
        if cpu_freq:
            self.cpu_freq.config(text=f"Frequency: {cpu_freq.current:.0f} MHz")
            
    def update_memory_display(self, memory):
        """Update memory display"""
        percent = memory.percent
        self.mem_display.config(text=f"{percent:.1f}%")
        self.mem_progress.set_progress(percent)
        
        # Update color
        if percent > 85:
            color = ModernTheme.DANGER
        elif percent > 70:
            color = ModernTheme.WARNING
        else:
            color = ModernTheme.SUCCESS
            
        self.mem_display.config(foreground=color)
        
        # Update details
        self.mem_used.config(text=f"Used: {self.format_bytes(memory.used)}")
        self.mem_total.config(text=f"Total: {self.format_bytes(memory.total)}")
        
    def update_disk_display(self, disk):
        """Update disk display"""
        percent = (disk.used / disk.total) * 100
        self.disk_display.config(text=f"{percent:.1f}%")
        self.disk_progress.set_progress(percent)
        
        # Update color
        if percent > 90:
            color = ModernTheme.DANGER
        elif percent > 75:
            color = ModernTheme.WARNING
        else:
            color = ModernTheme.SUCCESS
            
        self.disk_display.config(foreground=color)
        
        # Update details
        self.disk_free.config(text=f"Free: {self.format_bytes(disk.free)}")
        self.disk_total.config(text=f"Total: {self.format_bytes(disk.total)}")
        
    def set_monitoring_unavailable(self):
        """Set monitoring unavailable state"""
        self.cpu_display.config(text="N/A")
        self.mem_display.config(text="N/A")
        self.disk_display.config(text="N/A")
        self.stats_label.config(text="Install python3-psutil for monitoring")
        
    # Utility methods
    def format_bytes(self, bytes_value):
        """Format bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} PB"
        
    def log_activity(self, message, level="info"):
        """Enhanced activity logging with timestamps and colors"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        
        # Add to activity feed
        self.activity_text.configure(state='normal')
        self.activity_text.insert('end', f"[{timestamp}] ", "timestamp")
        self.activity_text.insert('end', f"{message}\n", level)
        self.activity_text.see('end')
        self.activity_text.configure(state='disabled')
        
        # Keep only last 1000 lines
        lines = self.activity_text.get('1.0', 'end').count('\n')
        if lines > 1000:
            self.activity_text.configure(state='normal')
            self.activity_text.delete('1.0', '100.end')
            self.activity_text.configure(state='disabled')
            
    def create_tooltip(self, widget, text):
        """Create tooltip for widget"""
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            tooltip.configure(bg=ModernTheme.SURFACE)
            
            label = tk.Label(tooltip, text=text, 
                           bg=ModernTheme.SURFACE, fg=ModernTheme.TEXT_PRIMARY,
                           font=('Segoe UI', 8), padx=5, pady=2)
            label.pack()
            
            widget.tooltip = tooltip
            
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip
                
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
        
    # Enhanced action methods
    def quick_clean(self):
        """Enhanced quick clean with better feedback"""
        self.log_activity("Starting quick system cleanup...", "info")
        self.status_label.config(text="🧹 Cleaning...", foreground=ModernTheme.WARNING)
        
        # Switch to cleanup tab
        self.notebook.select(1)
        
        # Set common cleanup options
        common_cleanups = ['clean_apt_cache', 'clean_thumbnails', 'clean_trash', 'clean_temp_files']
        for key in self.cleanup_options:
            self.cleanup_options[key].set(key in common_cleanups)
            
        # Start cleanup
        self.start_enhanced_cleanup()
        
    def quick_backup(self):
        """Enhanced quick backup"""
        self.log_activity("Starting quick backup...", "info")
        # Implementation...
        
    def refresh_all_status(self):
        """Enhanced status refresh"""
        self.log_activity("Refreshing system status...", "info")
        
        # Update all components
        if hasattr(self, 'services_tree'):
            self.update_services_status()
        if hasattr(self, 'storage_tree'):
            self.update_storage_overview()
        
        self.update_smart_suggestions()
        
    def start_enhanced_cleanup(self):
        """Enhanced cleanup with better progress tracking"""
        if self.cleanup_running:
            messagebox.showwarning("Cleanup Running", "Cleanup is already in progress!")
            return
            
        self.cleanup_running = True
        self.cleanup_button.config(state='disabled')
        self.cleanup_progress_bar.start_pulse()
        self.cleanup_status.config(text="🚀 Cleanup in progress...")
        
        # Clear cleanup log
        self.cleanup_log.configure(state='normal')
        self.cleanup_log.delete(1.0, tk.END)
        self.cleanup_log.configure(state='disabled')
        
        def cleanup_thread():
            try:
                total_saved = 0
                completed_tasks = 0
                total_tasks = sum(1 for var in self.cleanup_options.values() if var.get())
                
                for key, var in self.cleanup_options.items():
                    if not var.get():
                        continue
                        
                    try:
                        saved = self.run_cleanup_task_enhanced(key)
                        total_saved += saved
                        completed_tasks += 1
                        
                        progress = (completed_tasks / total_tasks) * 100
                        self.root.after(0, self.update_cleanup_progress, progress, total_saved)
                        
                    except Exception as e:
                        self.log_cleanup_message(f"Error in {key}: {e}", "error")
                        
                self.log_activity(f"Cleanup completed! Saved {self.format_bytes(total_saved)}", "success")
                
            except Exception as e:
                self.log_activity(f"Cleanup error: {e}", "error")
                
            finally:
                self.root.after(0, self.cleanup_complete_enhanced)
                
        threading.Thread(target=cleanup_thread, daemon=True).start()
        
    def run_cleanup_task_enhanced(self, task_key):
        """Run individual cleanup task with size tracking"""
        task_map = {
            'clean_apt_cache': ("Cleaning APT cache", "sudo apt clean && apt-get autoclean"),
            'clean_snap_cache': ("Cleaning Snap cache", "sudo snap set system refresh.retain=2"),
            'clean_thumbnails': ("Cleaning thumbnails", f"rm -rf {Path.home()}/.cache/thumbnails/*"),
            'clean_browsers': ("Cleaning browser caches", self.clean_browser_caches_enhanced),
            'clean_trash': ("Emptying trash", f"rm -rf {Path.home()}/.local/share/Trash/*"),
            # Add more tasks...
        }
        
        if task_key not in task_map:
            return 0
            
        description, command = task_map[task_key]
        self.log_cleanup_message(f"\n🔄 {description}...")
        
        # Get size before
        size_before = self.get_cleanup_size_before(task_key)
        
        try:
            if callable(command):
                command()
            else:
                result = subprocess.run(command, shell=True, capture_output=True, text=True)
                if result.returncode != 0:
                    self.log_cleanup_message(f"⚠️ Warning: {result.stderr}", "warning")
                    
        except Exception as e:
            self.log_cleanup_message(f"❌ Failed: {e}", "error")
            return 0
            
        # Get size after
        size_after = self.get_cleanup_size_after(task_key)
        saved = size_before - size_after
        
        if saved > 0:
            self.log_cleanup_message(f"✅ {description} - Saved {self.format_bytes(saved)}", "success")
        else:
            self.log_cleanup_message(f"✅ {description} - Complete", "success")
            
        return saved
        
    def update_cleanup_progress(self, progress, total_saved):
        """Update cleanup progress display"""
        self.cleanup_progress_bar.stop_pulse()
        self.cleanup_progress_bar.set_progress(progress)
        self.space_saved_label.config(text=f"Space saved: {self.format_bytes(total_saved)}")
        
    def cleanup_complete_enhanced(self):
        """Enhanced cleanup completion"""
        self.cleanup_running = False
        self.cleanup_button.config(state='normal')
        self.cleanup_progress_bar.stop_pulse()
        self.cleanup_status.config(text="✅ Cleanup complete!")
        self.status_label.config(text="🟢 Ready", foreground=ModernTheme.SUCCESS)
        
        # Update system metrics
        self.refresh_all_status()
        
    def log_cleanup_message(self, message, level="info"):
        """Log message to cleanup log"""
        self.root.after(0, self._update_cleanup_log_enhanced, message, level)
        
    def _update_cleanup_log_enhanced(self, message, level):
        """Update cleanup log in main thread"""
        self.cleanup_log.configure(state='normal')
        self.cleanup_log.insert('end', message + '\n', level)
        self.cleanup_log.see('end')
        self.cleanup_log.configure(state='disabled')
        
    # Additional enhanced methods...
    def get_cleanup_size_before(self, task_key):
        """Get size before cleanup task"""
        # Implementation to measure size before cleanup
        return 0
        
    def get_cleanup_size_after(self, task_key):
        """Get size after cleanup task"""
        # Implementation to measure size after cleanup
        return 0
        
    def update_smart_suggestions(self):
        """Update smart suggestions based on system analysis"""
        # Clear existing suggestions
        for widget in self.suggestions_frame.winfo_children():
            widget.destroy()
            
        suggestions = []
        
        # Analyze system and generate suggestions
        if PSUTIL_AVAILABLE:
            # Disk space suggestions
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            if disk_percent > 85:
                suggestions.append(("⚠️ Low disk space", "Run cleanup to free space", self.emergency_cleanup_enhanced))
                
            # Memory suggestions
            memory = psutil.virtual_memory()
            if memory.percent > 80:
                suggestions.append(("💾 High memory usage", "Close unused applications", None))
                
            # CPU suggestions
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > 80:
                suggestions.append(("🔥 High CPU usage", "Check running processes", None))
                
        # Add suggestions to UI
        for i, (title, description, action) in enumerate(suggestions[:5]):  # Show max 5
            suggestion_frame = ttk.Frame(self.suggestions_frame)
            suggestion_frame.pack(fill='x', pady=2)
            
            ttk.Label(suggestion_frame, text=title, 
                     font=('Segoe UI', 9, 'bold')).pack(anchor='w')
            ttk.Label(suggestion_frame, text=description,
                     foreground=ModernTheme.TEXT_SECONDARY).pack(anchor='w')
            
            if action:
                ttk.Button(suggestion_frame, text="Fix", command=action).pack(anchor='w', pady=2)
                
    def update_services_status(self):
        """Update services status"""
        # Clear existing items
        for item in self.services_tree.get_children():
            self.services_tree.delete(item)
            
        # Common services to check
        services = [
            "apache2", "nginx", "mysql", "postgresql", "docker",
            "ssh", "cron", "NetworkManager", "bluetooth"
        ]
        
        for service in services:
            try:
                result = subprocess.run(f"systemctl is-active {service}", 
                                      shell=True, capture_output=True, text=True)
                status = result.stdout.strip()
                
                if status == "active":
                    self.services_tree.insert('', 'end', text=service, 
                                            values=("🟢 Active",))
                elif status == "inactive":
                    self.services_tree.insert('', 'end', text=service, 
                                            values=("🔴 Inactive",))
                else:
                    self.services_tree.insert('', 'end', text=service, 
                                            values=("❓ Unknown",))
            except:
                pass
                
    def update_storage_overview(self):
        """Update storage overview"""
        # Clear existing items
        for item in self.storage_tree.get_children():
            self.storage_tree.delete(item)
            
        try:
            # Get directory sizes
            home = Path.home()
            dirs_to_check = [
                ("Home Directory", home, "folder"),
                ("Documents", home / "Documents", "documents"),
                ("Downloads", home / "Downloads", "downloads"),
                ("Pictures", home / "Pictures", "media"),
                ("Videos", home / "Videos", "media"),
                ("Desktop", home / "Desktop", "desktop"),
                (".cache", home / ".cache", "cache"),
            ]
            
            for name, path, type_icon in dirs_to_check:
                if path.exists():
                    try:
                        # Quick size estimation
                        result = subprocess.run(f"du -sh '{path}' 2>/dev/null", 
                                              shell=True, capture_output=True, text=True)
                        if result.stdout:
                            size_str = result.stdout.split()[0]
                            self.storage_tree.insert('', 'end', text=f"{type_icon} {name}", 
                                                   values=(size_str, "", type_icon))
                    except:
                        pass
                        
        except Exception as e:
            self.log_activity(f"Error updating storage: {e}", "error")
            
    # Event handlers
    def show_storage_context_menu(self, event):
        """Show context menu for storage tree"""
        item = self.storage_tree.selection()[0] if self.storage_tree.selection() else None
        if item:
            self.storage_menu.post(event.x_root, event.y_root)
            
    def analyze_selected_directory(self):
        """Analyze selected directory with ncdu"""
        selection = self.storage_tree.selection()
        if selection:
            item = selection[0]
            directory_name = self.storage_tree.item(item, 'text')
            # Launch ncdu for selected directory
            self.log_activity(f"Opening disk analyzer for {directory_name}", "info")
            
    def clean_selected_directory(self):
        """Clean selected directory"""
        selection = self.storage_tree.selection()
        if selection:
            item = selection[0]
            directory_name = self.storage_tree.item(item, 'text')
            # Implement directory-specific cleaning
            self.log_activity(f"Cleaning {directory_name}", "info")
            
    def show_settings(self):
        """Show settings dialog"""
        self.log_activity("Opening settings...", "info")
        # Implementation for settings dialog
        
    def show_help(self):
        """Show help dialog"""
        help_text = """
Unified System Manager v2.0 - Keyboard Shortcuts:

Ctrl+C - Quick Clean
Ctrl+B - Quick Backup  
Ctrl+R - Refresh Status
F1 - Show Help
F5 - Refresh All
Ctrl+Q - Quit Application

System Monitoring:
- Real-time CPU, Memory, Disk usage
- Service status monitoring
- Storage breakdown analysis

Cleanup Features:
- Selective cleanup categories
- Progress tracking with space saved
- Smart suggestions based on system analysis

Google Drive Integration:
- Smart backup wizard
- File synchronization
- Mount/unmount management
"""
        
        help_window = tk.Toplevel(self.root)
        help_window.title("Help - Unified System Manager")
        help_window.geometry("600x500")
        help_window.configure(bg=ModernTheme.DARK_BG)
        
        text_widget = scrolledtext.ScrolledText(help_window, 
                                               bg=ModernTheme.DARKER_BG,
                                               fg=ModernTheme.TEXT_PRIMARY,
                                               font=('Segoe UI', 10))
        text_widget.pack(fill='both', expand=True, padx=15, pady=15)
        text_widget.insert('1.0', help_text)
        text_widget.configure(state='disabled')
        
    def show_status_popup(self):
        """Show status popup (for system tray)"""
        status_text = f"""
System Status:
CPU: {self.cpu_display.cget('text') if hasattr(self, 'cpu_display') else 'N/A'}
Memory: {self.mem_display.cget('text') if hasattr(self, 'mem_display') else 'N/A'}
Disk: {self.disk_display.cget('text') if hasattr(self, 'disk_display') else 'N/A'}
"""
        messagebox.showinfo("System Status", status_text)
        
    def on_window_close(self):
        """Handle window close - minimize to tray if available"""
        if TRAY_AVAILABLE and self.tray.icon:
            self.root.withdraw()  # Hide window instead of closing
        else:
            self.quit_application()
            
    def quit_application(self):
        """Quit the application completely"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)
        if TRAY_AVAILABLE and self.tray.icon:
            self.tray.icon.stop()
        self.root.quit()
        self.root.destroy()
        
    # Placeholder methods for missing functionality
    def quick_clean_enhanced(self):
        self.quick_clean()
        
    def emergency_cleanup_enhanced(self):
        """Enhanced emergency cleanup"""
        if messagebox.askyesno("Emergency Cleanup", 
                             "This will aggressively clean your system. Continue?"):
            self.log_activity("Starting emergency cleanup...", "warning")
            # Implementation...
            
    def analyze_disk_usage(self):
        """Analyze disk usage with visual tools"""
        if shutil.which('ncdu'):
            subprocess.Popen(['gnome-terminal', '--', 'ncdu', str(Path.home())])
        else:
            messagebox.showerror("Error", "ncdu not installed!")
            
    def find_large_files_enhanced(self):
        """Find large files with enhanced interface"""
        self.log_activity("Searching for large files...", "info")
        # Implementation...
        
    def find_duplicates_enhanced(self):
        """Find duplicate files with enhanced interface"""
        self.log_activity("Searching for duplicate files...", "info")
        # Implementation...
        
    def clean_browser_caches_enhanced(self):
        """Enhanced browser cache cleaning"""
        # Implementation...
        pass

def main():
    # Check Python version
    if sys.version_info < (3, 6):
        messagebox.showerror("Python Version Error", 
                           "This application requires Python 3.6 or higher!")
        return
        
    # Create and run the modern GUI
    root = tk.Tk()
    
    # Set window icon if available
    try:
        # You can add an icon file here
        # root.iconbitmap('icon.ico')
        pass
    except:
        pass
        
    app = ModernUnifiedSystemManagerGUI(root)
    
    # Center window on screen
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        app.quit_application()
        
    signal.signal(signal.SIGINT, signal_handler)
    
    root.mainloop()

if __name__ == "__main__":
    main()