
import numpy as np

def get_legal_moves(board, player):
    moves = []
    player_positions = np.argwhere(board == player)
    
    # Directions for queen-like movement
    directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    
    for start_r, start_c in player_positions:
        for dr, dc in directions:
            for dist in range(1, 6):
                tr, tc = start_r + dr * dist, start_c + dc * dist
                if 0 <= tr < 6 and 0 <= tc < 6 and board[tr, tc] == 0:
                    # Temporary move to find arrow shots
                    board[start_r, start_c] = 0
                    board[tr, tc] = player
                    
                    for adr, adc in directions:
                        for adist in range(1, 6):
                            ar, ac = tr + adr * adist, tc + adc * adist
                            if 0 <= ar < 6 and 0 <= ac < 6 and board[ar, ac] == 0:
                                moves.append(((start_r, start_c), (tr, tc), (ar, ac)))
                            else:
                                break
                    # Backtrack
                    board[tr, tc] = 0
                    board[start_r, start_c] = player
                else:
                    break
    return moves

def evaluate(board, player):
    opp = 3 - player
    score = 0
    
    # 1. Mobility: Count available squares reachable in one queen move
    directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    
    def count_mobility(p):
        count = 0
        nodes = np.argwhere(board == p)
        for r, c in nodes:
            for dr, dc in directions:
                for d in range(1, 6):
                    nr, nc = r + dr * d, c + dc * d
                    if 0 <= nr < 6 and 0 <= nc < 6 and board[nr, nc] == 0:
                        count += 1
                    else:
                        break
        return count

    score += (count_mobility(player) - count_mobility(opp)) * 2
    
    # 2. Simple Centrality (Amazon positions)
    for r, c in np.argwhere(board == player):
        score += (2.5 - abs(r - 2.5)) + (2.5 - abs(c - 2.5))
        
    return score

def policy(board: np.ndarray) -> str:
    player = 1
    moves = get_legal_moves(board, player)
    
    if not moves:
        return "" # Should not happen based on rules

    best_score = -float('inf')
    best_move = moves[0]
    
    # Sort moves slightly to find good ones faster (optional for 1-ply)
    # We evaluate all moves due to 6x6 size and speed
    for start, to, arrow in moves:
        # Simulate
        board[start] = 0
        board[to] = player
        board[arrow] = -1
        
        score = evaluate(board, player)
        
        # Undo
        board[arrow] = 0
        board[to] = 0
        board[start] = player
        
        if score > best_score:
            best_score = score
            best_move = (start, to, arrow)
            
    s, t, a = best_move
    return f"{s[0]},{s[1]}:{t[0]},{t[1]}:{a[0]},{a[1]}"
