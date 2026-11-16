
import numpy as np

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    def get_legal_moves():
        moves = []
        for r in range(8):
            for c in range(8):
                if you[r][c] == 1 or opponent[r][c] == 1:
                    continue
                valid = False
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < 8 and 0 <= nc < 8 and opponent[nr][nc] == 1:
                            curr_r, curr_c = nr + dr, nc + dc
                            found = False
                            while 0 <= curr_r < 8 and 0 <= curr_c < 8:
                                if you[curr_r][curr_c] == 1:
                                    found = True
                                    break
                                if opponent[curr_r][curr_c] == 0:
                                    break
                                curr_r += dr
                                curr_c += dc
                            if found:
                                valid = True
                                break
                if valid:
                    moves.append((r, c))
        return moves

    def simulate_move(r, c):
        new_you = np.copy(you)
        new_opp = np.copy(opponent)
        new_you[r][c] = 1
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                curr_r, curr_c = r + dr, c + dc
                to_flip = []
                while 0 <= curr_r < 8 and 0 <= curr_c < 8:
                    if opponent[curr_r][curr_c] == 1:
                        to_flip.append((curr_r, curr_c))
                        curr_r += dr
                        curr_c += dc
                    else:
                        break
                if 0 <= curr_r < 8 and 0 <= curr_c < 8 and you[curr_r][curr_c] == 1 and to_flip:
                    for fr, fc in to_flip:
                        new_you[fr][fc] = 1
                        new_opp[fr][fc] = 0
        return new_you, new_opp

    def evaluate_board(y, o):
        weights = [
            [100, -1, 8, 5, 5, 8, -1, 100],
            [-1, -20, -4, -3, -3, -4, -20, -1],
            [8, -4, 7, 1, 1, 7, -4, 8],
            [5, -3, 1, 0, 0, 1, -3, 5],
            [5, -3, 1, 0, 0, 1, -3, 5],
            [8, -4, 7, 1, 1, 7, -4, 8],
            [-1, -20, -4, -3, -3, -4, -20, -1],
            [100, -1, 8, 5, 5, 8, -1, 100]
        ]
        score = 0
        for r in range(8):
            for c in range(8):
                w = weights[r][c]
                if y[r][c] == 1:
                    score += w
                elif o[r][c] == 1:
                    score -= w
        return score

    legal_moves = get_legal_moves()
    if not legal_moves:
        return "pass"
    best_move, best_score = legal_moves[0], -float('inf')
    for r, c in legal_moves:
        new_you, new_opp = simulate_move(r, c)
        score = evaluate_board(new_you, new_opp)
        if score > best_score:
            best_score, best_move = score, (r, c)
    col = chr(ord('a') + best_move[1])
    row = best_move[0] + 1
    return f"{col}{row}"
