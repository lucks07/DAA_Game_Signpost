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
# CPU PLAYER
# ====================

class GreedyCPU:
    def __init__(self, graph, game_state):
        self.graph = graph
        self.game_state = game_state

    def distance_to_goal(self, label):
        node = self.graph.nodes[label]
        goal = self.graph.nodes['P']
        return abs(node.row - goal.row) + abs(node.col - goal.col)

    def get_best_move(self):
        current = self.game_state.current_position
        neighbors = self.graph.get_neighbors(current)
        history = self.game_state.cpu_illegal_history

        primary = [
            n for n in neighbors
            if not self.graph.nodes[n].visited
            and (current, n) not in history
        ]

        fallback = [n for n in neighbors if not self.graph.nodes[n].visited]

        candidates = primary or fallback or neighbors

        if not candidates:
            return random.choice(list(self.graph.nodes.keys()))

        return min(candidates, key=self.distance_to_goal)


# ====================
# GUI
# ====================

class PuzzleGameGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Arrow Grid Puzzle - Human vs CPU")

        self.graph = self.create_fixed_puzzle()
        self.game_state = GameState(self.graph)
        self.cpu_player = GreedyCPU(self.graph, self.game_state)

        self.buttons = {}
        self.create_gui()
        self.update_display()

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
    # ===== Root container (centers everything) =====
        container = tk.Frame(self.root)
        container.pack(expand=True, padx=20, pady=20)

        # ===== Title =====
        tk.Label(
            container,
            text="Signpost Puzzle Game",
            font=('Arial', 18, 'bold')
        ).pack(pady=10)

        # ===== Main content frame =====
        main_frame = tk.Frame(container)
        main_frame.pack()

        # ===== LEFT: Grid Frame =====
        grid_frame = tk.LabelFrame(
            main_frame,
            text="Puzzle Grid",
            font=('Arial', 12, 'bold'),
            padx=10,
            pady=10
        )
        grid_frame.grid(row=0, column=0, padx=15, pady=5)

        for label, node in self.graph.nodes.items():
            btn = tk.Button(
                grid_frame,
                text=f"{label}\n{node.arrow_direction}",
                width=8,
                height=4,
                font=('Arial', 12),
                command=lambda l=label: self.on_cell_click(l)
            )
            btn.grid(row=node.row, column=node.col, padx=3, pady=3)
            self.buttons[label] = btn

        # ===== RIGHT: Side Panel =====
        side_frame = tk.Frame(main_frame)
        side_frame.grid(row=0, column=1, padx=15, sticky="n")

        # ----- Move History -----
        history_frame = tk.LabelFrame(
            side_frame,
            text="Move History",
            font=('Arial', 12, 'bold'),
            padx=8,
            pady=8
        )
        history_frame.pack(fill="both", pady=5)

        self.history = tk.Text(history_frame, width=30, height=16)
        self.history.pack()
        self.history.tag_config("legal", foreground="green")
        self.history.tag_config("illegal", foreground="red")
        self.history.insert(tk.END, "MOVE HISTORY\n\n")
        self.history.config(state="disabled")

        # ----- Game Info -----
        info_frame = tk.LabelFrame(
            side_frame,
            text="Game Info",
            font=('Arial', 12, 'bold'),
            padx=10,
            pady=8
        )
        info_frame.pack(fill="x", pady=10)

        self.turn_label = tk.Label(info_frame, font=('Arial', 11, 'bold'))
        self.turn_label.pack(pady=3)

        self.position_label = tk.Label(info_frame)
        self.position_label.pack(pady=3)

        # ----- Stats -----
        stats_frame = tk.LabelFrame(
            side_frame,
            text="Statistics",
            font=('Arial', 12, 'bold'),
            padx=10,
            pady=8
        )
        stats_frame.pack(fill="x")

        self.human_stats = tk.Label(stats_frame, justify="left")
        self.human_stats.pack(anchor="w")

        self.cpu_stats = tk.Label(stats_frame, justify="left")
        self.cpu_stats.pack(anchor="w")


    def log(self, text, tag):
        self.history.config(state="normal")
        self.history.insert(tk.END, text + "\n", tag)
        self.history.config(state="disabled")
        self.history.see(tk.END)

    def flash_illegal(self, label):
        self.buttons[label].config(bg="red")
        self.root.after(800, self.update_display)

    def on_cell_click(self, label):
        if self.game_state.current_turn != 'Human' or self.game_state.game_over:
            return

        success,_ = self.game_state.make_move(label)

        if success:
            self.log(f"Human → {label}", "legal")
        else:
            self.log(f"Human illegal → {label}", "illegal")
            self.flash_illegal(label)

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
            self.log(f"CPU → {move}", "legal")
        else:
            self.log(f"CPU illegal → {move}", "illegal")
            self.flash_illegal(move)

        self.update_display()

        if self.game_state.game_over:
            self.show_winner()

    def update_display(self):
        for label,node in self.graph.nodes.items():
            btn = self.buttons[label]
            if node.visited:
                btn.config(text=f"{node.visit_order}\n{node.arrow_direction}", bg="lightgreen")
            else:
                btn.config(text=f"{label}\n{node.arrow_direction}", bg="SystemButtonFace")
            if label == self.game_state.current_position:
                btn.config(bg="yellow")

        self.turn_label.config(text=f"Current Turn: {self.game_state.current_turn}")
        self.human_stats.config(
            text=f"Human\nCorrect: {self.game_state.human_correct_moves}\nIllegal: {self.game_state.human_illegal_moves}"
        )
        self.cpu_stats.config(
            text=f"CPU\nCorrect: {self.game_state.cpu_correct_moves}\nIllegal: {self.game_state.cpu_illegal_moves}"
        )

        order = self.graph.nodes[self.game_state.current_position].visit_order
        self.position_label.config(
            text=f"Current Position: {self.game_state.current_position} (Grid {order})"
        )

    def show_winner(self):
        messagebox.showinfo("Game Over", f"Winner: {self.game_state.winner}")


# ====================
# MAIN
# ====================

if __name__ == "__main__":
    root = tk.Tk()
    PuzzleGameGUI(root)
    root.mainloop()
