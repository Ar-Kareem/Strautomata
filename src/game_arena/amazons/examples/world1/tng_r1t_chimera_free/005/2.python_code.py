
import numpy as np

def policy(board) -> str:
    centrality = [
        [2, 2, 3, 3, 2, 2],
        [2, 3, 4, 4, 3, 2],
        [3, 4, 5, 5, 4, 3],
        [3, 4, 5, 5, 4, 3],
        [2, 3, 4, 4, 3, 2],
        [2, 2, 3, 3, 2, 2]
    ]

    def get_mobility(b, r, c):
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1),
                      (-1, -1), (-1, 1), (1, -1), (1, 1)]
        mobility = 0
        for dr, dc in directions:
            steps = 0
            nr, nc = r + dr, c + dc
            while 0 <= nr < 6 and 0 <= nc < 6:
                if b[nr, nc] != 0:
                    break
                steps += 1
                nr += dr
                nc += dc
            mobility += steps
        return mobility

    def evaluate(b):
        my_score = 0
        opp_score = 0
        for r in range(6):
            for c in range(6):
                if b[r, c] == 1:
                    my_score += get_mobility(b, r, c) + centrality[r][c]
                elif b[r, c] == 2:
                    opp_score += get_mobility(b, r, c) + centrality[r][c]
        return my_score - opp_score

    def generate_legal_moves(b):
        moves = []
        amazon_positions = np.argwhere(b == 1)
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1),
                    (-1, -1), (-1, 1), (1, -1), (1, 1)]
        for r, c in amazon_positions:
            for dr, dc in directions:
                steps = 1
                while True:
                    nr = r + dr * steps
                    nc = c + dc * steps
                    if not (0 <= nr < 6 and 0 <= nc < 6) or b[nr, nc] != 0:
                        break
                    # Generate arrow moves from (nr, nc)
                    for adr, adc in directions:
                        asteps = 1
                        while True:
                            ar = nr + adr * asteps
                            ac = nc + adc * asteps
                            if not (0 <= ar < 6 and 0 <= ac < 6):
                                break
                            if b[ar, ac] != 0:
                                # Check arrow path validity
                                valid = True
                                step_r = 0 if adr == 0 else (1 if adr > 0 else -1)
                                step_c = 0 if adc == 0 else (1 if adc > 0 else -1)
                                dist = max(abs(ar - nr), abs(ac - nc))
                                for i in range(1, dist + 1):
                                    cr = nr + step_r * i
                                    cc = nc + step_c * i
                                    if cr == r and cc == c:
                                        continue
                                    if cr == ar and cc == ac:
                                        break
                                    if b[cr, cc] != 0:
                                        valid = False
                                        break
                                if valid and b[ar, ac] == 0:
                                    moves.append(f"{r},{c}:{nr},{nc}:{ar},{ac}")
                                break
                            else:
                                # Check arrow path validity
                                valid = True
                                step_r = 0 if adr == 0 else (1 if adr > 0 else -1)
                                step_c = 0 if adc == 0 else (1 if adc > 0 else -1)
                                dist = max(abs(ar - nr), abs(ac - nc))
                                for i in range(1, dist + 1):
                                    cr = nr + step_r * i
                                    cc = nc + step_c * i
                                    if cr == r and cc == c:
                                        continue
                                    if b[cr, cc] != 0:
                                        valid = False
                                        break
                                if valid:
                                    moves.append(f"{r},{c}:{nr},{nc}:{ar},{ac}")
                            asteps += 1
                    steps += 1
        return moves

    legal_moves = generate_legal_moves(board)
    if not legal_moves:
        return ""
    best_move = None
    best_score = -float('inf')
    for move in legal_moves:
        parts = move.split(':')
        from_r, from_c = map(int, parts[0].split(','))
        to_r, to_c = map(int, parts[1].split(','))
        arrow_r, arrow_c = map(int, parts[2].split(','))
        new_board = board.copy()
        new_board[from_r, from_c] = 0
        new_board[to_r, to_c] = 1
        new_board[arrow_r, arrow_c] = -1
        score = evaluate(new_board)
        if score > best_score:
            best_score = score
            best_move = move
    return best_move
