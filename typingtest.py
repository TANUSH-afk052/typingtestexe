import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import random
import time
import threading
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import numpy as np

class TypingTest:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Advanced 60 Second Typing Test - Continuous Mode")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')
        
        # Initialize database
        self.init_database()
        
        # Enhanced word list with common words
        self.words = [
            # Common words
            "the", "and", "for", "are", "but", "not", "you", "all", "can", "had", "her", "was", "one", "our", "out",
            "day", "get", "has", "him", "his", "how", "man", "new", "now", "old", "see", "two", "way", "who", "boy",
            "did", "its", "let", "put", "say", "she", "too", "use", "dad", "mom", "red", "big", "box", "yes", "yet",
            "run", "sun", "fun", "cat", "dog", "car", "eat", "got", "lot", "hot", "sit", "bit", "hit", "fit", "win",
            "end", "far", "off", "own", "try", "why", "ask", "men", "cut", "job", "eye", "oil", "six", "war", "lay",
            "may", "few", "pop", "top", "bad", "bag", "bed", "leg", "egg", "add", "age", "ago", "air", "arm", "art",
            
            # Additional common words for better practice
            "about", "after", "again", "against", "among", "another", "any", "around", "because", "before",
            "being", "between", "both", "came", "come", "could", "each", "even", "every", "first", "from",
            "give", "going", "good", "great", "group", "hand", "hard", "have", "here", "high", "home", "into",
            "just", "know", "large", "last", "left", "life", "like", "line", "little", "long", "look", "made",
            "make", "many", "most", "move", "much", "must", "name", "need", "next", "night", "number", "only",
            "open", "order", "other", "over", "part", "people", "place", "point", "right", "said", "same",
            "school", "seem", "several", "should", "show", "since", "small", "some", "still", "such", "system",
            "take", "than", "them", "there", "these", "they", "thing", "think", "this", "those", "three",
            "through", "time", "today", "together", "turn", "under", "until", "very", "water", "well", "went",
            "were", "what", "when", "where", "which", "while", "will", "with", "without", "work", "world",
            "would", "write", "year", "young", "your", "house", "never", "found", "every", "great", "where",
            "help", "through", "much", "before", "move", "right", "line", "too", "any", "came", "want"
        ]
        
        self.test_text = ""
        self.typed_text = ""
        self.start_time = None
        self.time_left = 60
        self.test_active = False
        self.test_completed = False
        self.timer_thread = None
        self.user_name = ""
        
        # For tracking performance
        self.correct_chars = 0
        self.incorrect_chars = 0
        self.total_chars_typed = 0
        
        self.setup_ui()
        self.generate_text()
        
    def init_database(self):
        """Initialize SQLite database for storing user stats"""
        self.conn = sqlite3.connect('typing_test_stats.db')
        cursor = self.conn.cursor()
        
        # Create table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                wpm INTEGER NOT NULL,
                accuracy INTEGER NOT NULL,
                total_chars INTEGER NOT NULL,
                correct_chars INTEGER NOT NULL,
                incorrect_chars INTEGER NOT NULL,
                chars_per_minute INTEGER NOT NULL,
                test_duration INTEGER NOT NULL,
                test_date TEXT NOT NULL,
                test_time TEXT NOT NULL
            )
        ''')
        
        self.conn.commit()
        
    def save_test_result(self, username, wpm, accuracy, total_chars, correct_chars, incorrect_chars, cpm, duration):
        """Save test result to database"""
        cursor = self.conn.cursor()
        current_datetime = datetime.now()
        test_date = current_datetime.strftime("%Y-%m-%d")
        test_time = current_datetime.strftime("%H:%M:%S")
        
        cursor.execute('''
            INSERT INTO user_stats (username, wpm, accuracy, total_chars, correct_chars, incorrect_chars, 
                                  chars_per_minute, test_duration, test_date, test_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (username, wpm, accuracy, total_chars, correct_chars, incorrect_chars, cpm, duration, test_date, test_time))
        
        self.conn.commit()
        
    def get_user_stats(self, username=None):
        """Get user statistics from database"""
        cursor = self.conn.cursor()
        
        if username:
            cursor.execute('''
                SELECT * FROM user_stats WHERE username = ? ORDER BY test_date DESC, test_time DESC
            ''', (username,))
        else:
            cursor.execute('''
                SELECT * FROM user_stats ORDER BY test_date DESC, test_time DESC
            ''')
            
        return cursor.fetchall()
        
    def get_user_best_stats(self, username):
        """Get user's best statistics"""
        cursor = self.conn.cursor()
        
        # Best WPM
        cursor.execute('SELECT MAX(wpm) FROM user_stats WHERE username = ?', (username,))
        best_wpm = cursor.fetchone()[0] or 0
        
        # Best Accuracy
        cursor.execute('SELECT MAX(accuracy) FROM user_stats WHERE username = ?', (username,))
        best_accuracy = cursor.fetchone()[0] or 0
        
        # Average WPM
        cursor.execute('SELECT AVG(wpm) FROM user_stats WHERE username = ?', (username,))
        avg_wpm = cursor.fetchone()[0] or 0
        
        # Total tests
        cursor.execute('SELECT COUNT(*) FROM user_stats WHERE username = ?', (username,))
        total_tests = cursor.fetchone()[0] or 0
        
        return {
            'best_wpm': int(best_wpm),
            'best_accuracy': int(best_accuracy),
            'avg_wpm': round(avg_wpm, 1),
            'total_tests': total_tests
        }
        
    def setup_ui(self):
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Test Tab
        self.test_frame = tk.Frame(self.notebook, bg='#f0f0f0')
        self.notebook.add(self.test_frame, text="Typing Test")
        
        # Stats Tab
        self.stats_frame = tk.Frame(self.notebook, bg='#f0f0f0')
        self.notebook.add(self.stats_frame, text="Statistics")
        
        # Analytics Tab
        self.analytics_frame = tk.Frame(self.notebook, bg='#f0f0f0')
        self.notebook.add(self.analytics_frame, text="Analytics")
        
        self.setup_test_tab()
        self.setup_stats_tab()
        self.setup_analytics_tab()
        
    def setup_test_tab(self):
        """Setup the main typing test interface"""
        # Title
        title_label = tk.Label(self.test_frame, text="Advanced 60 Second Typing Test - Continuous Mode", 
                              font=("Arial", 20, "bold"), bg='#f0f0f0', fg='#333')
        title_label.pack(pady=15)
        
        # Instructions
        instructions = tk.Label(self.test_frame, 
                               text="💡 Type the entire text below continuously. Words will be highlighted as you type.", 
                               font=("Arial", 12, "italic"), bg='#f0f0f0', fg='#666')
        instructions.pack(pady=5)
        
        # Stats frame
        stats_frame = tk.Frame(self.test_frame, bg='#f0f0f0')
        stats_frame.pack(pady=10)
        
        # Timer
        self.timer_label = tk.Label(stats_frame, text="Time: 60s", 
                                   font=("Arial", 16, "bold"), bg='#e3f2fd', 
                                   fg='#1976d2', padx=20, pady=10, relief='raised')
        self.timer_label.grid(row=0, column=0, padx=10)
        
        # WPM
        self.wpm_label = tk.Label(stats_frame, text="WPM: 0", 
                                 font=("Arial", 16, "bold"), bg='#e8f5e8', 
                                 fg='#388e3c', padx=20, pady=10, relief='raised')
        self.wpm_label.grid(row=0, column=1, padx=10)
        
        # Accuracy
        self.accuracy_label = tk.Label(stats_frame, text="Accuracy: 100%", 
                                      font=("Arial", 16, "bold"), bg='#fff3e0', 
                                      fg='#f57c00', padx=20, pady=10, relief='raised')
        self.accuracy_label.grid(row=0, column=2, padx=10)
        
        # Characters
        self.chars_label = tk.Label(stats_frame, text="Chars: 0", 
                                   font=("Arial", 16, "bold"), bg='#f3e5f5', 
                                   fg='#7b1fa2', padx=20, pady=10, relief='raised')
        self.chars_label.grid(row=0, column=3, padx=10)
        
        # Text display frame (SMALLER)
        text_frame = tk.Frame(self.test_frame, bg='white', relief='sunken', bd=2)
        text_frame.pack(pady=10, padx=40, fill='x')  # Removed expand=True to make it smaller
        
        # Text display with scrollbar
        text_container = tk.Frame(text_frame)
        text_container.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.text_display = tk.Text(text_container, font=("Courier New", 12), 
                                   wrap='word', height=4, state='disabled',  # Reduced height from 6 to 4
                                   bg='white', fg='#333', selectbackground='#ccc')
        scrollbar = tk.Scrollbar(text_container, orient='vertical', command=self.text_display.yview)
        self.text_display.configure(yscrollcommand=scrollbar.set)
        
        self.text_display.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Configure text tags for highlighting
        self.text_display.tag_configure('correct', background='#c8e6c9', foreground='#2e7d32', font=("Courier New", 12, "bold"))
        self.text_display.tag_configure('incorrect', background='#ffcdd2', foreground='#c62828', font=("Courier New", 12, "bold"))
        self.text_display.tag_configure('current', background='#fff3e0', foreground='#333', font=("Courier New", 12, "bold"))
        self.text_display.tag_configure('default', background='white', foreground='#666', font=("Courier New", 12))
        
        # Input frame (LARGER)
        input_frame = tk.Frame(self.test_frame, bg='#f0f0f0')
        input_frame.pack(pady=15, padx=40, fill='both', expand=True)  # Added expand=True for larger input area
        
        # User input label
        tk.Label(input_frame, text="Type the text above here:", font=("Arial", 14, "bold"), 
                bg='#f0f0f0').pack(anchor='w')
        
        # Large text area for typing
        input_text_frame = tk.Frame(input_frame, bg='white', relief='sunken', bd=2)
        input_text_frame.pack(fill='both', expand=True, pady=5)
        
        self.user_input = tk.Text(input_text_frame, font=("Courier New", 14), 
                                 wrap='word', height=8, state='disabled',  # Much larger input area
                                 bg='white', fg='#333', insertbackground='#333')
        input_scrollbar = tk.Scrollbar(input_text_frame, orient='vertical', command=self.user_input.yview)
        self.user_input.configure(yscrollcommand=input_scrollbar.set)
        
        self.user_input.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        input_scrollbar.pack(side='right', fill='y', pady=5)
        
        self.user_input.bind('<KeyRelease>', self.on_key_release)
        
        # Name input frame
        name_frame = tk.Frame(self.test_frame, bg='#f0f0f0')
        name_frame.pack(pady=10)
        
        tk.Label(name_frame, text="Your Name:", font=("Arial", 12), 
                bg='#f0f0f0').pack(side='left', padx=5)
        
        self.name_entry = tk.Entry(name_frame, font=("Arial", 12), width=20)
        self.name_entry.pack(side='left', padx=5)
        
        # Show user's best stats
        self.user_best_frame = tk.Frame(name_frame, bg='#f0f0f0')
        self.user_best_frame.pack(side='left', padx=20)
        
        self.best_stats_label = tk.Label(self.user_best_frame, text="", 
                                        font=("Arial", 10), bg='#f0f0f0', fg='#666')
        self.best_stats_label.pack()
        
        # Bind name entry to show stats
        self.name_entry.bind('<KeyRelease>', self.on_name_change)
        
        # Buttons frame
        button_frame = tk.Frame(self.test_frame, bg='#f0f0f0')
        button_frame.pack(pady=15)
        
        self.start_button = tk.Button(button_frame, text="Start Test", 
                                     font=("Arial", 14, "bold"), bg='#4caf50', 
                                     fg='white', padx=30, pady=10, 
                                     command=self.start_test)
        self.start_button.pack(side='left', padx=10)
        
        self.reset_button = tk.Button(button_frame, text="Reset", 
                                     font=("Arial", 14, "bold"), bg='#ff9800', 
                                     fg='white', padx=30, pady=10, 
                                     command=self.reset_test)
        self.reset_button.pack(side='left', padx=10)
        
        self.submit_button = tk.Button(button_frame, text="Submit Test", 
                                      font=("Arial", 14, "bold"), bg='#2196f3', 
                                      fg='white', padx=30, pady=10, 
                                      command=self.submit_test, state='disabled')
        self.submit_button.pack(side='left', padx=10)
        
    def setup_stats_tab(self):
        """Setup the statistics viewing interface"""
        # Title
        stats_title = tk.Label(self.stats_frame, text="User Statistics & History", 
                              font=("Arial", 20, "bold"), bg='#f0f0f0', fg='#333')
        stats_title.pack(pady=20)
        
        # Filter frame
        filter_frame = tk.Frame(self.stats_frame, bg='#f0f0f0')
        filter_frame.pack(pady=10)
        
        tk.Label(filter_frame, text="Filter by user:", font=("Arial", 12), 
                bg='#f0f0f0').pack(side='left', padx=5)
        
        self.stats_user_entry = tk.Entry(filter_frame, font=("Arial", 12), width=20)
        self.stats_user_entry.pack(side='left', padx=5)
        
        tk.Button(filter_frame, text="Show Stats", font=("Arial", 12), 
                 bg='#2196f3', fg='white', padx=20, pady=5,
                 command=self.show_user_stats).pack(side='left', padx=10)
        
        tk.Button(filter_frame, text="Show All", font=("Arial", 12), 
                 bg='#9c27b0', fg='white', padx=20, pady=5,
                 command=self.show_all_stats).pack(side='left', padx=5)
        
        # Stats display frame
        stats_display_frame = tk.Frame(self.stats_frame, bg='white', relief='sunken', bd=2)
        stats_display_frame.pack(pady=20, padx=20, fill='both', expand=True)
        
        # Create treeview for stats table
        self.stats_tree = ttk.Treeview(stats_display_frame, columns=(
            'Username', 'WPM', 'Accuracy', 'Total Chars', 'Correct', 'Incorrect', 'CPM', 'Date', 'Time'
        ), show='headings', height=15)
        
        # Define headings
        self.stats_tree.heading('Username', text='Username')
        self.stats_tree.heading('WPM', text='WPM')
        self.stats_tree.heading('Accuracy', text='Accuracy %')
        self.stats_tree.heading('Total Chars', text='Total Chars')
        self.stats_tree.heading('Correct', text='Correct')
        self.stats_tree.heading('Incorrect', text='Incorrect')
        self.stats_tree.heading('CPM', text='CPM')
        self.stats_tree.heading('Date', text='Date')
        self.stats_tree.heading('Time', text='Time')
        
        # Configure column widths
        self.stats_tree.column('Username', width=100)
        self.stats_tree.column('WPM', width=70)
        self.stats_tree.column('Accuracy', width=80)
        self.stats_tree.column('Total Chars', width=90)
        self.stats_tree.column('Correct', width=70)
        self.stats_tree.column('Incorrect', width=80)
        self.stats_tree.column('CPM', width=70)
        self.stats_tree.column('Date', width=90)
        self.stats_tree.column('Time', width=70)
        
        # Add scrollbar to treeview
        stats_scrollbar = ttk.Scrollbar(stats_display_frame, orient='vertical', command=self.stats_tree.yview)
        self.stats_tree.configure(yscrollcommand=stats_scrollbar.set)
        
        self.stats_tree.pack(side='left', fill='both', expand=True, padx=10, pady=10)
        stats_scrollbar.pack(side='right', fill='y', pady=10)
        
        # Summary frame
        self.summary_frame = tk.Frame(self.stats_frame, bg='#e3f2fd', relief='raised', bd=2)
        self.summary_frame.pack(pady=10, padx=20, fill='x')
        
        self.summary_label = tk.Label(self.summary_frame, text="Select a user to see detailed statistics", 
                                     font=("Arial", 12), bg='#e3f2fd', fg='#1976d2')
        self.summary_label.pack(pady=15)
        
        # Load all stats initially
        self.show_all_stats()
        
    def setup_analytics_tab(self):
        """Setup the analytics and visualization interface"""
        # Title
        analytics_title = tk.Label(self.analytics_frame, text="Performance Analytics & Insights", 
                                  font=("Arial", 20, "bold"), bg='#f0f0f0', fg='#333')
        analytics_title.pack(pady=20)
        
        # Control frame
        control_frame = tk.Frame(self.analytics_frame, bg='#f0f0f0')
        control_frame.pack(pady=10)
        
        tk.Label(control_frame, text="Analyze user:", font=("Arial", 12), 
                bg='#f0f0f0').pack(side='left', padx=5)
        
        self.analytics_user_entry = tk.Entry(control_frame, font=("Arial", 12), width=20)
        self.analytics_user_entry.pack(side='left', padx=5)
        
        tk.Button(control_frame, text="Generate Charts", font=("Arial", 12), 
                 bg='#4caf50', fg='white', padx=20, pady=5,
                 command=self.generate_analytics).pack(side='left', padx=10)
        
        tk.Button(control_frame, text="Compare Users", font=("Arial", 12), 
                 bg='#ff5722', fg='white', padx=20, pady=5,
                 command=self.generate_comparison_analytics).pack(side='left', padx=5)
        
        # Canvas frame for matplotlib plots
        self.canvas_frame = tk.Frame(self.analytics_frame, bg='white')
        self.canvas_frame.pack(pady=20, padx=20, fill='both', expand=True)
        
    def on_name_change(self, event):
        """Show user's best stats when name is entered"""
        username = self.name_entry.get().strip()
        if username and len(username) > 2:  # Show stats after 3 characters
            stats = self.get_user_best_stats(username)
            if stats['total_tests'] > 0:
                text = f"Best: {stats['best_wpm']} WPM, {stats['best_accuracy']}% | Avg: {stats['avg_wpm']} WPM | Tests: {stats['total_tests']}"
                self.best_stats_label.config(text=text, fg='#2e7d32')
            else:
                self.best_stats_label.config(text="New user - no previous tests", fg='#666')
        else:
            self.best_stats_label.config(text="")
            
    def show_user_stats(self):
        """Show statistics for specific user"""
        username = self.stats_user_entry.get().strip()
        if not username:
            messagebox.showwarning("Username Required", "Please enter a username to filter stats.")
            return
            
        stats = self.get_user_stats(username)
        self.populate_stats_table(stats)
        
        # Show summary for user
        best_stats = self.get_user_best_stats(username)
        if best_stats['total_tests'] > 0:
            summary_text = f"""
Stats for {username}:
Best WPM: {best_stats['best_wpm']} | Best Accuracy: {best_stats['best_accuracy']}%
Average WPM: {best_stats['avg_wpm']} | Total Tests: {best_stats['total_tests']}
            """
            self.summary_label.config(text=summary_text.strip())
        else:
            self.summary_label.config(text=f"No test records found for user: {username}")
            
    def show_all_stats(self):
        """Show all user statistics"""
        stats = self.get_user_stats()
        self.populate_stats_table(stats)
        
        # Show general summary
        if stats:
            total_tests = len(stats)
            unique_users = len(set(stat[1] for stat in stats))  # Count unique usernames
            avg_wpm = sum(stat[2] for stat in stats) / total_tests
            avg_accuracy = sum(stat[3] for stat in stats) / total_tests
            
            summary_text = f"""
Overall Statistics:
Total Tests: {total_tests} | Unique Users: {unique_users}
Average WPM: {avg_wpm:.1f} | Average Accuracy: {avg_accuracy:.1f}%
            """
            self.summary_label.config(text=summary_text.strip())
        else:
            self.summary_label.config(text="No test records found in database.")
            
    def populate_stats_table(self, stats):
        """Populate the statistics table with data"""
        # Clear existing data
        for item in self.stats_tree.get_children():
            self.stats_tree.delete(item)
            
        # Insert new data
        for stat in stats:
            self.stats_tree.insert('', 'end', values=(
                stat[1],  # username
                stat[2],  # wpm
                f"{stat[3]}%",  # accuracy
                stat[4],  # total_chars
                stat[5],  # correct_chars
                stat[6],  # incorrect_chars
                stat[7],  # chars_per_minute
                stat[9],  # test_date
                stat[10]  # test_time
            ))
            
    def generate_text(self):
        """Generate text for typing test"""
        # Create sentences from random words
        sentences = []
        for _ in range(8):  # 8 sentences
            sentence_words = random.choices(self.words, k=random.randint(4, 8))
            sentence = ' '.join(sentence_words) + '.'
            sentences.append(sentence.capitalize())
        
        self.test_text = ' '.join(sentences)
        self.display_text()
        
    def display_text(self):
        """Display the test text"""
        self.text_display.config(state='normal')
        self.text_display.delete(1.0, tk.END)
        self.text_display.insert(tk.END, self.test_text, 'default')
        self.text_display.config(state='disabled')
        
    def start_test(self):
        """Start the typing test"""
        if not self.name_entry.get().strip():
            messagebox.showwarning("Name Required", "Please enter your name before starting the test.")
            return
            
        self.user_name = self.name_entry.get().strip()
        self.test_active = True
        self.test_completed = False
        self.start_time = time.time()
        self.time_left = 60
        self.typed_text = ""
        self.correct_chars = 0
        self.incorrect_chars = 0
        self.total_chars_typed = 0
        
        # Enable input and disable start button
        self.user_input.config(state='normal', bg='white')
        self.user_input.delete(1.0, tk.END)
        self.user_input.focus()
        self.start_button.config(state='disabled')
        self.submit_button.config(state='disabled')
        self.name_entry.config(state='disabled')
        
        # Start timer
        self.start_timer()
        
    def start_timer(self):
        """Start the countdown timer"""
        def countdown():
            while self.test_active and self.time_left > 0:
                self.timer_label.config(text=f"Time: {self.time_left}s")
                time.sleep(1)
                self.time_left -= 1
                
            if self.test_active and self.time_left <= 0:
                self.test_active = False
                self.test_completed = True
                self.root.after(0, self.enable_submit)
                
        self.timer_thread = threading.Thread(target=countdown, daemon=True)
        self.timer_thread.start()
        
    def enable_submit(self):
        """Enable submit button when test is completed"""
        self.user_input.config(state='disabled', bg='#f0f0f0')
        self.submit_button.config(state='normal', bg='#4caf50')
        self.timer_label.config(text="Time: 0s - Test Complete!")
        messagebox.showinfo("Test Complete", "Time's up! Click 'Submit Test' to save your results.")
        
    def on_key_release(self, event):
        """Handle key release events for continuous typing"""
        if not self.test_active:
            return
            
        # Get typed text
        self.typed_text = self.user_input.get(1.0, tk.END).rstrip('\n')
        self.total_chars_typed = len(self.typed_text)
        
        # Update display with highlighting
        self.update_text_highlighting()
        
        # Update statistics
        self.update_stats()
            
    def update_text_highlighting(self):
        """Update text highlighting based on typed input"""
        self.text_display.config(state='normal')
        self.text_display.delete(1.0, tk.END)
        
        # Reset counters
        self.correct_chars = 0
        self.incorrect_chars = 0
        
        # Compare character by character
        for i, char in enumerate(self.test_text):
            if i < len(self.typed_text):
                typed_char = self.typed_text[i]
                if char == typed_char:
                    self.text_display.insert(tk.END, char, 'correct')
                    self.correct_chars += 1
                else:
                    self.text_display.insert(tk.END, char, 'incorrect')
                    self.incorrect_chars += 1
            elif i == len(self.typed_text):
                # Current position
                self.text_display.insert(tk.END, char, 'current')
            else:
                # Not yet typed
                self.text_display.insert(tk.END, char, 'default')
                
        self.text_display.config(state='disabled')
        
    def update_stats(self):
        """Update WPM, accuracy, and character count display"""
        if self.start_time:
            elapsed_time = time.time() - self.start_time
            if elapsed_time > 0:
                # Calculate WPM (assuming average word length of 5 characters)
                words_typed = self.correct_chars / 5
                wpm = int((words_typed / elapsed_time) * 60)
                self.wpm_label.config(text=f"WPM: {wpm}")
                
        # Calculate accuracy
        if self.total_chars_typed > 0:
            accuracy = int((self.correct_chars / self.total_chars_typed) * 100)
            self.accuracy_label.config(text=f"Accuracy: {accuracy}%")
        else:
            self.accuracy_label.config(text="Accuracy: 100%")
            
        self.chars_label.config(text=f"Chars: {self.total_chars_typed}")
            
    def submit_test(self):
        """Submit the test results"""
        if not self.test_completed:
            messagebox.showwarning("Test Not Complete", "Please complete the test before submitting.")
            return
            
        # Calculate final stats
        elapsed_time = 60  # Full test duration
        
        # Calculate WPM (correct characters / 5 characters per word)
        words_typed = self.correct_chars / 5
        wpm = int(words_typed)
        
        # Calculate accuracy
        accuracy = int((self.correct_chars / self.total_chars_typed) * 100) if self.total_chars_typed > 0 else 0
        
        # Calculate characters per minute
        cpm = int((self.total_chars_typed / elapsed_time) * 60)
        
        # Save to database
        self.save_test_result(self.user_name, wpm, accuracy, self.total_chars_typed, 
                             self.correct_chars, self.incorrect_chars, cpm, elapsed_time)
        
        self.show_results(wpm, accuracy, self.total_chars_typed, cpm)
        
        # Update the user's best stats display
        self.on_name_change(None)
        
        # Reset submit button
        self.submit_button.config(state='disabled', bg='#2196f3')
        self.start_button.config(state='normal')
        self.name_entry.config(state='normal')
        
    def show_results(self, wpm, accuracy, total_chars, cpm):
        """Display test results"""
        # Results popup
        popup = tk.Toplevel(self.root)
        popup.title("Test Results")
        popup.geometry("500x450")
        popup.configure(bg='#e8f5e8')
        popup.transient(self.root)
        popup.grab_set()
        
        # Center the popup
        popup.update_idletasks()
        x = (popup.winfo_screenwidth() // 2) - (popup.winfo_width() // 2)
        y = (popup.winfo_screenheight() // 2) - (popup.winfo_height() // 2)
        popup.geometry(f"+{x}+{y}")
        
        tk.Label(popup, text=f"🎉 Results for {self.user_name}", 
                font=("Arial", 18, "bold"), bg='#e8f5e8', fg='#2e7d32').pack(pady=20)
        
        results_text = f"""
📊 PERFORMANCE METRICS:

Words Per Minute (WPM): {wpm}
Characters Per Minute: {cpm}
Accuracy: {accuracy}%
Total Characters Typed: {total_chars}
Correct Characters: {self.correct_chars}
Incorrect Characters: {self.incorrect_chars}

✅ Results saved to database!
"""
        
        tk.Label(popup, text=results_text, 
                font=("Arial", 12), bg='#e8f5e8', justify='left').pack(pady=10)
        
        # Performance message
        if wpm >= 40 and accuracy >= 95:
            message = "🏆 Excellent! You're a typing master!"
            color = '#2e7d32'
        elif wpm >= 30 and accuracy >= 90:
            message = "👍 Great job! You're doing well!"
            color = '#388e3c'
        elif wpm >= 20 and accuracy >= 80:
            message = "📈 Good work! Keep practicing!"
            color = '#689f38'
        else:
            message = "💪 Keep practicing to improve!"
            color = '#f57c00'
            
        tk.Label(popup, text=message, 
                font=("Arial", 14, "bold"), bg='#e8f5e8', fg=color).pack(pady=10)
        
        # Show personal best info
        best_stats = self.get_user_best_stats(self.user_name)
        if best_stats['total_tests'] > 1:  # More than current test
            improvement_text = f"""
📈 YOUR PERSONAL RECORDS:
Best WPM: {best_stats['best_wpm']} | Best Accuracy: {best_stats['best_accuracy']}%
Average WPM: {best_stats['avg_wpm']} | Total Tests: {best_stats['total_tests']}
"""
            tk.Label(popup, text=improvement_text, 
                    font=("Arial", 10), bg='#e8f5e8', fg='#666').pack(pady=5)
        
        # Button frame
        button_frame = tk.Frame(popup, bg='#e8f5e8')
        button_frame.pack(pady=20)
        
        tk.Button(button_frame, text="View Analytics", 
                 font=("Arial", 12, "bold"), bg='#4caf50', fg='white',
                 padx=20, pady=5, command=lambda: [popup.destroy(), self.switch_to_analytics()]).pack(side='left', padx=10)
        
        tk.Button(button_frame, text="New Test", 
                 font=("Arial", 12, "bold"), bg='#2196f3', fg='white',
                 padx=20, pady=5, command=lambda: [popup.destroy(), self.reset_test()]).pack(side='left', padx=10)
        
        tk.Button(button_frame, text="Close", 
                 font=("Arial", 12, "bold"), bg='#ff5722', fg='white',
                 padx=20, pady=5, command=popup.destroy).pack(side='left', padx=10)
        
    def switch_to_analytics(self):
        """Switch to analytics tab and generate charts for current user"""
        self.notebook.select(2)  # Select analytics tab
        self.analytics_user_entry.delete(0, tk.END)
        self.analytics_user_entry.insert(0, self.user_name)
        self.generate_analytics()
        
    def reset_test(self):
        """Reset the test to initial state"""
        self.test_active = False
        self.test_completed = False
        self.typed_text = ""
        self.correct_chars = 0
        self.incorrect_chars = 0
        self.total_chars_typed = 0
        self.time_left = 60
        
        self.user_input.config(state='disabled', bg='white')
        self.user_input.delete(1.0, tk.END)
        self.start_button.config(state='normal')
        self.submit_button.config(state='disabled', bg='#2196f3')
        self.name_entry.config(state='normal')
        self.timer_label.config(text="Time: 60s")
        self.wpm_label.config(text="WPM: 0")
        self.accuracy_label.config(text="Accuracy: 100%")
        self.chars_label.config(text="Chars: 0")
        
        self.generate_text()
        
    def generate_analytics(self):
        """Generate analytics charts for specific user"""
        username = self.analytics_user_entry.get().strip()
        if not username:
            messagebox.showwarning("Username Required", "Please enter a username to generate analytics.")
            return
            
        stats = self.get_user_stats(username)
        if not stats:
            messagebox.showinfo("No Data", f"No test data found for user: {username}")
            return
            
        # Clear existing plots
        for widget in self.canvas_frame.winfo_children():
            widget.destroy()
            
        # Set seaborn style
        sns.set_style("whitegrid")
        sns.set_palette("husl")
        
        # Create figure with subplots
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 8))
        fig.suptitle(f'Performance Analytics for {username}', fontsize=16, fontweight='bold')
        
        # Prepare data
        dates = [datetime.strptime(stat[9], "%Y-%m-%d") for stat in stats]
        wpms = [stat[2] for stat in stats]
        accuracies = [stat[3] for stat in stats]
        total_chars = [stat[4] for stat in stats]
        cpms = [stat[7] for stat in stats]
        
        # Chart 1: WPM Progress Over Time with seaborn style
        sns.lineplot(x=dates, y=wpms, marker='o', linewidth=3, markersize=8, ax=ax1, color='#2196f3')
        ax1.fill_between(dates, wpms, alpha=0.3, color='#2196f3')
        ax1.set_title('WPM Progress Over Time', fontweight='bold', fontsize=12)
        ax1.set_ylabel('Words Per Minute')
        ax1.tick_params(axis='x', rotation=45)
        
        # Chart 2: Accuracy Over Time with trend
        sns.lineplot(x=dates, y=accuracies, marker='s', linewidth=3, markersize=8, ax=ax2, color='#4caf50')
        ax2.fill_between(dates, accuracies, alpha=0.3, color='#4caf50')
        ax2.set_title('Accuracy Progress Over Time', fontweight='bold', fontsize=12)
        ax2.set_ylabel('Accuracy (%)')
        ax2.tick_params(axis='x', rotation=45)
        
        # Chart 3: WPM vs Accuracy Scatter with regression line
        sns.scatterplot(x=wpms, y=accuracies, s=100, alpha=0.7, ax=ax3)
        sns.regplot(x=wpms, y=accuracies, ax=ax3, scatter=False, color='red', line_kws={'linewidth': 2})
        ax3.set_title('WPM vs Accuracy Correlation', fontweight='bold', fontsize=12)
        ax3.set_xlabel('Words Per Minute')
        ax3.set_ylabel('Accuracy (%)')
        
        # Chart 4: Performance Distribution with KDE
        sns.histplot(wpms, bins=10, kde=True, ax=ax4, color='#ff9800', alpha=0.7)
        ax4.axvline(np.mean(wpms), color='red', linestyle='--', linewidth=2, label=f'Average: {np.mean(wpms):.1f}')
        ax4.set_title('WPM Distribution with Density', fontweight='bold', fontsize=12)
        ax4.set_xlabel('Words Per Minute')
        ax4.set_ylabel('Frequency')
        ax4.legend()
        
        plt.tight_layout()
        
        # Embed plot in tkinter
        canvas = FigureCanvasTkAgg(fig, self.canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)
        
        # Add statistics summary
        stats_summary = tk.Frame(self.canvas_frame, bg='#f0f0f0', relief='raised', bd=2)
        stats_summary.pack(fill='x', pady=10)
        
        summary_text = f"""
📊 DETAILED ANALYTICS FOR {username.upper()}:
Total Tests: {len(stats)} | Best WPM: {max(wpms)} | Average WPM: {np.mean(wpms):.1f} | Best Accuracy: {max(accuracies)}%
Average Accuracy: {np.mean(accuracies):.1f}% | Total Characters Typed: {sum(total_chars)} | Average CPM: {np.mean(cpms):.1f}
Improvement Trend: {"📈 Improving" if len(wpms) > 1 and wpms[-1] > wpms[0] else "📊 Stable"}
"""
        
        tk.Label(stats_summary, text=summary_text, font=("Arial", 10), 
                bg='#f0f0f0', fg='#333', justify='left').pack(pady=10)
        
    def generate_comparison_analytics(self):
        """Generate comparison analytics for top users"""
        all_stats = self.get_user_stats()
        if not all_stats:
            messagebox.showinfo("No Data", "No test data found in database.")
            return
            
        # Clear existing plots
        for widget in self.canvas_frame.winfo_children():
            widget.destroy()
            
        # Create DataFrame for easier analysis
        df = pd.DataFrame(all_stats, columns=['id', 'username', 'wpm', 'accuracy', 'total_chars', 
                                             'correct_chars', 'incorrect_chars', 'cpm', 'duration', 
                                             'test_date', 'test_time'])
        
        # Set seaborn style
        sns.set_style("whitegrid")
        try:
            plt.style.use('seaborn-v0_8')
        except:
            try:
                plt.style.use('seaborn')
            except:
                pass  # Use default style if seaborn styles not available
        
        # Create figure with subplots
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 8))
        fig.suptitle('User Comparison Analytics', fontsize=16, fontweight='bold')
        
        # Chart 1: Top Users by Average WPM (Seaborn barplot)
        user_avg_wpm = df.groupby('username')['wpm'].mean().sort_values(ascending=False).head(10)
        sns.barplot(x=user_avg_wpm.values, y=user_avg_wpm.index, ax=ax1, hue=user_avg_wpm.index, palette='viridis', legend=False)
        ax1.set_title('Top 10 Users by Average WPM', fontweight='bold', fontsize=12)
        ax1.set_xlabel('Average WPM')
        
        # Chart 2: WPM vs Accuracy Comparison (Enhanced scatter)
        user_stats = df.groupby('username').agg({'wpm': 'mean', 'accuracy': 'mean', 'id': 'count'}).reset_index()
        user_stats.columns = ['username', 'avg_wpm', 'avg_accuracy', 'test_count']
        
        scatter = ax2.scatter(user_stats['avg_wpm'], user_stats['avg_accuracy'], 
                            s=user_stats['test_count']*20, alpha=0.6, c=user_stats['avg_wpm'], 
                            cmap='plasma', edgecolors='black', linewidth=1)
        ax2.set_title('User Performance Comparison\n(Size = Number of Tests)', fontweight='bold', fontsize=12)
        ax2.set_xlabel('Average WPM')
        ax2.set_ylabel('Average Accuracy (%)')
        plt.colorbar(scatter, ax=ax2, label='Avg WPM')
        
        # Chart 3: Performance Distribution Comparison (Violin plot)
        top_users = user_avg_wpm.head(5).index.tolist()
        df_top = df[df['username'].isin(top_users)]
        
        if len(df_top) > 0:
            sns.violinplot(data=df_top, x='username', y='wpm', ax=ax3, hue='username', palette='Set2', legend=False)
            ax3.set_title('WPM Distribution - Top 5 Users', fontweight='bold', fontsize=12)
            ax3.tick_params(axis='x', rotation=45)
            ax3.set_ylabel('Words Per Minute')
        
        # Chart 4: User Activity Heatmap
        df['test_date'] = pd.to_datetime(df['test_date'])
        df['day_of_week'] = df['test_date'].dt.day_name()
        df['hour'] = pd.to_datetime(df['test_time']).dt.hour
        
        # Create activity heatmap data
        activity_data = df.groupby(['day_of_week', 'hour']).size().unstack(fill_value=0)
        
        # Reorder days
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        activity_data = activity_data.reindex([day for day in day_order if day in activity_data.index])
        
        if not activity_data.empty:
            sns.heatmap(activity_data, annot=True, fmt='d', ax=ax4, cmap='YlOrRd', cbar_kws={'label': 'Tests'})
            ax4.set_title('User Activity Heatmap', fontweight='bold', fontsize=12)
            ax4.set_xlabel('Hour of Day')
            ax4.set_ylabel('Day of Week')
        
        plt.tight_layout()
        
        # Embed plot in tkinter
        canvas = FigureCanvasTkAgg(fig, self.canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)
        
        # Add comparison statistics
        stats_summary = tk.Frame(self.canvas_frame, bg='#f0f0f0', relief='raised', bd=2)
        stats_summary.pack(fill='x', pady=10)
        
        unique_users = df['username'].nunique()
        total_tests = len(df)
        avg_wpm = df['wpm'].mean()
        avg_accuracy = df['accuracy'].mean()
        total_chars = df['total_chars'].sum()
        top_performer = user_avg_wpm.index[0] if len(user_avg_wpm) > 0 else "N/A"
        
        summary_text = f"""
🏆 PLATFORM COMPARISON ANALYTICS:
Total Users: {unique_users} | Total Tests: {total_tests} | Platform Avg WPM: {avg_wpm:.1f} | Platform Avg Accuracy: {avg_accuracy:.1f}%
Total Characters Typed: {total_chars:,} | Top Performer: {top_performer} ({user_avg_wpm.iloc[0]:.1f} WPM avg)
Most Active User: {df['username'].value_counts().index[0]} ({df['username'].value_counts().iloc[0]} tests)
"""
        
        tk.Label(stats_summary, text=summary_text, font=("Arial", 10), 
                bg='#f0f0f0', fg='#333', justify='left').pack(pady=10)
        
    def run(self):
        """Start the application"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
        
    def on_closing(self):
        """Handle application closing"""
        self.conn.close()
        self.root.destroy()

if __name__ == "__main__":
    app = TypingTest()
    app.run()