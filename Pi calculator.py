import tkinter as tk
from tkinter import scrolledtext, ttk
from decimal import Decimal, getcontext
import time
import threading
import multiprocessing

CORE_THRESHOLD = 250000  

def compute_leaf_range(start_idx, end_idx):
    local_leaves = []
    for a in range(start_idx, end_idx):
        if a == 0:
            local_leaves.append((1, 1, 13591409))
        else:
            P = (6 * a - 5) * (2 * a - 1) * (6 * a - 1)
            Q = a**3 * 262537412640768000
            T = 13591409 + 545140134 * a
            if a % 2 != 0:
                T = -T
            local_leaves.append((P, Q, T))
    return local_leaves

class DarkHybridPiApp:
    def __init__(self, root):
        self.root = root
        self.root.geometry("520x620")
        self.root.title("Pi")
        self.root.resizable(True, True)
        self.is_calculating = False
        
        self.bg_dark = "#1e1e24"      
        self.bg_panel = "#2a2a35"     
        self.fg_light = "#e1e1e6"     
        self.fg_dim = "#a4a4b5"       
        self.accent_blue = "#00adb5"  
        self.btn_stop = "#ff2e63"     
        self.text_area_bg = "#111115" 
        
        self.root.configure(bg=self.bg_dark)
        self.setup_ui()

    def setup_ui(self):
        style = ttk.Style()
        style.theme_use('default')
        style.configure("Dark.Horizontal.TProgressbar", 
                        troughcolor=self.bg_panel, 
                        background=self.accent_blue, 
                        thickness=8, 
                        borderwidth=0)

        top_frame = tk.Frame(self.root, bg=self.bg_dark, pady=10)
        top_frame.pack(fill=tk.X)

        entry_label = tk.Label(top_frame, text="Target Digits:", font=("Arial", 10, "bold"), bg=self.bg_dark, fg=self.fg_light)
        entry_label.pack(side=tk.LEFT, padx=15)

        self.digits_entry = tk.Entry(
            top_frame, 
            font=("Arial", 11), 
            bg=self.bg_panel, 
            fg=self.fg_light, 
            insertbackground=self.fg_light,  
            bd=1, 
            relief="flat",
            highlightthickness=1,
            highlightbackground="#444454",
            highlightcolor=self.accent_blue
        )
        self.digits_entry.insert(0, "10000") 
        self.digits_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 15))

        self.stats_label = tk.Label(
            self.root, 
            text="Digits: 0   |   Iterations: 0\nTime: 0.00s   |   Speed: 0 Digits/s", 
            font=("Courier", 10, "bold"), 
            bg=self.bg_dark, 
            fg=self.fg_dim,
            justify="center", 
            pady=8
        )
        self.stats_label.pack(fill=tk.X)

        self.progress_frame = tk.Frame(self.root, bg=self.bg_dark, padx=15, pady=4)
        self.progress_frame.pack(fill=tk.X)
        
        self.progress_bar = ttk.Progressbar(self.progress_frame, orient="horizontal", mode="indeterminate", style="Dark.Horizontal.TProgressbar")
        self.progress_bar.pack(fill=tk.X)

        self.pi_display_area = scrolledtext.ScrolledText(
            self.root, 
            font=("Courier", 11), 
            wrap=tk.NONE, 
            bd=0, 
            bg=self.text_area_bg, 
            fg=self.accent_blue,
            insertbackground=self.fg_light,
            padx=10,
            pady=10
        )
        self.pi_display_area.insert(tk.END, f"Below {CORE_THRESHOLD:,} digits uses single-core.\nAbove uses multi-core processing pool.")
        self.pi_display_area.config(state='disabled')
        self.pi_display_area.pack(fill=tk.BOTH, expand=True, padx=15, pady=8)

        self.button = tk.Button(
            self.root, 
            text="Run Hybrid Engine", 
            bg=self.accent_blue, 
            fg=self.bg_dark, 
            activebackground="#00ffe0",
            activeforeground=self.bg_dark,
            font=("Arial", 11, "bold"), 
            command=self.start_calculation, 
            relief="flat",
            bd=0,
            pady=8,
            cursor="hand2"
        )
        self.button.pack(fill=tk.X, padx=15, pady=15)

    def start_calculation(self):
        if self.is_calculating:
            return
            
        try:
            digits = int(self.digits_entry.get())
            if digits <= 0: raise ValueError
        except ValueError:
            self.stats_label.config(text="Please enter a valid positive integer.", fg="#ff5555")
            return
            
        self.is_calculating = True
        self.button.config(text="Calculating...", bg="#444454", fg=self.fg_dim, state="disabled")
        self.stats_label.config(fg=self.fg_dim)
        self.progress_bar.start(12)
        
        if digits < CORE_THRESHOLD:
            self.stats_label.config(text="Routing to Single-Core Engine...\nBypassing core-spawn overhead.")
            mode = "Single-Core Engine"
        else:
            self.stats_label.config(text="Routing to Multi-Core Process Pool...\nSpawning background processing cores.")
            mode = "Multi-Core Engine"
            
        threading.Thread(target=self.calculation_task, args=(digits, mode), daemon=True).start()

    def calculation_task(self, digits, mode):
        try:
            terms = max(1, int(digits / 14.18164746272566) + 1)
            getcontext().prec = digits + 50
            
            start_time = time.time()
            leaves = []

            if mode == "Single-Core Engine":
                leaves = [None] * terms
                for a in range(terms):
                    if a == 0:
                        leaves[a] = (1, 1, 13591409)
                    else:
                        P = (6 * a - 5) * (2 * a - 1) * (6 * a - 1)
                        Q = a**3 * 262537412640768000
                        T = 13591409 + 545140134 * a
                        if a % 2 != 0:
                            T = -T
                        leaves[a] = (P, Q, T)

            else:
                num_cores = multiprocessing.cpu_count()
                chunk_size = max(1, terms // num_cores)
                ranges = []
                
                for i in range(num_cores):
                    start_idx = i * chunk_size
                    end_idx = terms if i == num_cores - 1 else (i + 1) * chunk_size
                    if start_idx < terms:
                        ranges.append((start_idx, end_idx))

                with multiprocessing.Pool(processes=num_cores) as pool:
                    results = pool.starmap(compute_leaf_range, ranges)
                    for sublist in results:
                        leaves.extend(sublist)

            while len(leaves) > 1:
                next_level = []
                for i in range(0, len(leaves), 2):
                    if i + 1 < len(leaves):
                        P1, Q1, T1 = leaves[i]
                        P2, Q2, T2 = leaves[i+1]
                        
                        P = P1 * P2
                        Q = Q1 * Q2
                        T = Q2 * T1 + P1 * T2
                        next_level.append((P, Q, T))
                    else:
                        next_level.append(leaves[i])
                leaves = next_level

            P, Q, T = leaves[0]
            
            D_Q = Decimal(Q)
            D_T = Decimal(T)
            
            sqrt_10005 = Decimal(10005).sqrt()
            C = 426880 * sqrt_10005
            pi_estimate = (C * D_Q) / D_T
            
            pi_string = str(pi_estimate)[:digits + 2] 
            
            elapsed = time.time() - start_time
            dps = digits / elapsed if elapsed > 0 else 0
            
            self.root.after(0, lambda: self.update_ui_final(digits, terms, elapsed, dps, pi_string, mode))
            
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda: self.handle_error(error_msg))

    def handle_error(self, error_msg):
        self.is_calculating = False
        self.progress_bar.stop()
        self.stats_label.config(text="An engine crash occurred during processing.", fg=self.btn_stop)
        self.pi_display_area.config(state='normal')
        self.pi_display_area.delete("1.0", tk.END)
        self.pi_display_area.insert(tk.END, f"Error Details:\n{error_msg}\n\nMake sure to execute the script directly from your system terminal.")
        self.pi_display_area.config(state='disabled')
        self.button.config(text="Run Hybrid Engine", bg=self.accent_blue, fg=self.bg_dark, state="normal")

    def update_ui_final(self, digits, terms, elapsed, dps, pi_string, mode):
        self.is_calculating = False
        self.progress_bar.stop()
        
        self.stats_label.config(
            text=f"Engine: {mode}   |   Iterations: {terms:,}\n"
                 f"Digits: {digits:,}   |   Time: {elapsed:.2f}s   |   Speed: {int(dps):,} D/s",
            fg=self.fg_light
        )
        
        formatted_pi = "\n".join(
            [pi_string[i:i+40] for i in range(0, len(pi_string), 40)]
        )
        
        self.pi_display_area.config(state='normal')
        self.pi_display_area.delete("1.0", tk.END)
        self.pi_display_area.insert(tk.END, formatted_pi)
        self.pi_display_area.config(state='disabled')
        
        self.button.config(text="Run Hybrid Engine", bg=self.accent_blue, fg=self.bg_dark, state="normal")

if __name__ == '__main__':
    multiprocessing.freeze_support()
    root = tk.Tk()
    app = DarkHybridPiApp(root)
    root.mainloop()
