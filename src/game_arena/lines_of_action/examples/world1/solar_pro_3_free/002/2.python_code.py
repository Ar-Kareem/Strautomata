
import random
from typing import List, Tuple

# LoA direction vectors: (dr, dc)
DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1),
        (-1, -1), (1, 1), (-1, 1), (1, -1)]

def policy(board: List[List[int]]) -> str:
    """
    Returns a legal move string for the player with pieces = 1.
    Format: "row,column:to_row,to_column"
    """
    N = len(board)               # board size (always 8 in the arena)

    # --------------------------------------------------------------------
    # Helper functions
    # --------------------------------------------------------------------
    def parse_move(m: str) -> Tuple[int, int, int, int]:
        """Extract source and target coordinates from a move string."""
        src, tgt = m.split(":")
        sr, sc = map(int, src.split(","))
        tr, tc = map(int, tgt.split(","))
        return sr, sc, tr, tc

    def distance_to_nearest_other(target: Tuple[int, int], source: Tuple[int, int]) -> int:
        """Manhattan distance from target to any friendly piece other than the moving one."""
        min_d = float('inf')
        for pr, pc in own_pos:
            if (pr, pc) == (source[0], source[1]):
                continue
            d = abs(target[0] - pr) + abs(target[1] - pc)
            if d < min_d:
                min_d = d
        return min_d

    def generate_legal_moves() -> Set[str]:
        """Compute all legal moves for the current player."""
        legal = set()
        own_pos = [(r, c) for r in range(N) for c in range(N) if board[r][c] == 1]
        for r, c in own_pos:
            for dr, dc in DIRS:
                # Count pieces forward and backward
                forward_cnt = 0
                rr, cc = r + dr, c + dc
                while 0 <= rr < N and 0 <= cc < N:
                    if board[rr][cc] != 0:
                        forward_cnt += 1
                    rr += dr
                    cc += dc

                backward_cnt = 0
                rr, cc = r - dr, c - dc
                while 0 <= rr < N and 0 <= cc < N:
                    if board[rr][cc] != 0:
                        backward_cnt += 1
                    rr -= dr
                    cc -= dc

                total_pieces = forward_cnt + backward_cnt + 1
                tr = r + total_pieces * dr
                tc = c + total_pieces * dc

                if not (0 <= tr < N and 0 <= tc < N):
                    continue   # move would leave the board

                # Check for enemy pieces on the path (excluding target)
                blocked = False
                rr, cc = r + dr, c + dc
                for step in range(1, total_pieces):
                    if not (0 <= rr < N and 0 <= cc < N):
                        # The target is inside the board but we ran out of squares early → illegal
                        blocked = True
                        break
                    if board[rr][cc] == -1:
                        blocked = True
                        break
                    rr += dr
                    cc += dc
                if blocked:
                    continue

                # Cannot land on a friendly piece
                if board[tr][tc] == 1:
                    continue

                legal.add(f"{r},{c}:{tr},{tc}")
        return legal

    # --------------------------------------------------------------------
    # Compute legal moves
    # --------------------------------------------------------------------
    legal_moves = generate_legal_moves()
    if not legal_moves:
        # This should never happen in a valid LoA position, but we return a dummy
        # move (the arena will consider the player stuck).  In practice the arena
        # always provides at least one legal move.
        return "0,0:1,1"

    # Separate captures from non‑captures
    capture_moves = []
    non_capture_moves = []
    parsed = []
    for mv in legal_moves:
        sr, sc, tr, tc = parse_move(mv)
        parsed.append((mv, sr, sc, tr, tc))
        if board[tr][tc] == -1:
            capture_moves.append(parsed[-1])
        else:
            non_capture_moves.append(parsed[-1])

    # Heuristic score: distance to nearest own piece after the move
    def score(move_info):
        _, _, _, _, target = move_info
        sr, sc = move_info[1], move_info[2]
        return distance_to_nearest_other(target, (sr, sc))

    # --------------------------------------------------------------------
    # Choose the best move
    # --------------------------------------------------------------------
    if capture_moves:
        # Capture first, then closest to a friend
        candidates = capture_moves
    else:
        # Connect pieces
        candidates = non_capture_moves

    scores = [(score(mv), mv) for mv in candidates]
    # Sort by distance, ties are broken randomly
    scores.sort(key=lambda x: x[0])
    best = scores[0][1]
    # Random tie‑breaker for moves with identical distances
    min_score = scores[0][0]
    best_set = [mv[1] for mv in scores if mv[0] == min_score]
    return random.choice(best_set)
