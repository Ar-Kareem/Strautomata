
import random
import time
from typing import List, Tuple, Set

# Type aliases
Pos = Tuple[int, int]
Move = Tuple[Pos, Pos]

INF = 10**6

def policy(me: List[Pos], opp: List[Pos], color: str) -> Move:
    """
    Decide a move for Breakthrough on an 8x8 board.
    me: list of (row, col) for my pieces
    opp: list of (row, col) for opponent pieces
    color: 'b' or 'w' - 'b' moves downwards (to lower row values), 'w' moves upwards (to higher row values)
    Returns a legal move ((from_row, from_col), (to_row, to_col))
    """
    # Convert to sets for fast operations
    me_set = set(me)
    opp_set = set(opp)
    root_color = color

    # Direction and goal row for a given color
    def dir_for(c: str) -> int:
        return 1 if c == 'w' else -1

    def goal_row_for(c: str) -> int:
        return 7 if c == 'w' else 0

    # Generate all legal moves for side with pieces 'pieces' and opponent 'enemies'
    def generate_moves(pieces: Set[Pos], enemies: Set[Pos], c: str):
        moves = []
        d = dir_for(c)
        for (r, col) in pieces:
            nr = r + d
            if 0 <= nr <= 7:
                # forward
                if (nr, col) not in pieces and (nr, col) not in enemies:
                    moves.append(((r, col), (nr, col)))
                # diagonal left
                nc = col - 1
                if 0 <= nc <= 7:
                    if (nr, nc) in enemies:
                        moves.append(((r, col), (nr, nc)))
                    elif (nr, nc) not in pieces and (nr, nc) not in enemies:
                        # diagonal non-capturing is allowed
                        moves.append(((r, col), (nr, nc)))
                # diagonal right
                nc = col + 1
                if 0 <= nc <= 7:
                    if (nr, nc) in enemies:
                        moves.append(((r, col), (nr, nc)))
                    elif (nr, nc) not in pieces and (nr, nc) not in enemies:
                        moves.append(((r, col), (nr, nc)))
        return moves

    # Apply a move, returning new sets
    def apply_move(pieces: Set[Pos], enemies: Set[Pos], move: Move):
        (fr, fc), (tr, tc) = move
        new_pieces = set(pieces)
        new_enemies = set(enemies)
        new_pieces.remove((fr, fc))
        # capture?
        if (tr, tc) in new_enemies:
            new_enemies.remove((tr, tc))
        new_pieces.add((tr, tc))
        return new_pieces, new_enemies

    # Quick terminal checks
    def is_win(pieces: Set[Pos], enemies: Set[Pos], c: str) -> bool:
        # Win if any piece reaches opponent home row or opponent has no pieces
        if not enemies:
            return True
        g = goal_row_for(c)
        for (r, _) in pieces:
            if r == g:
                return True
        return False

    # For evaluating vulnerability: can the opponent capture a given square next move?
    def vulnerable_positions(pieces: Set[Pos], enemies: Set[Pos], enemies_color: str) -> Set[Pos]:
        # Return set of positions in 'pieces' that can be captured by enemies in one move
        vuln = set()
        ed = dir_for(enemies_color)
        # enemies at (er, ec) can capture to (er+ed, ec±1)
        for (er, ec) in enemies:
            tr = er + ed
            if 0 <= tr <= 7:
                for tc in (ec - 1, ec + 1):
                    if 0 <= tc <= 7 and (tr, tc) in pieces:
                        vuln.add((tr, tc))
        return vuln

    # Evaluation function from perspective of root_color (positive = good for root)
    def evaluate(me_p: Set[Pos], opp_p: Set[Pos], me_color: str) -> float:
        # Map which set belongs to root
        root_is_me = (me_color == root_color)
        if root_is_me:
            root_set = me_p
            other_set = opp_p
            root_col = me_color
            other_col = 'w' if me_color == 'b' else 'b'
        else:
            root_set = opp_p
            other_set = me_p
            root_col = 'w' if me_color == 'b' else 'b'
            other_col = me_color

        # Terminal wins
        if is_win(root_set, other_set, root_col):
            return INF
        if is_win(other_set, root_set, other_col):
            return -INF

        # Material
        mat = 100 * (len(root_set) - len(other_set))

        # Advancement: pieces closer to opponent home row are better
        adv = 0.0
        # normalize by 7 (distance)
        goal_row = goal_row_for(root_col)
        for (r, _) in root_set:
            dist = abs(goal_row - r)
            adv += (7 - dist) / 7.0
        for (r, _) in other_set:
            dist = abs(goal_row - r)
            adv -= 0.9 * ((7 - dist) / 7.0)  # slightly less weight for opponent advancement

        adv_score = 40 * adv

        # Vulnerability: pieces that can be captured next move are penalized
        root_vuln = vulnerable_positions(root_set, other_set, other_col)
        other_vuln = vulnerable_positions(other_set, root_set, root_col)
        vuln_score = -30 * len(root_vuln) + 15 * len(other_vuln)

        # Mobility: number of moves
        root_moves = len(generate_moves(root_set, other_set, root_col))
        other_moves = len(generate_moves(other_set, root_set, other_col))
        mob_score = 5 * (root_moves - other_moves)

        total = mat + adv_score + vuln_score + mob_score
        return total

    # Alpha-beta minimax. 'me_p' is set for side to move, 'me_color' is its color.
    # We always evaluate from root_color perspective.
    def alphabeta(me_p: Set[Pos], opp_p: Set[Pos], me_color: str, depth: int, alpha: float, beta: float, start_time: float, time_limit: float) -> Tuple[float, Move]:
        # Time check
        if time.time() - start_time > time_limit:
            # Abort by returning current eval without move
            return evaluate(me_p, opp_p, me_color), None

        # Terminal
        if is_win(me_p, opp_p, me_color):
            return INF, None
        if is_win(opp_p, me_p, 'w' if me_color == 'b' else 'b'):
            return -INF, None
        if depth == 0:
            return evaluate(me_p, opp_p, me_color), None

        moves = generate_moves(me_p, opp_p, me_color)
        if not moves:
            # No moves: losing-ish position
            return -INF / 2, None

        # Order moves: captures and goal-reaching moves first
        def move_key(mv):
            (fr, fc), (tr, tc) = mv
            score = 0
            # capture?
            if (tr, tc) in opp_p:
                score += 1000
            # reaches goal?
            if tr == goal_row_for(me_color):
                score += 800
            # advancement delta
            score += (tr - fr) * dir_for(me_color) * 10
            return -score  # negative because sorted ascending

        moves.sort(key=move_key)

        best_move = None
        maximizing = True  # we are always maximizing for the side to move in this implementation
        for mv in moves:
            new_me, new_opp = apply_move(me_p, opp_p, mv)
            # Next node: opponent to move; swap roles
            val, _ = alphabeta(new_opp, new_me, 'w' if me_color == 'b' else 'b', depth - 1, -beta, -alpha, start_time, time_limit)
            val = -val  # because we swapped perspective
            if val > alpha:
                alpha = val
                best_move = mv
            if alpha >= beta:
                break
            # time check inside loop
            if time.time() - start_time > time_limit:
                break
        return alpha, best_move

    # Main search
    start = time.time()
    time_limit = 0.90  # seconds; keep a margin
    max_depth = 3  # shallow but effective
    best_move = None
    best_score = -INF

    moves0 = generate_moves(me_set, opp_set, color)
    # If no moves (shouldn't happen in proper game), just return any legal-ish move
    if not moves0:
        # Try pass or invalid but return something safe: choose a piece and a forward if possible
        for (r, c) in me:
            d = dir_for(color)
            nr = r + d
            if 0 <= nr <= 7:
                for nc in (c, c - 1, c + 1):
                    if 0 <= nc <= 7:
                        # if capture is possible or empty move is legal
                        if (nr, nc) not in me_set:
                            return ((r, c), (nr, nc))
        # fallback: return first piece to itself (invalid but required a move) - but we must return legal move, so random legal move from all board
        # We'll scan opponent positions as capture
        if opp:
            return (me[0], opp[0])
        # absolute fallback (shouldn't happen)
        return (me[0], me[0])

    # Try increasing depth if time allows (here single depth)
    for depth in range(1, max_depth + 1):
        if time.time() - start > time_limit:
            break
        score, mv = alphabeta(me_set, opp_set, color, depth, -INF, INF, start, time_limit)
        if mv is not None:
            best_move = mv
            best_score = score

    # If search failed to find a move within time, pick a greedy fallback: prefer captures and forward progress
    if best_move is None:
        # Greedy selection
        def greedy_key(mv):
            (fr, fc), (tr, tc) = mv
            s = 0
            if (tr, tc) in opp_set:
                s += 1000
            if tr == goal_row_for(color):
                s += 800
            s += (tr - fr) * dir_for(color) * 10
            # prefer center columns slightly
            s -= abs(tc - 3.5)
            return -s
        moves0.sort(key=greedy_key)
        best_move = moves0[0]

    # Ensure move is legal; final safety: if returned move is not legal, pick legal one
    all_moves = set(generate_moves(me_set, opp_set, color))
    if best_move not in all_moves:
        # choose first legal move
        best_move = next(iter(all_moves))

    return best_move

# Simple self-test if run as script (not used by the arena)
if __name__ == "__main__":
    # Starting position example: white on row 0, black on row 7
    white = [(0, i) for i in range(8)]
    black = [(7, i) for i in range(8)]
    move = policy(white, black, 'w')
    print("Example move (white):", move)
