
import numpy as np

def get_legal_moves(you, opponent):
    dirs = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    legal = []
    for r in range(8):
        for c in range(8):
            if you[r][c] != 0 or opponent[r][c] != 0:
                continue
            for dr, dc in dirs:
                br, bc = r + dr, c + dc
                if not (0 <= br < 8 and 0 <= bc < 8):
                    continue
                if opponent[br][bc] != 1:
                    continue
                nr, nc = br + dr, bc + dc
                valid = False
                while True:
                    if not (0 <= nr < 8 and 0 <= nc < 8):
                        break
                    if you[nr][nc] == 1:
                        valid = True
                        break
                    if you[nr][nc] == 0:
                        break
                    nr += dr
                    nc += dc
                if valid:
                    legal.append((r, c))
                    break
    return list(set(legal))

def get_flips(you, opponent, r, c):
    flips = 0
    dirs = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    for dr, dc in dirs:
        nr, nc = r + dr, c + dc
        if not (0 <= nr < 8 and 0 <= nc < 8):
            continue
        if opponent[nr][nc] != 1:
            continue
        temp_flips = 0
        cur_r, cur_c = nr, nc
        valid = False
        while True:
            if not (0 <= nr < 8 and 0 <= nc < 8):
                break
            if you[nr][nc] == 1:
                valid = True
                break
            if you[nr][nc] == 0:
                break
            cur_r += dr
            cur_c += dc
        if valid:
            flip_count = 0
            cur_r, cur_c = r + dr, c + dc
            while 0 <= cur_r < 8 and 0 <= cur_c < 8 and opponent[cur_r][cur_c] == 1:
                flip_count += 1
                cur_r += dr
                cur_c += dc
            flips += flip_count
    return flips

def policy(you, opponent):
    dirs = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    legal_moves = get_legal_moves(you, opponent)
    
    if not legal_moves:
        return "pass"
    
    corners = {(0,0), (0,7), (7,0), (7,7)}
    legal_moves_sorted = []
    
    # Classify moves by their position
    corner_moves = []
    edge_moves = []
    center_moves = []
    for (r, c) in legal_moves:
        if (r, c) in corners:
            corner_moves.append((r, c))
        elif (r == 0 or r == 7) or (c == 0 or c == 7):
            edge_moves.append((r, c))
        else:
            center_moves.append((r, c))
    
    # Select best move in priority order
    best_move = None
    if corner_moves:
        max_flips = 0
        for move in corner_moves:
            f = get_flips(you, opponent, move[0], move[1])
            if f > max_flips:
                best_move = move
                max_flips = f
    elif edge_moves:
        max_flips = 0
        for move in edge_moves:
            f = get_flips(you, opponent, move[0], move[1])
            if f > max_flips:
                best_move = move
                max_flips = f
    else:
        max_flips = 0
        for move in center_moves:
            f = get_flips(you, opponent, move[0], move[1])
            if f > max_flips:
                best_move = move
                max_flips = f
    
    # Convert best_move to algebraic notation
    r, c = best_move
    return f"{chr(c + ord('a'))}{r + 1}"
