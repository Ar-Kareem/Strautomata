
import numpy as np
from collections import deque

def policy(board) -> str:
    board = np.array(board)
    
    def get_pieces(b, player):
        return list(zip(*np.where(b == player)))
    
    def count_components(b, player):
        pieces = set(get_pieces(b, player))
        if not pieces:
            return 0
        visited = set()
        components = 0
        for start in pieces:
            if start not in visited:
                components += 1
                queue = deque([start])
                while queue:
                    r, c = queue.popleft()
                    if (r, c) in visited:
                        continue
                    visited.add((r, c))
                    for dr in [-1, 0, 1]:
                        for dc in [-1, 0, 1]:
                            if dr == 0 and dc == 0:
                                continue
                            nr, nc = r + dr, c + dc
                            if (nr, nc) in pieces and (nr, nc) not in visited:
                                queue.append((nr, nc))
        return components
    
    def get_legal_moves(b, player):
        moves = []
        pieces = get_pieces(b, player)
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
        
        for r, c in pieces:
            for dr, dc in directions:
                # Count pieces in line
                count = 0
                if dr == 0:  # horizontal
                    count = np.count_nonzero(b[r, :])
                elif dc == 0:  # vertical
                    count = np.count_nonzero(b[:, c])
                else:  # diagonal
                    for i in range(-7, 8):
                        nr, nc = r + i * dr, c + i * dc
                        if 0 <= nr < 8 and 0 <= nc < 8 and b[nr, nc] != 0:
                            count += 1
                
                nr, nc = r + dr * count, c + dc * count
                if not (0 <= nr < 8 and 0 <= nc < 8):
                    continue
                if b[nr, nc] == player:
                    continue
                
                # Check path for enemy pieces
                valid = True
                for step in range(1, count):
                    sr, sc = r + dr * step, c + dc * step
                    if b[sr, sc] == -player:
                        valid = False
                        break
                if valid:
                    moves.append((r, c, nr, nc))
        return moves
    
    def evaluate(b):
        my_pieces = get_pieces(b, 1)
        opp_pieces = get_pieces(b, -1)
        
        if not my_pieces:
            return -10000
        if not opp_pieces:
            return 10000
        
        my_comp = count_components(b, 1)
        opp_comp = count_components(b, -1)
        
        if my_comp == 1:
            return 10000
        if opp_comp == 1:
            return -10000
        
        # Compactness
        def avg_dist(pieces):
            if len(pieces) <= 1:
                return 0
            total = 0
            for i, (r1, c1) in enumerate(pieces):
                for r2, c2 in pieces[i+1:]:
                    total += max(abs(r1-r2), abs(c1-c2))
            return total / (len(pieces) * (len(pieces) - 1) / 2)
        
        my_dist = avg_dist(my_pieces)
        opp_dist = avg_dist(opp_pieces)
        
        score = (opp_comp - my_comp) * 100
        score += (opp_dist - my_dist) * 5
        score += (len(opp_pieces) - len(my_pieces)) * 10
        
        return score
    
    def minimax(b, depth, alpha, beta, maximizing):
        player = 1 if maximizing else -1
        
        if depth == 0:
            return evaluate(b), None
        
        moves = get_legal_moves(b, player)
        if not moves:
            return evaluate(b), None
        
        best_move = moves[0]
        
        if maximizing:
            max_eval = -float('inf')
            for move in moves:
                r, c, nr, nc = move
                new_b = b.copy()
                new_b[r, c] = 0
                new_b[nr, nc] = player
                
                eval_score, _ = minimax(new_b, depth - 1, alpha, beta, False)
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = move
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval, best_move
        else:
            min_eval = float('inf')
            for move in moves:
                r, c, nr, nc = move
                new_b = b.copy()
                new_b[r, c] = 0
                new_b[nr, nc] = player
                
                eval_score, _ = minimax(new_b, depth - 1, alpha, beta, True)
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval, best_move
    
    moves = get_legal_moves(board, 1)
    if not moves:
        # Should not happen if called correctly
        pieces = get_pieces(board, 1)
        if pieces:
            r, c = pieces[0]
            return f"{r},{c}:{r},{c}"
    
    if len(moves) == 1:
        r, c, nr, nc = moves[0]
        return f"{r},{c}:{nr},{nc}"
    
    _, best_move = minimax(board, 3, -float('inf'), float('inf'), True)
    
    if best_move:
        r, c, nr, nc = best_move
        return f"{r},{c}:{nr},{nc}"
    
    r, c, nr, nc = moves[0]
    return f"{r},{c}:{nr},{nc}"
