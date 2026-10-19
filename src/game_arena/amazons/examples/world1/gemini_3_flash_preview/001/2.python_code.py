
import numpy as np

def policy(board) -> str:
    # Directions: Horizontal, Vertical, Diagonal
    DIRECTIONS = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
    SIZE = 6

    def get_reachable(pos, current_board):
        reachable = []
        r, c = pos
        for dr, dc in DIRECTIONS:
            nr, nc = r + dr, c + dc
            while 0 <= nr < SIZE and 0 <= nc < SIZE and current_board[nr, nc] == 0:
                reachable.append((nr, nc))
                nr += dr
                nc += dc
        return reachable

    my_amazons = []
    opp_amazons = []
    for r in range(SIZE):
        for c in range(SIZE):
            if board[r, c] == 1:
                my_amazons.append((r, c))
            elif board[r, c] == 2:
                opp_amazons.append((r, c))

    best_move = None
    max_score = -float('inf')

    # Iterate through all my amazons
    for start_pos in my_amazons:
        # Possible landing spots
        for move_to in get_reachable(start_pos, board):
            # Temporarily update board to simulate the move
            board[start_pos] = 0
            
            # Possible arrow shots from move_to
            # Note: start_pos is now empty and available for the arrow
            for arrow_to in get_reachable(move_to, board):
                # Simple Heuristic: Count my mobility minus opponent mobility
                # To speed up, we look at local mobility around the landing spot
                
                # Mock place pieces to calculate mobility
                board[move_to] = 1
                board[arrow_to] = -1
                
                my_mobility = 0
                for m_pos in my_amazons:
                    # use actual current pos for this amazon, others as they are
                    p = move_to if m_pos == start_pos else m_pos
                    my_mobility += len(get_reachable(p, board))
                
                opp_mobility = 0
                for o_pos in opp_amazons:
                    opp_mobility += len(get_reachable(o_pos, board))
                
                score = my_mobility - opp_mobility
                
                if score > max_score:
                    max_score = score
                    best_move = f"{start_pos[0]},{start_pos[1]}:{move_to[0]},{move_to[1]}:{arrow_to[0]},{arrow_to[1]}"
                
                # Undo arrow
                board[arrow_to] = 0
            
            # Undo move
            board[move_to] = 0
            board[start_pos] = 1
            
            # Optimization: If we found a decent move, check time or return 
            # (Given 6x6, we can usually check most within 1s)

    if best_move:
        return best_move
    
    # Fallback to absolute first legal move found if heuristic fails
    for start_pos in my_amazons:
        moves = get_reachable(start_pos, board)
        if moves:
            m = moves[0]
            board[start_pos] = 0
            arrows = get_reachable(m, board)
            board[start_pos] = 1
            if arrows:
                return f"{start_pos[0]},{start_pos[1]}:{m[0]},{m[1]}:{arrows[0][0]},{arrows[0][1]}"

    return "" # Should not happen in valid state
