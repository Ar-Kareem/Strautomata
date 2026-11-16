
import random
import numpy as np
from collections import defaultdict

def get_neighbors(row, col):
    """Get all 6 neighboring hexagonal positions."""
    neighbors = []
    # Hexagonal neighbors: up, up-right, down-right, down, down-left, up-left
    offsets = [(-1, 0), (-1, 1), (0, 1), (1, 0), (1, -1), (0, -1)]
    for dr, dc in offsets:
        nr, nc = row + dr, col + dc
        neighbors.append((nr, nc))
    return neighbors

def is_valid_position(row, col, valid_mask):
    """Check if position is valid and unoccupied."""
    if row < 0 or row >= len(valid_mask) or col < 0 or col >= len(valid_mask[0]):
        return False
    return valid_mask[row][col]

def check_ring(me_board, row, col):
    """Check if placing a stone at (row, col) creates a ring."""
    # A ring requires at least 6 connected stones forming a loop
    # This is a simplified check - full implementation would be more complex
    return False  # Not implemented for efficiency (would require advanced connectivity algo)

def check_bridge(me_board, row, col):
    """Check if placing a stone at (row, col) can help form a bridge."""
    # Consider 6 corners: (0,0), (0,14), (7,14), (14,14), (14,0), (7,0)
    # Simple check: if we're close to connecting two corners
    return False  # Simplified for efficiency

def check_fork(me_board, row, col):
    """Check if placing a stone at (row, col) can help form a fork."""
    # Fork connects 3 edges - simplified check
    return False  # Simplified for efficiency

def evaluate_position(me_board, opp_board, row, col, valid_mask):
    """Evaluate how good a position is."""
    # Check for immediate win
    if check_ring(me_board, row, col) or check_bridge(me_board, row, col) or check_fork(me_board, row, col):
        return 1000
    
    # Check for opponent's immediate win (block it)
    # Local evaluation based on connectivity and control
    score = 0
    
    # Center control
    center_distance = max(abs(row - 7), abs(col - 7))
    score += (15 - center_distance) * 2
    
    # Connectivity - how many neighbors are already connected
    neighbors = get_neighbors(row, col)
    connected = 0
    for nr, nc in neighbors:
        if is_valid_position(nr, nc, valid_mask) and (nr, nc) in me_board:
            connected += 1
    score += connected * 5
    
    # Potential patterns
    if connected >= 2:
        score += 10
    
    return score

class MCTSNode:
    def __init__(self, parent=None, move=None, board_state=None):
        self.parent = parent
        self.move = move  # the move that led to this node
        self.board_state = board_state
        self.children = []
        self.visits = 0
        self.wins = 0
        self.untried_moves = []
        self.is_terminal = False
    
    def is_fully_expanded(self):
        return len(self.untried_moves) == 0
    
    def is_terminal_node(self):
        # Check for winning conditions - simplified
        return self.is_terminal
    
    def expand(self):
        # Expand with valid moves from current board state
        if not self.untried_moves:
            # Generate all possible moves (simplified)
            board = np.zeros((15, 15), dtype=bool)
            for r, c in self.board_state[0]:
                board[r][c] = True
            for r, c in self.board_state[1]:
                board[r][c] = True
                
            for r in range(15):
                for c in range(15):
                    if board[r][c] == False and self.board_state[2][r][c]:
                        self.untried_moves.append((r, c))
        
        # Remove a random move
        move = self.untried_moves.pop()
        new_board = (list(self.board_state[0]), list(self.board_state[1]), self.board_state[2])
        new_board[0].append(move)
        new_node = MCTSNode(self, move, new_board)
        self.children.append(new_node)
        return new_node

def ucb1_selection(node, exploration_param=1.41):
    """Select a child using UCB1 formula."""
    best_score = float('-inf')
    best_children = []
    
    for child in node.children:
        if child.visits == 0:
            return child
        
        exploitation = child.wins / child.visits
        exploration = exploration_param * np.sqrt(np.log(node.visits) / child.visits)
        score = exploitation + exploration
        
        if score > best_score:
            best_score = score
            best_children = [child]
        elif score == best_score:
            best_children.append(child)
    
    return random.choice(best_children) if best_children else None

def mcts_simulation(node, me_board, opp_board, valid_mask):
    """Perform a single MCTS simulation."""
    current_node = node
    board_copy = [list(me_board), list(opp_board), valid_mask]
    
    # Find untried moves at start
    untried_moves = []
    for r in range(15):
        for c in range(15):
            if board_copy[2][r][c] and (r, c) not in me_board and (r, c) not in opp_board:
                untried_moves.append((r, c))
    
    # Select and expand
    while not current_node.is_fully_expanded() and not current_node.is_terminal_node():
        # For simplicity, just expand one level
        if len(untried_moves) > 0:
            move = untried_moves.pop()
            current_node = current_node.expand()
            current_node.board_state[0].append(move)
            board_copy[0].append(move)
        else:
            break
    
    # Play out (simple evaluation)
    score = evaluate_position(board_copy[0], board_copy[1], 7, 7)  # Center evaluation
    return 1 if score > 100 else 0

def monte_carlo_tree_search(initial_board, valid_mask, time_limit=0.9):
    """Main MCTS implementation."""
    # Create initial node with current board state
    me_board = initial_board[0]
    opp_board = initial_board[1]
    root = MCTSNode(board_state=initial_board)
    
    # Do some iterations
    iterations = 0
    while iterations < 300:  # Limit number of iterations
        # Selection
        current_node = root
        while not current_node.is_terminal_node() and current_node.is_fully_expanded():
            selected_child = ucb1_selection(current_node)
            if selected_child:
                current_node = selected_child
            else:
                break
        
        # Expansion
        if not current_node.is_terminal_node():
            if current_node.untried_moves:
                # Existing untried moves
                pass
            else:
                # Make new valid moves
                pass
            new_node = current_node.expand()
            current_node = new_node
        
        # Simulation
        result = mcts_simulation(current_node, me_board, opp_board, valid_mask)
        
        # Backpropagation
        current = current_node
        while current is not None:
            current.visits += 1
            current.wins += result
            current = current.parent
        
        iterations += 1
    
    # Choose best move based on visit count or win rate
    best_child = max(root.children, key=lambda c: c.visits)
    return best_child.move if best_child else (7, 7)

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    """Main policy function."""
    # Convert to standard format
    board_state = (me, opp, valid_mask)
    
    # Early win check
    for row in range(15):
        for col in range(15):
            if valid_mask[row][col]:
                # Check if this move creates a winning pattern (simplified)
                try_moves = [(row, col)]
                test_me = list(me) + try_moves
                # Very rough win pattern check for immediate win possibilities
                if evaluate_position(test_me, opp, row, col, valid_mask) >= 1000:
                    return (row, col)
    
    # Apply MCTS approach with time limit
    try:
        move = monte_carlo_tree_search(board_state, valid_mask)
        if valid_mask[move[0]][move[1]]:
            return move
    except:
        pass
    
    # Fallback to simple heuristic
    # Prioritize center of board and look for available valid moves
    center_row, center_col = 7, 7
    if valid_mask[center_row][center_col]:
        return (center_row, center_col)
    
    # Pick a random valid move
    valid_moves = []
    for r in range(15):
        for c in range(15):
            if valid_mask[r][c]:
                valid_moves.append((r, c))
    
    if valid_moves:
        return random.choice(valid_moves)
    
    # Should never happen, but for completeness
    return (7, 7)
