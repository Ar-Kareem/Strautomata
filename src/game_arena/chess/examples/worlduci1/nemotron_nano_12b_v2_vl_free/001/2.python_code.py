
def policy(pieces: dict, to_play: str) -> str:
    current_color = to_play[0]
    board = [[None for _ in range(8)] for _ in range(8)]
    for (sq, p) in pieces.items():
        row = ord(sq[0]) - ord('a')
        col = int(sq[1]) - 1
        board[col][row] = p

    def is_attacking(pc, from_pos, to_pos):
        ptype = pc[1]
        dr, dc = to_pos[0] - from_pos[0], to_pos[1] - from_pos[1]
        if ptype == 'N':
            return (abs(dr) == 2 and abs(dc) == 1) or (abs(dr) == 1 and abs(dc) == 2)
        elif ptype == 'B':
            return abs(dr) == abs(dc)
        elif ptype == 'R':
            return dr == 0 or dc == 0
        elif ptype == 'Q':
            return abs(dr) == abs(dc) or dr == 0 or dc == 0
        elif ptype == 'P':
            return (from_pos[0] + (1 if pc[0] == 'w' else -1), from_pos[1] + 1) == to_pos or (from_pos[0] + (1 if pc[0] == 'w' else -1), from_pos[1] - 1) == to_pos
        elif ptype == 'K':
            return max(abs(dr), abs(dc)) == 1

    def move_is_checking_king(move):
        src = (move[1], move[0]) if move[2] else (move[3], move[2])
        return board[src[0]][src[1]][0] == ('b' if current_color == 'w' else 'w')

    def is_checkmate_after_move(move):
        new_board = [row[:] for row in board]
        src_r, src_c, dest_r, dest_c = move
        src_piece = new_board[src_r][src_c]
        dest_piece = new_board[dest_r][dest_c]
        new_board[dest_r][dest_c] = src_piece
        if src_piece[1] == 'P' and ((current_color == 'w' and dest_r == 7) or (current_color == 'b' and dest_r == 0)):
            new_board[dest_r][dest_c] += 'P'  # Promotion to queen by default
        knight_moves = [(-2, -1), (-1, -2), (-1, 2), (2, -1), (2, 1), (1, 2), (1, -2), (-2, 1)]
        for r in range(8):
            for c in range(8):
                pc = new_board[r][c]
                if pc and pc[0] != current_color:
                    if pc[1] == 'N':
                        for dr, dc in knight_moves:
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < 8 and 0 <= nc < 8 and (nr, nc) == (dest_r, dest_c):
                                return True
                    elif pc[1] == 'B':
                        dr, dc = new_board[r][c][1] == 'B' and (1, 1) or (1, -1) or (-1, 1) or (-1, -1)
                        i = 1
                        while 0 <= r + dr * i < 8 and 0 <= c + dc * i < 8:
                            if (r + dr * i, c + dc * i) == (dest_r, dest_c):
                                return True
                            if board[r + dr * i][c + dc * i]:
                                break
                            i += 1
                    elif pc[1] == 'R':
                        dr, dc = 0, 1
                        if src_r == new_r or src_c == new_c:
                            dx = dest_c - src_c if src_r == dest_r else 0
                            dy = dest_r - src_r if src_c == dest_c else 0
                            step = 1 if dx > 0 else -1 if dx < 0 else 0
                            for i in range(abs(dx), 0, -1):
                                if src_r + dy * i < 0 or src_r + dy * i >= 8 or new_board[src_r + dy * i][src_c + dx * i]:
                                    break
                            return True
                    elif pc[1] == 'Q':
                        if (dr == 0 or dc == 0) or (abs(dr) == abs(dc)):
                            if pc[1] in 'RQ' and (src_r == dest_r or src_c == dest_c):
                                dx = dest_c - src_c
                                dy = dest_r - src_r
                                step = 1 if dx > 0 else -1 if dx < 0 else 0
                                for i in range(1, abs(dx)):
                                    if board[src_r][src_c + step * i]:
                                        break
                                else:
                                    return True
                            elif pc[1] in 'BQ' and abs(dr) == abs(dc):
                                dr = 1 if new_r > src_r else -1
                                dc = 1 if new_c > src_c else -1
                                for i in range(abs(new_r - src_r) - 1):
                                    if board[src_r + dr * i][src_c + dc * i]:
                                        break
                                else:
                                    return True
                    elif pc[1] == 'K':
                        if abs(dr) <= 1 and abs(dc) <= 1:
                            return True
                    elif pc[1] == 'P':
                        dir = 1 if pc[0] == 'w' else -1
                        if pc[0] == 'w' and dest_r == row - 1 and dest_c in [c - 1, c + 1]:
                            return True
                        elif pc[0] == 'b' and dest_r == row + 1 and dest_c in [c - 1, c + 1]:
                            return True
        return False

    def get_king_position():
        for r in range(8):
            for c in range(8):
                if board[c][r] and board[c][r][1] == 'K' and board[c][r][0] == current_color:
                    return (r, c)
        return None

    legal_moves = []
    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if not piece or piece[0] != current_color:
                continue
            ptype = piece[1]
            if ptype == 'N':
                for dr, dc in [(-2, -1), (-1, -2), (-1, 2), (2, -1), (2, 1), (1, 2), (1, -2), (-2, 1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 8 and 0 <= nc < 8:
                        target = board[nr][nc]
                        if not target or target[0] != current_color:
                            legal_moves.append((r, c, nr, nc))
            elif ptype == 'B':
                for dr, dc in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
                    for i in range(1, 8):
                        nr, nc = r + dr * i, c + dc * i
                        if 0 <= nr < 8 and 0 <= nc < 8:
                            target = board[nr][nc]
                            if not target or target[0] != current_color:
                                legal_moves.append((r, c, nr, nc))
                            else:
                                break
                        else:
                            break
            elif ptype == 'R':
                for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    for i in range(1, 8):
                        nr, nc = r + dr * i, c + dc * i
                        if 0 <= nr < 8 and 0 <= nc < 8:
                            target = board[nr][nc]
                            if not target or target[0] != current_color:
                                legal_moves.append((r, c, nr, nc))
                            else:
                                break
                        else:
                            break
            elif ptype == 'Q':
                for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]:
                    for i in range(1, 8):
                        nr, nc = r + dr * i, c + dc * i
                        if 0 <= nr < 8 and 0 <= nc < 8:
                            target = board[nr][nc]
                            if not target or target[0] != current_color:
                                legal_moves.append((r, c, nr, nc))
                            else:
                                break
                        else:
                            break
            elif ptype == 'K':
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < 8 and 0 <= nc < 8:
                            target = board[nr][nc]
                            if not target or target[0] != current_color:
                                legal_moves.append((r, c, nr, nc))
            elif ptype == 'P':
                dir = 1 if current_color == 'w' else -1
                new_r = r + dir
                if 0 <= new_r < 8:
                    target = board[new_r][c]
                    if not target:
                        legal_moves.append((r, c, new_r, c))
                        if (current_color == 'w' and new_r == 7) or (current_color == 'b' and new_r == 0):
                            for prom in ['q', 'r', 'b', 'n']:
                                legal_moves.append((r, c, new_r, c, prom))
                    for new_c in [c - 1, c + 1]:
                        if 0 <= new_c < 8:
                            target = board[new_r][new_c]
                            if target and target[0] != current_color:
                                legal_moves.append((r, c, new_r, new_c))

    best_move = None
    best_score = -float('inf')

    for move in legal_moves:
        if isinstance(move, tuple) and len(move) == 4:
            src_r, src_c, dest_r, dest_c = move
        elif isinstance(move, tuple) and len(move) == 5:
            src_r, src_c, dest_r, dest_c, prom = move
            move = (src_r, src_c, dest_r, dest_c)
        src_piece = board[src_r][src_c]
        dest_piece = board[dest_r][dest_c] if 0 <= dest_r < 8 and 0 <= dest_c < 8 else None
        score = 0
        if dest_piece and dest_piece[0] != current_color:
            captured = dest_piece[1].lower()
            score += 10 * (captured == 'q') + 5 * (captured == 'r') + 3 * (captured in ['b', 'n']) + 1
        if move_is_checking_king((src_r, src_c, dest_r, dest_c)):
            score += 100
        src_central = (abs(c - 3.5) + abs(r - 3.5)) <= 2.5
        dest_central = (abs(dest_c - 3.5) + abs(dest_r - 3.5)) <= 2.5
        if src_central and not dest_central:
            score -= 5
        elif not src_central and dest_central:
            score += 5
        if best_score < score:
            best_score = score
            best_move = move

    if best_move:
        src_r, src_c, dest_r, dest_c = best_move
        src_sq = chr(src_c + ord('a')) + str(src_r + 1)
        dest_sq = chr(dest_c + ord('a')) + str(dest_r + 1)
        if best_move[4] and len(best_move) == 5:
            promotion = best_move[4]
            return f"{src_sq}{dest_sq}{promotion.upper()}"
        return src_sq + dest_sq
    return ""
