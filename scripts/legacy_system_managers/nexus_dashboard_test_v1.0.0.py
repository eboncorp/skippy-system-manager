#!/usr/bin/env python3
"""
Dashboard Creation Test - Isolate segfault cause
"""

import sys
import tkinter as tk
from tkinter import ttk

def test_basic_dashboard():
    """Test basic dashboard without styling"""
    print("Testing basic dashboard...")
    
    root = tk.Tk()
    root.title("Dashboard Test")
    root.geometry("800x600")
    
    # Basic notebook
    notebook = ttk.Notebook(root)
    notebook.pack(fill='both', expand=True)
    
    # Basic frame
    frame = ttk.Frame(notebook)
    notebook.add(frame, text="Test")
    
    # Basic label
    label = tk.Label(frame, text="Basic Dashboard Test")
    label.pack(pady=20)
    
    print("Basic dashboard created successfully!")
    return root

def test_styled_dashboard():
    """Test dashboard with styling - potential segfault"""
    print("Testing styled dashboard...")
    
    root = tk.Tk()
    root.title("Styled Dashboard Test")
    root.geometry("800x600")
    
    # This might cause the segfault
    print("Creating ttk.Style...")
    style = ttk.Style()
    style.theme_use('clam')
    style.configure('TNotebook', background='#1a1a2e', borderwidth=0)
    style.configure('TNotebook.Tab', background='#2a2a3e', foreground='white', 
                   padding=[20, 10])
    style.map('TNotebook.Tab', background=[('selected', '#3a3a4e')])
    
    print("Style created, creating notebook...")
    notebook = ttk.Notebook(root)
    notebook.pack(fill='both', expand=True)
    
    print("Creating frame...")
    frame = ttk.Frame(notebook)
    notebook.add(frame, text="Styled Test")
    
    print("Styled dashboard created successfully!")
    return root

def test_complex_widgets():
    """Test complex widget creation"""
    print("Testing complex widgets...")
    
    root = tk.Tk()
    root.title("Complex Widgets Test")
    root.geometry("800x600")
    
    # Basic notebook first
    notebook = ttk.Notebook(root)
    notebook.pack(fill='both', expand=True)
    
    frame = ttk.Frame(notebook)
    notebook.add(frame, text="Complex")
    
    print("Creating complex colored frames...")
    # This might cause issues
    main_frame = tk.Frame(frame, bg='#0f0f1e')
    main_frame.pack(fill='both', expand=True)
    
    overview_frame = tk.Frame(main_frame, bg='#1a1a2e', relief='ridge', bd=2)
    overview_frame.pack(fill='x', padx=10, pady=10)
    
    # Complex labels with custom colors
    print("Creating colored labels...")
    title = tk.Label(overview_frame, text="SYSTEM STATUS", 
                    font=("Courier", 14, "bold"), fg='#00d4ff', bg='#1a1a2e')
    title.pack(pady=10)
    
    cpu_label = tk.Label(overview_frame, text="⚡ CPU: Testing...", 
                         bg='#1a1a2e', fg='#0f8', font=("Courier", 10))
    cpu_label.pack(anchor='w', padx=10, pady=2)
    
    print("Complex widgets created successfully!")
    return root

def test_grid_layout():
    """Test grid layout which might cause issues"""
    print("Testing grid layout...")
    
    root = tk.Tk()
    root.title("Grid Layout Test")
    root.geometry("800x600")
    
    frame = tk.Frame(root)
    frame.pack(fill='both', expand=True, padx=10, pady=10)
    
    # Grid with buttons - this might cause segfault
    print("Creating button grid...")
    button_frame = tk.Frame(frame, bg='#1a1a2e')
    button_frame.pack(pady=10)
    
    button_style = {
        'font': ('Courier', 10, 'bold'),
        'bg': '#2a2a3e',
        'fg': '#00d4ff',
        'activebackground': '#3a3a4e',
        'relief': 'raised',
        'bd': 2,
        'padx': 15
    }
    
    # Create buttons in grid
    for i in range(2):
        for j in range(3):
            btn = tk.Button(button_frame, text=f"BTN {i}-{j}", **button_style)
            btn.grid(row=i, column=j, padx=5, pady=5)
    
    print("Grid layout created successfully!")
    return root

if __name__ == '__main__':
    print("Starting dashboard segfault isolation test...")
    
    try:
        print("\\n=== Test 1: Basic Dashboard ===")
        root1 = test_basic_dashboard()
        root1.update()  # Just test creation, don't run mainloop
        root1.destroy()
        print("✓ Basic dashboard passed")
        
        print("\\n=== Test 2: Styled Dashboard ===")
        root2 = test_styled_dashboard()
        root2.update()
        root2.destroy()
        print("✓ Styled dashboard passed")
        
        print("\\n=== Test 3: Complex Widgets ===")
        root3 = test_complex_widgets()
        root3.update()
        root3.destroy()
        print("✓ Complex widgets passed")
        
        print("\\n=== Test 4: Grid Layout ===")
        root4 = test_grid_layout()
        root4.update()
        root4.destroy()
        print("✓ Grid layout passed")
        
        print("\\n🎉 All tests passed! Segfault is elsewhere.")
        
    except Exception as e:
        print(f"\\n💥 SEGFAULT FOUND IN: {e}")
        import traceback
        traceback.print_exc()
    
    print("Dashboard test complete.")