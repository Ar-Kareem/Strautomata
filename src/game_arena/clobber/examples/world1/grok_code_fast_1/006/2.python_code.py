
import numpy as np

def get_legal_moves(you_np, opp_np):
    moves = []
    for r in range(5):
        for c in range(6):
            if you_np[r, c]:
                dirs = [(-1, 0, 'U'), (1, 0, 'D'), (0, -1, 'L'), (0, 1, 'R')]
                for dr, dc, d in dirs:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 5 and 0 <= nc < 6 and opp_np[nr, nc]:
                        moves.append(f'{r},{c},{d}')
    return moves

def apply_move(you, opp, move_str):
    r, c, d = move_str.split(',')
    r, c = int(r), int(c)
    you_new = [row[:] for row in you]
    opp_new = [row[:] for row in opp]
    you_new[r][c] = 0
    delta = {'U': (-1, 0), 'D': (1, 0), 'L': (0, -1), 'R': (0, 1)}[d]
    nr, nc = r + delta[0], c + delta[1]
    opp_new[nr][nc] = 0
    you_new[nr][nc] = 1
    return you_new, opp_new

def policy(you: list[list[int]], opponent: list[list[int]]) -> str:
    you_np = np.array(you)
    opp_np = np.array(opponent)
    moves = get_legal_moves(you_np, opp_np)
    if not moves:
        # This should not happen as per rules
        return ''
    best_move = None
    best_val = -float('inf')
    for move in moves:
        you2, opp2 = apply_move(you, opponent, move)
        you2_np = np.array(you2)
        opp2_np = np.array(opp2)
        opp_moves = get_legal_moves(opp2_np, you2_np)
        if not opp_moves:
            val = float('inf')
        else:
            min_my_moves = float('inf')
            for opp_move in opp_moves:
                you3, opp3 = apply_move(you2, opp2, opp_move)
                my_moves_count = len(get_legal_moves(np.array(you3), np.array(opp3)))
                if my_moves_count < min_my_moves:
                    min_my_moves = my_moves_count
            val = min_my_moves
        if val > best_val:
            best_val = val
            best_move = move
    return best_move
