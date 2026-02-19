import tkinter as tk
from tkinter import messagebox
import random
from collections import deque

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
# CPU PLAYER (Top-Down Dynamic Programming with Memoization)
# ====================

class dncCPU:
    def __init__(self, graph, game_state, depth=6):
        self.graph = graph
        self.game_state = game_state
        self.depth = depth
        self.memo = {} 


    def bfs_distance_to_goal(self, start_label, visited_set):
        if start_label == 'P':
            return 0

        queue = deque([(start_label, 0)])
        seen = set([start_label])

        while queue:
            current, dist = queue.popleft()

            for neighbor in self.graph.get_neighbors(current):
                if neighbor in visited_set:
                    continue
                if neighbor == 'P':
                    return dist + 1
                if neighbor not in seen:
                    seen.add(neighbor)
                    queue.append((neighbor, dist + 1))

        return float('inf')  # unreachable
        


    def build_candidates(self, current, visited_set, illegal_history):
        neighbors = self.graph.get_neighbors(current)
        primary = [
            n for n in neighbors
            if n not in visited_set and (current, n) not in illegal_history
        ]
        fallback = [n for n in neighbors if n not in visited_set]
        candidates = primary or fallback or neighbors
        return candidates
        

    def score_state(self, position,visited_set):
        if position == 'P':
            return 10_000
        dist = self.bfs_distance_to_goal(position, visited_set)
        if dist == float('inf'):
            return -10_000
        return -dist
        

#TOP-DOWN DP 
    def evaluate_best_score(self, current, depth, visited_set, illegal_history):
        # ── Dynamic Programming: check memo cache before recomputing ──
        state_key = (current, depth, frozenset(visited_set))

        if state_key in self.memo:
            return self.memo[state_key]          # cache hit — skip recursion

        # Base case
        if depth == 0 or current == 'P':
            score = self.score_state(current,visited_set)
            self.memo[state_key] = score         # store in DP table
            return score

        candidates = self.build_candidates(current, visited_set, illegal_history)
        if not candidates:
            score = self.score_state(current,visited_set)
            self.memo[state_key] = score         # store in DP table
            return score

        best = -10**9

        for nxt in candidates:
            if nxt in visited_set:
                continue

            new_visited = set(visited_set)
            new_visited.add(nxt)

            sub_score = self.evaluate_best_score(
                nxt, depth - 1, new_visited, illegal_history
            )

            best = max(best, sub_score)

        if best == -10**9:
            best = self.score_state(current,visited_set)

        self.memo[state_key] = best              # store result in DP table
        return best

    def get_best_move(self):
        self.memo.clear()    # reset DP cache each turn — game state changes

        current = self.game_state.current_position
        illegal_history = self.game_state.cpu_illegal_history
        visited_set = {lbl for lbl, node in self.graph.nodes.items() if node.visited}

        candidates = self.build_candidates(current, visited_set, illegal_history)
        if not candidates:
            return random.choice(list(self.graph.nodes.keys()))

        best_move = candidates[0]
        best_score = -10**9

        for move in candidates:
            if move in visited_set:
                continue
            new_visited = set(visited_set)
            new_visited.add(move)
            sc = self.evaluate_best_score(move, self.depth - 1, new_visited, illegal_history)
            if sc > best_score:
                best_score = sc
                best_move = move

        return best_move


# ====================
# GUI
# ====================

class PuzzleGameGUI:
    C = {
        # backgrounds
        'bg':           '#1C1F26',  
        'surface':      '#252930',   
        'card':         '#2E3340',   
        'card_hover':   '#383E4E',

        # text
        'text_primary': '#EAEDF3',   
        'text_secondary':'#8A90A0',  
        'text_dim':     '#545B6E',   

        # accents
        'accent_blue':  '#5B9CF6', 
        'accent_green': '#4CAF82',   
        'accent_amber': '#E8A838',   
        'accent_red':   '#E05C5C',   

        # borders / dividers
        'border':       '#343A4A',
        'border_light': '#454D60',
        'divider':      '#2C3040',
    }

    def __init__(self, root):
        self.root = root
        self.root.title("Signpost — Path Solver")
        self.root.configure(bg=self.C['bg'])

        self.graph = self.create_fixed_puzzle()
        self.game_state = GameState(self.graph)
        self.cpu_player = dncCPU(self.graph, self.game_state, depth=6)

        self.buttons = {}

        # Timer
        self.timer_seconds = 0
        self.timer_max = 15
        self.timer_id = None

        self.create_gui()
        self.update_display()
        self.start_timer()

    # ────────────────────────────────────────────────
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

    # ────────────────────────────────────────────────
    def _make_frame(self, parent, bg=None, padx=0, pady=0):
        return tk.Frame(parent, bg=bg or self.C['surface'], padx=padx, pady=pady)

    def _label(self, parent, text, font, fg=None, bg=None, anchor='center', **kw):
        return tk.Label(
            parent, text=text, font=font,
            fg=fg or self.C['text_primary'],
            bg=bg or self.C['surface'],
            anchor=anchor, **kw
        )

    # ────────────────────────────────────────────────
    def create_gui(self):
        root_pad = tk.Frame(self.root, bg=self.C['bg'])
        root_pad.pack(fill='both', expand=True, padx=28, pady=22)

        # ── Header ──────────────────────────────────
        header = tk.Frame(root_pad, bg=self.C['bg'])
        header.pack(fill='x', pady=(0, 20))

        tk.Label(
            header, text="SIGNPOST",
            font=('Georgia', 30, 'bold'),
            fg=self.C['text_primary'], bg=self.C['bg']
        ).pack(side='left')

        tk.Label(
            header, text="  Path Solver  v2.2",
            font=('Georgia', 14, 'italic'),
            fg=self.C['text_secondary'], bg=self.C['bg']
        ).pack(side='left', pady=(12, 0))

        # thin horizontal rule
        tk.Frame(root_pad, bg=self.C['border'], height=1).pack(fill='x', pady=(0, 18))

        # ── Body: left grid | right panels ──────────
        body = tk.Frame(root_pad, bg=self.C['bg'])
        body.pack(fill='both', expand=True)

        body.grid_columnconfigure(0, weight=5, minsize=520)
        body.grid_columnconfigure(1, weight=0)          # spacer
        body.grid_columnconfigure(2, weight=4, minsize=360)
        body.grid_rowconfigure(0, weight=1)

        # ── LEFT: Grid ──────────────────────────────
        left = tk.Frame(body, bg=self.C['bg'])
        left.grid(row=0, column=0, sticky='nsew')
        left.grid_rowconfigure(0, weight=1)
        left.grid_columnconfigure(0, weight=1)

        grid_card = tk.Frame(
            left,
            bg=self.C['surface'],
            highlightbackground=self.C['border'],
            highlightthickness=1
        )
        grid_card.grid(row=0, column=0)

        self._label(
            grid_card, "GRID MATRIX",
            font=('Helvetica', 11, 'bold'),
            fg=self.C['text_secondary'],
            bg=self.C['surface']
        ).grid(row=0, column=0, columnspan=4, pady=(18, 12), padx=22)

        # ── Grid cells ──────────────────────────────
        for label, node in self.graph.nodes.items():
            cell = tk.Frame(
                grid_card,
                bg=self.C['card'],
                highlightbackground=self.C['border_light'],
                highlightthickness=1,
                width=96, height=80
            )
            cell.grid(row=node.row + 1, column=node.col, padx=6, pady=6)
            cell.grid_propagate(False)
            cell.grid_rowconfigure(0, weight=1)
            cell.grid_rowconfigure(1, weight=1)
            cell.grid_columnconfigure(0, weight=1)

            lbl_letter = tk.Label(
                cell, text=label,
                font=('Helvetica', 18, 'bold'),
                fg=self.C['text_primary'], bg=self.C['card'],
                anchor='center', cursor='hand2'
            )
            lbl_letter.grid(row=0, column=0, sticky='sew', pady=(10, 2))

            lbl_arrow = tk.Label(
                cell, text=node.arrow_direction,
                font=('Helvetica', 16),
                fg=self.C['text_secondary'], bg=self.C['card'],
                anchor='center', cursor='hand2'
            )
            lbl_arrow.grid(row=1, column=0, sticky='new', pady=(2, 8))

            # bind clicks on all parts of the cell
            for widget in (cell, lbl_letter, lbl_arrow):
                widget.bind('<Button-1>', lambda e, l=label: self.on_cell_click(l))

            # store widgets for later styling
            self.buttons[label] = {
                'frame': cell,
                'letter': lbl_letter,
                'arrow': lbl_arrow,
            }

        # padding row at bottom
        tk.Frame(grid_card, bg=self.C['surface'], height=14).grid(
            row=6, column=0, columnspan=4)

        # ── Vertical divider ────────────────────────
        tk.Frame(body, bg=self.C['border'], width=1).grid(
            row=0, column=1, sticky='ns', padx=20)

        # ── RIGHT: Panels ───────────────────────────
        right = tk.Frame(body, bg=self.C['bg'])
        right.grid(row=0, column=2, sticky='nsew')
        right.grid_rowconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=0)
        right.grid_rowconfigure(2, weight=0)
        right.grid_columnconfigure(0, weight=1)

        # ── Panel 1: Move History ────────────────────
        hist_card = tk.Frame(
            right, bg=self.C['surface'],
            highlightbackground=self.C['border'],
            highlightthickness=1
        )
        hist_card.grid(row=0, column=0, sticky='nsew', pady=(0, 12))

        self._label(
            hist_card, "MOVE HISTORY",
            font=('Helvetica', 11, 'bold'),
            fg=self.C['text_secondary'],
            bg=self.C['surface']
        ).pack(anchor='w', padx=18, pady=(14, 8))

        tk.Frame(hist_card, bg=self.C['divider'], height=1).pack(fill='x', padx=18)

        self.history = tk.Text(
            hist_card,
            width=34, height=13,
            font=('Courier New', 10),
            bg=self.C['surface'],
            fg=self.C['text_primary'],
            relief='flat', bd=0,
            wrap='word',
            padx=18, pady=10,
            cursor='arrow',
            selectbackground=self.C['card']
        )
        self.history.pack(fill='both', expand=True)

        # tag styles
        self.history.tag_config("move_ok",  foreground=self.C['accent_green'])
        self.history.tag_config("move_err", foreground=self.C['accent_red'])
        self.history.tag_config("meta",     foreground=self.C['text_dim'])
        self.history.tag_config("header",   foreground=self.C['text_secondary'])

        self.history.config(state='disabled')
        self._hist("Game started — make your move.", "meta")

        # ── Panel 2: Status ──────────────────────────
        status_card = tk.Frame(
            right, bg=self.C['surface'],
            highlightbackground=self.C['border'],
            highlightthickness=1
        )
        status_card.grid(row=1, column=0, sticky='ew', pady=(0, 12))

        self._label(
            status_card, "SYSTEM STATUS",
            font=('Helvetica', 11, 'bold'),
            fg=self.C['text_secondary'],
            bg=self.C['surface']
        ).pack(anchor='w', padx=18, pady=(14, 6))

        tk.Frame(status_card, bg=self.C['divider'], height=1).pack(fill='x', padx=18)

        inner_status = tk.Frame(status_card, bg=self.C['surface'])
        inner_status.pack(fill='x', padx=18, pady=12)

        # Turn row
        turn_row = tk.Frame(inner_status, bg=self.C['surface'])
        turn_row.pack(fill='x', pady=3)
        self._label(turn_row, "Turn", font=('Helvetica', 10), fg=self.C['text_dim'], bg=self.C['surface'], anchor='w').pack(side='left')
        self.turn_label = tk.Label(turn_row, text="—", font=('Helvetica', 11, 'bold'), fg=self.C['accent_blue'], bg=self.C['surface'], anchor='e')
        self.turn_label.pack(side='right')

        # Timer row
        timer_row = tk.Frame(inner_status, bg=self.C['surface'])
        timer_row.pack(fill='x', pady=3)
        self._label(timer_row, "Time left", font=('Helvetica', 10), fg=self.C['text_dim'], bg=self.C['surface'], anchor='w').pack(side='left')
        self.timer_label = tk.Label(timer_row, text="—", font=('Helvetica', 11, 'bold'), fg=self.C['text_primary'], bg=self.C['surface'], anchor='e')
        self.timer_label.pack(side='right')

        # Position row
        pos_row = tk.Frame(inner_status, bg=self.C['surface'])
        pos_row.pack(fill='x', pady=3)
        self._label(pos_row, "Position", font=('Helvetica', 10), fg=self.C['text_dim'], bg=self.C['surface'], anchor='w').pack(side='left')
        self.position_label = tk.Label(pos_row, text="—", font=('Helvetica', 11, 'bold'), fg=self.C['text_primary'], bg=self.C['surface'], anchor='e')
        self.position_label.pack(side='right')

        # DP Cache row
        dp_row = tk.Frame(inner_status, bg=self.C['surface'])
        dp_row.pack(fill='x', pady=3)
        self._label(dp_row, "DP Cache", font=('Helvetica', 10), fg=self.C['text_dim'], bg=self.C['surface'], anchor='w').pack(side='left')
        self.dp_cache_label = tk.Label(dp_row, text="0 states", font=('Helvetica', 11, 'bold'), fg=self.C['accent_amber'], bg=self.C['surface'], anchor='e')
        self.dp_cache_label.pack(side='right')

        tk.Frame(status_card, bg=self.C['surface'], height=6).pack()

        # ── Panel 3: Scoreboard ──────────────────────
        score_card = tk.Frame(
            right, bg=self.C['surface'],
            highlightbackground=self.C['border'],
            highlightthickness=1
        )
        score_card.grid(row=2, column=0, sticky='ew')

        self._label(
            score_card, "SCOREBOARD",
            font=('Helvetica', 11, 'bold'),
            fg=self.C['text_secondary'],
            bg=self.C['surface']
        ).pack(anchor='w', padx=18, pady=(14, 6))

        tk.Frame(score_card, bg=self.C['divider'], height=1).pack(fill='x', padx=18)

        score_inner = tk.Frame(score_card, bg=self.C['surface'])
        score_inner.pack(fill='x', padx=18, pady=12)

        # Header row
        hdr = tk.Frame(score_inner, bg=self.C['surface'])
        hdr.pack(fill='x', pady=(0, 6))
        tk.Label(hdr, text="Player",  width=10, anchor='w',      font=('Helvetica', 10, 'bold'), fg=self.C['text_dim'], bg=self.C['surface']).pack(side='left')
        tk.Label(hdr, text="Correct", width=8,  anchor='center', font=('Helvetica', 10, 'bold'), fg=self.C['text_dim'], bg=self.C['surface']).pack(side='left')
        tk.Label(hdr, text="Errors",  width=8,  anchor='center', font=('Helvetica', 10, 'bold'), fg=self.C['text_dim'], bg=self.C['surface']).pack(side='left')

        tk.Frame(score_inner, bg=self.C['border'], height=1).pack(fill='x', pady=4)

        # Human row
        human_row = tk.Frame(score_inner, bg=self.C['surface'])
        human_row.pack(fill='x', pady=4)
        tk.Label(human_row, text="Human", width=10, anchor='w', font=('Helvetica', 11), fg=self.C['accent_blue'], bg=self.C['surface']).pack(side='left')
        self.human_correct_lbl = tk.Label(human_row, text="0", width=8, anchor='center', font=('Helvetica', 11, 'bold'), fg=self.C['accent_green'], bg=self.C['surface'])
        self.human_correct_lbl.pack(side='left')
        self.human_errors_lbl  = tk.Label(human_row, text="0", width=8, anchor='center', font=('Helvetica', 11, 'bold'), fg=self.C['accent_red'], bg=self.C['surface'])
        self.human_errors_lbl.pack(side='left')

        # CPU row
        cpu_row = tk.Frame(score_inner, bg=self.C['surface'])
        cpu_row.pack(fill='x', pady=4)
        tk.Label(cpu_row, text="CPU", width=10, anchor='w', font=('Helvetica', 11), fg=self.C['text_secondary'], bg=self.C['surface']).pack(side='left')
        self.cpu_correct_lbl = tk.Label(cpu_row, text="0", width=8, anchor='center', font=('Helvetica', 11, 'bold'), fg=self.C['accent_green'], bg=self.C['surface'])
        self.cpu_correct_lbl.pack(side='left')
        self.cpu_errors_lbl  = tk.Label(cpu_row, text="0", width=8, anchor='center', font=('Helvetica', 11, 'bold'), fg=self.C['accent_red'], bg=self.C['surface'])
        self.cpu_errors_lbl.pack(side='left')

        tk.Frame(score_card, bg=self.C['surface'], height=8).pack()


    # ────────────────────────────────────────────────
    # Helpers
    # ────────────────────────────────────────────────

    def _hist(self, text, tag="move_ok"):
        self.history.config(state='normal')
        self.history.insert(tk.END, text + "\n", tag)
        self.history.config(state='disabled')
        self.history.see(tk.END)

    def _cell_style(self, label, bg, fg_letter, fg_arrow, border_color, border_w=1):
        w = self.buttons[label]
        w['frame'].config(bg=bg, highlightbackground=border_color, highlightthickness=border_w)
        w['letter'].config(bg=bg, fg=fg_letter)
        w['arrow'].config(bg=bg, fg=fg_arrow)

    # ────────────────────────────────────────────────
    # Timer
    # ────────────────────────────────────────────────

    def start_timer(self):
        self.timer_seconds = 0
        self.update_timer()

    def update_timer(self):
        if self.game_state.game_over:
            return

        if self.game_state.current_turn == 'Human':
            self.timer_seconds += 1
            remaining = self.timer_max - self.timer_seconds
            color = self.C['accent_red'] if remaining <= 5 else self.C['text_primary']
            self.timer_label.config(text=f"{remaining}s", fg=color)

            if self.timer_seconds >= self.timer_max:
                self.on_timeout()
                return
        else:
            self.timer_label.config(text="CPU thinking…", fg=self.C['text_dim'])

        self.timer_id = self.root.after(1000, self.update_timer)

    def reset_timer(self):
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
        self.timer_seconds = 0
        self.start_timer()

    def on_timeout(self):
        self._hist("Human timed out", "move_err")
        self.game_state.human_illegal_moves += 1
        self.game_state.switch_turn()
        self.reset_timer()
        self.update_display()
        self.root.after(600, self.cpu_turn)

    def on_cell_click(self, label):
        if self.game_state.current_turn != 'Human' or self.game_state.game_over:
            return

        success, _ = self.game_state.make_move(label)

        if success:
            self._hist(f"Human  →  {label}", "move_ok")
        else:
            self._hist(f"Human  →  {label}  (invalid)", "move_err")
            self.flash_error(label)

        self.reset_timer()
        self.update_display()

        if self.game_state.game_over:
            self.show_winner()
        else:
            self.root.after(700, self.cpu_turn)

    def cpu_turn(self):
        if self.game_state.game_over:
            return

        move = self.cpu_player.get_best_move()
        success, _ = self.game_state.make_move(move)

        if success:
            self._hist(f"CPU    →  {move}  [DP:{len(self.cpu_player.memo)} states]", "move_ok")
            self.flash_cpu(move)
        else:
            self._hist(f"CPU    →  {move}  (invalid)", "move_err")
            self.flash_error(move)

        self.reset_timer()
        self.update_display()

        if self.game_state.game_over:
            self.root.after(900, self.show_winner)

    # ────────────────────────────────────────────────
    # Animations
    # ────────────────────────────────────────────────

    def flash_error(self, label):
        """Briefly tint red then restore."""
        ERR  = '#3D2020'
        ERR2 = '#4A2020'
        seq  = [ERR, ERR2, ERR, ERR2, self.C['card']]

        def step(i):
            if i < len(seq):
                w = self.buttons[label]
                w['frame'].config(bg=seq[i])
                w['letter'].config(bg=seq[i])
                w['arrow'].config(bg=seq[i])
                self.root.after(120, lambda: step(i + 1))
            else:
                self.update_display()
        step(0)

    def flash_cpu(self, label):
        """Subtle highlight pulse for CPU move."""
        PULSE = '#2B3A52'
        seq   = [PULSE, self.C['card'], PULSE, self.C['card']]

        def step(i):
            if i < len(seq):
                w = self.buttons[label]
                w['frame'].config(bg=seq[i])
                w['letter'].config(bg=seq[i])
                w['arrow'].config(bg=seq[i])
                self.root.after(200, lambda: step(i + 1))
            else:
                self.update_display()
        step(0)

    def update_display(self):
        for label, node in self.graph.nodes.items():
            w = self.buttons[label]
            is_current = (label == self.game_state.current_position)

            if is_current:
                bg       = '#1F3557'
                border   = self.C['accent_blue']
                border_w = 2
                fg_letter = self.C['accent_blue']
                fg_arrow  = self.C['accent_blue']
                w['letter'].config(text=f"[{node.visit_order}]", font=('Helvetica', 14, 'bold'))
            elif node.visited:
                bg       = '#1E3028'
                border   = self.C['accent_green']
                border_w = 1
                fg_letter = self.C['accent_green']
                fg_arrow  = self.C['accent_green']
                w['letter'].config(text=f"[{node.visit_order}]", font=('Helvetica', 14, 'bold'))
            else:
                bg       = self.C['card']
                border   = self.C['border_light']
                border_w = 1
                fg_letter = self.C['text_primary']
                fg_arrow  = self.C['text_secondary']
                w['letter'].config(text=label, font=('Helvetica', 18, 'bold'))

            w['frame'].config(bg=bg, highlightbackground=border, highlightthickness=border_w)
            w['letter'].config(bg=bg, fg=fg_letter)
            w['arrow'].config(bg=bg, fg=fg_arrow)

        # Turn label
        if self.game_state.current_turn == 'Human':
            self.turn_label.config(text="Human", fg=self.C['accent_blue'])
        else:
            self.turn_label.config(text="CPU", fg=self.C['text_secondary'])

        # Position
        node = self.graph.nodes[self.game_state.current_position]
        self.position_label.config(text=f"{self.game_state.current_position}  (step {node.visit_order})")

        # DP Cache size — live counter
        self.dp_cache_label.config(text=f"{len(self.cpu_player.memo)} states")

        # Scores
        gs = self.game_state
        self.human_correct_lbl.config(text=str(gs.human_correct_moves))
        self.human_errors_lbl.config(text=str(gs.human_illegal_moves))
        self.cpu_correct_lbl.config(text=str(gs.cpu_correct_moves))
        self.cpu_errors_lbl.config(text=str(gs.cpu_illegal_moves))

    # ────────────────────────────────────────────────
    # Game over
    # ────────────────────────────────────────────────

    def show_winner(self):
        if self.timer_id:
            self.root.after_cancel(self.timer_id)

        gs  = self.game_state
        msg = (
            f"Winner:  {gs.winner}\n\n"
            f"Human    Correct: {gs.human_correct_moves}   Errors: {gs.human_illegal_moves}\n"
            f"CPU      Correct: {gs.cpu_correct_moves}   Errors: {gs.cpu_illegal_moves}"
        )
        messagebox.showinfo("Game Over — Signpost", msg)


# ====================
# MAIN
# ====================

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1100x680")
    root.minsize(1000, 620)
    PuzzleGameGUI(root)
    root.mainloop()
