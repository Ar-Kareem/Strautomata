
import itertools

def dist(r, col):
    if col == 'b':
        return r
    else:
        return 7 - r

def is_on_board(r, c):
    return 0 <= r <= 7 and 0 <= c <= 7

def generate_moves(me, opp, color, opp_color):
    moves = []
    dir = 1 if color == 'w' else -1
    goal_row = 0 if color == 'b' else 7
    for piece in me:
        r, c = piece
        to_r = r + dir
        # straight forward
        if is_on_board(to_r, c) and (to_r, c) not in [p for p in me] and (to_r, c) not in [p for p in opp]:
            moves.append((piece, (to_r, c)))
        # diag left
        if is_on_board(to_r, c-1) and (to_r, c-1) not in [p for p in me] and (to_r, c-1) not in [p for p in opp]:
            moves.append((piece, (to_r, c-1)))
        # diag right
        if is_on_board(to_r, c+1) and (to_r, c+1) not in [p for p in me] and (to_r, c+1) not in [p for p in opp]:
            moves.append((piece, (to_r, c+1)))
        # capture left
        if is_on_board(to_r, c-1) and (to_r, c-1) in [p for p in opp]:
            moves.append((piece, (to_r, c-1)))
        # capture right
        if is_on_board(to_r, c+1) and (to_r, c+1) in [p for p in opp]:
            moves.append((piece, (to_r, c+1)))
    return moves

def simulate_move(me, opp, move, color, opp_color):
    new_me = list(me)
    new_opp = list(opp)
    from_p, to_p = move
    new_me.remove(from_p)
    new_me.append(to_p)
    captured = []
    for p in opp:
        if p == to_p:
            captured = [to_p]
            break
    if captured:
        new_opp.remove(to_p)
    return new_me, new_opp

def heuristic(me_pos, opp_pos, color, opp_color):
    my_total = sum(dist(r, color) for r, c in me_pos)
    opp_total = sum(dist(r, opp_color) for r, c in opp_pos)
    return opp_total - my_total

def check_win(me_pos, opp_pos, goal_row):
    return any(r == goal_row for r, c in me_pos) or len(opp_pos) == 0

def policy(me, opp, color):
    opp_color = 'w' if color == 'b' else 'b'
    goal_row = 0 if color == 'b' else 7
    possible_moves = generate_moves(me, opp, color, opp_color)
    if not possible_moves:
        # Should not happen, but return first if yes
        return ((0,0),(0,1))  # arbitrary legal? But it will be legal
    best_move = None
    best_heur = float('-inf')
    for move in possible_moves:
        new_me, new_opp = simulate_move(me, opp, move, color, opp_color)
        if check_win(new_me, new_opp, goal_row):
            return move  # instant win
        h = heuristic(new_me, new_opp, color, opp_color)
        if h > best_heur:
            best_heur = h
            best_move = move
    return best_move
