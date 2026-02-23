import tkinter as tk
from tkinter import messagebox
import random

# ====================
# GRAPH IMPLEMENTATION
# ====================

class GraphNode:
    def __init__(self, label, row, col, arrow_direction):
        self.label = label
        self.row = row
        self.col = col
        self.arrow_direction = arrow_direction
        self.visited = False
        self.visit_order = None


class PuzzleGraph:
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

        self.cpu_illegal_history = set()  # remembers (from, to) pairs the CPU already failed

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




class dncCPU:
    # ── Quadrant layout (rows 0-1 / cols 0-1 split) ──────────────────────
    # Q0: rows 0-1, cols 0-1  →  A B E F
    # Q1: rows 0-1, cols 2-3  →  C D G H
    # Q2: rows 2-3, cols 0-1  →  I J M N
    # Q3: rows 2-3, cols 2-3  →  K L O P
    QUADRANT_NODES = {
        0: frozenset({'A', 'B', 'E', 'F'}),
        1: frozenset({'C', 'D', 'G', 'H'}),
        2: frozenset({'I', 'J', 'M', 'N'}),
        3: frozenset({'K', 'L', 'O', 'P'}),
    }

    def __init__(self, graph, game_state, depth_limit=2):
        self.graph       = graph
        self.game_state  = game_state
        self.depth_limit = depth_limit


    def _quadrant_of(self, label):
        for qid, members in self.QUADRANT_NODES.items():
            if label in members:
                return qid
        return None

    def _solve_quadrant_visit(self, entry, q_remaining_fset):
   
        best = [entry]   

        for nxt in self.graph.get_neighbors(entry):
            if nxt not in q_remaining_fset:
                continue   
            sub = self._solve_quadrant_visit(nxt, frozenset(q_remaining_fset - {nxt}))
            if len(sub) + 1 > len(best):
                best = [entry] + sub

        return best

  
    def _combine_quadrant_visits(self, cur, all_unvisited_fset, depth, illegal_history):
      
        if not all_unvisited_fset:
            return [cur]

        for nxt in self.graph.get_neighbors(cur):
            if nxt not in all_unvisited_fset:
                continue
            if (cur, nxt) in illegal_history:
                continue                         

            nxt_q = self._quadrant_of(nxt)

            
            q_bucket = frozenset(all_unvisited_fset & self.QUADRANT_NODES[nxt_q])

       
            chain = self._solve_quadrant_visit(nxt, frozenset(q_bucket - {nxt}))

  
            remaining = frozenset(all_unvisited_fset - set(chain))

            if depth <= 0:
                return [cur] + chain

            rest = self._combine_quadrant_visits(
                chain[-1], remaining, depth - 1, illegal_history)

            if rest is not None:
                return [cur] + chain + rest[1:]

        return None

    def get_best_move(self):
        cur           = self.game_state.current_position
        visited_set   = {lbl for lbl, n in self.graph.nodes.items() if n.visited}
        all_unvisited = frozenset(self.graph.nodes.keys()) - visited_set
        illegal_hist  = self.game_state.cpu_illegal_history

        result = self._combine_quadrant_visits(
            cur, all_unvisited, self.depth_limit, illegal_hist)

        if result and len(result) >= 2:
            return result[1]
        result = self._combine_quadrant_visits(
            cur, all_unvisited, 999, set())

        if result and len(result) >= 2:
            return result[1]

        return self._fallback(cur, visited_set)

    def _fallback(self, cur, visited_set):
        """Random legal move, avoiding known failed pairs."""
        candidates = [
            n for n in self.graph.get_neighbors(cur)
            if n not in visited_set
            and (cur, n) not in self.game_state.cpu_illegal_history
        ]
        if candidates:
            return random.choice(candidates)
        candidates = [n for n in self.graph.get_neighbors(cur) if n not in visited_set]
        if candidates:
            return random.choice(candidates)
        return random.choice(list(self.graph.nodes.keys()))



class PuzzleGameGUI:
    C = {
        'bg':             '#1C1F26',
        'surface':        '#252930',
        'card':           '#2E3340',
        'card_hover':     '#383E4E',
        'text_primary':   '#EAEDF3',
        'text_secondary': '#8A90A0',
        'text_dim':       '#545B6E',
        'accent_blue':    '#5B9CF6',
        'accent_green':   '#4CAF82',
        'accent_amber':   '#E8A838',
        'accent_red':     '#E05C5C',
        'border':         '#343A4A',
        'border_light':   '#454D60',
        'divider':        '#2C3040',
    }

    def __init__(self, root):
        self.root = root
        self.root.title("Signpost - Puzzle")
        self.root.configure(bg=self.C['bg'])

        self.buttons = {}
        self.timer_seconds = 0
        self.timer_max = 15
        self.timer_id = None

        self._build_puzzle()
        self.create_gui()
        self.update_display()
        self.start_timer()


    def _build_puzzle(self):
        """(Re-)create graph, game state, and CPU player."""
        self.graph = self._create_fixed_puzzle()
        self.game_state = GameState(self.graph)
        self.cpu_player = dncCPU(self.graph, self.game_state, depth_limit=2)

    def _create_fixed_puzzle(self):
        graph = PuzzleGraph()
        grid = [
            ('A', 0, 0, '↘'), ('B', 0, 1, '↘'), ('C', 0, 2, '↙'), ('D', 0, 3, '←'),
            ('E', 1, 0, '↗'), ('F', 1, 1, '→'), ('G', 1, 2, '←'), ('H', 1, 3, '←'),
            ('I', 2, 0, '→'), ('J', 2, 1, '↙'), ('K', 2, 2, '↖'), ('L', 2, 3, '↑'),
            ('M', 3, 0, '→'), ('N', 3, 1, '→'), ('O', 3, 2, '→'), ('P', 3, 3, '★'),
        ]
        for l, r, c, a in grid:
            graph.add_node(l, r, c, a)

        edges = [
            ('A', 'K'),('A','F'),('K', 'F'),('A','P'),('F', 'G'), ('F', 'H'),('H','F'),('H','E'),
            ('H', 'G'), ('G', 'F'), ('G', 'E'), ('E', 'B'),('B','G'),
            ('B', 'L'), ('L', 'H'), ('L', 'D'), ('D', 'C'),('C','F'), ('C', 'I'),('I','J'),
            ('I','K'),('I','L'),('J', 'M'), ('M', 'N'),('M','O'),('M','P'),
            ('N', 'O'),('N','P'), ('O', 'P'),('K','G'),('K','N'),('E','A'),('B','F'),('C','G'),('J','N')
        ]

        for u, v in edges:
            graph.add_edge(u, v)

        graph.set_solution_path(
            ['A', 'K', 'F', 'H', 'G', 'E', 'B', 'L', 'D', 'C', 'I', 'J', 'M', 'N', 'O', 'P']
        )
        return graph

   

    def _label(self, parent, text, font, fg=None, bg=None, anchor='center', **kw):
        return tk.Label(
            parent, text=text, font=font,
            fg=fg or self.C['text_primary'],
            bg=bg or self.C['surface'],
            anchor=anchor, **kw
        )

    def create_gui(self):
    
        root_pad = tk.Frame(self.root, bg=self.C['bg'])
        root_pad.pack(fill='both', expand=True, padx=28, pady=22)

       
        header = tk.Frame(root_pad, bg=self.C['bg'])
        header.pack(fill='x', pady=(0, 20))

        tk.Label(header, text="SIGNPOST",
                 font=('Georgia', 30, 'bold'),
                 fg=self.C['text_primary'], bg=self.C['bg']).pack(side='left')
        tk.Label(header, text="  Puzzle",
                 font=('Georgia', 14, 'italic'),
                 fg=self.C['text_secondary'], bg=self.C['bg']).pack(side='left', pady=(12, 0))

        tk.Frame(root_pad, bg=self.C['border'], height=1).pack(fill='x', pady=(0, 18))

    
        body = tk.Frame(root_pad, bg=self.C['bg'])
        body.pack(fill='both', expand=True)
        body.grid_columnconfigure(0, weight=5, minsize=520)
        body.grid_columnconfigure(1, weight=0)
        body.grid_columnconfigure(2, weight=4, minsize=340)
        body.grid_rowconfigure(0, weight=1)

   
        left = tk.Frame(body, bg=self.C['bg'])
        left.grid(row=0, column=0, sticky='nsew')
        left.grid_rowconfigure(0, weight=1)
        left.grid_columnconfigure(0, weight=1)

        grid_card = tk.Frame(left, bg=self.C['surface'],
                             highlightbackground=self.C['border'], highlightthickness=1)
        grid_card.grid(row=0, column=0, sticky='')

        self._label(grid_card, "GRID MATRIX",
                    font=('Helvetica', 11, 'bold'),
                    fg=self.C['text_secondary'], bg=self.C['surface']
                    ).grid(row=0, column=0, columnspan=4, pady=(18, 12), padx=22)

        # ── Grid cells ──────────────────────────────
        for label, node in self.graph.nodes.items():
            cell = tk.Frame(grid_card, bg=self.C['card'],
                            highlightbackground=self.C['border_light'], highlightthickness=1,
                            width=96, height=80)
            cell.grid(row=node.row + 1, column=node.col, padx=6, pady=6)
            cell.grid_propagate(False)
            cell.grid_rowconfigure(0, weight=1)
            cell.grid_rowconfigure(1, weight=1)
            cell.grid_columnconfigure(0, weight=1)

            lbl_letter = tk.Label(cell, text=label,
                                  font=('Helvetica', 18, 'bold'),
                                  fg=self.C['text_primary'], bg=self.C['card'],
                                  anchor='center', cursor='hand2')
            lbl_letter.grid(row=0, column=0, sticky='sew', pady=(10, 2))

            lbl_arrow = tk.Label(cell, text=node.arrow_direction,
                                 font=('Helvetica', 16),
                                 fg=self.C['text_secondary'], bg=self.C['card'],
                                 anchor='center', cursor='hand2')
            lbl_arrow.grid(row=1, column=0, sticky='new', pady=(2, 8))

            for widget in (cell, lbl_letter, lbl_arrow):
                widget.bind('<Button-1>', lambda e, l=label: self.on_cell_click(l))

            self.buttons[label] = {'frame': cell, 'letter': lbl_letter, 'arrow': lbl_arrow}

        # padding bottom row
        tk.Frame(grid_card, bg=self.C['surface'], height=14).grid(row=6, column=0, columnspan=4)

        tk.Frame(body, bg=self.C['border'], width=1).grid(row=0, column=1, sticky='ns', padx=20)


        right = tk.Frame(body, bg=self.C['bg'])
        right.grid(row=0, column=2, sticky='nsew')
        right.grid_rowconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=0)
        right.grid_rowconfigure(2, weight=0)
        right.grid_columnconfigure(0, weight=1)

        hist_card = tk.Frame(right, bg=self.C['surface'],
                             highlightbackground=self.C['border'], highlightthickness=1)
        hist_card.grid(row=0, column=0, sticky='nsew', pady=(0, 12))

        self._label(hist_card, "MOVE HISTORY",
                    font=('Helvetica', 11, 'bold'),
                    fg=self.C['text_secondary'], bg=self.C['surface']
                    ).pack(anchor='w', padx=18, pady=(14, 8))
        tk.Frame(hist_card, bg=self.C['divider'], height=1).pack(fill='x', padx=18)

        self.history = tk.Text(
            hist_card, width=34, height=13,
            font=('Courier New', 10),
            bg=self.C['surface'], fg=self.C['text_primary'],
            relief='flat', bd=0, wrap='word',
            padx=18, pady=10, cursor='arrow',
            selectbackground=self.C['card']
        )
        self.history.pack(fill='both', expand=True)
        self.history.tag_config("move_ok",  foreground=self.C['accent_green'])
        self.history.tag_config("move_err", foreground=self.C['accent_red'])
        self.history.tag_config("meta",     foreground=self.C['text_dim'])
        self.history.config(state='disabled')
        self._hist("Game started — make your move.", "meta")
        self._hist("CPU: Quadrant D&C solver.", "meta")

     
        status_card = tk.Frame(right, bg=self.C['surface'],
                               highlightbackground=self.C['border'], highlightthickness=1)
        status_card.grid(row=1, column=0, sticky='ew', pady=(0, 12))

        self._label(status_card, "SYSTEM STATUS",
                    font=('Helvetica', 11, 'bold'),
                    fg=self.C['text_secondary'], bg=self.C['surface']
                    ).pack(anchor='w', padx=18, pady=(14, 6))
        tk.Frame(status_card, bg=self.C['divider'], height=1).pack(fill='x', padx=18)

        inner = tk.Frame(status_card, bg=self.C['surface'])
        inner.pack(fill='x', padx=18, pady=12)

        def stat_row(label_text):
            row = tk.Frame(inner, bg=self.C['surface'])
            row.pack(fill='x', pady=3)
            tk.Label(row, text=label_text,
                     font=('Helvetica', 10),
                     fg=self.C['text_dim'], bg=self.C['surface'],
                     anchor='w').pack(side='left')
            val = tk.Label(row, text="—",
                           font=('Helvetica', 11, 'bold'),
                           fg=self.C['text_primary'], bg=self.C['surface'],
                           anchor='e')
            val.pack(side='right')
            return val

        self.turn_label     = stat_row("Turn")
        self.timer_label    = stat_row("Time left")
        self.position_label = stat_row("Position")

        self.turn_label.config(fg=self.C['accent_blue'])

        tk.Frame(status_card, bg=self.C['surface'], height=6).pack()

        # ── Panel 3: Scoreboard ──────────────────────
        score_card = tk.Frame(right, bg=self.C['surface'],
                              highlightbackground=self.C['border'], highlightthickness=1)
        score_card.grid(row=2, column=0, sticky='ew')

        self._label(score_card, "SCOREBOARD",
                    font=('Helvetica', 11, 'bold'),
                    fg=self.C['text_secondary'], bg=self.C['surface']
                    ).pack(anchor='w', padx=18, pady=(14, 6))
        tk.Frame(score_card, bg=self.C['divider'], height=1).pack(fill='x', padx=18)

        score_inner = tk.Frame(score_card, bg=self.C['surface'])
        score_inner.pack(fill='x', padx=18, pady=12)

        # header row
        hdr = tk.Frame(score_inner, bg=self.C['surface'])
        hdr.pack(fill='x', pady=(0, 6))
        for txt, w, anc in [("Player", 10, 'w'), ("Correct", 8, 'center'), ("Errors", 8, 'center')]:
            tk.Label(hdr, text=txt, width=w, anchor=anc,
                     font=('Helvetica', 10, 'bold'),
                     fg=self.C['text_dim'], bg=self.C['surface']).pack(side='left')

        tk.Frame(score_inner, bg=self.C['border'], height=1).pack(fill='x', pady=4)

        for player, color in [('Human', self.C['accent_blue']), ('CPU', self.C['text_secondary'])]:
            row = tk.Frame(score_inner, bg=self.C['surface'])
            row.pack(fill='x', pady=4)
            tk.Label(row, text=player, width=10, anchor='w',
                     font=('Helvetica', 11), fg=color, bg=self.C['surface']).pack(side='left')
            c_lbl = tk.Label(row, text="0", width=8, anchor='center',
                             font=('Helvetica', 11, 'bold'),
                             fg=self.C['accent_green'], bg=self.C['surface'])
            c_lbl.pack(side='left')
            e_lbl = tk.Label(row, text="0", width=8, anchor='center',
                             font=('Helvetica', 11, 'bold'),
                             fg=self.C['accent_red'], bg=self.C['surface'])
            e_lbl.pack(side='left')

            if player == 'Human':
                self.human_correct_lbl, self.human_errors_lbl = c_lbl, e_lbl
            else:
                self.cpu_correct_lbl, self.cpu_errors_lbl = c_lbl, e_lbl

        tk.Frame(score_card, bg=self.C['surface'], height=8).pack()

    # ────────────────────────────────────────────────

    def _hist(self, text, tag="move_ok"):
        self.history.config(state='normal')
        self.history.insert(tk.END, text + "\n", tag)
        self.history.config(state='disabled')
        self.history.see(tk.END)


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

    # ────────────────────────────────────────────────
    # Click / moves
    # ────────────────────────────────────────────────

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
            self._hist(f"CPU    →  {move}", "move_ok")
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
        seq = ['#3D2020', '#4A2020', '#3D2020', '#4A2020', self.C['card']]
        def step(i):
            if i < len(seq):
                w = self.buttons[label]
                for k in ('frame', 'letter', 'arrow'):
                    w[k].config(bg=seq[i])
                self.root.after(120, lambda: step(i + 1))
            else:
                self.update_display()
        step(0)

    def flash_cpu(self, label):
        seq = ['#2B3A52', self.C['card'], '#2B3A52', self.C['card']]
        def step(i):
            if i < len(seq):
                w = self.buttons[label]
                for k in ('frame', 'letter', 'arrow'):
                    w[k].config(bg=seq[i])
                self.root.after(200, lambda: step(i + 1))
            else:
                self.update_display()
        step(0)

    # ────────────────────────────────────────────────
    # Display
    # ────────────────────────────────────────────────

    def update_display(self):
        for label, node in self.graph.nodes.items():
            w = self.buttons[label]
            is_current = (label == self.game_state.current_position)

            if is_current:
                bg, border, bw = '#1F3557', self.C['accent_blue'], 2
                fg_l = fg_a = self.C['accent_blue']
                w['letter'].config(text=f"[{node.visit_order}]", font=('Helvetica', 14, 'bold'))
            elif node.visited:
                bg, border, bw = '#1E3028', self.C['accent_green'], 1
                fg_l = fg_a = self.C['accent_green']
                w['letter'].config(text=f"[{node.visit_order}]", font=('Helvetica', 14, 'bold'))
            else:
                bg, border, bw = self.C['card'], self.C['border_light'], 1
                fg_l = self.C['text_primary']
                fg_a = self.C['text_secondary']
                w['letter'].config(text=label, font=('Helvetica', 18, 'bold'))

            w['frame'].config(bg=bg, highlightbackground=border, highlightthickness=bw)
            w['letter'].config(bg=bg, fg=fg_l)
            w['arrow'].config(bg=bg, fg=fg_a)

        turn = self.game_state.current_turn
        self.turn_label.config(
            text=turn,
            fg=self.C['accent_blue'] if turn == 'Human' else self.C['text_secondary']
        )

        node = self.graph.nodes[self.game_state.current_position]
        self.position_label.config(
            text=f"{self.game_state.current_position}  (step {node.visit_order})")

        gs = self.game_state
        self.human_correct_lbl.config(text=str(gs.human_correct_moves))
        self.human_errors_lbl.config(text=str(gs.human_illegal_moves))
        self.cpu_correct_lbl.config(text=str(gs.cpu_correct_moves))
        self.cpu_errors_lbl.config(text=str(gs.cpu_illegal_moves))


    def show_winner(self):
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None

        gs = self.game_state
        msg = (
            f"Winner:  {gs.winner}\n\n"
            f"Human    Correct: {gs.human_correct_moves}   Errors: {gs.human_illegal_moves}\n"
            f"CPU      Correct: {gs.cpu_correct_moves}   Errors: {gs.cpu_illegal_moves}\n\n"
            f"Click OK to play again."
        )
        messagebox.showinfo("Game Over — Signpost", msg)
        self.reset_game()

    def reset_game(self):
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None

        self._build_puzzle()

        for label, node in self.graph.nodes.items():
            w = self.buttons[label]
            bg = self.C['card']
            w['frame'].config(bg=bg,
                              highlightbackground=self.C['border_light'],
                              highlightthickness=1)
            w['letter'].config(text=label, bg=bg,
                               fg=self.C['text_primary'],
                               font=('Helvetica', 18, 'bold'))
            w['arrow'].config(text=node.arrow_direction, bg=bg,
                              fg=self.C['text_secondary'])

        self.history.config(state='normal')
        self.history.delete('1.0', tk.END)
        self.history.config(state='disabled')
        self._hist("Game reset — make your move.", "meta")
        self._hist("CPU: Quadrant D&C solver.", "meta")

        self.human_correct_lbl.config(text="0")
        self.human_errors_lbl.config(text="0")
        self.cpu_correct_lbl.config(text="0")
        self.cpu_errors_lbl.config(text="0")

        self.update_display()
        self.timer_seconds = 0
        self.start_timer()


# ====================
# MAIN
# ====================

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1100x680")
    root.minsize(1000, 620)
    PuzzleGameGUI(root)
    root.mainloop()
