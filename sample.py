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
        
        # Mark starting position as visited
        self.graph.nodes['A'].visited = True
        self.visit_count = 1
        self.graph.nodes['A'].visit_order = 1
        
        self.game_over = False
        self.winner = None
        
    def is_legal_move(self, target_label):
        """Check if move is legal (follows arrow and unvisited)"""
        # Check if target is a valid neighbor
        neighbors = self.graph.get_neighbors(self.current_position)
        if target_label not in neighbors:
            return False
        
        # Check if target is unvisited
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
        
        # Illegal move: increment counter, switch turn
        if not is_legal or not is_correct:
            if self.current_turn == 'Human':
                self.human_illegal_moves += 1
            else:
                self.cpu_illegal_moves += 1
            
            self.switch_turn()
            return False, False
        
        # Legal and correct move: update position
        self.visit_count += 1
        self.graph.nodes[target_label].visited = True
        self.graph.nodes[target_label].visit_order = self.visit_count
        self.current_position = target_label
        
        # Update correct move counter
        if self.current_turn == 'Human':
            self.human_correct_moves += 1
        else:
            self.cpu_correct_moves += 1
        
        # Check win condition (reached Grid 16 / label 'P')
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
# CPU PLAYER (GREEDY)
# ====================

class GreedyCPU:
    """CPU player using greedy strategy"""
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
        Greedy strategy: Choose move that gets closest to goal
        without making illegal moves if possible
        """
        current_pos = self.game_state.current_position
        neighbors = self.graph.get_neighbors(current_pos)
        
        # Filter legal moves (unvisited neighbors)
        legal_moves = [n for n in neighbors if not self.graph.nodes[n].visited]
        
        # If no legal moves, try any neighbor (will be illegal but game rule requires move)
        if not legal_moves:
            legal_moves = neighbors if neighbors else []
        
        if not legal_moves:
            # No moves possible, make a random illegal attempt
            all_labels = list(self.graph.nodes.keys())
            return random.choice(all_labels)
        
        # Greedy choice: pick the neighbor closest to goal
        best_move = min(legal_moves, key=lambda x: self.calculate_distance_to_goal(x))
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
        
        Solution path from Image 2 (visiting order):
        1(A) → 2(K) → 3(F) → 4(H) → 5(G) → 6(E) → 7(B) → 8(L) 
        → 9(D) → 10(C) → 11(I) → 12(J) → 13(M) → 14(N) → 15(O) → 16(P)
        """
        graph = PuzzleGraph()
        
        # Define grid (label, row, col, arrow_direction)
        grid_config = [
            ('A', 0, 0, '↘'), ('B', 0, 1, '↘'), ('C', 0, 2, '↙'), ('D', 0, 3, '←'),
            ('E', 1, 0, '↗'), ('F', 1, 1, '→'), ('G', 1, 2, '←'), ('H', 1, 3, '←'),
            ('I', 2, 0, '→'), ('J', 2, 1, '↙'), ('K', 2, 2, '↖'), ('L', 2, 3, '↑'),
            ('M', 3, 0, '→'), ('N', 3, 1, '→'), ('O', 3, 2, '→'), ('P', 3, 3, '★')
        ]
        
        # Add all nodes
        for label, row, col, arrow in grid_config:
            graph.add_node(label, row, col, arrow)
        
        # Add edges based on arrow directions from Image 1
        # Following the solution path to determine edges
        edges = [
            # From A(↙) - down-left diagonal
            ('A', 'E'),  # A to E (down)
            ('A', 'K'),  # A to K (diagonal down-right to reach position)
            
            # From K(↗) - up-right diagonal  
            ('K', 'G'),  # K to G (up)
            ('K', 'F'),  # K to F (up-left diagonal)
            
            # From F(→) - right
            ('F', 'G'),  # F to G (right)
            ('F', 'H'),  # F to H (following path)
            
            # From H(←) - left
            ('H', 'G'),  # H to G (left)
            
            # From G(←) - left
            ('G', 'F'),  # G to F (left)
            ('G', 'E'),  # G to E (left-down)
            
            # From E(↗) - up-right diagonal
            ('E', 'B'),  # E to B (up)
            ('E', 'A'),  # E to A (up)
            
            # From B(↙) - down-left diagonal
            ('B', 'F'),  # B to F (down)
            ('B', 'L'),  # B to L (to continue path)
            
            # From L(↑) - up
            ('L', 'H'),  # L to H (up)
            ('L', 'D'),  # L to D (up)
            
            # From D(←) - left
            ('D', 'C'),  # D to C (left)
            
            # From C(↙) - down-left diagonal
            ('C', 'G'),  # C to G (down)
            ('C', 'I'),  # C to I (down-left to reach I)
            
            # From I(→) - right
            ('I', 'J'),  # I to J (right)
            
            # From J(↙) - down-left diagonal
            ('J', 'N'),  # J to N (down)
            ('J', 'M'),  # J to M (down-left)
            
            # From M(→) - right
            ('M', 'N'),  # M to N (right)
            
            # From N(→) - right
            ('N', 'O'),  # N to O (right)
            
            # From O(→) - right
            ('O', 'P'),  # O to P (right - GOAL!)
        ]
        
        for from_node, to_node in edges:
            graph.add_edge(from_node, to_node)
        
        # Define the unique solution path from Image 2
        # Following the number sequence: 1→2→3→4→5→6→7→8→9→10→11→12→13→14→15→16
        solution = ['A', 'K', 'F', 'H', 'G', 'E', 'B', 'L', 'D', 'C', 'I', 'J', 'M', 'N', 'O', 'P']
        graph.set_solution_path(solution)
        
        return graph
    
    def create_gui(self):
        """Create the GUI layout"""
        # Title
        title_label = tk.Label(self.root, text="Arrow Grid Puzzle Game", 
                              font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=4, pady=10)
        
        # Grid frame
        grid_frame = tk.Frame(self.root)
        grid_frame.grid(row=1, column=0, columnspan=4, padx=20, pady=10)
        
        # Create 4x4 grid buttons
        for label, node in self.graph.nodes.items():
            btn = tk.Button(grid_frame, text=f"{label}\n{node.arrow_direction}",
                          width=8, height=4, font=('Arial', 12),
                          command=lambda l=label: self.on_cell_click(l))
            btn.grid(row=node.row, column=node.col, padx=2, pady=2)
            self.buttons[label] = btn
        
        # Info panel
        info_frame = tk.Frame(self.root)
        info_frame.grid(row=2, column=0, columnspan=4, pady=10)
        
        # Turn indicator
        self.turn_label = tk.Label(info_frame, text="Current Turn: Human",
                                   font=('Arial', 12, 'bold'))
        self.turn_label.grid(row=0, column=0, columnspan=2, pady=5)
        
        # Counters
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
        
        # Current position indicator
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
        
        # Attempt move
        success, is_correct = self.game_state.make_move(label)
        
        self.update_display()
        
        if not success:
            messagebox.showinfo("Illegal Move", 
                              f"Move to {label} is illegal!\nIllegal move count increased.")
        
        # Check if game ended
        if self.game_state.game_over:
            self.show_winner()
            return
        
        # CPU's turn
        if self.game_state.current_turn == 'CPU':
            self.root.after(1000, self.cpu_turn)  # 1 second delay for CPU
    
    def cpu_turn(self):
        """Execute CPU's turn"""
        if self.game_state.game_over:
            return
        
        # Get CPU's move using greedy strategy
        cpu_move = self.cpu_player.get_best_move()
        
        # Make the move
        success, is_correct = self.game_state.make_move(cpu_move)
        
        self.update_display()
        
        # Show CPU's move result
        if not success:
            messagebox.showinfo("CPU Move", 
                              f"CPU attempted illegal move to {cpu_move}!")
        
        # Check if game ended
        if self.game_state.game_over:
            self.show_winner()
    
    def update_display(self):
        """Update all GUI elements"""
        # Update grid buttons
        for label, node in self.graph.nodes.items():
            btn = self.buttons[label]
            
            # Update text to show visit order
            if node.visited and node.visit_order:
                btn.config(text=f"{node.visit_order}\n{node.arrow_direction}")
            else:
                btn.config(text=f"{label}\n{node.arrow_direction}")
            
            # Highlight current position
            if label == self.game_state.current_position:
                btn.config(bg='yellow')
            elif node.visited:
                btn.config(bg='lightgreen')
            else:
                btn.config(bg='SystemButtonFace')
        
        # Update turn indicator
        self.turn_label.config(text=f"Current Turn: {self.game_state.current_turn}")
        
        # Update counters
        self.human_correct_label.config(text=f"Correct: {self.game_state.human_correct_moves}")
        self.human_illegal_label.config(text=f"Illegal: {self.game_state.human_illegal_moves}")
        self.cpu_correct_label.config(text=f"Correct: {self.game_state.cpu_correct_moves}")
        self.cpu_illegal_label.config(text=f"Illegal: {self.game_state.cpu_illegal_moves}")
        
        # Update position
        current_node = self.graph.nodes[self.game_state.current_position]
        order = current_node.visit_order if current_node.visit_order else 0
        self.position_label.config(text=f"Current Position: {self.game_state.current_position} (Grid {order})")
    
    def show_winner(self):
        """Display winner message"""
        winner = self.game_state.winner
        h_illegal = self.game_state.human_illegal_moves
        c_illegal = self.game_state.cpu_illegal_moves
        
        if winner == 'Human':
            msg = f"🎉 You Win! 🎉\n\nYour illegal moves: {h_illegal}\nCPU illegal moves: {c_illegal}"
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
