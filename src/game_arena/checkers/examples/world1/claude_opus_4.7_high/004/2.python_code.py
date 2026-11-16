
import time

def policy(my_men, my_kings, opp_men, opp_kings, color):
    board = {}
    for pos in my_men:
        board[tuple(pos)] = 'm'
    for pos in my_kings:
        board[tuple(pos)] = 'M'
    for pos in opp_men:
        board[tuple(pos)] = 'o'
    for pos in opp_kings:
        board[tuple(pos)] = 'O'

    my_forward = 1 if color == 'w' else -1

    moves = gen_moves(board, 'm', 'M', 'o', 'O', my_forward)
    if not moves:
        # fallback
        return ((0, 0), (1, 1))

    start_time = time.time()
    time_budget = 0.85

    best_move = moves[0]

    for depth in range(1, 10):
        try:
            score, move = alphabeta(board, depth, -10**9, 10**9, True,
                                    my_forward, start_time, time_budget)
            if move is not None:
                best_move = move
            if time.time() - start_time > time_budget * 0.55:
                break
        except TimeoutError:
            break

    path = best_move[0]
    return (tuple(path[0]), tuple(path[1]))


def gen_moves(board, my_m, my_k, opp_m, opp_k, forward):
    my_positions = [pos for pos, p in board.items() if p == my_m or p == my_k]

    all_jumps = []
    for pos in my_positions:
        p = board[pos]
        is_king = (p == my_k)
        jumps = find_jumps(board, pos, is_king, forward, opp_m, opp_k)
        all_jumps.extend(jumps)

    if all_jumps:
        return all_jumps

    moves = []
    for pos in my_positions:
        p = board[pos]
        is_king = (p == my_k)
        if is_king:
            dirs = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        else:
            dirs = [(forward, -1), (forward, 1)]
        for dr, dc in dirs:
            nr, nc = pos[0] + dr, pos[1] + dc
            if 0 <= nr < 8 and 0 <= nc < 8 and (nr, nc) not in board:
                moves.append(([pos, (nr, nc)], frozenset()))
    return moves


def find_jumps(board, start_pos, is_king, forward, opp_m, opp_k):
    results = []

    def recurse(pos, is_k, path, captured):
        if is_k:
            dirs = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        else:
            dirs = [(forward, -1), (forward, 1)]

        for dr, dc in dirs:
            mid = (pos[0] + dr, pos[1] + dc)
            land = (pos[0] + 2 * dr, pos[1] + 2 * dc)
            if not (0 <= land[0] < 8 and 0 <= land[1] < 8):
                continue
            if mid in captured:
                continue
            if mid not in board:
                continue
            if board[mid] != opp_m and board[mid] != opp_k:
                continue
            if land in board and land != start_pos:
                continue

            new_captured = captured | frozenset([mid])
            new_is_k = is_k
            king_row = 7 if forward == 1 else 0
            became_king = (not is_k) and (land[0] == king_row)
            if became_king:
                new_is_k = True

            new_path = path + [land]

            if became_king:
                results.append((new_path, new_captured))
            else:
                before = len(results)
                recurse(land, new_is_k, new_path, new_captured)
                if len(results) == before:
                    results.append((new_path, new_captured))

    recurse(start_pos, is_king, [start_pos], frozenset())
    return results


def apply_move(board, move, my_m, my_k, forward):
    path, captured = move
    new_board = dict(board)
    start = path[0]
    end = path[-1]
    piece = new_board.pop(start)
    for c in captured:
        new_board.pop(c, None)
    king_row = 7 if forward == 1 else 0
    if piece == my_m and end[0] == king_row:
        piece = my_k
    new_board[end] = piece
    return new_board


def alphabeta(board, depth, alpha, beta, maximizing, my_forward, start, time_budget):
    if time.time() - start > time_budget:
        raise TimeoutError

    if maximizing:
        my_m, my_k, opp_m, opp_k, forward = 'm', 'M', 'o', 'O', my_forward
    else:
        my_m, my_k, opp_m, opp_k, forward = 'o', 'O', 'm', 'M', -my_forward

    moves = gen_moves(board, my_m, my_k, opp_m, opp_k, forward)

    if not moves:
        # no moves: this side loses
        return (-100000 - depth if maximizing else 100000 + depth), None

    if depth == 0:
        return evaluate(board, my_forward), None

    # Simple move ordering: prefer larger captures
    moves.sort(key=lambda m: -len(m[1]))

    best_move = None
    if maximizing:
        best = -10**9
        for move in moves:
            new_board = apply_move(board, move, my_m, my_k, forward)
            score, _ = alphabeta(new_board, depth - 1, alpha, beta, False,
                                 my_forward, start, time_budget)
            if score > best:
                best = score
                best_move = move
            if best > alpha:
                alpha = best
            if beta <= alpha:
                break
        return best, best_move
    else:
        best = 10**9
        for move in moves:
            new_board = apply_move(board, move, my_m, my_k, forward)
            score, _ = alphabeta(new_board, depth - 1, alpha, beta, True,
                                 my_forward, start, time_budget)
            if score < best:
                best = score
                best_move = move
            if best < beta:
                beta = best
            if beta <= alpha:
                break
        return best, best_move


def evaluate(board, my_forward):
    score = 0
    my_count = 0
    opp_count = 0
    for pos, p in board.items():
        r, c = pos
        if p == 'm':
            my_count += 1
            score += 100
            if my_forward == 1:
                score += r * 2
            else:
                score += (7 - r) * 2
            if 2 <= c <= 5:
                score += 2
            # back rank defense
            back_row = 0 if my_forward == 1 else 7
            if r == back_row:
                score += 3
        elif p == 'M':
            my_count += 1
            score += 170
            # kings prefer center
            cdist = 6 - (abs(r - 3) + abs(c - 3))
            score += cdist
        elif p == 'o':
            opp_count += 1
            score -= 100
            if my_forward == 1:
                score -= (7 - r) * 2
            else:
                score -= r * 2
            if 2 <= c <= 5:
                score -= 2
            back_row = 7 if my_forward == 1 else 0
            if r == back_row:
                score -= 3
        elif p == 'O':
            opp_count += 1
            score -= 170
            cdist = 6 - (abs(r - 3) + abs(c - 3))
            score -= cdist

    # Encourage trading when ahead
    if my_count > opp_count:
        score += (my_count - opp_count) * 3 * (12 - opp_count)
    elif opp_count > my_count:
        score -= (opp_count - my_count) * 3 * (12 - my_count)

    return int(score)
