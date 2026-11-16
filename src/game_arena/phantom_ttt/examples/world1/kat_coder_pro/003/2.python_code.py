
import random
import numpy as np
from collections import defaultdict

def policy(board: list[list[int]], legal_moves: list[int]) -> int:
    """
    Phantom Tic Tac Toe policy using Monte Carlo simulation.
    
    Args:
        board: 3x3 list of lists where 1 indicates confirmed player marks, 0 indicates uncertainty
        legal_moves: list of valid move indices (0-8)
        
    Returns:
        Move index (0-8) as integer
    """
    
    def index_to_coords(idx):
        return idx // 3, idx % 3
    
    def coords_to_index(r, c):
        return r * 3 + c
    
    def is_winning_state(b):
        """Check if board has a winning line for either player"""
        # Check rows
        for r in range(3):
            if all(b[r][c] == 1 for c in range(3)):
                return True
        # Check columns
        for c in range(3):
            if all(b[r][c] == 1 for r in range(3)):
                return True
        # Check diagonals
        if all(b[i][i] == 1 for i in range(3)):
            return True
        if all(b[i][2-i] == 1 for i in range(3)):
            return True
        return False
    
    def get_possible_opponent_states(board):
        """Generate possible opponent configurations consistent with current board"""
        # Find all cells that are not confirmed as ours
        uncertain_cells = []
        for r in range(3):
            for c in range(3):
                if board[r][c] == 0:
                    uncertain_cells.append((r, c))
        
        # For Monte Carlo, we'll sample a subset of possible opponent configurations
        # This is a simplified approach due to time constraints
        samples = []
        for _ in range(50):  # Limit samples for performance
            # Randomly assign some uncertain cells to opponent
            sample_board = [row[:] for row in board]
            for r, c in uncertain_cells:
                # 30% chance opponent has this cell (heuristic)
                if random.random() < 0.3:
                    sample_board[r][c] = -1  # Mark as opponent
            samples.append(sample_board)
        
        return samples
    
    def simulate_game(board, move_idx):
        """Simulate a game starting from board after making move_idx"""
        # Copy board
        sim_board = [row[:] for row in board]
        
        # Make our move
        r, c = index_to_coords(move_idx)
        if sim_board[r][c] == 0:  # Only place if not already ours
            sim_board[r][c] = 1
        
        # Check immediate win
        if is_winning_state(sim_board):
            return 1.0  # Win
        
        # Simple rollout simulation (random moves)
        current_player = -1  # Opponent's turn
        empty_cells = []
        for r in range(3):
            for c in range(3):
                if sim_board[r][c] == 0:
                    empty_cells.append((r, c))
        
        random.shuffle(empty_cells)
        
        for r, c in empty_cells:
            if current_player == 1:  # Our turn
                # Try to win or block opponent
                if random.random() < 0.7:  # 70% chance to play smart
                    # Check if we can win
                    temp_board = [row[:] for row in sim_board]
                    temp_board[r][c] = 1
                    if is_winning_state(temp_board):
                        sim_board[r][c] = 1
                        return 1.0
                    # Check if opponent can win next turn and block
                    for r2 in range(3):
                        for c2 in range(3):
                            if sim_board[r2][c2] == 0:
                                temp_board[r2][c2] = -1
                                if is_winning_state(temp_board):
                                    sim_board[r2][c2] = 1  # Block
                                    break
                                temp_board[r2][c2] = 0
                else:  # Random move
                    sim_board[r][c] = 1
            else:  # Opponent's turn
                # Random opponent move
                sim_board[r][c] = -1
            
            # Check win for current player
            if is_winning_state(sim_board):
                return 1.0 if current_player == 1 else 0.0
            
            current_player *= -1
        
        return 0.5  # Draw
    
    # Evaluate each legal move
    move_scores = defaultdict(float)
    
    # Generate possible opponent configurations
    opponent_states = get_possible_opponent_states(board)
    
    # Evaluate each move across opponent configurations
    for move_idx in legal_moves:
        total_score = 0.0
        
        # Test against each possible opponent state
        for opp_board in opponent_states:
            # Run simulations for this move
            for _ in range(20):  # Limit simulations per move for performance
                score = simulate_game(opp_board, move_idx)
                total_score += score
        
        move_scores[move_idx] = total_score
    
    # Choose best move
    best_move = max(legal_moves, key=lambda x: move_scores[x])
    
    return best_move
