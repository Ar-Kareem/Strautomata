
import numpy as np

def policy(board) -> str:
    def count_landing_squares(b, color):
        count = 0
        for r in range(6):
            for c in range(6):
                if b[r, c] == color:
                    for dr in [-1, 0, 1]:
                        for dc in [-1, 0, 1]:
                            if dr == 0 and dc == 0: continue
                            step = 1
                            while True:
                                nr = r + step * dr
                                nc = c + step * dc
                                if nr < 0 or nr >= 6 or nc < 0 or nc >= 6:
                                    break
                                # Check path validity
                                valid_path = True
                                tr, tc = r + dr, c + dc
                                while True:
                                    if not (0 <= tr < 6 and 0 <= tc < 6):
                                        valid_path = False
                                        break
                                    if b[tr, tc] != 0:
                                        valid_path = False
                                        break
                                    tr += dr
                                    tc += dc
                                    if (tr, tc) == (nr, nc):
                                        if b[nr, nc] != 0:
                                            valid_path = False
                                        else:
                                            valid_path = True
                                        break
                                if valid_path:
                                    count += 1
                                step += 1
        return count

    def evaluate(b):
        our_mob = count_landing_squares(b, 1)
        opp_mob = count_landing_squares(b, 2)
        center_our = 0
        center_opp = 0
        for r in range(6):
            for c in range(6):
                if b[r, c] == 1 and r in (2, 3) and c in (2, 3):
                    center_our += 1
                if b[r, c] == 2 and r in (2, 3) and c in (2, 3):
                    center_opp += 1
        return (our_mob - opp_mob) + (center_our - center_opp)

    moves = []
    for r in range(6):
        for c in range(6):
            if board[r, c] == 1:
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        if dr == 0 and dc == 0: continue
                        step = 1
                        while True:
                            nr, nc = r + step * dr, c + step * dc
                            if not (0 <= nr < 6 and 0 <= nc < 6):
                                break
                            # Check move path validity
                            valid_move = True
                            tr, tc = r + dr, c + dc
                            while True:
                                if not (0 <= tr < 6 and 0 <= tc < 6):
                                    valid_move = False
                                    break
                                if board[tr, tc] != 0:
                                    valid_move = False
                                    break
                                tr += dr
                                tc += dc
                                if (tr, tc) == (nr, nc):
                                    if board[nr, nc] != 0:
                                        valid_move = False
                                    else:
                                        valid_move = True
                                    break
                            if not valid_move:
                                step += 1
                                continue
                            if board[nr, nc] != 0:
                                step += 1
                                continue

                            # Generate all arrow shots from landing square
                            for ar_dr in [-1, 0, 1]:
                                for ar_dc in [-1, 0, 1]:
                                    if ar_dr == 0 and ar_dc == 0: continue
                                    m = 1
                                    while True:
                                        aro_r, aro_c = nr + m * ar_dr, nc + m * ar_dc
                                        if not (0 <= aro_r < 6 and 0 <= aro_c < 6):
                                            break
                                        # Check arrow path with vacated source as empty
                                        clear = True
                                        start_row, start_col = nr + ar_dr, nc + ar_dc
                                        if (aro_r, aro_c) == (r, c):
                                            clear = True  # automatically empty
                                        else:
                                            while True:
                                                if not (0 <= start_row < 6 and 0 <= start_col < 6):
                                                    clear = False
                                                    break
                                                # Special case: if path passes through vacated square
                                                if (start_row, start_col) == (r, c):
                                                    start_row += ar_dr
                                                    start_col += ar_dc
                                                    continue
                                                if board[start_row, start_col] != 0:
                                                    clear = False
                                                    break
                                                start_row += ar_dr
                                                start_col += ar_dc
                                                if (start_row, start_col) == (aro_r, aro_c):
                                                    break
                                        if not clear:
                                            m += 1
                                            continue
                                        # Check landing square emptiness
                                        if (aro_r, aro_c) != (r, c) and board[aro_r, aro_c] != 0:
                                            m += 1
                                            continue
                                        # Record valid move
                                        move_str = f"{r},{c}:{nr},{nc}:{aro_r},{aro_c}"
                                        moves.append(move_str)
                                        m += 1
                            step += 1

    best_move = None
    best_score = -float('inf')
    for move_str in moves:
        parts = move_str.split(':')
        if len(parts) != 3: continue
        from_r, from_c = map(int, parts[0].split(','))
        to_r, to_c = map(int, parts[1].split(','))
        arrow_r, arrow_c = map(int, parts[2].split(','))
        # Apply move to evaluate
        new_board = board.copy()
        new_board[from_r, from_c] = 0
        new_board[to_r, to_c] = 1
        new_board[arrow_r, arrow_c] = -1
        score = evaluate(new_board)
        if score > best_score:
            best_score = score
            best_move = move_str
    return best_move
