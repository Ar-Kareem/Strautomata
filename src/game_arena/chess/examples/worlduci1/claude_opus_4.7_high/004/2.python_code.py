
import time

def policy(pieces, to_play):
    start_time = time.time()
    TIME_LIMIT = 0.80

    color = 'w' if to_play == 'white' else 'b'

    board = [None] * 64
    for sq, p in pieces.items():
        x = ord(sq[0]) - ord('a')
        y = int(sq[1]) - 1
        board[y*8+x] = p

    piece_values = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}

    def gen_moves(c):
        moves = []
        for idx in range(64):
            p = board[idx]
            if p is None or p[0] != c:
                continue
            x = idx % 8
            y = idx // 8
            pt = p[1]
            if pt == 'P':
                d = 1 if c == 'w' else -1
                start_y = 1 if c == 'w' else 6
                promo_y = 7 if c == 'w' else 0
                ny = y + d
                if 0 <= ny < 8:
                    if board[ny*8+x] is None:
                        if ny == promo_y:
                            for pr in 'qrbn':
                                moves.append((idx, ny*8+x, pr))
                        else:
                            moves.append((idx, ny*8+x, None))
                            if y == start_y and board[(y+2*d)*8+x] is None:
                                moves.append((idx, (y+2*d)*8+x, None))
                    for dx in (-1, 1):
                        nx = x + dx
                        if 0 <= nx < 8:
                            t = board[ny*8+nx]
                            if t is not None and t[0] != c:
                                if ny == promo_y:
                                    for pr in 'qrbn':
                                        moves.append((idx, ny*8+nx, pr))
                                else:
                                    moves.append((idx, ny*8+nx, None))
            elif pt == 'N':
                for dx, dy in ((1,2),(2,1),(-1,2),(-2,1),(1,-2),(2,-1),(-1,-2),(-2,-1)):
                    nx, ny = x+dx, y+dy
                    if 0 <= nx < 8 and 0 <= ny < 8:
                        t = board[ny*8+nx]
                        if t is None or t[0] != c:
                            moves.append((idx, ny*8+nx, None))
            elif pt == 'K':
                for dx in (-1,0,1):
                    for dy in (-1,0,1):
                        if dx==0 and dy==0:
                            continue
                        nx, ny = x+dx, y+dy
                        if 0 <= nx < 8 and 0 <= ny < 8:
                            t = board[ny*8+nx]
                            if t is None or t[0] != c:
                                moves.append((idx, ny*8+nx, None))
                hy = 0 if c == 'w' else 7
                if y == hy and x == 4:
                    if board[hy*8+7] == c+'R' and board[hy*8+5] is None and board[hy*8+6] is None:
                        moves.append((idx, hy*8+6, None))
                    if board[hy*8+0] == c+'R' and board[hy*8+1] is None and board[hy*8+2] is None and board[hy*8+3] is None:
                        moves.append((idx, hy*8+2, None))
            else:
                dirs = []
                if pt in ('B', 'Q'):
                    dirs += [(1,1),(1,-1),(-1,1),(-1,-1)]
                if pt in ('R', 'Q'):
                    dirs += [(1,0),(-1,0),(0,1),(0,-1)]
                for dx, dy in dirs:
                    nx, ny = x+dx, y+dy
                    while 0 <= nx < 8 and 0 <= ny < 8:
                        t = board[ny*8+nx]
                        if t is None:
                            moves.append((idx, ny*8+nx, None))
                        else:
                            if t[0] != c:
                                moves.append((idx, ny*8+nx, None))
                            break
                        nx += dx
                        ny += dy
        return moves

    def find_king(c):
        target = c + 'K'
        for i in range(64):
            if board[i] == target:
                return i
        return -1

    def attacked(sq_idx, by_color):
        x = sq_idx % 8
        y = sq_idx // 8
        d = 1 if by_color == 'w' else -1
        py = y - d
        if 0 <= py < 8:
            for dx in (-1, 1):
                px = x + dx
                if 0 <= px < 8:
                    if board[py*8+px] == by_color + 'P':
                        return True
        for dx, dy in ((1,2),(2,1),(-1,2),(-2,1),(1,-2),(2,-1),(-1,-2),(-2,-1)):
            nx, ny = x+dx, y+dy
            if 0 <= nx < 8 and 0 <= ny < 8:
                if board[ny*8+nx] == by_color + 'N':
                    return True
        for dx in (-1,0,1):
            for dy in (-1,0,1):
                if dx==0 and dy==0:
                    continue
                nx, ny = x+dx, y+dy
                if 0 <= nx < 8 and 0 <= ny < 8:
                    if board[ny*8+nx] == by_color + 'K':
                        return True
        for dx, dy in ((1,1),(1,-1),(-1,1),(-1,-1)):
            nx, ny = x+dx, y+dy
            while 0 <= nx < 8 and 0 <= ny < 8:
                t = board[ny*8+nx]
                if t is not None:
                    if t[0] == by_color and (t[1] == 'B' or t[1] == 'Q'):
                        return True
                    break
                nx += dx
                ny += dy
        for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
            nx, ny = x+dx, y+dy
            while 0 <= nx < 8 and 0 <= ny < 8:
                t = board[ny*8+nx]
                if t is not None:
                    if t[0] == by_color and (t[1] == 'R' or t[1] == 'Q'):
                        return True
                    break
                nx += dx
                ny += dy
        return False

    def make_move(mv):
        from_idx, to_idx, promo = mv
        piece = board[from_idx]
        captured = board[to_idx]
        if promo:
            board[to_idx] = piece[0] + promo.upper()
        else:
            board[to_idx] = piece
        board[from_idx] = None
        rook_info = None
        if piece[1] == 'K' and abs((to_idx%8) - (from_idx%8)) == 2:
            y = from_idx // 8
            if to_idx % 8 == 6:
                board[y*8+5] = board[y*8+7]
                board[y*8+7] = None
                rook_info = (y*8+7, y*8+5)
            else:
                board[y*8+3] = board[y*8+0]
                board[y*8+0] = None
                rook_info = (y*8+0, y*8+3)
        return piece, captured, rook_info

    def unmake_move(mv, piece, captured, rook_info):
        from_idx, to_idx, _ = mv
        board[from_idx] = piece
        board[to_idx] = captured
        if rook_info:
            orig, new = rook_info
            board[orig] = board[new]
            board[new] = None

    def legal_moves_list(c):
        pseudo = gen_moves(c)
        legal = []
        opp = 'b' if c == 'w' else 'w'
        for mv in pseudo:
            from_idx, to_idx, _ = mv
            piece = board[from_idx]
            if piece[1] == 'K' and abs((to_idx%8) - (from_idx%8)) == 2:
                if attacked(from_idx, opp):
                    continue
                mid = (from_idx + to_idx) // 2
                if attacked(mid, opp):
                    continue
            p, cap, ri = make_move(mv)
            ki = find_king(c)
            ok = ki == -1 or not attacked(ki, opp)
            unmake_move(mv, p, cap, ri)
            if ok:
                legal.append(mv)
        return legal

    def evaluate():
        score = 0
        for i in range(64):
            p = board[i]
            if p is None:
                continue
            v = piece_values[p[1]]
            x = i % 8
            y = i // 8
            if p[1] == 'N' or p[1] == 'B':
                cd = max(abs(3.5 - x), abs(3.5 - y))
                v += int((3.5 - cd) * 5)
            elif p[1] == 'P':
                if p[0] == 'w':
                    v += y * 5
                    if x in (3,4) and y >= 2:
                        v += 8
                else:
                    v += (7 - y) * 5
                    if x in (3,4) and y <= 5:
                        v += 8
            elif p[1] == 'K':
                # King safety: prefer corner early
                if p[0] == 'w':
                    if y == 0 and (x < 3 or x > 5):
                        v += 20
                else:
                    if y == 7 and (x < 3 or x > 5):
                        v += 20
            if p[0] == 'w':
                score += v
            else:
                score -= v
        return score

    timed_out = [False]

    def mscore(mv):
        f, t, pr = mv
        s = 0
        tgt = board[t]
        if tgt is not None:
            s += 10 * piece_values[tgt[1]] - piece_values[board[f][1]]
        if pr:
            s += 800
        return -s

    def qsearch(alpha, beta, c, qdepth):
        opp = 'b' if c == 'w' else 'w'
        ev = evaluate() if c == 'w' else -evaluate()
        if ev >= beta:
            return beta
        if ev > alpha:
            alpha = ev
        if qdepth <= 0:
            return alpha
        pseudo = gen_moves(c)
        caps = []
        for mv in pseudo:
            f, t, pr = mv
            if board[t] is not None or pr:
                caps.append(mv)
        caps.sort(key=mscore)
        for mv in caps:
            p, cap, ri = make_move(mv)
            ki = find_king(c)
            if ki != -1 and attacked(ki, opp):
                unmake_move(mv, p, cap, ri)
                continue
            val = -qsearch(-beta, -alpha, opp, qdepth - 1)
            unmake_move(mv, p, cap, ri)
            if val >= beta:
                return beta
            if val > alpha:
                alpha = val
        return alpha

    def search(depth, alpha, beta, c):
        if time.time() - start_time > TIME_LIMIT:
            timed_out[0] = True
            return 0
        opp = 'b' if c == 'w' else 'w'
        if depth == 0:
            return qsearch(alpha, beta, c, 4)
        moves = legal_moves_list(c)
        if not moves:
            ki = find_king(c)
            if ki != -1 and attacked(ki, opp):
                return -99000 - depth
            return 0
        moves.sort(key=mscore)
        best = -1000000
        for mv in moves:
            p, cap, ri = make_move(mv)
            val = -search(depth - 1, -beta, -alpha, opp)
            unmake_move(mv, p, cap, ri)
            if timed_out[0]:
                return best if best > -1000000 else 0
            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
        return best

    root_moves = legal_moves_list(color)
    if not root_moves:
        return "0000"

    root_moves.sort(key=mscore)
    best_move = root_moves[0]

    opp = 'b' if color == 'w' else 'w'

    for depth in range(1, 5):
        if time.time() - start_time > TIME_LIMIT * 0.4 and depth > 2:
            break
        current_best = None
        current_val = -1000000
        alpha = -1000000
        beta = 1000000
        for mv in root_moves:
            p, cap, ri = make_move(mv)
            val = -search(depth - 1, -beta, -alpha, opp)
            unmake_move(mv, p, cap, ri)
            if timed_out[0]:
                break
            if val > current_val:
                current_val = val
                current_best = mv
            if current_val > alpha:
                alpha = current_val
        if not timed_out[0] and current_best is not None:
            best_move = current_best
            root_moves.remove(current_best)
            root_moves.insert(0, current_best)
        else:
            break

    f, t, pr = best_move
    uci = chr(ord('a') + f%8) + str(f//8+1) + chr(ord('a') + t%8) + str(t//8+1)
    if pr:
        uci += pr
    return uci
