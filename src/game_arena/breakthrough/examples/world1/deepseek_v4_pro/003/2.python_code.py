
import random
import time
from collections import defaultdict
from typing import Optional

# ---------------------------------------------------------------------------
# Zobrist hashing utilities for transposition table
# ---------------------------------------------------------------------------
_zobrist_piece = {}
_zobrist_side = random.getrandbits(64)

def _init_zobrist():
    for r in range(8):
        for c in range(8):
            _zobrist_piece[(r, c, 'w')] = random.getrandbits(64)
            _zobrist_piece[(r, c, 'b')] = random.getrandbits(64)

_init_zobrist()

def _compute_hash(me, opp, color):
    h = 0
    for (r, c) in me:
        h ^= _zobrist_piece[(r, c, color)]
    other = 'w' if color == 'b' else 'b'
    for (r, c) in opp:
        h ^= _zobrist_piece[(r, c, other)]
    if color == 'b':
        h ^= _zobrist_side
    return h

# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------
def evaluate(me, opp, color):
    """
    Positive score favors 'color'.
    """
    # Determine home rows based on color
    if color == 'w':
        my_home = 0
        opp_home = 7
    else:
        my_home = 7
        opp_home = 0

    score = 0

    # Material: simple piece count
    score += 100 * (len(me) - len(opp))

    # Advancement toward opponent's home row
    my_advance = 0
    for r, c in me:
        if color == 'w':
            dist = r  # distance from my home (row 0)
        else:
            dist = 7 - r
        # Exponential reward for being very close to promotion
        if dist == 6:
            my_advance += 10000  # one step from winning
        elif dist == 5:
            my_advance += 500
        elif dist == 4:
            my_advance += 200
        elif dist == 3:
            my_advance += 80
        elif dist == 2:
            my_advance += 30
        else:
            my_advance += 10

    opp_advance = 0
    for r, c in opp:
        if color == 'w':
            dist = 7 - r  # opponent's distance from row 7
        else:
            dist = r
        if dist == 6:
            opp_advance += 10000
        elif dist == 5:
            opp_advance += 500
        elif dist == 4:
            opp_advance += 200
        elif dist == 3:
            opp_advance += 80
        elif dist == 2:
            opp_advance += 30
        else:
            opp_advance += 10

    score += my_advance - opp_advance

    # Center control bonus
    center_files = {3, 4}
    for r, c in me:
        if c in center_files:
            score += 5
    for r, c in opp:
        if c in center_files:
            score -= 5

    # Penalty for isolated / doubled pawns
    my_cols = defaultdict(int)
    for r, c in me:
        my_cols[c] += 1
    for c, cnt in my_cols.items():
        if cnt > 1:
            score -= 8
        left = c - 1 in my_cols
        right = c + 1 in my_cols
        if not left and not right:
            score -= 5

    opp_cols = defaultdict(int)
    for r, c in opp:
        opp_cols[c] += 1
    for c, cnt in opp_cols.items():
        if cnt > 1:
            score += 8
        left = c - 1 in opp_cols
        right = c + 1 in opp_cols
        if not left and not right:
            score += 5

    return score

# ---------------------------------------------------------------------------
# Move generation
# ---------------------------------------------------------------------------
def generate_moves(me, opp, color):
    """
    Generate all legal moves for 'color' given 'me' (our pieces) and 'opp'.
    Returns list of ((from_r, from_c), (to_r, to_c)).
    """
    if color == 'w':
        direction = 1
    else:
        direction = -1

    occupied_me = set(me)
    occupied_opp = set(opp)
    all_occupied = occupied_me | occupied_opp
    moves = []

    for r, c in me:
        # Straight move
        nr = r + direction
        nc = c
        if 0 <= nr <= 7 and (nr, nc) not in all_occupied:
            moves.append(((r, c), (nr, nc)))

        # Diagonal captures (and diagonal non-captures)
        for dc in (-1, 1):
            nc2 = c + dc
            if 0 <= nc2 <= 7:
                nr2 = r + direction
                if 0 <= nr2 <= 7:
                    if (nr2, nc2) in occupied_opp:
                        moves.append(((r, c), (nr2, nc2)))
                    elif (nr2, nc2) not in all_occupied:
                        moves.append(((r, c), (nr2, nc2)))

    return moves

def is_winning_move(me, opp, color, move):
    """Check if move immediately wins (reaches opponent's home row or captures last piece)."""
    (fr, fc), (tr, tc) = move
    if color == 'w' and tr == 7:
        return True
    if color == 'b' and tr == 0:
        return True
    # Check if capturing the last opponent piece
    if (tr, tc) in set(opp) and len(opp) == 1:
        return True
    return False

def apply_move(me, opp, move):
    """Return (new_me, new_opp) after applying move."""
    (fr, fc), (tr, tc) = move
    new_me = set(me)
    new_opp = set(opp)
    new_me.remove((fr, fc))
    new_me.add((tr, tc))
    if (tr, tc) in new_opp:
        new_opp.remove((tr, tc))
    return list(new_me), list(new_opp)

# ---------------------------------------------------------------------------
# Move ordering
# ---------------------------------------------------------------------------
def order_moves(me, opp, color, moves):
    """Order moves to improve pruning efficiency."""
    def move_priority(move):
        (fr, fc), (tr, tc) = move
        # Winning moves first
        if is_winning_move(me, opp, color, move):
            return 0
        # Captures before non-captures
        is_capture = (tr, tc) in set(opp)
        capture_score = 0 if is_capture else 1
        # Advancement (closer to promotion)
        if color == 'w':
            advance = -tr
        else:
            advance = tr
        # Center preference
        center = abs(tc - 3.5)
        return (capture_score, advance, center)
    
    return sorted(moves, key=move_priority)

# ---------------------------------------------------------------------------
# Transposition table
# ---------------------------------------------------------------------------
TT = {}  # hash -> (depth, value, flag, best_move)  flag: 0=exact, 1=lower, 2=upper
TT_HIT = 0
TT_MISS = 0

# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------
def minimax(me, opp, color, depth, alpha, beta, maximizing, start_time, time_limit):
    """
    Minimax with alpha-beta and transposition table.
    Returns (score, best_move).
    """
    # Time check
    if time.time() - start_time > time_limit:
        raise TimeoutError()

    # Terminal checks
    if len(opp) == 0:
        return (100000 + depth, None)  # win
    if len(me) == 0:
        return (-100000 - depth, None)  # loss

    # Check for immediate wins
    for r, c in me:
        if (color == 'w' and r == 7) or (color == 'b' and r == 0):
            return (100000 + depth, None)

    if depth == 0:
        return (evaluate(me, opp, color), None)

    # Transposition table
    h = _compute_hash(me, opp, color)
    if h in TT:
        tt_depth, tt_value, tt_flag, tt_move = TT[h]
        if tt_depth >= depth:
            if tt_flag == 0:  # exact
                return (tt_value, tt_move)
            elif tt_flag == 1:  # lower bound
                alpha = max(alpha, tt_value)
            elif tt_flag == 2:  # upper bound
                beta = min(beta, tt_value)
            if alpha >= beta:
                return (tt_value, tt_move)

    moves = generate_moves(me, opp, color)
    if not moves:
        return (-100000 - depth, None)  # no moves = loss

    moves = order_moves(me, opp, color, moves)

    if maximizing:
        best_score = -float('inf')
        best_move = moves[0]
        for move in moves:
            new_me, new_opp = apply_move(me, opp, move)
            next_color = 'w' if color == 'b' else 'b'
            try:
                score, _ = minimax(new_opp, new_me, next_color, depth - 1, alpha, beta, False, start_time, time_limit)
            except TimeoutError:
                raise
            if score > best_score:
                best_score = score
                best_move = move
            alpha = max(alpha, score)
            if alpha >= beta:
                break
        
        # Store in TT
        flag = 0
        if best_score <= alpha:
            flag = 2  # upper bound
        elif best_score >= beta:
            flag = 1  # lower bound
        TT[h] = (depth, best_score, flag, best_move)
        return (best_score, best_move)
    else:
        best_score = float('inf')
        best_move = moves[0]
        for move in moves:
            new_me, new_opp = apply_move(me, opp, move)
            next_color = 'w' if color == 'b' else 'b'
            try:
                score, _ = minimax(new_opp, new_me, next_color, depth - 1, alpha, beta, True, start_time, time_limit)
            except TimeoutError:
                raise
            if score < best_score:
                best_score = score
                best_move = move
            beta = min(beta, score)
            if alpha >= beta:
                break
        
        flag = 0
        if best_score <= alpha:
            flag = 2
        elif best_score >= beta:
            flag = 1
        TT[h] = (depth, best_score, flag, best_move)
        return (best_score, best_move)

def iterative_deepening(me, opp, color, time_limit=0.95):
    """Iterative deepening search."""
    global TT
    TT.clear()
    start_time = time.time()
    best_move = None
    best_score = None

    try:
        for depth in range(1, 100):
            score, move = minimax(me, opp, color, depth, -float('inf'), float('inf'), True, start_time, time_limit)
            if move is not None:
                best_move = move
                best_score = score
            # If we found a win, just return it
            if best_score is not None and best_score > 90000:
                break
    except TimeoutError:
        pass

    if best_move is None:
        # Fallback: return first legal move
        moves = generate_moves(me, opp, color)
        if moves:
            best_move = moves[0]

    return best_move

# ---------------------------------------------------------------------------
# Required API
# ---------------------------------------------------------------------------
def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    """
    Return the next move for Breakthrough.
    """
    move = iterative_deepening(me, opp, color)
    
    # Safety fallback: ensure move is legal
    if move is None:
        moves = generate_moves(me, opp, color)
        if moves:
            move = random.choice(moves)
        else:
            # Should never happen unless we have no pieces
            return ((0, 0), (0, 0))
    
    # Verify legality
    moves = generate_moves(me, opp, color)
    if move not in moves:
        move = moves[0] if moves else ((0, 0), (0, 0))
    
    return move
