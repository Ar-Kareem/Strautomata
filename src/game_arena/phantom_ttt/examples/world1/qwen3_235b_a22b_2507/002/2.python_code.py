
import numpy as np
import random
from typing import List, Tuple

def policy(board: List[List[int]], legal_moves: List[int]) -> Tuple[int, int]:
    # Convert to numpy array for easier manipulation
    board_arr = np.array(board)
    
    # Map from 0-8 to (row, col)
    def to_move(action: int) -> Tuple[int, int]:
        return (action // 3, action % 3)
    
    def to_action(row: int, col: int) -> int:
        return row * 3 + col
    
    # Get current confirmed marks (only 1s are ours)
    my_marks = np.where(board_arr == 1)
    my_positions = list(zip(my_marks[0], my_marks[1]))
    
    # Prefer moves that are not already ours
    unowned_moves = [a for a in legal_moves if board_arr[a//3][a%3] != 1]
    if not unowned_moves:
        unowned_moves = legal_moves  # Fallback
    
    # If only one legal move, take it
    if len(unowned_moves) == 1:
        return to_move(unowned_moves[0])
    
    # We don't observe opponent moves, but failed attempts reveal opponent cells
    # However, failure info is not directly passed — so we *cannot* infer opponent marks
    # Hence, we assume any 0-cell *could* be opponent or empty
    # But: we know that if we ever tried a move and failed, it must be opponent
    # However, failed attempts are not recorded in board or legal_moves in this API
    # So we must rely only on current board and legal_moves
    
    # We will use a lightweight MCTS-inspired rollout with 1000 samples
    move_scores = {}
    n_samples = 1000
    
    # Lines to check for win
    lines = [
        [(0,0), (0,1), (0,2)],
        [(1,0), (1,1), (1,2)],
        [(2,0), (2,1), (2,2)],
        [(0,0), (1,0), (2,0)],
        [(0,1), (1,1), (2,1)],
        [(0,2), (1,2), (2,2)],
        [(0,0), (1,1), (2,2)],
        [(0,2), (1,1), (2,0)]
    ]
    
    def is_win(marks: List[Tuple[int,int]]) -> bool:
        mark_set = set(marks)
        for line in lines:
            if all(pos in mark_set for pos in line):
                return True
        return False
    
    for action in unowned_moves:
        row, col = to_move(action)
        win_count = 0
        
        for _ in range(n_samples):
            # Sample a possible full board
            # Start with our known marks
            my_cells = my_positions + [(row, col)]  # Assume we place here
            # Opponent cells: any 0 not in my_cells could be opponent or empty
            empty_slots = []
            opp_cells = []
            for r in range(3):
                for c in range(3):
                    if board_arr[r][c] == 1:  # Already ours
                        if (r,c) not in my_cells:
                            my_cells.append((r,c))
                    elif (r,c) == (row,col):
                        continue  # We are placing here
                    else:
                        empty_slots.append((r,c))
            
            # Randomly assign half of empty slots to opponent (simplified model)
            # But opponent has placed same number of marks as us, minus one (since we just moved)
            opp_mark_count = len(my_cells) - 1
            opp_existing = 0
            # We don't know how many opponent marks exist — assume same as ours before this move
            # So after our move, opponent has len(my_positions) marks
            opp_target = len(my_positions)
            
            # Sample opponent positions from empty slots
            if len(empty_slots) <= opp_target:
                sampled_opp = empty_slots
            else:
                sampled_opp = random.sample(empty_slots, opp_target)
            
            opp_cells = sampled_opp
            
            # Check if we win
            if is_win(my_cells):
                # But only if not blocked by opponent having taken a cell in the line?
                # Actually, even if opponent has marks, we win if our line is complete
                win_count += 1
            else:
                # Check if opponent already has a completed line — then this state is invalid
                # But in valid game, opponent cannot have already won, since game would have ended
                # So skip check
                pass

        move_scores[action] = win_count / n_samples
    
    # Also, encourage blocking opponent threats
    # But we don't observe opponent, so instead: prefer moves that appear in many possible winning lines
    # Bonus for center and corners
    heuristic_bonus = {
        0: 0.05, 1: 0.02, 2: 0.05,
        3: 0.02, 4: 0.08, 5: 0.02,
        6: 0.05, 7: 0.02, 8: 0.05
    }
    
    # Combine scores
    final_scores = {a: s + heuristic_bonus[a] for a, s in move_scores.items()}
    
    # Choose the move with highest score
    best_action = max(final_scores, key=final_scores.get)
    
    return to_move(best_action)
