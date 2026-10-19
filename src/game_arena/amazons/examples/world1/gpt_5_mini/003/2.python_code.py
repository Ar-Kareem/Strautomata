
import numpy as np

# Policy for Amazons on 6x6 board.
# Always returns a legal move string: "fr,fc:tr,tc:ar,ac"
# Deterministic: iterates your amazons in row-major order and picks
# the move (from,to,arrow) with the largest number of arrow options.

DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]

def in_bounds(r, c):
    return 0 <= r < 6 and 0 <= c < 6

def ray_moves(board, start_r, start_c):
    """
    Return list of reachable squares (r,c) by queen-like moves from (start_r,start_c)
    on the given board. Does not include the start square.
    A square is reachable if all intermediate squares are empty (==0).
    """
    moves = []
    for dr, dc in DIRS:
        r, c = start_r + dr, start_c + dc
        while in_bounds(r, c) and board[r, c] == 0:
            moves.append((r, c))
            r += dr
            c += dc
    return moves

def policy(board) -> str:
    board = np.asarray(board)
    # Positions of our amazons (value == 1)
    my_positions = list(zip(*np.where(board == 1)))
    # Sort deterministically
    my_positions = sorted(my_positions)
    best_move = None
    best_arrow_options = -1

    # Enumerate all legal moves
    for fr, fc in my_positions:
        # From-square must contain our amazon (it does)
        # Find all legal landing squares in original board
        landing_squares = ray_moves(board, fr, fc)
        for tr, tc in landing_squares:
            # Simulate move: amazon vacates (fr,fc) and occupies (tr,tc)
            board2 = board.copy()
            board2[fr, fc] = 0
            board2[tr, tc] = 1
            # From landing square, find all legal arrow shots (queen-like into empty squares)
            arrow_squares = ray_moves(board2, tr, tc)
            if not arrow_squares:
                continue  # cannot shoot an arrow from this landing square -> illegal move
            # Choose the move that gives the most arrow options (tie-breaker first encountered)
            if len(arrow_squares) > best_arrow_options:
                best_arrow_options = len(arrow_squares)
                # choose first arrow square for determinism (could be improved)
                ar, ac = arrow_squares[0]
                best_move = (fr, fc, tr, tc, ar, ac)
                # Early exit if very large number (not necessary on 6x6)
    # As a fallback (shouldn't be needed if there is at least one legal move),
    # do a full brute-force search over all combinations to find any legal move.
    if best_move is None:
        # Brute force: for each from (our amazon), for each possible to (board==0 reachable),
        # for each arrow (reachable from to on updated board), return first found.
        for fr, fc in my_positions:
            # try all board squares as candidate landing and verify path
            for tr in range(6):
                for tc in range(6):
                    if board[tr, tc] != 0:
                        continue
                    # check queen-line path from fr,fc to tr,tc
                    dr = tr - fr
                    dc = tc - fc
                    # must be in a straight line
                    if dr == 0 and dc == 0:
                        continue
                    step_r = 0 if dr == 0 else (dr // abs(dr))
                    step_c = 0 if dc == 0 else (dc // abs(dc))
                    if step_r != 0 and step_c != 0 and abs(dr) != abs(dc):
                        continue
                    if step_r == 0 and step_c == 0:
                        continue
                    # verify path is clear
                    rr, cc = fr + step_r, fc + step_c
                    path_clear = True
                    while (rr, cc) != (tr, tc):
                        if not in_bounds(rr, cc) or board[rr, cc] != 0:
                            path_clear = False
                            break
                        rr += step_r
                        cc += step_c
                    if not path_clear:
                        continue
                    # path to tr,tc exists; now simulate and find arrows
                    board2 = board.copy()
                    board2[fr, fc] = 0
                    board2[tr, tc] = 1
                    arrow_squares = ray_moves(board2, tr, tc)
                    if arrow_squares:
                        ar, ac = arrow_squares[0]
                        best_move = (fr, fc, tr, tc, ar, ac)
                        break
                if best_move is not None:
                    break
            if best_move is not None:
                break

    # At this point we should have a legal move; if not, as a last resort try to find any legal
    # (extremely unlikely given problem guarantees). Return a dummy valid-looking string if all fails.
    if best_move is None:
        # Try to find any move by weaker checks: move to any adjacent empty and arrow to any empty
        # This is a last-ditch effort; construct something legal if possible.
        for fr, fc in my_positions:
            for dr, dc in DIRS:
                tr, tc = fr + dr, fc + dc
                if not in_bounds(tr, tc):
                    continue
                if board[tr, tc] != 0:
                    continue
                board2 = board.copy()
                board2[fr, fc] = 0
                board2[tr, tc] = 1
                for ar, ac in ray_moves(board2, tr, tc):
                    best_move = (fr, fc, tr, tc, ar, ac)
                    break
                if best_move is not None:
                    break
            if best_move is not None:
                break
    if best_move is None:
        # As absolute last resort, return the first syntactically valid move using arbitrary indices.
        # This should never be reached in normal play per problem statement.
        return "0,0:0,1:0,2"

    fr, fc, tr, tc, ar, ac = best_move
    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"
