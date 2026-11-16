
import numpy as np

def policy(board) -> str:
    """
    Amazons on a 6x6 board.
    board: 6x6 numpy array with values:
      0 empty, 1 our amazon, 2 opponent amazon, -1 arrow (blocked)
    returns: "fr,fc:tr,tc:ar,ac"
    """
    b = np.array(board, copy=False)
    N = 6

    # Directions: 8 queen directions
    dirs = [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]

    # Locate pieces
    my_pos = np.argwhere(b == 1)
    opp_pos = np.argwhere(b == 2)

    def inb(r, c):
        return 0 <= r < N and 0 <= c < N

    def ray_moves_from(fr, fc, occ):
        """Yield (tr,tc) reachable by queen move from fr,fc given occ as blocked grid (1D check)."""
        for dr, dc in dirs:
            r, c = fr + dr, fc + dc
            while inb(r, c) and occ[r, c] == 0:
                yield (r, c)
                r += dr
                c += dc

    def ray_shots_from(tr, tc, occ):
        """Yield (ar,ac) reachable by arrow shot from tr,tc given occ grid blocked."""
        for dr, dc in dirs:
            r, c = tr + dr, tc + dc
            while inb(r, c) and occ[r, c] == 0:
                yield (r, c)
                r += dr
                c += dc

    # Build occupancy with current board
    # We'll treat any non-zero as blocked for move generation.
    # board already uses -1/1/2, so blocked if !=0.
    blocked0 = (b != 0).astype(np.int8)

    # If no pieces, return a safe dummy (shouldn't happen in valid games)
    if len(my_pos) == 0:
        return "0,0:0,0:0,0"

    def count_legal_moves_for(side_blocked, my_positions):
        """Count legal (move+shot) sequences for current side given blocked grid.
        side_blocked: blocked mask (1 means occupied/blocked)
        my_positions: list of (r,c)
        """
        total = 0
        for fr, fc in my_positions:
            # Generate destinations for amazon move
            occ = side_blocked
            # For move destinations, we need fr to be treated as empty temporarily (since amazon vacates).
            # We'll just compute rays with a temporary occupancy grid per start.
            occ2 = occ.copy()
            occ2[fr, fc] = 0
            for tr, tc in ray_moves_from(fr, fc, occ2):
                # After amazon moves to (tr,tc), that square becomes occupied by amazon for shooting purposes.
                occ3 = occ2.copy()
                occ3[tr, tc] = 1
                # Shoot arrows from (tr,tc); landing arrow square must be empty (0) in occ3.
                for _ in ray_shots_from(tr, tc, occ3):
                    total += 1
        return total

    # Precompute center weights
    center = np.array([2.5, 2.5])
    def pos_score(r, c):
        # Prefer closer to center slightly
        d = (r - center[0])**2 + (c - center[1])**2
        return -d

    # Heuristic:
    # score = (our mobility after move) - (opp mobility after move) + small positional term
    # Also prefer moves that increase distance from opponent (avoid direct confrontation isn't always relevant on Amazons)
    # We'll compute opponent mobility after our move assuming opponent doesn't move yet.
    best_move = None
    best_score = -10**18

    # To make it faster, compute opponent positions once
    opp_positions = [tuple(x) for x in opp_pos]

    # For tie-breaking determinism
    def move_key(move_str):
        fr, rest = move_str.split(":")
        tr, tc = fr.split(",")[1:], None
        # We'll just return move_str itself; lexicographic is deterministic
        return move_str

    # Generate all our legal moves (move+shot)
    # For efficiency we will evaluate only a subset if needed, but on 6x6 it's manageable.
    # Evaluate all.
    occ_base = blocked0

    for fr, fc in my_pos:
        fr = int(fr); fc = int(fc)

        # Occupancy after vacating fr
        occ_after_vacate = occ_base.copy()
        occ_after_vacate[fr, fc] = 0

        for tr, tc in ray_moves_from(fr, fc, occ_after_vacate):
            tr = int(tr); tc = int(tc)

            # Occupancy with amazon placed at to for arrow shooting
            occ_after_move = occ_after_vacate.copy()
            occ_after_move[tr, tc] = 1  # treat amazon as blocked for arrow placement

            # Possible arrow shots
            for ar, ac in ray_shots_from(tr, tc, occ_after_move):
                ar = int(ar); ac = int(ac)

                # Create new board occupancy for mobility scoring
                occ_new = occ_after_move.copy()
                occ_new[ar, ac] = 1  # arrow blocks

                # Build our new amazon positions (since only one amazon moved)
                # We'll keep it simple: determine positions list
                # (This is small; avoid expensive full board updates.)
                my_positions_new = []
                # All our amazons except (fr,fc) plus (tr,tc)
                for rr, cc in my_pos:
                    rr = int(rr); cc = int(cc)
                    if rr == fr and cc == fc:
                        continue
                    my_positions_new.append((rr, cc))
                my_positions_new.append((tr, tc))

                # Opponent mobility after our move
                # For opponent move generation, opponent positions are fixed, but blocked map includes our moved amazon and arrow.
                opp_mob = count_legal_moves_for(occ_new, opp_positions)

                # Our mobility after our move (optional; can help)
                my_mob = count_legal_moves_for(occ_new, my_positions_new)

                # Positional term
                pos_term = 0.2 * (pos_score(tr, tc))

                # Small "escape" term: prefer being farther from opponent average position
                if len(opp_positions) > 0:
                    avg_r = sum(p[0] for p in opp_positions) / len(opp_positions)
                    avg_c = sum(p[1] for p in opp_positions) / len(opp_positions)
                    dist2 = (tr - avg_r)**2 + (tc - avg_c)**2
                    escape_term = 0.05 * dist2
                else:
                    escape_term = 0.0

                # Main score: maximize our mobility, minimize opponent mobility.
                score = (my_mob - opp_mob) + pos_term + escape_term

                # If opponent has no moves, this should be best (win), so amplify
                if opp_mob == 0:
                    score += 10**6

                move_str = f"{fr},{fc}:{tr},{tc}:{ar},{ac}"

                # Select best (max score), tie-break lexicographically
                if (score > best_score) or (score == best_score and (best_move is None or move_str < best_move)):
                    best_score = score
                    best_move = move_str

    # Fallback: if somehow no move generated (shouldn't happen), return any legal-looking move
    if best_move is None:
        # Try a simple first available move
        for fr, fc in my_pos:
            fr = int(fr); fc = int(fc)
            occ_after_vacate = occ_base.copy()
            occ_after_vacate[fr, fc] = 0
            for tr, tc in ray_moves_from(fr, fc, occ_after_vacate):
                occ_after_move = occ_after_vacate.copy()
                occ_after_move[tr, tc] = 1
                for ar, ac in ray_shots_from(tr, tc, occ_after_move):
                    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"
        return "0,0:0,0:0,0"

    return best_move
