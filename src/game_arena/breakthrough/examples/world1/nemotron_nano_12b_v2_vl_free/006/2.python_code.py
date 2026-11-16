
import sys
sys.setrecursionlimit(10000)

black_piece_value = [
    [7, 10, 12, 12, 12, 12, 10, 7],
    [6, 9, 11, 11, 11, 11, 9, 6],
    [5, 8, 10, 10, 10, 10, 8, 5],
    [4, 7, 9, 9, 9, 9, 7, 4],
    [3, 6, 8, 8, 8, 8, 6, 3],
    [2, 5, 7, 7, 7, 7, 5, 2],
    [1, 4, 6, 6, 6, 6, 4, 1],
    [0, 3, 5, 5, 5, 5, 3, 0]
]

white_piece_value = [
    [0, 3, 5, 5, 5, 5, 3, 0],
    [1, 4, 6, 6, 6, 6, 4, 1],
    [2, 5, 7, 7, 7, 7, 5, 2],
    [3, 6, 8, 8, 8, 8, 6, 3],
    [4, 7, 9, 9, 9, 9, 7, 4],
    [5, 8, 10, 10, 10, 10, 8, 5],
    [6, 9, 11, 11, 11, 11, 9, 6],
    [7, 10, 12, 12, 12, 12, 10, 7]
]

def make_move(me, opp, move, color):
    from_pos, to_pos = move
    new_me = []
    moved = False
    for piece in me:
        if piece == from_pos:
            new_me.append(to_pos)
            moved = True
        else:
            new_me.append(piece)
    if not moved:
        new_me = me[:]
    new_opp = [p for p in opp if p != to_pos]
    return new_me, new_opp

def generate_moves(me, opp, color):
    me_set = set(me)
    opp_set = set(opp)
    moves = []
    for piece in me:
        r, c = piece
        if color == 'b':
            directions = [(-1, 0), (-1, 1), (-1, -1)]
        else:
            directions = [(1, 0), (1, 1), (1, -1)]
        for dr, dc in directions:
            nr = r + dr
            nc = c + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                new_pos = (nr, nc)
                if new_pos in me_set:
                    continue
                if new_pos in opp_set:
                    moves.append((piece, new_pos))
                else:
                    moves.append((piece, new_pos))
    return moves

def evaluate(me, opp, color):
    if color == 'b':
        if any(r == 0 for (r, c) in me):
            return 1000000
        if not opp:
            return 1000000
        if not me:
            return -1000000
        our_val = sum(black_piece_value[r][c] for (r, c) in me)
        opp_val = sum(white_piece_value[r][c] for (r, c) in opp)
        return our_val - opp_val
    else:
        if any(r == 7 for (r, c) in me):
            return 1000000
        if not opp:
            return 1000000
        if not me:
            return -1000000
        our_val = sum(white_piece_value[r][c] for (r, c) in me)
        opp_val = sum(black_piece_value[r][c] for (r, c) in opp)
        return our_val - opp_val

def negamax(me, opp, color, depth, max_depth, alpha, beta):
    if color == 'b':
        if any(r == 0 for (r, c) in me):
            return 1000000, None
        if not opp:
            return 1000000, None
        if not me:
            return -1000000, None
    else:
        if any(r == 7 for (r, c) in me):
            return 1000000, None
        if not opp:
            return 1000000, None
        if not me:
            return -1000000, None

    if depth == max_depth:
        eval_val = evaluate(me, opp, color)
        return eval_val, None

    moves = generate_moves(me, opp, color)
    if not moves:
        return evaluate(me, opp, color), None

    best_score = -10**9
    best_move = None
    for move in moves:
        new_me, new_opp = make_move(me, opp, move, color)
        next_color = 'w' if color == 'b' else 'b'
        score_inner, _ = negamax(new_me, new_opp, next_color, depth+1, max_depth, -beta, -alpha)
        if score_inner > best_score:
            best_score = score_inner
            best_move = move
        alpha = max(alpha, score_inner)
        if beta <= alpha:
            break
            
    return best_score, best_move

def policy(me, opp, color):
    _, best_move = negamax(me, opp, color, 0, 2, -10**9, 10**9)
    if best_move is None:
        moves = generate_moves(me, opp, color)
        if moves:
            return moves[0]
        else:
            return (me[0][0], me[0][1], me[0][0], me[0][1])
    return best_move
