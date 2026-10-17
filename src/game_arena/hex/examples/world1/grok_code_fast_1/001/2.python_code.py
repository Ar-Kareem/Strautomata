
from collections import deque
import random

def neighbors(i, j):
    dirs = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]
    n = []
    for di, dj in dirs:
        ni, nj = i + di, j + dj
        if 0 <= ni <= 10 and 0 <= nj <= 10:
            n.append((ni, nj))
    return n

def is_winner(board, color):
    if color == 'b':
        starts = [(0, j) for j in range(11) if (0, j) in board]
        is_target = lambda i, j: i == 10
    else:
        starts = [(i, 0) for i in range(11) if (i, 0) in board]
        is_target = lambda i, j: j == 10
    
    visited = set()
    queue = deque(starts)
    visited.update(starts)
    while queue:
        i, j = queue.popleft()
        if is_target(i, j):
            return True
        for ni, nj in neighbors(i, j):
            if (ni, nj) in board and (ni, nj) not in visited:
                visited.add((ni, nj))
                queue.append((ni, nj))
    return False

def policy(me, opp, color):
    all_cells = [(i, j) for i in range(11) for j in range(11)]
    occupied = set(me) | set(opp)
    legal = [c for c in all_cells if c not in occupied]
    opp_color = 'w' if color == 'b' else 'b'
    
    wins = {}
    N = 100  # Number of simulations per legal move
    empties_base = [c for c in all_cells if c not in occupied]
    
    for move in legal:
        w = 0
        for sim in range(N):
            sim_my = set(me) | {move}
            sim_opp = set(opp)
            sim_occ = occupied | {move}
            sim_empties = [c for c in empties_base if c != move and c not in sim_occ]  # Fresh empties excluding the move
            random.shuffle(sim_empties)
            turn = 'opp'  # Opponent's turn after my move
            for e in sim_empties:
                if turn == 'opp':
                    sim_opp.add(e)
                else:
                    sim_my.add(e)
                turn = 'me' if turn == 'opp' else 'opp'
            if is_winner(sim_my, color):
                w += 1
        wins[move] = w
    
    if not wins:
        # Fallback to random if no simulations, but shouldn't happen
        return random.choice(legal)
    
    best_move = max(wins, key=wins.get)
    return best_move
