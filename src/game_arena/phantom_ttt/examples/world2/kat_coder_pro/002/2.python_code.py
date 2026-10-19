
import random
import math
import time
from typing import List, Tuple, Optional, Set, Dict

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Monte Carlo Tree Search policy for Phantom Tic Tac Toe.
    
    Args:
        board: 3x3 list where 1 indicates a cell where we have successfully placed a mark,
               0 indicates a cell that is not confirmed to be ours.
    
    Returns:
        A tuple (row, col) representing the chosen move.
    """
    
    # Constants
    SIMULATION_TIME_LIMIT = 0.95  # seconds
    EXPLORATION_CONSTANT = 1.4
    
    # Game state representation
    class GameState:
        def __init__(self, our_board: List[List[int]]):
            # our_board: 3x3 with 1 for our confirmed marks, 0 for unconfirmed
            self.our_board = [row[:] for row in our_board]
            self.move_history = []  # Track moves to handle turn order
            self.is_our_turn = True  # We always start as our turn in this context
            
        def get_possible_moves(self) -> List[Tuple[int, int]]:
            """Get all possible moves, prioritizing unconfirmed cells."""
            moves = []
            for r in range(3):
                for c in range(3):
                    # Don't place on cells already confirmed as ours
                    if self.our_board[r][c] != 1:
                        moves.append((r, c))
            return moves
            
        def is_terminal(self) -> bool:
            """Check if the game is over."""
            # Check rows, columns, and diagonals for a win
            for i in range(3):
                if self.check_line([(i, 0), (i, 1), (i, 2)]) or \
                   self.check_line([(0, i), (1, i), (2, i)]):
                    return True
            
            # Check diagonals
            if self.check_line([(0, 0), (1, 1), (2, 2)]) or \
               self.check_line([(0, 2), (1, 1), (2, 0)]):
                return True
                
            # Check if board is full (draw)
            if len(self.get_possible_moves()) == 0:
                return True
                
            return False
            
        def check_line(self, positions: List[Tuple[int, int]]) -> bool:
            """Check if all positions in a line are confirmed as ours."""
            return all(self.our_board[r][c] == 1 for r, c in positions)
            
        def make_move(self, move: Tuple[int, int]) -> 'GameState':
            """Make a move and return new state."""
            new_state = GameState(self.our_board)
            new_state.move_history = self.move_history + [move]
            r, c = move
            
            # In Phantom Tic Tac Toe, we attempt to place but might fail if occupied
            # For simulation purposes, we'll assume success for our moves
            new_state.our_board[r][c] = 1  # Assume we successfully placed here
            
            return new_state
            
        def get_random_opponent_board(self) -> List[List[int]]:
            """
            Generate a random opponent board consistent with our observations.
            This represents the uncertainty in Phantom Tic Tac Toe.
            """
            # Start with our board, then randomly place opponent marks
            opponent_board = [row[:] for row in self.our_board]
            
            # Get unconfirmed cells
            unconfirmed_cells = []
            for r in range(3):
                for c in range(3):
                    if opponent_board[r][c] == 0:
                        unconfirmed_cells.append((r, c))
            
            # Randomly place opponent marks (assume opponent has played roughly half as many moves as us)
            # This is a simplification for the simulation
            random.shuffle(unconfirmed_cells)
            opponent_moves = min(len(self.move_history) // 2, len(unconfirmed_cells))
            
            for i in range(opponent_moves):
                r, c = unconfirmed_cells[i]
                opponent_board[r][c] = -1  # Opponent's mark
                
            return opponent_board
            
        def evaluate(self) -> float:
            """
            Evaluate the current board state for our player.
            Returns a value between 0 and 1, where 1 is a certain win.
            """
            # Count our potential winning lines
            our_lines = 0
            total_lines = 8  # 3 rows + 3 cols + 2 diagonals
            
            # Check rows
            for i in range(3):
                if all(self.our_board[i][j] == 1 for j in range(3)):
                    return 1.0  # Win
                elif all(self.our_board[i][j] != 0 for j in range(3)):
                    our_lines += 1
                    
            # Check columns
            for j in range(3):
                if all(self.our_board[i][j] == 1 for i in range(3)):
                    return 1.0  # Win
                elif all(self.our_board[i][j] != 0 for i in range(3)):
                    our_lines += 1
                    
            # Check diagonals
            if all(self.our_board[i][i] == 1 for i in range(3)):
                return 1.0  # Win
            elif all(self.our_board[i][i] != 0 for i in range(3)):
                our_lines += 1
                
            if all(self.our_board[i][2-i] == 1 for i in range(3)):
                return 1.0  # Win
            elif all(self.our_board[i][2-i] != 0 for i in range(3)):
                our_lines += 1
                
            # Check for opponent win (random opponent board)
            opponent_board = self.get_random_opponent_board()
            for i in range(3):
                if all(opponent_board[i][j] == -1 for j in range(3)):
                    return 0.0  # Loss
            for j in range(3):
                if all(opponent_board[i][j] == -1 for i in range(3)):
                    return 0.0  # Loss
            if all(opponent_board[i][i] == -1 for i in range(3)):
                return 0.0  # Loss
            if all(opponent_board[i][2-i] == -1 for i in range(3)):
                return 0.0  # Loss
                
            return our_lines / total_lines
            
    # Monte Carlo Tree Search Node
    class MCTSNode:
        def __init__(self, state: GameState, parent: Optional['MCTSNode'] = None, move: Optional[Tuple[int, int]] = None):
            self.state = state
            self.parent = parent
            self.move = move
            self.children: List['MCTSNode'] = []
            self.visits = 0
            self.wins = 0
            
        def is_fully_expanded(self) -> bool:
            return len(self.children) == len(self.state.get_possible_moves())
            
        def select_child(self) -> 'MCTSNode':
            """Select child using UCB1 formula."""
            log_parent_visits = math.log(self.visits)
            best_score = -float('inf')
            best_child = None
            
            for child in self.children:
                if child.visits == 0:
                    return child
                    
                # UCB1 formula
                exploit = child.wins / child.visits
                explore = EXPLORATION_CONSTANT * math.sqrt(log_parent_visits / child.visits)
                score = exploit + explore
                
                if score > best_score:
                    best_score = score
                    best_child = child
                    
            return best_child
            
        def expand(self) -> 'MCTSNode':
            """Expand node by adding a child."""
            possible_moves = self.state.get_possible_moves()
            existing_moves = {child.move for child in self.children}
            
            # Find a move that hasn't been tried yet
            for move in possible_moves:
                if move not in existing_moves:
                    new_state = self.state.make_move(move)
                    child = MCTSNode(new_state, self, move)
                    self.children.append(child)
                    return child
                    
            return None
            
        def backpropagate(self, result: float):
            """Backpropagate result up the tree."""
            self.visits += 1
            self.wins += result
            if self.parent:
                # Invert result for parent (opponent's perspective)
                self.parent.backpropagate(1 - result)
                
    # MCTS main loop
    root = MCTSNode(GameState(board))
    start_time = time.time()
    
    simulation_count = 0
    
    while time.time() - start_time < SIMULATION_TIME_LIMIT:
        # Selection
        node = root
        while not node.state.is_terminal() and node.is_fully_expanded():
            node = node.select_child()
            
        # Expansion
        if not node.state.is_terminal() and not node.is_fully_expanded():
            node = node.expand()
            
        # Simulation
        if node:
            # Use heuristic evaluation for faster simulation
            result = node.state.evaluate()
            
            # Backpropagation
            node.backpropagate(result)
            
        simulation_count += 1
        
    # Choose the best move
    best_move = None
    best_ratio = -1
    
    for child in root.children:
        if child.visits > 0:
            ratio = child.wins / child.visits
            if ratio > best_ratio:
                best_ratio = ratio
                best_move = child.move
                
    # Fallback if no move found (shouldn't happen)
    if best_move is None:
        possible_moves = root.state.get_possible_moves()
        if possible_moves:
            best_move = possible_moves[0]
        else:
            # If no moves available, return a random move (shouldn't happen in valid game)
            best_move = (0, 0)
            
    return best_move
