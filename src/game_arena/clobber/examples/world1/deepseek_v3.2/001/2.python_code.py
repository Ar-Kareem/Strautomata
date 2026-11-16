
import itertools
import time

ROWS = 5
COLS = 6
DIRS = [('U', -1, 0), ('R', 0, 1), ('D', 1, 0), ('L', 0, -1)]

def policy(you, opponent):
    start_time = time.time()
    you_board = [list(row) for row in you]
    opp_board = [list(row) for row in opponent]
    
    # convert to tuple for hashing
    def board_to_tuple(you_b, opp_b):
        return (tuple(tuple(r) for r in you_b), tuple(tuple(r) for r in opp_b))
    
    # generate all legal moves from given boards
    def generate_moves(yb, ob):
        moves = []
        for r in range(ROWS):
            for c in range(COLS):
                if yb[r][c] == 1:
                    for d, dr, dc in DIRS:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < ROWS and 0 <= nc < COLS and ob[nr][nc] == 1:
                            moves.append((r, c, d))
        return moves
    
    # apply move, return new boards (copied)
    def make_move(yb, ob, move):
        r, c, d = move
        # find direction
        dr, dc = next((dr, dc) for (dd, drr, dcc) in DIRS if dd == d)
        nr, nc = r + dr, c + dc
        new_you = [list(row) for row in yb]
        new_opp = [list(row) for row in ob]
        new_you[r][c] = 0
        new_you[nr][nc] = 1
        new_opp[nr][nc] = 0
        return new_you, new_opp
    
    # static evaluation
    def evaluate(yb, ob):
        our_moves = len(generate_moves(yb, ob))
        # opponent moves after we move? we evaluate from current player perspective.
        opp_moves = len(generate_moves(ob, yb))
        our_pieces = sum(sum(r) for r in yb)
        opp_pieces = sum(sum(r) for r in ob)
        return 0.5 * (our_moves - opp_moves) + (our_pieces - opp_pieces)
    
    # transposition table: dict[tuple_board] -> (score, depth)
    transposition = {}
    
    # alpha-beta search
    def alpha_beta(yb, ob, depth, alpha, beta, maximizing):
        key = board_to_tuple(yb, ob)
        if key in transposition and transposition[key][1] >= depth:
            return transposition[key][0]
        
        moves = generate_moves(yb, ob)
        if depth == 0 or not moves:
            # terminal or leaf
            score = evaluate(yb, ob)
            transposition[key] = (score, depth)
            return score
        
        if maximizing:
            value = float('-inf')
            for m in moves:
                ny, no = make_move(yb, ob, m)
                value = max(value, alpha_beta(ny, no, depth-1, alpha, beta, False))
                alpha = max(alpha, value)
                if value >= beta:
                    break
            transposition[key] = (value, depth)
            return value
        else:
            value = float('inf')
            for m in moves:
                ny, no = make_move(yb, ob, m)
                value = min(value, alpha_beta(ny, no, depth-1, alpha, beta, True))
                beta = min(beta, value)
                if value <= alpha:
                    break
            transposition[key] = (value, depth)
            return value
    
    # iterative deepening
    best_move = None
    legal_moves = generate_moves(you_board, opp_board)
    if not legal_moves:
        # should not happen per spec, but fallback
        return "0,0,U"
    
    # ensure we return a move even if time expires quickly
    best_move = legal_moves[0]
    
    depth = 1
    while time.time() - start_time < 0.95:  # leave 50ms buffer
        current_best = None
        best_score = float('-inf')
        alpha = float('-inf')
        beta = float('inf')
        for m in legal_moves:
            ny, no = make_move(you_board, opp_board, m)
            score = alpha_beta(ny, no, depth-1, alpha, beta, False)
            if score > best_score:
                best_score = score
                current_best = m
                alpha = max(alpha, score)
        if current_best is not None:
            best_move = current_best
        depth += 1
        # if depth exceeds remaining pieces, break
        total_pieces = sum(sum(r) for r in you_board) + sum(sum(r) for r in opp_board)
        if depth > total_pieces:
            break
    
    r, c, d = best_move
    return f"{r},{c},{d}"

