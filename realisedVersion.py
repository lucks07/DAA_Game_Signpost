import tkinter as tk
from tkinter import messagebox
import random

# ====================
# GRAPH IMPLEMENTATION
# ====================

class GraphNode:
    """Represents a single grid cell in the puzzle"""
    def __init__(self, label, row, col, arrow_direction):
        self.label = label  # 'A', 'B', 'C', etc.
        self.row = row
        self.col = col
        self.arrow_direction = arrow_direction  # 'up', 'down', 'left', 'right'
        self.visited = False
        self.visit_order = None  # Will be 1, 2, 3... when visited

class PuzzleGraph:
    """Graph representation using adjacency list"""
    def __init__(self):
        self.nodes = {}  # Dictionary: label -> GraphNode
        self.adjacency_list = {}  # Dictionary: label -> [neighbor_labels]
        self.solution_path = []  # Correct sequence of moves
        
    def add_node(self, label, row, col, arrow_direction):
        """Add a node (grid cell) to the graph"""
        node = GraphNode(label, row, col, arrow_direction)
        self.nodes[label] = node
        self.adjacency_list[label] = []
        
    def add_edge(self, from_label, to_label):
        """Add directed edge based on arrow direction"""
        if from_label in self.adjacency_list:
            self.adjacency_list[from_label].append(to_label)
    
    def get_neighbors(self, label):
        """Get all possible neighbors from current position"""
        return self.adjacency_list.get(label, [])
    
    def set_solution_path(self, path):
        """Set the unique solution path for the puzzle"""
        self.solution_path = path

# ====================
# GAME LOGIC
# ====================

class GameState:
    """Manages the game state and rules"""
    def __init__(self, graph):
        self.graph = graph
        self.current_position = 'A'  # Start at top-left
        self.current_turn = 'Human'  # 'Human' or 'CPU'
        self.visit_count = 0  # Tracks numbering for visited cells
        
        # Counters for both players
        self.human_correct_moves = 0
        self.human_illegal_moves = 0
        self.cpu_correct_moves = 0
        self.cpu_illegal_moves = 0

        # CPU memory: (from_label, to_label) pairs that were illegal/wrong
        self.cpu_illegal_history = set()
        
        # Mark starting position as visited
        self.graph.nodes['A'].visited = True
        self.visit_count = 1
        self.graph.nodes['A'].visit_order = 1
        
        self.game_over = False
        self.winner = None
        
    def is_legal_move(self, target_label):
        """Check if move is legal (follows arrow and unvisited)"""
        neighbors = self.graph.get_neighbors(self.current_position)
        if target_label not in neighbors:
            return False
        
        if self.graph.nodes[target_label].visited:
            return False
            
        return True
    
    def is_correct_move(self, target_label):
        """Check if move matches the solution path"""
        try:
            current_index = self.graph.solution_path.index(self.current_position)
            next_in_solution = self.graph.solution_path[current_index + 1]
            return target_label == next_in_solution
        except (ValueError, IndexError):
            return False
    
    def make_move(self, target_label):
        """
        Attempt to make a move
        Returns: (success: bool, is_correct: bool)
        """
        if self.game_over:
            return False, False
        
        is_legal = self.is_legal_move(target_label)
        is_correct = self.is_correct_move(target_label)
        
        # Illegal OR wrong move
        if not is_legal or not is_correct:
            if self.current_turn == 'Human':
                self.human_illegal_moves += 1
            else:
                self.cpu_illegal_moves += 1
                # Record this bad attempt for CPU (from current -> target)
                self.cpu_illegal_history.add((self.current_position, target_label))
            
            self.switch_turn()
            return False, False
        
        # Legal and correct move: update position
        self.visit_count += 1
        self.graph.nodes[target_label].visited = True
        self.graph.nodes[target_label].visit_order = self.visit_count
        self.current_position = target_label
        
        if self.current_turn == 'Human':
            self.human_correct_moves += 1
        else:
            self.cpu_correct_moves += 1
        
        if target_label == 'P':
            self.game_over = True
            self.determine_winner()
        
        self.switch_turn()
        return True, True
    
    def switch_turn(self):
        """Switch between Human and CPU turn"""
        self.current_turn = 'CPU' if self.current_turn == 'Human' else 'Human'
    
    def determine_winner(self):
        """Determine winner based on illegal move count"""
        if self.human_illegal_moves < self.cpu_illegal_moves:
            self.winner = 'Human'
        elif self.cpu_illegal_moves < self.human_illegal_moves:
            self.winner = 'CPU'
        else:
            self.winner = 'Draw'

# ====================
# CPU PLAYER (GREEDY + MEMORY)
# ====================

class GreedyCPU:
    """CPU player using greedy strategy with illegal-move memory"""
    def __init__(self, graph, game_state):
        self.graph = graph
        self.game_state = game_state
    
    def calculate_distance_to_goal(self, label):
        """Calculate Manhattan distance to goal (Grid 16 / label 'P')"""
        node = self.graph.nodes[label]
        goal_node = self.graph.nodes['P']
        distance = abs(node.row - goal_node.row) + abs(node.col - goal_node.col)
        return distance
    
    def get_best_move(self):
        """
        Greedy strategy:
        - Among neighbors, consider only unvisited moves that are not in cpu_illegal_history.
        - If none, fall back to normal greedy among unvisited neighbors.
        - If still none, fall back to any neighbor or a random node.
        """
        current_pos = self.game_state.current_position
        neighbors = self.graph.get_neighbors(current_pos)
        history = self.game_state.cpu_illegal_history
        
        # 1. Prefer legal moves not in illegal history
        primary_moves = [
            n for n in neighbors
            if (not self.graph.nodes[n].visited)
            and ((current_pos, n) not in history)
        ]
        
        # 2. If none, allow legal moves even if they are in history (to avoid total deadlock)
        fallback_moves = [
            n for n in neighbors
            if not self.graph.nodes[n].visited
        ]
        
        candidate_moves = primary_moves or fallback_moves
        
        # 3. If no unvisited neighbors, try any neighbor (will be illegal but required by rules)
        if not candidate_moves:
            candidate_moves = neighbors
        
        # 4. If still no neighbors, random illegal attempt anywhere
        if not candidate_moves:
            all_labels = list(self.graph.nodes.keys())
            return random.choice(all_labels)
        
        # Greedy choice: pick the neighbor closest to goal
        best_move = min(candidate_moves, key=lambda x: self.calculate_distance_to_goal(x))
        return best_move

# ====================
# GUI WITH TKINTER
# ====================

class PuzzleGameGUI:
    """Tkinter GUI for the puzzle game"""
    def __init__(self, root):
        self.root = root
        self.root.title("Arrow Grid Puzzle - Human vs CPU")
        
        # Initialize graph with fixed puzzle
        self.graph = self.create_fixed_puzzle()
        self.game_state = GameState(self.graph)
        self.cpu_player = GreedyCPU(self.graph, self.game_state)
        
        # GUI components
        self.buttons = {}  # Dictionary: label -> button widget
        self.create_gui()
        self.update_display()
    
    def create_fixed_puzzle(self):
        """
        Create a fixed 4x4 puzzle based on prototype images
        Grid layout (row, col):
        A(↘) B(↘) C(↙) D(←)
        E(↗) F(→) G(←) H(←)
        I(→) J(↙) K(↖) L(↑)
        M(→) N(→) O(→) P(★)
        
        Solution path (visiting order):
        A → K → F → H → G → E → B → L → D → C → I → J → M → N → O → P
        """
        graph = PuzzleGraph()
        
        grid_config = [
            ('A', 0, 0, '↘'), ('B', 0, 1, '↘'), ('C', 0, 2, '↙'), ('D', 0, 3, '←'),
            ('E', 1, 0, '↗'), ('F', 1, 1, '→'), ('G', 1, 2, '←'), ('H', 1, 3, '←'),
            ('I', 2, 0, '→'), ('J', 2, 1, '↙'), ('K', 2, 2, '↖'), ('L', 2, 3, '↑'),
            ('M', 3, 0, '→'), ('N', 3, 1, '→'), ('O', 3, 2, '→'), ('P', 3, 3, '★')
        ]
        
        for label, row, col, arrow in grid_config:
            graph.add_node(label, row, col, arrow)
        
        edges = [
            ('A', 'E'), ('A', 'K'),
            ('K', 'G'), ('K', 'F'),
            ('F', 'G'), ('F', 'H'),
            ('H', 'G'),
            ('G', 'F'), ('G', 'E'),
            ('E', 'B'), ('E', 'A'),
            ('B', 'F'), ('B', 'L'),
            ('L', 'H'), ('L', 'D'),
            ('D', 'C'),
            ('C', 'G'), ('C', 'I'),
            ('I', 'J'),
            ('J', 'N'), ('J', 'M'),
            ('M', 'N'),
            ('N', 'O'),
            ('O', 'P'),
        ]
        
        for u, v in edges:
            graph.add_edge(u, v)
        
        solution = ['A', 'K', 'F', 'H', 'G', 'E', 'B', 'L', 'D', 'C', 'I', 'J', 'M', 'N', 'O', 'P']
        graph.set_solution_path(solution)
        
        return graph
    
    def create_gui(self):
        """Create the GUI layout"""
        title_label = tk.Label(self.root, text="Arrow Grid Puzzle Game", 
                              font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=4, pady=10)
        
        grid_frame = tk.Frame(self.root)
        grid_frame.grid(row=1, column=0, columnspan=4, padx=20, pady=10)
        
        for label, node in self.graph.nodes.items():
            btn = tk.Button(grid_frame, text=f"{label}\n{node.arrow_direction}",
                          width=8, height=4, font=('Arial', 12),
                          command=lambda l=label: self.on_cell_click(l))
            btn.grid(row=node.row, column=node.col, padx=2, pady=2)
            self.buttons[label] = btn
        
        info_frame = tk.Frame(self.root)
        info_frame.grid(row=2, column=0, columnspan=4, pady=10)
        
        self.turn_label = tk.Label(info_frame, text="Current Turn: Human",
                                   font=('Arial', 12, 'bold'))
        self.turn_label.grid(row=0, column=0, columnspan=2, pady=5)
        
        tk.Label(info_frame, text="Human Stats:", font=('Arial', 10, 'bold')).grid(row=1, column=0, sticky='w')
        self.human_correct_label = tk.Label(info_frame, text="Correct: 0")
        self.human_correct_label.grid(row=2, column=0, sticky='w')
        self.human_illegal_label = tk.Label(info_frame, text="Illegal: 0")
        self.human_illegal_label.grid(row=3, column=0, sticky='w')
        
        tk.Label(info_frame, text="CPU Stats:", font=('Arial', 10, 'bold')).grid(row=1, column=1, sticky='w', padx=20)
        self.cpu_correct_label = tk.Label(info_frame, text="Correct: 0")
        self.cpu_correct_label.grid(row=2, column=1, sticky='w', padx=20)
        self.cpu_illegal_label = tk.Label(info_frame, text="Illegal: 0")
        self.cpu_illegal_label.grid(row=3, column=1, sticky='w', padx=20)
        
        self.position_label = tk.Label(info_frame, text="Current Position: A (Grid 1)",
                                      font=('Arial', 10))
        self.position_label.grid(row=4, column=0, columnspan=2, pady=5)
    
    def on_cell_click(self, label):
        """Handle human player's cell click"""
        if self.game_state.game_over:
            return
        
        if self.game_state.current_turn != 'Human':
            messagebox.showwarning("Not Your Turn", "Wait for CPU's turn to finish!")
            return
        
        success, is_correct = self.game_state.make_move(label)
        
        self.update_display()
        
        if not success:
            messagebox.showinfo("Illegal Move", 
                              f"Move to {label} is illegal!\nIllegal move count increased.")
        
        if self.game_state.game_over:
            self.show_winner()
            return
        
        if self.game_state.current_turn == 'CPU':
            self.root.after(1000, self.cpu_turn)
    
    def cpu_turn(self):
        """Execute CPU's turn"""
        if self.game_state.game_over:
            return
        
        cpu_move = self.cpu_player.get_best_move()
        
        success, is_correct = self.game_state.make_move(cpu_move)
        
        self.update_display()
        
        if not success:
            messagebox.showinfo("CPU Move", 
                              f"CPU attempted illegal move to {cpu_move}!")
        
        if self.game_state.game_over:
            self.show_winner()
    
    def update_display(self):
        """Update all GUI elements"""
        for label, node in self.graph.nodes.items():
            btn = self.buttons[label]
            
            if node.visited and node.visit_order:
                btn.config(text=f"{node.visit_order}\n{node.arrow_direction}")
            else:
                btn.config(text=f"{label}\n{node.arrow_direction}")
            
            if label == self.game_state.current_position:
                btn.config(bg='yellow')
            elif node.visited:
                btn.config(bg='lightgreen')
            else:
                btn.config(bg='SystemButtonFace')
        
        self.turn_label.config(text=f"Current Turn: {self.game_state.current_turn}")
        
        self.human_correct_label.config(text=f"Correct: {self.game_state.human_correct_moves}")
        self.human_illegal_label.config(text=f"Illegal: {self.game_state.human_illegal_moves}")
        self.cpu_correct_label.config(text=f"Correct: {self.game_state.cpu_correct_moves}")
        self.cpu_illegal_label.config(text=f"Illegal: {self.game_state.cpu_illegal_moves}")
        
        current_node = self.graph.nodes[self.game_state.current_position]
        order = current_node.visit_order if current_node.visit_order else 0
        self.position_label.config(text=f"Current Position: {self.game_state.current_position} (Grid {order})")
    
    def show_winner(self):
        """Display winner message"""
        winner = self.game_state.winner
        h_illegal = self.game_state.human_illegal_moves
        c_illegal = self.game_state.cpu_illegal_moves
        
        if winner == 'Human':
            msg = f"You Win!\n\nYour illegal moves: {h_illegal}\nCPU illegal moves: {c_illegal}"
        elif winner == 'CPU':
            msg = f"CPU Wins!\n\nYour illegal moves: {h_illegal}\nCPU illegal moves: {c_illegal}"
        else:
            msg = f"It's a Draw!\n\nBoth players had {h_illegal} illegal moves"
        
        messagebox.showinfo("Game Over", msg)

# ====================
# MAIN EXECUTION
# ====================

if __name__ == "__main__":
    root = tk.Tk()
    game = PuzzleGameGUI(root)
    root.mainloop()
