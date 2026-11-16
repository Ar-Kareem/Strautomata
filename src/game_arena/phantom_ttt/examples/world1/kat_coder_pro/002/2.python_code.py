
import numpy as np
import random
import time
from collections import defaultdict

# Constants for the game
EMPTY = 0
PLAYER_X = 1
PLAYER_O = -1

# Lines to check for a win
LINES = [
    [(0,0), (0,1), (0,2)], # Top row
    [(1,0), (1,1), (1,2)], # Middle row
    [(2,0), (2,1), (2,2)], # Bottom row
    [(0,0), (1,0), (2,0)], # Left column
    [(0,1), (1,1), (2,1)], # Middle column
    [(0,2), (1,2), (2,2)], # Right column
    [(0,0), (1,1), (2,2)], # Main diagonal
    [(0,2), (1,1), (2,0)], # Anti-diagonal
]

class Node:
    def __init__(self, state, untried_actions, player=PLAYER_X):
        self.state = state  # 3x3 board
        self.untried_actions = untried_actions
        self.player = player
        self.children = []
        self.visits = 0
        self.wins = 0
        self.parent = None

    def uct_value(self, c=1.4):
        if self.visits == 0:
            return float('inf')
        return self.wins / self.visits + c * np.sqrt(np.log(self.parent.visits) / self.visits)

    def is_fully_expanded(self):
        return len(self.untried_actions) == 0

    def best_child(self, c=1.4):
        return max(self.children, key=lambda x: x.uct_value(c))

    def expand(self):
        action = self.untried_actions.pop()
        new_state = [row[:] for row in self.state]  # Deep copy
        row, col = action // 3, action % 3
        new_state[row][col] = self.player
        
        # Check if the game is over after this move
        if check_win(new_state, self.player) or len(get_legal_moves(new_state)) == 0:
            # If the game is over, we don't need to expand further
            child = Node(new_state, [], -self.player)
        else:
            child = Node(new_state, get_legal_moves(new_state), -self.player)
        
        child.parent = self
        self.children.append(child)
        return child

    def rollout(self):
        current_player = self.player
        state = [row[:] for row in self.state]  # Deep copy
        
        while True:
            legal_moves = get_legal_moves(state)
            if not legal_moves:
                return 0  # Draw
            
            # Randomly select a move
            action = random.choice(legal_moves)
            row, col = action // 3, action % 3
            state[row][col] = current_player
            
            if check_win(state, current_player):
                return 1 if current_player == PLAYER_X else -1
            
            current_player = -current_player

    def backpropagate(self, result):
        self.visits += 1
        self.wins += result
        if self.parent:
            self.parent.backpropagate(-result)

def get_legal_moves(state):
    """Get all legal moves (empty cells) from the current state."""
    moves = []
    for i in range(3):
        for j in range(3):
            if state[i][j] == EMPTY:
                moves.append(i * 3 + j)
    return moves

def check_win(state, player):
    """Check if the given player has won."""
    for line in LINES:
        if all(state[r][c] == player for r, c in line):
            return True
    return False

def is_game_over(state):
    """Check if the game is over (either won or draw)."""
    return check_win(state, PLAYER_X) or check_win(state, PLAYER_O) or len(get_legal_moves(state)) == 0

def select_move(board, legal_moves):
    # Convert board to state format
    state = [row[:] for row in board]
    
    # Filter out moves that are already ours
    filtered_moves = [move for move in legal_moves if state[move // 3][move % 3] != PLAYER_X]
    
    # If there's only one move left, take it
    if len(filtered_moves) == 1:
        return filtered_moves[0] // 3, filtered_moves[0] % 3
    
    # Check if there's a winning move
    for move in filtered_moves:
        row, col = move // 3, move % 3
        state[row][col] = PLAYER_X
        if check_win(state, PLAYER_X):
            # Reset the state
            state[row][col] = EMPTY
            return row, col
        state[row][col] = EMPTY
    
    # Run MCTS
    root = Node(state, filtered_moves)
    start_time = time.time()
    
    while time.time() - start_time < 0.9:  # Leave some time for other operations
        # Selection
        node = root
        while not node.is_fully_expanded() and node.children:
            node = node.best_child()
        
        # Expansion
        if not node.is_fully_expanded():
            node = node.expand()
        
        # Simulation
        result = node.rollout()
        
        # Backpropagation
        node.backpropagate(result)
    
    # Choose the best move
    best_move = max(root.children, key=lambda x: x.visits)
    
    # Convert action to row, col
    action = None
    for move in filtered_moves:
        row, col = move // 3, move % 3
        if best_move.state[row][col] == PLAYER_X:
            action = move
            break
    
    if action is None:
        # Fallback to a random move
        action = random.choice(filtered_moves)
    
    return action // 3, action % 3

def policy(board: list[list[int]], legal_moves: list[int]) -> int:
    # Convert board to match our internal representation
    # Note: The input board uses 1 for our marks and 0 for unknown
    # We'll convert it to use PLAYER_X for our marks and EMPTY for unknown
    state = []
    for row in board:
        new_row = []
        for cell in row:
            if cell == 1:
                new_row.append(PLAYER_X)
            else:
                new_row.append(EMPTY)
        state.append(new_row)
    
    # Get the best move
    row, col = select_move(state, legal_moves)
    
    # Convert to the expected output format
    return row, col
