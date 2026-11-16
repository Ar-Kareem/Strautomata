
import numpy as np

DIRECTIONS = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
BOARD_SIZE = 6
OPPONENT = 2
ME = 1
EMPTY = 0
ARROW = -1

def is_on_board(r, c):
    return 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE

def get_reachable_squares(board, r, c):
    squares = []
    for dr, dc in DIRECTIONS:
        nr, nc = r + dr, c + dc
        while is_on_board(nr, nc) and board[nr, nc] == EMPTY:
            squares.append((nr, nc))
            nr += dr
            nc += dc
    return squares

def count_reachable_squares(board, r, c):
    count = 0
    for dr, dc in DIRECTIONS:
        nr, nc = r + dr, c + dc
        while is_on_board(nr, nc) and board[nr, nc] == EMPTY:
            count += 1
            nr += dr
            nc += dc
    return count

def count_reachable_from_pos(board, pos):
    count = 0
    for dr, dc in DIRECTIONS:
        nr, nc = pos[0] + dr, pos[1] + dc
        while is_on_board(nr, nc) and board[nr, nc] == EMPTY:
            count += 1
            nr += dr
            nc += dc
    return count

def policy(board) -> str:
    my_amazons = []
    opp_amazons = []
    
    # Identify positions
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r, c] == ME:
                my_amazons.append((r, c))
            elif board[r, c] == OPPONENT:
                opp_amazons.append((r, c))

    best_move = None
    best_score = -float('inf')
    
    # Prioritize capturing opponent amazon
    # If I can move to an opponent's position (should not happen in standard rules as it's occupied),
    # but more likely, if I can trap them.
    # In standard Amazons, you cannot land on an opponent.
    
    # Strategy:
    # 1. Maximize my future mobility.
    # 2. Minimize opponent's future mobility.
    # 3. If I can block an opponent's queen line or restrict them significantly, do it.
    
    # Since the opponent has 2 amazons, let's see if we can restrict them.
    # We check if we can move such that we block their paths.
    
    # Let's calculate opponent's current mobility to evaluate cuts
    # This is expensive (O(N^3)) but acceptable for 6x6 within 1s.
    
    # We will iterate through all my amazons and all their reachable moves
    for my_pos in my_amazons:
        reachable_moves = get_reachable_squares(board, my_pos[0], my_pos[1])
        for move_to in reachable_moves:
            # Simulate move
            board_sim = board.copy()
            board_sim[my_pos] = EMPTY
            board_sim[move_to] = ME
            
            # Now check all possible arrow shots from move_to
            arrow_targets = get_reachable_squares(board_sim, move_to[0], move_to[1])
            
            # Optimization: If we have many moves, sample the best few to avoid TLE
            # But for 6x6, total nodes are limited.
            
            for arrow in arrow_targets:
                # Simulate arrow
                board_sim[arrow] = ARROW
                
                # Calculate Score
                # 1. My mobility
                # 2. Opponent mobility
                # 3. Add bonus if opponent is trapped (mobility 0)
                
                my_mobility_after = 0
                # Calculate my mobility (excluding the moved queen)
                my_amazons_after = [p for p in my_amazons if p != my_pos] + [move_to]
                for p in my_amazons_after:
                    my_mobility_after += count_reachable_from_pos(board_sim, p)
                
                opp_mobility_after = 0
                opp_trapped = 0
                for opp in opp_amazons:
                    mob = count_reachable_from_pos(board_sim, opp)
                    opp_mobility_after += mob
                    if mob == 0:
                        opp_trapped += 1
                
                # Score components
                # High weight on trapping opponent (win condition)
                # Medium weight on reducing opponent mobility
                # Low weight on maintaining my mobility
                
                score = 0
                score += opp_trapped * 10000  # Huge bonus for trapping
                score -= opp_mobility_after * 10 # Bonus for reducing opp mobility
                score += my_mobility_after * 1  # Keep some mobility
                
                # Heuristic: Bonus for moving to center (usually good)
                dist_from_center = abs(move_to[0] - 2.5) + abs(move_to[1] - 2.5)
                score -= dist_from_center * 0.1
                
                if score > best_score:
                    best_score = score
                    best_move = (my_pos, move_to, arrow)
                
                # Revert arrow
                board_sim[arrow] = EMPTY

    if best_move:
        return f"{best_move[0][0]},{best_move[0][1]}:{best_move[1][0]},{best_move[1][1]}:{best_move[2][0]},{best_move[2][1]}"
    
    # Fallback if something goes wrong (should not happen if logic is correct and moves exist)
    # Try to find any legal move
    for my_pos in my_amazons:
        reachable_moves = get_reachable_squares(board, my_pos[0], my_pos[1])
        for move_to in reachable_moves:
            board_sim = board.copy()
            board_sim[my_pos] = EMPTY
            board_sim[move_to] = ME
            arrow_targets = get_reachable_squares(board_sim, move_to[0], move_to[1])
            for arrow in arrow_targets:
                return f"{my_pos[0]},{my_pos[1]}:{move_to[0]},{move_to[1]}:{arrow[0]},{arrow[1]}"
    
    # If no moves found (should be caught by environment but just in case)
    return ""

