#!/usr/bin/env python3
"""
Test ScrolledText with different color combinations
"""

import tkinter as tk
from tkinter import ttk, scrolledtext

def test_scrolledtext_colors():
    """Test various ScrolledText color combinations"""
    
    root = tk.Tk()
    root.title("ScrolledText Color Test")
    root.geometry("800x600")
    
    notebook = ttk.Notebook(root)
    notebook.pack(fill='both', expand=True, padx=10, pady=10)
    
    # Test 1: Basic ScrolledText (should work)
    print("Test 1: Basic ScrolledText...")
    frame1 = ttk.Frame(notebook)
    notebook.add(frame1, text="Test 1: Basic")
    
    text1 = scrolledtext.ScrolledText(frame1, height=10, width=60)
    text1.pack(pady=10)
    text1.insert('1.0', "Test 1: Basic ScrolledText - should work\\n")
    
    # Test 2: Dark background only
    print("Test 2: Dark background...")
    frame2 = ttk.Frame(notebook)
    notebook.add(frame2, text="Test 2: Dark BG")
    
    text2 = scrolledtext.ScrolledText(frame2, height=10, width=60,
                                     bg='#333333')
    text2.pack(pady=10)
    text2.insert('1.0', "Test 2: Dark background only\\n")
    
    # Test 3: Dark background + light text
    print("Test 3: Dark + light text...")
    frame3 = ttk.Frame(notebook)
    notebook.add(frame3, text="Test 3: Dark+Light")
    
    text3 = scrolledtext.ScrolledText(frame3, height=10, width=60,
                                     bg='#333333', fg='white')
    text3.pack(pady=10)
    text3.insert('1.0', "Test 3: Dark background + white text\\n")
    
    # Test 4: The problematic combination
    print("Test 4: CRITICAL - Exact colors from crash...")
    frame4 = ttk.Frame(notebook)
    notebook.add(frame4, text="Test 4: CRITICAL")
    
    try:
        text4 = scrolledtext.ScrolledText(frame4, height=10, width=60,
                                         bg='#0a0a1e', fg='#0f8',
                                         font=('Arial', 10))
        text4.pack(pady=10)
        text4.insert('1.0', "Test 4: This exact combination caused the crash\\n")
        print("✓ Test 4 passed!")
    except Exception as e:
        print(f"✗ Test 4 failed: {e}")
    
    # Test 5: Different dark combination
    print("Test 5: Alternative dark colors...")
    frame5 = ttk.Frame(notebook)
    notebook.add(frame5, text="Test 5: Alt Dark")
    
    text5 = scrolledtext.ScrolledText(frame5, height=10, width=60,
                                     bg='#1a1a1a', fg='#00ff00',
                                     font=('Arial', 10))
    text5.pack(pady=10)
    text5.insert('1.0', "Test 5: Alternative dark color scheme\\n")
    
    # Test 6: System tab frame structure
    print("Test 6: CRITICAL - Exact system tab structure...")
    frame6 = ttk.Frame(notebook)
    notebook.add(frame6, text="Test 6: System Tab")
    
    try:
        # Recreate exact system tab structure
        content = tk.Frame(frame6, bg='#0f0f1e')
        content.pack(fill='both', expand=True, padx=10, pady=10)
        
        title = tk.Label(content, text="SYSTEM MANAGEMENT", 
                       font=("Arial", 14, "bold"), fg='#00d4ff', bg='#0f0f1e')
        title.pack(pady=10)
        
        # The problematic ScrolledText
        system_text = scrolledtext.ScrolledText(content, height=15, width=80,
                                               bg='#0a0a1e', fg='#0f8',
                                               font=('Arial', 10))
        system_text.pack(fill='both', expand=True, pady=10)
        
        system_text.insert('1.0', "Test 6: Exact system tab recreation\\n")
        print("✓ Test 6 passed!")
    except Exception as e:
        print(f"✗ Test 6 failed: {e}")
    
    print("All tests completed! Starting main loop...")
    root.mainloop()

if __name__ == '__main__':
    print("Testing ScrolledText color combinations...")
    test_scrolledtext_colors()
    print("ScrolledText test complete.")