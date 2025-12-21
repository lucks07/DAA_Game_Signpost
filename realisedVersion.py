import tkinter as tk
from tkinter import messagebox
import random

# ============================================================
# GRAPH IMPLEMENTATION
# ============================================================

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

    def add_node(self, label, row, col, arrow):
        self.nodes[label] = GraphNode(label, row, col, arrow)
        self.adjacency_list[label] = []

    def add_edge(self, u, v):
        self.adjacency_list[u].append(v)

    def get_neighbors(self, label):
        return self.adjacency_list.get(label, [])

    def set_solution_path(self, path):
        self.solution_path = path


# ============================================================
# GAME LOGIC (from realisedVersion.py)
# ============================================================

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

        start = self.graph.nodes['A']
        start.visited = True
        start.visit_order = 1

        self.game_over = False
        self.winner = None

    def is_legal_move(self, target):
        return (
            target in self.graph.get_neighbors(self.current_position)
            and not self.graph.nodes[target].visited
        )

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


# ============================================================
# GREEDY CPU WITH MEMORY
# ============================================================

class GreedyCPU:
    def __init__(self, graph, state):
        self.graph = graph
        self.state = state

    def dist(self, label):
        n = self.graph.nodes[label]
        g = self.graph.nodes['P']
        return abs(n.row - g.row) + abs(n.col - g.col)

    def get_best_move(self):
        cur = self.state.current_position
        neighbors = self.graph.get_neighbors(cur)
        history = self.state.cpu_illegal_history

        primary = [
            n for n in neighbors
            if not self.graph.nodes[n].visited and (cur, n) not in history
        ]

        fallback = [n for n in neighbors if not self.graph.nodes[n].visited]
        candidates = primary or fallback or neighbors

        if not candidates:
            return random.choice(list(self.graph.nodes.keys()))

        return min(candidates, key=self.dist)


# ============================================================
# GUI (from final2.py)
# ============================================================

class PuzzleGameGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Signpost Game")

        self.graph = self.create_fixed_puzzle()
        self.state = GameState(self.graph)
        self.cpu = GreedyCPU(self.graph, self.state)

        self.buttons = {}
        self.create_gui()
        self.update_display()

    def create_fixed_puzzle(self):
        g = PuzzleGraph()

        grid = [
            ('A',0,0,'↘'),('B',0,1,'↘'),('C',0,2,'↙'),('D',0,3,'←'),
            ('E',1,0,'↗'),('F',1,1,'→'),('G',1,2,'←'),('H',1,3,'←'),
            ('I',2,0,'→'),('J',2,1,'↙'),('K',2,2,'↖'),('L',2,3,'↑'),
            ('M',3,0,'→'),('N',3,1,'→'),('O',3,2,'→'),('P',3,3,'★')
        ]

        for l,r,c,a in grid:
            g.add_node(l,r,c,a)

        edges = [
            ('A','E'),('A','K'),('K','G'),('K','F'),('F','G'),('F','H'),
            ('H','G'),('G','F'),('G','E'),('E','B'),('E','A'),
            ('B','F'),('B','L'),('L','H'),('L','D'),('D','C'),
            ('C','G'),('C','I'),('I','J'),('J','N'),('J','M'),
            ('M','N'),('N','O'),('O','P')
        ]

        for u,v in edges:
            g.add_edge(u,v)

        g.set_solution_path(
            ['A','K','F','H','G','E','B','L','D','C','I','J','M','N','O','P']
        )

        return g

    def create_gui(self):
        tk.Label(self.root, text="SIGNPOST GAME",
                 font=("Helvetica",28)).pack(pady=10)

        main = tk.Frame(self.root)
        main.pack()

        grid_frame = tk.Frame(main)
        grid_frame.grid(row=0, column=0, padx=30)

        for label, node in self.graph.nodes.items():
            b = tk.Button(
                grid_frame, width=12, height=6,
                font=("Helvetica",14),
                text=f"{label}\n{node.arrow_direction}",
                command=lambda l=label: self.on_click(l)
            )
            b.grid(row=node.row, column=node.col, padx=6, pady=6)
            self.buttons[label] = b

        self.history = tk.Text(main, width=26, height=22)
        self.history.grid(row=0, column=1)
        self.history.tag_config("legal", foreground="green")
        self.history.tag_config("illegal", foreground="red")
        self.history.insert(tk.END, "MOVE HISTORY\n\n")
        self.history.config(state="disabled")

        self.turn_label = tk.Label(self.root, font=("Helvetica",16))
        self.turn_label.pack()

        stats = tk.Frame(self.root)
        stats.pack()

        self.human_stats = tk.Label(stats, font=("Helvetica",12))
        self.human_stats.pack(side="left", padx=60)

        self.cpu_stats = tk.Label(stats, font=("Helvetica",12))
        self.cpu_stats.pack(side="left", padx=60)

    def log(self, msg, tag):
        self.history.config(state="normal")
        self.history.insert(tk.END, msg + "\n", tag)
        self.history.config(state="disabled")
        self.history.see(tk.END)

    def flash_illegal(self, label):
        self.buttons[label].config(bg="red")
        self.root.after(800, self.update_display)

    def on_click(self, label):
        if self.state.current_turn != "Human":
            return

        ok, _ = self.state.make_move(label)

        if ok:
            self.log(f"Human → {label}", "legal")
        else:
            self.log(f"Human illegal → {label}", "illegal")
            self.flash_illegal(label)

        self.update_display()

        if self.state.game_over:
            self.show_winner()
        else:
            self.root.after(800, self.cpu_turn)

    def cpu_turn(self):
        move = self.cpu.get_best_move()
        ok, _ = self.state.make_move(move)

        if ok:
            self.log(f"CPU → {move}", "legal")
        else:
            self.log(f"CPU illegal → {move}", "illegal")
            self.flash_illegal(move)

        self.update_display()

        if self.state.game_over:
            self.show_winner()

    def update_display(self):
        for label, node in self.graph.nodes.items():
            b = self.buttons[label]
            if node.visited:
                b.config(text=f"{node.visit_order}\n{node.arrow_direction}",
                         bg="lightgreen")
            else:
                b.config(text=f"{label}\n{node.arrow_direction}",
                         bg="SystemButtonFace")

            if label == self.state.current_position:
                b.config(bg="yellow")

        self.turn_label.config(
            text=f"NOW {self.state.current_turn.upper()} TURN"
        )

        self.human_stats.config(
            text=f"Human\n{self.state.human_correct_moves} Correct\n"
                 f"{self.state.human_illegal_moves} Illegal"
        )

        self.cpu_stats.config(
            text=f"CPU\n{self.state.cpu_correct_moves} Correct\n"
                 f"{self.state.cpu_illegal_moves} Illegal"
        )

    def show_winner(self):
        messagebox.showinfo(
            "Game Over",
            f"Winner: {self.state.winner}"
        )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    root = tk.Tk()
    PuzzleGameGUI(root)
    root.mainloop()
