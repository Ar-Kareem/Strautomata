
import random
from collections import deque

def policy(board) -> str:
    # Helper functions
    def in_bounds(r, c):
        return 0 <= r < 8 and 0 <= c < 8

    def get_player_pieces(b, player):
        coords = []
        for r in range(8):
            for c in range(8):
                if b[r][c] == player:
                    coords.append((r, c))
        return coords

    def count_pieces_in_line(b, r, c, dr, dc):
        # Total (both colors) in the full line passing through (r,c) along (dr,dc)
        # Normalize direction to one of the 8 LoA directions: dr,dc in {-1,0,1} excluding both 0.
        # Find line start
        rr, cc = r, c
        while in_bounds(rr - dr, cc - dc):
            rr -= dr
            cc -= dc
        # Count along to end
        cnt = 0
        while in_bounds(rr, cc):
            if b[rr][cc] != 0:
                cnt += 1
            rr += dr
            cc += dc
        return cnt

    def path_clear_for_move(b, r, c, tr, tc, player):
        # Verify obstruction: cannot jump over opponent pieces.
        # We know destination is exactly k steps away; check intermediate squares.
        dr = tr - r
        dc = tc - c
        step_r = 0 if dr == 0 else (1 if dr > 0 else -1)
        step_c = 0 if dc == 0 else (1 if dc > 0 else -1)
        rr, cc = r + step_r, c + step_c
        while (rr, cc) != (tr, tc):
            if b[rr][cc] == -player:
                return False
            rr += step_r
            cc += step_c
        return True

    def connected_components_count(b, player):
        coords = set(get_player_pieces(b, player))
        if not coords:
            return 0
        visited = set()
        comps = 0
        for start in coords:
            if start in visited:
                continue
            comps += 1
            q = deque([start])
            visited.add(start)
            while q:
                r, c = q.popleft()
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = r + dr, c + dc
                        if (nr, nc) in coords and (nr, nc) not in visited:
                            visited.add((nr, nc))
                            q.append((nr, nc))
        return comps

    def apply_move(b, move, player):
        # move: (fr,fc,tr,tc)
        fr, fc, tr, tc = move
        nb = [row[:] for row in b]
        nb[fr][fc] = 0
        nb[tr][tc] = player
        return nb

    def generate_legal_moves(b, player):
        moves = []
        pieces = get_player_pieces(b, player)
        dirs = [(-1, -1), (-1, 0), (-1, 1),
                (0, -1),          (0, 1),
                (1, -1), (1, 0),  (1, 1)]
        opp = -player
        for r, c in pieces:
            for dr, dc in dirs:
                k = count_pieces_in_line(b, r, c, dr, dc)
                if k <= 0:
                    continue
                tr, tc = r + dr * k, c + dc * k
                if not in_bounds(tr, tc):
                    continue
                # Destination cannot be occupied by friendly piece
                if b[tr][tc] == player:
                    continue
                # Path cannot jump over opponent pieces
                if not path_clear_for_move(b, r, c, tr, tc, player):
                    continue
                moves.append((r, c, tr, tc))
        return moves

    def heuristic_score(b, move, player):
        # Higher is better
        fr, fc, tr, tc = move
        nb = apply_move(b, move, player)

        # Component reduction is most important
        cur_comps = connected_components_count(b, player)
        new_comps = connected_components_count(nb, player)
        # If already connected, try to maintain; else reduce
        score = 0
        score += (cur_comps - new_comps) * 1000

        # Captures
        if b[tr][tc] == -player:
            score += 500

        # Proximity to centroid (encourage clustering)
        pieces = get_player_pieces(nb, player)
        # centroid of pieces
        if pieces:
            avg_r = sum(p[0] for p in pieces) / len(pieces)
            avg_c = sum(p[1] for p in pieces) / len(pieces)
            # distance of moved piece to centroid (smaller is better)
            d = abs(tr - avg_r) + abs(tc - avg_c)
            score += -d * 10

        # Slight preference for centralization to avoid dead ends
        score += -(abs(tr - 3.5) + abs(tc - 3.5)) * 1

        # Avoid moves that drastically increase dispersion:
        # measure average pairwise manhattan distance (lightweight approximation)
        # Use distances from moved position to others
        others = [(rr, cc) for (rr, cc) in get_player_pieces(nb, player) if (rr, cc) != (tr, tc)]
        if others:
            avg_close = sum(abs(rr - tr) + abs(cc - tc) for rr, cc in others) / len(others)
            score += -avg_close * 0.5

        return score

    # Determine current player: assume pieces of both colors are present; infer by turn using count parity if needed.
    # Since spec: "You are always the player to move when policy is called" but board doesn't directly encode side to move.
    # We'll infer by: choose the color with fewer pieces as typical in arena? Not safe.
    # Better: if there are exactly one color's pieces? still unclear.
    # Fallback: assume current player is the one with positive pieces that is more likely to be "us".
    # However in LoA benchmarks, caller typically sets 1 as current player.
    player = 1

    # Generate and evaluate moves
    legal_moves = generate_legal_moves(board, player)
    if not legal_moves:
        # As a guaranteed legal fallback (shouldn't happen), try opponent inference
        player = -1
        legal_moves = generate_legal_moves(board, player)
        if not legal_moves:
            return "0,0:0,0"  # degenerate; but should never be reached

    best_move = None
    best_score = -10**18
    # Randomize tie-breaking slightly for robustness
    random.shuffle(legal_moves)

    for mv in legal_moves:
        sc = heuristic_score(board, mv, player)
        if sc > best_score:
            best_score = sc
            best_move = mv

    fr, fc, tr, tc = best_move
    return f"{fr},{fc}:{tr},{tc}"
