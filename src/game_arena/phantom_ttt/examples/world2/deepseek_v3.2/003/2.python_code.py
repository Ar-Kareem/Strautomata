
import random
import math
from typing import List, Tuple
import time

class MCTSNode:
    def __init__(self, board_state, player_moves, unknown_cells, parent=None, move=None):
        self.board_state = [row[:] for row in board_state]  # 0=unknown, 1=my confirmed
        self.player_moves = player_moves  # Positions where I have 1
        self.unknown_cells = unknown_cells  # Positions that are 0
        self.parent = parent
        self.move = move  # (row, col) that led here
        self.children = []
        self.visits = 0
        self.wins = 0
        self.untried_moves = self.get_legal_moves()
        
    def get_legal_moves(self) -> List[Tuple[int, int]]:
        """Return all positions that are not confirmed as mine (board == 0)"""
        moves = []
        for r in range(3):
            for c in range(3):
                if self.board_state[r][c] == 0:
                    moves.append((r, c))
        return moves
    
    def ucb1(self, exploration=1.414) -> float:
        """Calculate UCB1 value for node selection"""
        if self.visits == 0:
            return float('inf')
        return (self.wins / self.visits) + exploration * math.sqrt(math.log(self.parent.visits) / self.visits)
    
    def expand(self):
        """Expand one child from untried moves"""
        move = self.untried_moves.pop()
        # Create new board state (if move succeeds, it becomes 1; otherwise stays 0)
        new_board = [row[:] for row in self.board_state]
        new_player_moves = self.player_moves.copy()
        new_unknown = self.unknown_cells.copy()
        
        # In simulation: assume move succeeds if cell is empty in our simulation state
        # For expansion, we'll consider both possibilities
        new_board[move[0]][move[1]] = 1
        new_player_moves.add(move)
        if move in new_unknown:
            new_unknown.remove(move)
            
        child = MCTSNode(new_board, new_player_moves, new_unknown, self, move)
        self.children.append(child)
        return child
    
    def is_terminal(self) -> bool:
        """Check if game is over in this simulation"""
        # Check if I have 3 in a row
        for r in range(3):
            if all(self.board_state[r][c] == 1 for c in range(3)):
                return True
        for c in range(3):
            if all(self.board_state[r][c] == 1 for r in range(3)):
                return True
        if all(self.board_state[i][i] == 1 for i in range(3)):
            return True
        if all(self.board_state[i][2-i] == 1 for i in range(3)):
            return True
            
        # Check if board is full (all cells are either 1 or assumed opponent)
        if len(self.unknown_cells) == 0:
            return True
            
        return False
    
    def simulate(self) -> float:
        """Run a random simulation from this node, return reward"""
        board_copy = [row[:] for row in self.board_state]
        my_moves = self.player_moves.copy()
        unknown = self.unknown_cells.copy()
        
        # Assume opponent has placed marks in some unknown cells
        # For simulation, randomly place opponent marks in 0-4 of the unknown cells
        opp_moves = set()
        if unknown:
            num_opp = random.randint(0, min(4, len(unknown)))
            opp_positions = random.sample(list(unknown), num_opp)
            opp_moves.update(opp_positions)
        
        # Simulate alternating moves
        current_player = 'me'  # Just simulated me
        moves_made = 0
        
        while moves_made < 10:  # Limit simulation depth
            # Get legal moves (not in my confirmed or opponent simulated moves)
            legal = []
            for r in range(3):
                for c in range(3):
                    pos = (r, c)
                    if board_copy[r][c] == 0 and pos not in opp_moves:
                        legal.append(pos)
            
            if not legal:
                break
                
            if current_player == 'me':
                # I try to place a mark
                move = random.choice(legal)
                if move not in opp_moves:  # Success
                    board_copy[move[0]][move[1]] = 1
                    my_moves.add(move)
                    if move in unknown:
                        unknown.remove(move)
                # else: fail (do nothing)
                current_player = 'opp'
            else:
                # Opponent places a mark
                move = random.choice(legal)
                opp_moves.add(move)
                if move in unknown:
                    unknown.remove(move)
                current_player = 'me'
            
            moves_made += 1
            
            # Check if I win
            for r in range(3):
                if all(board_copy[r][c] == 1 for c in range(3)):
                    return 1.0
            for c in range(3):
                if all(board_copy[r][c] == 1 for r in range(3)):
                    return 1.0
            if all(board_copy[i][i] == 1 for i in range(3)):
                return 1.0
            if all(board_copy[i][2-i] == 1 for i in range(3)):
                return 1.0
        
        # No win - return partial score based on progress
        return len(my_moves) / 9.0

def policy(board: List[List[int]]) -> Tuple[int, int]:
    # Start timer
    start_time = time.time()
    
    # Parse current board state
    my_moves = set()
    unknown_cells = set()
    
    for r in range(3):
        for c in range(3):
            if board[r][c] == 1:
                my_moves.add((r, c))
            else:  # board[r][c] == 0
                unknown_cells.add((r, c))
    
    # If board is empty, prefer center or corners
    if len(my_moves) == 0:
        # Try center first
        if (1, 1) in unknown_cells:
            return (1, 1)
        # Then corners
        corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
        for corner in corners:
            if corner in unknown_cells:
                return corner
    
    # Create root node
    root = MCTSNode(board, my_moves, unknown_cells)
    
    # Run MCTS iterations until time limit
    iterations = 0
    while time.time() - start_time < 0.5:  # Use 0.5 seconds max
        # Selection
        node = root
        while node.children and not node.untried_moves:
            # Select child with highest UCB1
            node = max(node.children, key=lambda n: n.ucb1())
        
        # Expansion
        if node.untried_moves:
            node = node.expand()
        
        # Simulation
        reward = node.simulate()
        
        # Backpropagation
        while node:
            node.visits += 1
            node.wins += reward
            node = node.parent
        
        iterations += 1
    
    # Choose best move from root children
    if root.children:
        best_child = max(root.children, key=lambda n: n.visits)
        return best_child.move
    
    # Fallback: strategic heuristic
    # Priority: center, corners, edges
    priority_order = [
        (1, 1),  # Center
        (0, 0), (0, 2), (2, 0), (2, 2),  # Corners
        (0, 1), (1, 0), (1, 2), (2, 1)   # Edges
    ]
    
    for move in priority_order:
        r, c = move
        if board[r][c] == 0:
            return move
    
    # Ultimate fallback: first available
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                return (r, c)
    
    # Should never reach here
    return (0, 0)
