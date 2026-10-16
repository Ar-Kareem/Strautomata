
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
                visited.add(start)
                while queue:
                    r, c = queue.popleft()
                    for dr in [-1, 0, 1]:
                        for dc in [-1, 0, 1]:
                            if dr == 0 and dc == 0:
                                continue
                            nr, nc = r + dr, c + dc
                            if (nr, nc) in pieces and (nr, nc) not in visited:
                                visited.add((nr, nc))
                                queue.append((nr, nc))
        return components
    
    def is_winner(b, player):
        pieces = get_pieces(b, player)
        if len(pieces) <= 1:
            return True
        return count_components(b, player) == 1
    
    def get_legal_moves(b, player):
        moves = []
        pieces = get_pieces(b, player)
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
        
        for r, c in pieces:
            for dr, dc in directions:
                # Count pieces along this line
                count = 0
                for i in range(-7, 8):
                    nr, nc = r + dr * i, c + dc * i
                    if 0 <= nr < 8 and 0 <= nc < 8:
                        if b[nr, nc] != 0:
                            count += 1
                
                # Target position
                tr, tc = r + dr * count, c + dc * count
                if not (0 <= tr < 8 and 0 <= tc < 8):
                    continue
                if b[tr, tc] == player:
                    continue
                
                # Check path - can't jump over enemy pieces
                blocked = False
                for step in range(1, count):
                    mr, mc = r + dr * step, c + dc * step
                    if b[mr, mc] == -player:
                        blocked = True
                        break
                
                if not blocked:
                    moves.append((r, c, tr, tc))
        return moves
    
    def evaluate(b):
        my_pieces = get_pieces(b, 1)
        opp_pieces = get_pieces(b, -1)
        
        if len(my_pieces) == 0:
            return -10000
        if len(opp_pieces) == 0:
            return 10000
        
        my_comps = count_components(b, 1)
        opp_comps = count_components(b, -1)
        
        if my_comps == 1:
            return 10000
        if opp_comps == 1:
            return -10000
        
        # Center of mass distance for my pieces
        my_cr = sum(p[0] for p in my_pieces) / len(my_pieces)
        my_cc = sum(p[1] for p in my_pieces) / len(my_pieces)
        my_dist = sum(abs(p[0] - my_cr) + abs(p[1] - my_cc) for p in my_pieces)
        
        opp_cr = sum(p[0] for p in opp_pieces) / len(opp_pieces)
        opp_cc = sum(p[1] for p in opp_pieces) / len(opp_pieces)
        opp_dist = sum(abs(p[0] - opp_cr) + abs(p[1] - opp_cc) for p in opp_pieces)
        
        score = (opp_comps - my_comps) * 100 - my_dist + opp_dist * 0.5
        return score
    
    def make_move(b, move, player):
        nb = b.copy()
        r, c, tr, tc = move
        nb[r, c] = 0
        nb[tr, tc] = player
        return nb
    
    def minimax(b, depth, alpha, beta, maximizing):
        player = 1 if maximizing else -1
        
        if is_winner(b, 1):
            return 10000 + depth, None
        if is_winner(b, -1):
            return -10000 - depth, None
        
        if depth == 0:
            return evaluate(b), None
        
        moves = get_legal_moves(b, player)
        if not moves:
            return evaluate(b), None
        
        best_move = moves[0]
        
        if maximizing:
            max_eval = -float('inf')
            for move in moves:
                nb = make_move(b, move, player)
                eval_score, _ = minimax(nb, depth - 1, alpha, beta, False)
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
                nb = make_move(b, move, player)
                eval_score, _ = minimax(nb, depth - 1, alpha, beta, True)
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval, best_move
    
    moves = get_legal_moves(board, 1)
    if not moves:
        # Should not happen in valid game state, but fallback
        pieces = get_pieces(board, 1)
        if pieces:
            return f"{pieces[0][0]},{pieces[0][1]}:{pieces[0][0]},{pieces[0][1]}"
    
    # Check for immediate wins
    for move in moves:
        nb = make_move(board, move, 1)
        if is_winner(nb, 1):
            return f"{move[0]},{move[1]}:{move[2]},{move[3]}"
    
    # Use minimax with depth 3
    _, best_move = minimax(board, 3, -float('inf'), float('inf'), True)
    
    if best_move is None:
        best_move = moves[0]
    
    return f"{best_move[0]},{best_move[1]}:{best_move[2]},{best_move[3]}"
