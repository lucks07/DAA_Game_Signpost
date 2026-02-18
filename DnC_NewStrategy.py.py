import tkinter as tk
from tkinter import messagebox
import random

# ====================
# GRAPH IMPLEMENTATION
# ====================

class GraphNode:
    """Represents a single grid cell in the puzzle"""
    def __init__(self, label, row, col, arrow_direction):
        self.label = label
        self.row = row
        self.col = col
        self.arrow_direction = arrow_direction
        self.visited = False
        self.visit_order = None


class PuzzleGraph:
    """Graph representation using adjacency list"""
    def __init__(self):
        self.nodes = {}
        self.adjacency_list = {}
        self.solution_path = []

    def add_node(self, label, row, col, arrow_direction):
        self.nodes[label] = GraphNode(label, row, col, arrow_direction)
        self.adjacency_list[label] = []

    def add_edge(self, from_label, to_label):
        if from_label in self.adjacency_list:
            self.adjacency_list[from_label].append(to_label)

    def get_neighbors(self, label):
        return self.adjacency_list.get(label, [])

    def set_solution_path(self, path):
        self.solution_path = path


# ====================
# GAME LOGIC
# ====================

class GameState:
    def __init__(self, graph):
        self.graph = graph
        self.current_position = 'A'
        self.current_turn = 'Human'
        self.visit_count = 1

        self.human_correct_moves = 0
        self.human_illegal_moves = 0
        self.cpu_correct_moves = 0
        self.cpu_illegal_moves = 0

        self.cpu_illegal_history = set()

        self.graph.nodes['A'].visited = True
        self.graph.nodes['A'].visit_order = 1

        self.game_over = False
        self.winner = None

    def is_legal_move(self, target):
        if target not in self.graph.get_neighbors(self.current_position):
            return False
        if self.graph.nodes[target].visited:
            return False
        return True

    def is_correct_move(self, target):
        try:
            idx = self.graph.solution_path.index(self.current_position)
            return self.graph.solution_path[idx + 1] == target
        except:
            return False

    def make_move(self, target):
        if self.game_over:
            return False, False

        legal = self.is_legal_move(target)
        correct = self.is_correct_move(target)

        if not legal or not correct:
            if self.current_turn == 'Human':
                self.human_illegal_moves += 1
            else:
                self.cpu_illegal_moves += 1
                self.cpu_illegal_history.add((self.current_position, target))

            self.switch_turn()
            return False, False

        self.visit_count += 1
        node = self.graph.nodes[target]
        node.visited = True
        node.visit_order = self.visit_count
        self.current_position = target

        if self.current_turn == 'Human':
            self.human_correct_moves += 1
        else:
            self.cpu_correct_moves += 1

        if target == 'P':
            self.game_over = True
            self.determine_winner()

        self.switch_turn()
        return True, True

    def switch_turn(self):
        self.current_turn = 'CPU' if self.current_turn == 'Human' else 'Human'

    def determine_winner(self):
        if self.human_illegal_moves < self.cpu_illegal_moves:
            self.winner = 'Human'
        elif self.cpu_illegal_moves < self.human_illegal_moves:
            self.winner = 'CPU'
        else:
            self.winner = 'Draw'


# ====================
# CPU PLAYER (Depth-Limited Divide & Conquer Search)
# ====================

class dncCPU:
    """
    Divide & Conquer Search :
    - Divide: consider each candidate neighbor move as a subproblem
    - Conquer: recursively evaluate best outcome from that neighbor (depth-limited)
    - Combine: pick the move with the highest score
    """
    def __init__(self, graph, game_state, depth=6):
        self.graph = graph
        self.game_state = game_state
        self.depth = depth


    def distance_to_goal(self, label):
        node = self.graph.nodes[label]
        goal = self.graph.nodes['P']
        return abs(node.row - goal.row) + abs(node.col - goal.col)

    def build_candidates(self, current, visited_set, illegal_history):
        neighbors = self.graph.get_neighbors(current)

        primary = [
            n for n in neighbors
            if n not in visited_set and (current, n) not in illegal_history
        ]


        fallback = [n for n in neighbors if n not in visited_set]

        candidates = primary or fallback or neighbors

        return candidates


    def score_state(self, position):

        if position == 'P':
            return 10_000
        return -self.distance_to_goal(position)


    def evaluate_best_score(self, current, depth, visited_set, illegal_history):

        if depth == 0 or current == 'P':
            return self.score_state(current)

        candidates = self.build_candidates(current, visited_set, illegal_history)
        if not candidates:
            return self.score_state(current)

        best = -10**9

        # DIVIDE: each candidate leads to a subproblem
        for nxt in candidates:

            if nxt in visited_set:
                continue

            # CONQUER: solve subproblem recursively
            new_visited = set(visited_set)
            new_visited.add(nxt)

            sub_score = self.evaluate_best_score(
                nxt,
                depth - 1,
                new_visited,
                illegal_history
            )

            # COMBINE: take the maximum score
            if sub_score > best:
                best = sub_score

        # If everything was blocked
        if best == -10**9:
            return self.score_state(current)

        return best


    def get_best_move(self):
        current = self.game_state.current_position
        illegal_history = self.game_state.cpu_illegal_history


        visited_set = {lbl for lbl, node in self.graph.nodes.items() if node.visited}

        candidates = self.build_candidates(current, visited_set, illegal_history)
        if not candidates:
         
            return random.choice(list(self.graph.nodes.keys()))

        best_move = candidates[0]
        best_score = -10**9

        # DIVIDE: treat each candidate as a separate subproblem
        for move in candidates:
            if move in visited_set:
                continue

            new_visited = set(visited_set)
            new_visited.add(move)

            # CONQUER: evaluate outcome from this move
            sc = self.evaluate_best_score(
                move,
                self.depth - 1,
                new_visited,
                illegal_history
            )

            # COMBINE: choose move with best score
            if sc > best_score:
                best_score = sc
                best_move = move

        return best_move


# ====================
# GUI WITH RETRO GLITCH THEME
# ====================

class PuzzleGameGUI:
    
    COLORS = {
        'bg_dark': '#0a0520',
        'bg_panel': '#150a3d',
        'cyan': '#00ffff',
        'magenta': '#ff00ff',
        'yellow': '#ffff00',
        'green': '#00ff41',
        'red': '#ff0055',
        'orange': '#ff8800',
        'purple': '#b721ff',
        'blue': '#00d9ff',
        'text': '#ffffff',
        'grid_cell': '#2d1b69',
        'grid_visited': '#1a6b3a',
        'grid_current': '#ff00ff',
        'border_glow': '#00ff41',
        'cpu_highlight': '#ff00ff',
        'human_highlight': '#00ffff'
    }

    def __init__(self, root):
        self.root = root
        self.root.title("█▓▒░ SIGNPOST.EXE ░▒▓█")
        self.root.configure(bg=self.COLORS['bg_dark'])

        self.graph = self.create_fixed_puzzle()
        self.game_state = GameState(self.graph)
        self.cpu_player = dncCPU(self.graph, self.game_state, depth=6)

        self.buttons = {}
        self.glitch_chars = ['█', '▓', '▒', '░', '▀', '▄', '▌', '▐', '■', '□', '▪', '▫', '◘', '◙']
        self.glitch_colors = [self.COLORS['cyan'], self.COLORS['magenta'], self.COLORS['yellow'], 
                             self.COLORS['green'], self.COLORS['purple'], self.COLORS['orange']]
        
        # Timer variables
        self.timer_seconds = 0
        self.timer_max = 15
        self.timer_id = None
        
        self.create_gui()
        self.update_display()
        self.animate_glitch()
        self.animate_borders()
        self.start_timer()

    def create_fixed_puzzle(self):
        graph = PuzzleGraph()
        grid = [
            ('A',0,0,'↘'),('B',0,1,'↘'),('C',0,2,'↙'),('D',0,3,'←'),
            ('E',1,0,'↗'),('F',1,1,'→'),('G',1,2,'←'),('H',1,3,'←'),
            ('I',2,0,'→'),('J',2,1,'↙'),('K',2,2,'↖'),('L',2,3,'↑'),
            ('M',3,0,'→'),('N',3,1,'→'),('O',3,2,'→'),('P',3,3,'★')
        ]
        for l,r,c,a in grid:
            graph.add_node(l,r,c,a)

        edges = [
            ('A','E'),('A','K'),('K','G'),('K','F'),('F','G'),('F','H'),
            ('H','G'),('G','F'),('G','E'),('E','B'),('E','A'),('B','F'),
            ('B','L'),('L','H'),('L','D'),('D','C'),('C','G'),('C','I'),
            ('I','J'),('J','N'),('J','M'),('M','N'),('N','O'),('O','P')
        ]
        for u,v in edges:
            graph.add_edge(u,v)

        graph.set_solution_path(
            ['A','K','F','H','G','E','B','L','D','C','I','J','M','N','O','P']
        )
        return graph

    def create_gui(self):

        container = tk.Frame(self.root, bg=self.COLORS['bg_dark'])
        container.pack(fill='both', expand=True, padx=25, pady=20)

        title_frame = tk.Frame(container, bg=self.COLORS['bg_dark'])
        title_frame.pack(pady=(0, 20))
        
        tk.Label(
            title_frame,
            text="░▒▓█ SIGNPOST.EXE █▓▒░",
            font=('Courier New', 32, 'bold'),
            fg=self.COLORS['cyan'],
            bg=self.COLORS['bg_dark']
        ).pack()
        
        self.subtitle_label = tk.Label(
            title_frame,
            text="< NEURAL_PATH_SOLVER v2.1 >",
            font=('Courier New', 14),
            fg=self.COLORS['magenta'],
            bg=self.COLORS['bg_dark']
        )
        self.subtitle_label.pack()


        main_frame = tk.Frame(container, bg=self.COLORS['bg_dark'])
        main_frame.pack(fill='both', expand=True)

        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)  
        main_frame.grid_columnconfigure(1, weight=0, minsize=3) 
        main_frame.grid_columnconfigure(2, weight=1) 

        left_container = tk.Frame(main_frame, bg=self.COLORS['bg_dark'])
        left_container.grid(row=0, column=0, sticky='nsew', padx=(0, 15))
        
        left_container.grid_rowconfigure(0, weight=1)
        left_container.grid_columnconfigure(0, weight=1)
        
        self.grid_outer = tk.Frame(
            left_container,
            bg=self.COLORS['border_glow'],
            padx=4,
            pady=4
        )
        self.grid_outer.grid(row=0, column=0)
        
        grid_frame = tk.Frame(
            self.grid_outer,
            bg=self.COLORS['bg_panel'],
            padx=25,
            pady=25
        )
        grid_frame.pack()

        tk.Label(
            grid_frame,
            text="[ GRID MATRIX ]",
            font=('Courier New', 16, 'bold'),
            fg=self.COLORS['yellow'],
            bg=self.COLORS['bg_panel']
        ).grid(row=0, column=0, columnspan=4, pady=(0, 15))

        for label, node in self.graph.nodes.items():
            btn = tk.Button(
                grid_frame,
                text=f"{label}\n{node.arrow_direction}",
                width=5,
                height=2,
                font=('Courier New', 20, 'bold'),
                bg=self.COLORS['grid_cell'],
                fg=self.COLORS['cyan'],
                activebackground=self.COLORS['yellow'],
                activeforeground=self.COLORS['bg_dark'],
                relief='flat',
                bd=0,
                highlightthickness=4,
                highlightbackground=self.COLORS['purple'],
                highlightcolor=self.COLORS['cyan'],
                command=lambda l=label: self.on_cell_click(l)
            )
            btn.grid(row=node.row + 1, column=node.col, padx=5, pady=5)
            self.buttons[label] = btn

        separator = tk.Frame(
            main_frame,
            bg=self.COLORS['border_glow'],
            width=3
        )
        separator.grid(row=0, column=1, sticky='ns')

  
        right_container = tk.Frame(main_frame, bg=self.COLORS['bg_dark'])
        right_container.grid(row=0, column=2, sticky='nsew', padx=(15, 0))

        right_container.grid_rowconfigure(0, weight=2) 
        right_container.grid_rowconfigure(1, weight=0) 
        right_container.grid_rowconfigure(2, weight=0) 
        right_container.grid_columnconfigure(0, weight=1)

        # ----- Move History -----
        history_outer = tk.Frame(
            right_container,
            bg=self.COLORS['cyan'],
            padx=3,
            pady=3
        )
        history_outer.grid(row=0, column=0, sticky='nsew', pady=(0, 15))
        
        history_frame = tk.Frame(
            history_outer,
            bg=self.COLORS['bg_panel'],
            padx=15,
            pady=15
        )
        history_frame.pack(fill="both", expand=True)

        tk.Label(
            history_frame,
            text=">> TERMINAL_LOG.TXT",
            font=('Courier New', 13, 'bold'),
            fg=self.COLORS['green'],
            bg=self.COLORS['bg_panel']
        ).pack(anchor='w', pady=(0, 8))

        self.history = tk.Text(
            history_frame,
            width=35,
            height=14,
            font=('Courier New', 10),
            bg=self.COLORS['bg_dark'],
            fg=self.COLORS['green'],
            insertbackground=self.COLORS['cyan'],
            relief='flat',
            bd=0,
            wrap='word'
        )
        self.history.pack(fill='both', expand=True)
        self.history.tag_config("legal", foreground=self.COLORS['green'])
        self.history.tag_config("illegal", foreground=self.COLORS['red'])
        self.history.tag_config("header", foreground=self.COLORS['cyan'])
        self.history.insert(tk.END, "═══════════════════════════════════\n", "header")
        self.history.insert(tk.END, "   MOVE HISTORY INITIALIZED\n", "header")
        self.history.insert(tk.END, "═══════════════════════════════════\n\n", "header")
        self.history.config(state="disabled")

        # ----- System Status -----
        info_outer = tk.Frame(
            right_container,
            bg=self.COLORS['magenta'],
            padx=3,
            pady=3
        )
        info_outer.grid(row=1, column=0, sticky='ew', pady=(0, 15))
        
        info_frame = tk.Frame(
            info_outer,
            bg=self.COLORS['bg_panel'],
            padx=15,
            pady=12
        )
        info_frame.pack(fill="x")

        tk.Label(
            info_frame,
            text="[ SYSTEM STATUS ]",
            font=('Courier New', 13, 'bold'),
            fg=self.COLORS['yellow'],
            bg=self.COLORS['bg_panel']
        ).pack(pady=(0, 5))

        self.turn_label = tk.Label(
            info_frame,
            font=('Courier New', 14, 'bold'),
            fg=self.COLORS['cyan'],
            bg=self.COLORS['bg_panel']
        )
        self.turn_label.pack(pady=3)

        self.timer_label = tk.Label(
            info_frame,
            font=('Courier New', 13, 'bold'),
            fg=self.COLORS['yellow'],
            bg=self.COLORS['bg_panel']
        )
        self.timer_label.pack(pady=3)

        self.position_label = tk.Label(
            info_frame,
            font=('Courier New', 11),
            fg=self.COLORS['text'],
            bg=self.COLORS['bg_panel']
        )
        self.position_label.pack(pady=3)

        # ----- Scoreboard -----
        stats_outer = tk.Frame(
            right_container,
            bg=self.COLORS['orange'],
            padx=3,
            pady=3
        )
        stats_outer.grid(row=2, column=0, sticky='ew')
        
        stats_frame = tk.Frame(
            stats_outer,
            bg=self.COLORS['bg_panel'],
            padx=15,
            pady=12
        )
        stats_frame.pack(fill="x")

        tk.Label(
            stats_frame,
            text="[ SCOREBOARD ]",
            font=('Courier New', 13, 'bold'),
            fg=self.COLORS['yellow'],
            bg=self.COLORS['bg_panel']
        ).pack(pady=(0, 5))

        self.human_stats = tk.Label(
            stats_frame,
            justify="left",
            font=('Courier New', 11),
            fg=self.COLORS['cyan'],
            bg=self.COLORS['bg_panel']
        )
        self.human_stats.pack(anchor="w", pady=3)

        tk.Label(
            stats_frame,
            text="───────────────────────────────",
            font=('Courier New', 10),
            fg=self.COLORS['purple'],
            bg=self.COLORS['bg_panel']
        ).pack(pady=3)

        self.cpu_stats = tk.Label(
            stats_frame,
            justify="left",
            font=('Courier New', 11),
            fg=self.COLORS['magenta'],
            bg=self.COLORS['bg_panel']
        )
        self.cpu_stats.pack(anchor="w", pady=3)

    def animate_glitch(self):
        """Subtle glitch animation on subtitle"""
        glitch_text = random.choice([
            "< NEURAL_PATH_SOLVER v2.1 >",
            "< N3UR4L_P4TH_S0LV3R v2.1 >",
            "< █EURAL_PATH_SOLVER v2.1 >",
            "< NEURAL_PATH_S░LVER v2.1 >",
            "< NEURAL▓PATH_SOLVER v2.1 >",
            "< NEU░AL_PATH_SOLVER v2.1 >"
        ])
        self.subtitle_label.config(text=glitch_text)
        self.root.after(1500, self.animate_glitch)

    def animate_borders(self):
        """Random glitch effect on grid borders"""
        if hasattr(self, 'grid_outer'):
            color = random.choice(self.glitch_colors)
            self.grid_outer.config(bg=color)
        self.root.after(3000, self.animate_borders)

    def start_timer(self):
        """Start the turn timer"""
        self.timer_seconds = 0
        self.update_timer()

    def update_timer(self):
        """Update timer every second"""
        if self.game_state.game_over:
            return
        
        if self.game_state.current_turn == 'Human':
            self.timer_seconds += 1
            
            # Update timer display
            remaining = self.timer_max - self.timer_seconds
            if remaining <= 5:
                
                self.timer_label.config(
                    text=f"⏱ TIME: {remaining}s",
                    fg=self.COLORS['red']
                )
            else:
                self.timer_label.config(
                    text=f"⏱ TIME: {remaining}s",
                    fg=self.COLORS['yellow']
                )
            
   
            if self.timer_seconds >= self.timer_max:
                self.on_timeout()
                return
        else:
            
            self.timer_label.config(text="⏱ CPU THINKING...")
        
        self.timer_id = self.root.after(1000, self.update_timer)

    def reset_timer(self):
        """Reset timer for new turn"""
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
        self.timer_seconds = 0
        self.start_timer()

    def on_timeout(self):
        """Handle timeout - force turn switch"""
        self.log(f"HUMAN → TIMEOUT! [ERROR]", "illegal")
        self.game_state.human_illegal_moves += 1
        self.game_state.switch_turn()
        self.reset_timer()
        self.update_display()
        self.root.after(800, self.cpu_turn)

    def log(self, text, tag):
        self.history.config(state="normal")
        prefix = ">> " if tag == "legal" else "!! "
        self.history.insert(tk.END, prefix + text + "\n", tag)
        self.history.config(state="disabled")
        self.history.see(tk.END)

    def flash_illegal(self, label):
        """Enhanced glitch effect for illegal moves"""
        btn = self.buttons[label]
        original_text = btn.cget("text")
        
       
        def glitch_frame(count):
            if count > 0:
                glitch = random.choice(self.glitch_chars)
                btn.config(
                    bg=self.COLORS['red'],
                    text=f"{glitch}\n{glitch}",
                    fg=self.COLORS['yellow'],
                    font=('Courier New', 24, 'bold'),
                    highlightthickness=7,
                    highlightbackground=self.COLORS['red']
                )
                self.root.after(120, lambda: glitch_frame(count - 1))
            else:
                self.update_display()
        
        glitch_frame(5)

    def flash_cpu_move(self, label):
        """Ultra bright pulsing animation for CPU moves"""
        btn = self.buttons[label]
        
        def pulse_frame(count, bright):
            if count > 0:
                if bright:
                    btn.config(
                        bg=self.COLORS['cpu_highlight'],
                        fg=self.COLORS['yellow'],
                        highlightbackground=self.COLORS['yellow'],
                        highlightthickness=7,
                        font=('Courier New', 24, 'bold')
                    )
                else:
                    btn.config(
                        bg=self.COLORS['purple'],
                        fg=self.COLORS['text'],
                        highlightbackground=self.COLORS['purple'],
                        highlightthickness=7,
                        font=('Courier New', 24, 'bold')
                    )
                self.root.after(200, lambda: pulse_frame(count - 1, not bright))
            else:
                self.update_display()
        
        pulse_frame(8, True) 

    def on_cell_click(self, label):
        if self.game_state.current_turn != 'Human' or self.game_state.game_over:
            return

        success,_ = self.game_state.make_move(label)

        if success:
            self.log(f"HUMAN → {label} [OK]", "legal")
        else:
            self.log(f"HUMAN → {label} [ERROR]", "illegal")
            self.flash_illegal(label)

        self.reset_timer()
        self.update_display()

        if self.game_state.game_over:
            self.show_winner()
        else:
            self.root.after(800, self.cpu_turn)

    def cpu_turn(self):
        if self.game_state.game_over:
            return

        move = self.cpu_player.get_best_move()
        success,_ = self.game_state.make_move(move)

        if success:
            self.log(f"CPU → {move} [OK]", "legal")
            self.flash_cpu_move(move)
        else:
            self.log(f"CPU → {move} [ERROR]", "illegal")
            self.flash_illegal(move)

        self.reset_timer()

        if self.game_state.game_over:
            self.root.after(1000, self.show_winner)

    def update_display(self):
        for label, node in self.graph.nodes.items():
            btn = self.buttons[label]
            if node.visited:
                btn.config(
                    text=f"[{node.visit_order}]\n{node.arrow_direction}",
                    bg=self.COLORS['grid_visited'],
                    fg=self.COLORS['green'],
                    highlightbackground=self.COLORS['green'],
                    highlightthickness=3,
                    font=('Courier New', 20, 'bold')
                )
            else:
                btn.config(
                    text=f"{label}\n{node.arrow_direction}",
                    bg=self.COLORS['grid_cell'],
                    fg=self.COLORS['cyan'],
                    highlightbackground=self.COLORS['purple'],
                    highlightthickness=4,
                    font=('Courier New', 20, 'bold')
                )
            
            if label == self.game_state.current_position:
                btn.config(
                    bg=self.COLORS['grid_current'],
                    fg=self.COLORS['yellow'],
                    highlightbackground=self.COLORS['yellow'],
                    highlightthickness=6,
                    font=('Courier New', 20, 'bold')
                )

        turn_color = self.COLORS['cyan'] if self.game_state.current_turn == 'Human' else self.COLORS['magenta']
        self.turn_label.config(
            text=f">> TURN: {self.game_state.current_turn.upper()}",
            fg=turn_color
        )
        
        self.human_stats.config(
            text=f"█ HUMAN\n  Valid: {self.game_state.human_correct_moves}\n  Error: {self.game_state.human_illegal_moves}"
        )
        
        self.cpu_stats.config(
            text=f"█ CPU\n  Valid: {self.game_state.cpu_correct_moves}\n  Error: {self.game_state.cpu_illegal_moves}"
        )

        order = self.graph.nodes[self.game_state.current_position].visit_order
        self.position_label.config(
            text=f"Position: [{self.game_state.current_position}] | Node: {order}"
        )

    def show_winner(self):
 
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
        
        winner_text = f"""
╔═══════════════════════════╗
║   GAME TERMINATED         ║
║                           ║
║   WINNER: {self.game_state.winner.upper():^15} ║
║                           ║
║   Human Errors: {self.game_state.human_illegal_moves:^6}    ║
║   CPU Errors:   {self.game_state.cpu_illegal_moves:^6}    ║
╚═══════════════════════════╝
        """
        messagebox.showinfo("█▓▒░ GAME OVER ░▒▓█", winner_text)


# ====================
# MAIN
# ====================

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1200x750")
    root.minsize(1100, 700)
    PuzzleGameGUI(root)

    root.mainloop()
