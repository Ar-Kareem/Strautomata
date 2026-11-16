import numpy as np
import collections

def get_moves(board, player):
    moves = []
    player_pieces = []
    for r in range(8):
        for c in range(8):
            if board[r][c] == player:
                player_pieces.append((r, c))

    directions = [(0, 1), (1, 0), (1, 1), (1, -1), (0, -1), (-1, 0), (-1, -1), (-1, 1)]

    for r, c in player_pieces:
        for dr, dc in directions:
            # Calculate total pieces in this line
            count = 0
            # Check both directions along the line
            for step in range(-7, 8):
                nr, nc = r + dr * step, c + dc * step
                if 0 <= nr < 8 and 0 <= nc < 8:
                    if board[nr][nc] != 0:
                        count += 1
            
            # Target square
            tr, tc = r + dr * count, c + dc * count
            
            if 0 <= tr < 8 and 0 <= tc < 8:
                # Rule: Cannot land on own piece
                if board[tr][tc] == player:
                    continue
                
                # Rule: Cannot jump over opponent's piece
                blocked = False
                for step in range(1, count):
                    mr, mc = r + dr * step, c + dc * step
                    if board[mr][mc] == -player:
                        blocked = True
                        break
                
                if not blocked:
                    moves.append(f"{r},{c}:{tr},{tc}")
    return moves

def count_components(board, player):
    pieces = []
    for r in range(8):
        for c in range(8):
            if board[r][c] == player:
                pieces.append((r, c))
    
    if not pieces: return 0
    
    visited = set()
    components = 0
    for p in pieces:
        if p not in visited:
            components += 1
            queue = collections.deque([p])
            visited.add(p)
            while queue:
                r, c = queue.popleft()
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        if dr == 0 and dc == 0: continue
                        nr, nc = r + dr, c + dc
                        if (nr, nc) in pieces and (nr, nc) not in visited:
                            visited.add((nr, nc))
                            queue.append((nr, nc))
    return components

def evaluate(board):
    # My pieces are 1, Opponent is -1
    my_pieces = []
    opp_pieces = []
    for r in range(8):
        for c in range(8):
            if board[r][c] == 1:
                my_pieces.append((r, c))
            elif board[r][c] == -1:
                opp_pieces.append((r, c))
                
    if not my_pieces: return -10000
    if not opp_pieces: return 10000
    
    my_comps = count_components(board, 1)
    opp_comps = count_components(board, -1)
    
    if my_comps == 1: return 9000
    if opp_comps == 1: return -9000

    # Centralization: Reward pieces near middle
    center_score = 0
    for r, c in my_pieces:
        center_score += (3.5 - abs(r - 3.5)) + (3.5 - abs(c - 3.5))
    
    for r, c in opp_pieces:
        center_score -= (3.5 - abs(r - 3.5)) + (3.5 - abs(c - 3.5))

    # Concentration: Distance from center of mass
    def get_concentration(pts):
        if not pts: return 0
        mr = sum(p[0] for p in pts) / len(pts)
        mc = sum(p[1] for p in pts) / len(pts)
        return sum(abs(p[0]-mr) + abs(p[1]-mc) for p in pts)

    my_conc = get_concentration(my_pieces)
    opp_conc = get_concentration(opp_pieces)

    score = 0
    score -= my_comps * 100
    score += opp_comps * 100
    score += center_score * 5
    score -= my_conc * 2
    score += opp_conc * 2
    score += (len(my_pieces) - len(opp_pieces)) * 10
    
    return score

def apply_move(board, move_str, player):
    new_board = [row[:] for row in board]
    start, end = move_str.split(':')
    r1, c1 = map(int, start.split(','))
    r2, c2 = map(int, end.split(','))
    new_board[r2][c2] = player
    new_board[r1][c1] = 0
    return new_board

def policy(board) -> str:
    moves = get_moves(board, 1)
    if not moves:
        return "" # Should not happen in LOA if game not over

    best_move = moves[0]
    best_eval = -float('inf')
    
    # Simple 1-depth search with sorting for "smartness"
    # Given the complexity of connectivity checks, 1-2 depth is safe for 1s.
    for m in moves:
        temp_board = apply_move(board, m, 1)
        
        # Lookahead: simulate opponent's best response (greedy)
        opp_moves = get_moves(temp_board, -1)
        if not opp_moves:
            score = 10000
        else:
            # Standard Eval
            score = evaluate(temp_board)
            
            # Simple Minimax-lite: deduct points if opponent can win or improve
            # To stay within 1s, we sample or just use eval.
            
        if score > best_eval:
            best_eval = score
            best_move = m
            
    return best_move
