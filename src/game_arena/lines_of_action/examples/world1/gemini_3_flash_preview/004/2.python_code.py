
import collections
import time

def policy(board) -> str:
    start_time = time.time()
    
    def get_piece_count(b, r, c, dr, dc):
        count = 0
        # Check forward
        tr, tc = r, c
        while 0 <= tr < 8 and 0 <= tc < 8:
            if b[tr][tc] != 0: count += 1
            tr += dr
            tc += dc
        # Check backward
        tr, tc = r - dr, c - dc
        while 0 <= tr < 8 and 0 <= tc < 8:
            if b[tr][tc] != 0: count += 1
            tr -= dr
            tc -= dc
        return count

    def get_legal_moves(b, player):
        moves = []
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        for r in range(8):
            for c in range(8):
                if b[r][c] == player:
                    for dr, dc in directions:
                        dist = get_piece_count(b, r, c, dr, dc)
                        for s in [1, -1]:
                            nr, nc = r + s * dr * dist, c + s * dc * dist
                            if 0 <= nr < 8 and 0 <= nc < 8:
                                if b[nr][nc] == player: continue
                                # Check for enemy jump
                                blocked = False
                                for step in range(1, dist):
                                    ir, ic = r + s * dr * step, c + s * dc * step
                                    if b[ir][ic] == -player:
                                        blocked = True
                                        break
                                if not blocked:
                                    moves.append(((r, c), (nr, nc)))
        return moves

    def count_groups(b, player):
        visited = set()
        pieces = [(r, c) for r in range(8) for c in range(8) if b[r][c] == player]
        if not pieces: return 0
        groups = 0
        for r, c in pieces:
            if (r, c) not in visited:
                groups += 1
                q = collections.deque([(r, c)])
                visited.add((r, c))
                while q:
                    curr_r, curr_c = q.popleft()
                    for dr in [-1, 0, 1]:
                        for dc in [-1, 0, 1]:
                            nr, nc = curr_r + dr, curr_c + dc
                            if 0 <= nr < 8 and 0 <= nc < 8 and b[nr][nc] == player and (nr, nc) not in visited:
                                visited.add((nr, nc))
                                q.append((nr, nc))
        return groups

    def evaluate(b):
        p1_groups = count_groups(b, 1)
        p2_groups = count_groups(b, -1)
        
        if p1_groups == 1: return 10000
        if p2_groups == 1: return -10000
        
        score = 0
        # Penalize having many groups
        score -= p1_groups * 50
        score += p2_groups * 50
        
        # Centralization and piece count
        for r in range(8):
            for c in range(8):
                if b[r][c] == 1:
                    score += (4 - abs(3.5 - r)) + (4 - abs(3.5 - c))
                    score += 10
                elif b[r][c] == -1:
                    score -= (4 - abs(3.5 - r)) + (4 - abs(3.5 - c))
                    score -= 10
        return score

    def apply_move(b, move):
        (fr, fc), (tr, tc) = move
        new_board = [row[:] for row in b]
        new_board[tr][tc] = new_board[fr][fc]
        new_board[fr][fc] = 0
        return new_board

    best_move = None
    legal_moves = get_legal_moves(board, 1)
    if not legal_moves: return "" # Should not happen in LOA

    # Simple Iterative Deepening / Fixed Depth
    best_val = -float('inf')
    
    # Sort moves by a simple heuristic to improve pruning (captures first)
    legal_moves.sort(key=lambda m: abs(board[m[1][0]][m[1][1]]), reverse=True)

    def alphabeta(b, depth, alpha, beta, player):
        if depth == 0:
            return evaluate(b) * player
        
        moves = get_legal_moves(b, player)
        if not moves: # No moves or one piece left (technically connected)
            return evaluate(b) * player
        
        max_eval = -float('inf')
        for m in moves:
            nb = apply_move(b, m)
            # Terminal check
            if count_groups(nb, player) == 1:
                return 10000 # Depth reward could go here
            
            val = -alphabeta(nb, depth - 1, -beta, -alpha, -player)
            max_eval = max(max_eval, val)
            alpha = max(alpha, val)
            if beta <= alpha:
                break
        return max_eval

    # Depth 2 is safe for 1s.
    for m in legal_moves:
        nb = apply_move(board, m)
        if count_groups(nb, 1) == 1:
            best_move = m
            break
        val = -alphabeta(nb, 2, -float('inf'), float('inf'), -1)
        if val > best_val:
            best_val = val
            best_move = m
            
    if not best_move:
        best_move = legal_moves[0]
        
    return f"{best_move[0][0]},{best_move[0][1]}:{best_move[1][0]},{best_move[1][1]}"
