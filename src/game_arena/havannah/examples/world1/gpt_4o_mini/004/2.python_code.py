
import numpy as np

def check_winner(stones, target_stone):
    # Function to check if target_stone (0 or 1) has made a winning structure
    # Identify win conditions: bridge, fork or ring.
    # Implementing this would be quite complex, so we will simplify
    # by checking basic connections in different directions.
    return False  # replace with actual win checking logic

def find_winning_move(me, valid_mask):
    # Check each possible move for a winning position
    for r, c in valid_mask:
        if valid_mask[r][c] and (r, c) not in me:
            # Check if placing a stone here gives an immediate win
            me.append((r, c))
            if check_winner(me, 0):
                me.remove((r, c))
                return (r, c)
            me.remove((r, c))
    return None

def block_opponents_move(opp, valid_mask):
    # If the opponent is about to win, block them
    for r, c in valid_mask:
        if valid_mask[r][c] and (r, c) not in opp:
            opp.append((r, c))
            if check_winner(opp, 1):
                opp.remove((r, c))
                return (r, c)
            opp.remove((r, c))
    return None

def evaluate_move(r, c, me, opp, valid_mask):
    # Here we could evaluate how good the move is based on future potential
    score = 0
    # Calculate the connections possible and return a score
    return score

def find_best_move(me, opp, valid_mask):
    best_move = None
    best_score = -1
    for r, c in valid_mask:
        if valid_mask[r][c] and (r, c) not in me and (r, c) not in opp:
            score = evaluate_move(r, c, me, opp, valid_mask)
            if score > best_score:
                best_score = score
                best_move = (r, c)
    return best_move

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    valid_positions = [(r, c) for r in range(15) for c in range(15) if valid_mask[r][c]]
    
    # Step 1: Check for winning move
    winning_move = find_winning_move(me, valid_positions)
    if winning_move:
        return winning_move
    
    # Step 2: Check if need to block opponent's winning move
    blocking_move = block_opponents_move(opp, valid_positions)
    if blocking_move:
        return blocking_move
    
    # Step 3: No immediate win or block, find best strategic move
    best_move = find_best_move(me, opp, valid_positions)
    
    return best_move if best_move else valid_positions[0]  # fallback to first valid position

