
import numpy as np
from typing import List

def policy(you: List[int], opponent: List[int]) -> str:
    you_board = np.array(you).reshape(5, 6)
    opp_board = np.array(opponent).reshape(5, 6)
    
    directions = [('U', -1, 0), ('R', 0, 1), ('D', 1, 0), ('L', 0, -1)]
    legal_moves = []
    
    # Generate all legal moves
    for r in range(5):
        for c in range(6):
            if you_board[r, c] == 1:
                for dir_name, dr, dc in directions:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 5 and 0 <= nc < 6 and opp_board[nr, nc] == 1:
                        legal_moves.append((r, c, dir_name, nr, nc))
    
    # If no moves, return anything (should not happen as we lose)
    if not legal_moves:
        return "0,0,U"
    
    # Check for immediate win
    for r, c, dir_name, nr, nc in legal_moves:
        # Simulate the move
        new_you = you_board.copy()
        new_opp = opp_board.copy()
        new_you[r, c] = 0
        new_you[nr, nc] = 1
        new_opp[nr, nc] = 0
        
        # Check if opponent has any moves
        opp_has_move = False
        for rr in range(5):
            for cc in range(6):
                if new_opp[rr, cc] == 1:
                    for _, dr, dc in directions:
                        nrr, ncc = rr + dr, cc + dc
                        if 0 <= nrr < 5 and 0 <= ncc < 6 and new_you[nrr, ncc] == 1:
                            opp_has_move = True
                            break
                if opp_has_move:
                    break
            if opp_has_move:
                break
        
        if not opp_has_move:
            return f"{r},{c},{dir_name}"
    
    # Heuristic evaluation
    def count_mobility(y_board, o_board):
        count = 0
        for rr in range(5):
            for cc in range(6):
                if y_board[rr, cc] == 1:
                    for _, dr, dc in directions:
                        nrr, ncc = rr + dr, cc + dc
                        if 0 <= nrr < 5 and 0 <= ncc < 6 and o_board[nrr, ncc] == 1:
                            count += 1
        return count
    
    def positional_score(r, c):
        # Prefer center positions
        center_r, center_c = 2, 2.5
        return -(abs(r - center_r) + abs(c - center_c))
    
    def safety_score(y_board, o_board, r, c):
        # Count adjacent opponent pieces
        count = 0
        for _, dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 5 and 0 <= nc < 6 and o_board[nr, nc] == 1:
                count += 1
        return -count  # Prefer fewer adjacent opponents
    
    best_move = legal_moves[0]
    best_score = -float('inf')
    
    for r, c, dir_name, nr, nc in legal_moves:
        # Simulate move
        new_you = you_board.copy()
        new_opp = opp_board.copy()
        new_you[r, c] = 0
        new_you[nr, nc] = 1
        new_opp[nr, nc] = 0
        
        # Evaluate position
        our_mobility = count_mobility(new_you, new_opp)
        opp_mobility = count_mobility(new_opp, new_you)
        mobility_score = our_mobility - 0.5 * opp_mobility
        pos_score = positional_score(nr, nc)
        safety = safety_score(new_you, new_opp, nr, nc)
        
        total_score = mobility_score + 0.2 * pos_score + 0.3 * safety
        
        if total_score > best_score:
            best_score = total_score
            best_move = (r, c, dir_name, nr, nc)
    
    r, c, dir_name, _, _ = best_move
    return f"{r},{c},{dir_name}"
