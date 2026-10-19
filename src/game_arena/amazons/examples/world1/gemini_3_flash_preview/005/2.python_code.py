
import numpy as np

def get_queen_moves(board, start_pos, ignore_pos=None):
    """Returns a list of all reachable squares for a queen from start_pos."""
    moves = []
    directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    r_start, c_start = start_pos
    
    for dr, dc in directions:
        for dist in range(1, 6):
            r, c = r_start + dr * dist, c_start + dc * dist
            if 0 <= r < 6 and 0 <= c < 6:
                if board[r, c] == 0 or (ignore_pos is not None and (r, c) == ignore_pos):
                    moves.append((r, c))
                else:
                    break
            else:
                break
    return moves

def evaluate(board):
    """Calculates mobility score: (my_moves - opponent_moves)."""
    my_score = 0
    opp_score = 0
    for r in range(6):
        for c in range(6):
            if board[r, c] == 1:
                my_score += len(get_queen_moves(board, (r, c)))
            elif board[r, c] == 2:
                opp_score += len(get_queen_moves(board, (r, c)))
    return my_score - opp_score

def policy(board) -> str:
    my_amazons = []
    for r in range(6):
        for c in range(6):
            if board[r, c] == 1:
                my_amazons.append((r, c))
                
    best_move = None
    best_score = -float('inf')
    
    # Iterate through possible moves
    possible_moves_found = []
    for start in my_amazons:
        destinations = get_queen_moves(board, start)
        for dest in destinations:
            # Temporarily move amazon
            old_val_start = board[start]
            board[start] = 0
            board[dest] = 1
            
            # Find arrow shots (can shot at 'start' because it's now empty)
            arrows = get_queen_moves(board, dest)
            
            # Simple heuristic: prioritize shooting at squares that reduce enemy mobility
            # To stay within 1s, we sample or pick high-impact shots
            for arrow in arrows:
                board[arrow] = -1
                
                # Evaluation (Mobility is key in Amazons)
                score = evaluate(board)
                
                # Tie-breaking/Heuristic: favor moving closer to center
                dist_to_center = abs(dest[0]-2.5) + abs(dest[1]-2.5)
                score -= dist_to_center * 0.1
                
                if score > best_score:
                    best_score = score
                    best_move = f"{start[0]},{start[1]}:{dest[0]},{dest[1]}:{arrow[0]},{arrow[1]}"
                
                board[arrow] = 0 # backtrack
            
            board[dest] = 0
            board[start] = 1 # backtrack
            
    # Fallback if no move found (should not happen if legal moves exist)
    if not best_move:
        for start in my_amazons:
            dests = get_queen_moves(board, start)
            if dests:
                d = dests[0]
                board[start] = 0
                board[d] = 1
                arrows = get_queen_moves(board, d)
                board[d] = 0
                board[start] = 1
                if arrows:
                    a = arrows[0]
                    return f"{start[0]},{start[1]}:{d[0]},{d[1]}:{a[0]},{a[1]}"

    return best_move
