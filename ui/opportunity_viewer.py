#!/usr/bin/env python3
"""
Bitcoin News Scanner UI

A simple graphical user interface that displays recent opportunities
and allows clicking on them to open in the browser.
"""

import os
import sys
import json
import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
import threading
import time
from datetime import datetime
import subprocess

# Add the parent directory to the path so we can import from the main package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.db_manager import DatabaseManager
import config

class OpportunityViewer:
    """
    A simple GUI for viewing Bitcoin investment opportunities.
    """
    
    def __init__(self, root):
        self.root = root
        self.root.title("Bitcoin News Scanner - Opportunities")
        self.root.geometry("800x600")
        self.root.minsize(700, 500)
        
        # Initialize database manager
        self.db_manager = DatabaseManager(config.DB_FILE)
        
        # Create UI components
        self.create_widgets()
        
        # Track if scanner is running
        self.scanner_running = False
        self.scanner_process = None
        
        # Update opportunities list
        self.update_opportunities()
        
        # Set up auto-refresh every 30 seconds
        self.schedule_refresh()
    
    def create_widgets(self):
        """Create and arrange all UI components."""
        # Create main frame
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create header with status and controls
        self.header_frame = ttk.Frame(self.main_frame)
        self.header_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.title_label = ttk.Label(
            self.header_frame, 
            text="Bitcoin Investment Opportunities", 
            font=("Arial", 16, "bold")
        )
        self.title_label.pack(side=tk.LEFT, pady=5)
        
        # Control buttons
        self.controls_frame = ttk.Frame(self.header_frame)
        self.controls_frame.pack(side=tk.RIGHT)
        
        self.refresh_button = ttk.Button(
            self.controls_frame, 
            text="Refresh", 
            command=self.update_opportunities
        )
        self.refresh_button.pack(side=tk.LEFT, padx=5)
        
        self.scanner_button = ttk.Button(
            self.controls_frame, 
            text="Start Scanner", 
            command=self.toggle_scanner
        )
        self.scanner_button.pack(side=tk.LEFT, padx=5)
        
        # Status indicators
        self.status_frame = ttk.Frame(self.main_frame)
        self.status_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.last_updated_label = ttk.Label(
            self.status_frame, 
            text="Last updated: Never"
        )
        self.last_updated_label.pack(side=tk.LEFT)
        
        self.count_label = ttk.Label(
            self.status_frame, 
            text="0 opportunities found"
        )
        self.count_label.pack(side=tk.RIGHT)
        
        # Create opportunities list with scrollbar
        self.list_frame = ttk.Frame(self.main_frame)
        self.list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar
        self.scrollbar = ttk.Scrollbar(self.list_frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create a canvas for scrolling
        self.canvas = tk.Canvas(self.list_frame, yscrollcommand=self.scrollbar.set)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.scrollbar.config(command=self.canvas.yview)
        
        # Create a frame inside the canvas for opportunities
        self.opportunities_frame = ttk.Frame(self.canvas)
        self.canvas_frame = self.canvas.create_window(
            (0, 0), 
            window=self.opportunities_frame, 
            anchor="nw", 
            tags="opportunities_frame"
        )
        
        # Configure canvas scrolling
        self.opportunities_frame.bind("<Configure>", self.on_frame_configure)
        self.canvas.bind("<Configure>", self.on_canvas_configure)
        
        # Mouse wheel scrolling
        self.canvas.bind_all("<MouseWheel>", self.on_mousewheel)
        
        # Footer with app info
        self.footer_frame = ttk.Frame(self.main_frame)
        self.footer_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.app_info_label = ttk.Label(
            self.footer_frame, 
            text="Bitcoin News Scanner | " + 
                 "Click on an opportunity to open in browser",
            foreground="gray"
        )
        self.app_info_label.pack(side=tk.LEFT)
    
    def on_frame_configure(self, event=None):
        """Reset the scroll region to encompass the inner frame."""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def on_canvas_configure(self, event=None):
        """When canvas is resized, resize the inner frame to match."""
        self.canvas.itemconfig(
            self.canvas_frame, 
            width=event.width
        )
    
    def on_mousewheel(self, event):
        """Handle mouse wheel scrolling."""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def clear_opportunities(self):
        """Clear all opportunity widgets from the frame."""
        for widget in self.opportunities_frame.winfo_children():
            widget.destroy()
    
    def update_opportunities(self):
        """Fetch and display opportunities from the database."""
        self.clear_opportunities()
        
        # Get opportunities from the last 24 hours
        opportunities = self.db_manager.get_recent_opportunities(24)
        
        if not opportunities:
            # No opportunities found, show message
            no_results = ttk.Label(
                self.opportunities_frame,
                text="No opportunities found in the last 24 hours.",
                font=("Arial", 12),
                padding=20
            )
            no_results.pack(fill=tk.X, pady=10)
        else:
            # Display each opportunity
            for i, opp in enumerate(opportunities, 1):
                self.create_opportunity_card(opp, i)
        
        # Update status indicators
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.last_updated_label.config(text=f"Last updated: {now}")
        self.count_label.config(text=f"{len(opportunities)} opportunities found")
        
        # Update scrolling
        self.on_frame_configure()
    
    def create_opportunity_card(self, opportunity, index):
        """Create a card widget for an opportunity."""
        # Create frame for this opportunity
        card = ttk.Frame(self.opportunities_frame)
        card.pack(fill=tk.X, pady=5, padx=5)
        
        # Get opportunity details
        title = opportunity.get('article_title', 'Unknown article')
        url = opportunity.get('article_url', '#')
        source = opportunity.get('article_source', 'Unknown source')
        timestamp = opportunity.get('timestamp', '')
        
        try:
            date_obj = datetime.fromisoformat(timestamp)
            time_display = date_obj.strftime("%m/%d %H:%M")
        except:
            time_display = ""
        
        # Add clickable title
        title_label = ttk.Label(
            card, 
            text=f"{index}. {title}",
            font=("Arial", 11, "bold"),
            foreground="blue",
            cursor="hand2"
        )
        title_label.pack(fill=tk.X, anchor=tk.W, pady=(5, 2))
        title_label.bind("<Button-1>", lambda e, u=url: self.open_url(u))
        
        # Create info frame for metadata
        info_frame = ttk.Frame(card)
        info_frame.pack(fill=tk.X, pady=(0, 2))
        
        # Source and time
        source_time = ttk.Label(
            info_frame,
            text=f"Source: {source} | Found: {time_display}",
            font=("Arial", 9),
            foreground="gray"
        )
        source_time.pack(side=tk.LEFT)
        
        # URL display (shortened)
        url_label = ttk.Label(
            info_frame,
            text=self.shorten_url(url),
            font=("Arial", 9),
            foreground="gray"
        )
        url_label.pack(side=tk.RIGHT)
        
        # Get AI analysis if available
        ai_analysis = opportunity.get('ai_analysis', '')
        if ai_analysis:
            # Truncate if too long
            if len(ai_analysis) > 200:
                ai_analysis = ai_analysis[:197] + "..."
            
            analysis_label = ttk.Label(
                card,
                text=ai_analysis,
                wraplength=750,
                justify=tk.LEFT,
                font=("Arial", 10)
            )
            analysis_label.pack(fill=tk.X, anchor=tk.W, pady=(0, 5))
        
        # Add separator
        separator = ttk.Separator(card, orient="horizontal")
        separator.pack(fill=tk.X, pady=(5, 0))
    
    def shorten_url(self, url, max_length=60):
        """Shorten URL for display purposes."""
        if len(url) <= max_length:
            return url
        
        # Keep the domain part
        if '://' in url:
            protocol, rest = url.split('://', 1)
            if '/' in rest:
                domain, path = rest.split('/', 1)
                return f"{protocol}://{domain}/...{path[-20:]}"
        
        # Fallback to simple truncation
        return url[:max_length-3] + "..."
    
    def open_url(self, url):
        """Open URL in default browser."""
        if url and url != '#':
            webbrowser.open(url)
    
    def schedule_refresh(self):
        """Schedule periodic refresh of the opportunities list."""
        self.root.after(30000, self.auto_refresh)  # Refresh every 30 seconds
    
    def auto_refresh(self):
        """Auto-refresh the opportunities list and reschedule."""
        self.update_opportunities()
        self.schedule_refresh()
    
    def toggle_scanner(self):
        """Start or stop the Bitcoin News Scanner."""
        if not self.scanner_running:
            # Start scanner in non-blocking mode
            try:
                cmd = [sys.executable, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'main.py')]
                self.scanner_process = subprocess.Popen(cmd)
                self.scanner_running = True
                self.scanner_button.config(text="Stop Scanner")
                messagebox.showinfo("Scanner Started", "Bitcoin News Scanner is now running in the background.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to start scanner: {str(e)}")
        else:
            # Stop the scanner
            if self.scanner_process:
                self.scanner_process.terminate()
                self.scanner_process = None
            self.scanner_running = False
            self.scanner_button.config(text="Start Scanner")
            messagebox.showinfo("Scanner Stopped", "Bitcoin News Scanner has been stopped.")


def main():
    """Main entry point for the application."""
    root = tk.Tk()
    app = OpportunityViewer(root)
    root.mainloop()


if __name__ == "__main__":
    main()
