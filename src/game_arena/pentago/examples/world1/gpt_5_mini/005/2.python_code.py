
import numpy as np

# Pentago policy: returns "row,col,quad,dir"
def policy(you, opponent) -> str:
    """
    you, opponent: 6x6 array-like with 0/1 entries.
    Return move string "row,col,quad,dir" (1-based row/col, quad 0..3, dir 'L' or 'R').
    """
    # Convert to numpy array board: 0 empty, 1 our, 2 opp
    you_arr = np.array(you, dtype=np.int8)
    opp_arr = np.array(opponent, dtype=np.int8)
    board0 = np.zeros((6,6), dtype=np.int8)
    board0[you_arr == 1] = 1
    board0[opp_arr == 1] = 2

    # Precompute all 5-cell windows (start positions and directions)
    windows = []
    dirs = [(0,1),(1,0),(1,1),(1,-1)]
    for r in range(6):
        for c in range(6):
            for dr,dc in dirs:
                r_end = r + dr*4
                c_end = c + dc*4
                if 0 <= r_end < 6 and 0 <= c_end < 6:
                    coords = [(r + k*dr, c + k*dc) for k in range(5)]
                    windows.append(coords)

    # Helper functions
    def rotate_board(board, quad, direction):
        # board is 6x6 numpy array, direction 'L' or 'R'
        r0 = 0 if quad in (0,1) else 3
        c0 = 0 if quad in (0,2) else 3
        sub = board[r0:r0+3, c0:c0+3].copy()
        if direction == 'L':
            sub = np.rot90(sub, 1)
        else:  # 'R'
            sub = np.rot90(sub, -1)
        board2 = board.copy()
        board2[r0:r0+3, c0:c0+3] = sub
        return board2

    def check_win(board, player):
        # True if player (1 or 2) has any 5-in-a-row window
        for coords in windows:
            ok = True
            for (r,c) in coords:
                if board[r,c] != player:
                    ok = False
                    break
            if ok:
                return True
        return False

    # Precompute empty cells
    empties = [(r,c) for r in range(6) for c in range(6) if board0[r,c] == 0]
    rotations = [(q,d) for q in range(4) for d in ('L','R')]

    # Heuristic weights for windows based on number of stones in the 5-window
    own_weights = {0:0, 1:1, 2:10, 3:100, 4:1000, 5:100000}
    opp_weights = {0:0, 1:1, 2:10, 3:100, 4:2000, 5:100000}

    # Precompute center bonus values (prefer center positions slightly)
    center_bonus = np.array([
        [1,2,3,3,2,1],
        [2,4,5,5,4,2],
        [3,5,6,6,5,3],
        [3,5,6,6,5,3],
        [2,4,5,5,4,2],
        [1,2,3,3,2,1]
    ], dtype=np.int8)

    # Compute heuristic score for a board
    def heuristic(board):
        score = 0
        for coords in windows:
            ours = 0
            opps = 0
            for (r,c) in coords:
                v = board[r,c]
                if v == 1:
                    ours += 1
                elif v == 2:
                    opps += 1
            if opps == 0 and ours > 0:
                score += own_weights[ours]
            elif ours == 0 and opps > 0:
                score -= opp_weights[opps]
        return score

    # Check if opponent has a winning reply from a given board state (opponent to move)
    def opponent_has_winning_reply(board):
        empt = [(r,c) for r in range(6) for c in range(6) if board[r,c] == 0]
        # For each opponent move, simulate placement and rotation; if opp can force a win (and we don't also have 5), return True
        for (r,c) in empt:
            for (q,d) in rotations:
                # place opponent marble
                b = board.copy()
                b[r,c] = 2
                b = rotate_board(b, q, d)
                opp_w = check_win(b, 2)
                our_w = check_win(b, 1)
                if opp_w and (not our_w):
                    return True
        return False

    # If any immediate winning move for us exists, return it
    best_move = None
    best_score = -10**9
    best_vulnerable = True  # whether the move allows opponent instant win after reply
    losing_moves = []

    # Before searching, detect if opponent already has a forced win this turn (i.e., they have a winning move right now)
    # If so, we must attempt to block; but the search below will prioritize moves that avoid opponent replies.
    # Iterate all our legal moves
    for (r,c) in empties:
        for (q,d) in rotations:
            b = board0.copy()
            b[r,c] = 1
            b = rotate_board(b, q, d)
            our_win = check_win(b, 1)
            opp_win = check_win(b, 2)
            # If we win and opponent doesn't also have 5, it's a forced win -> pick immediately
            if our_win and (not opp_win):
                # Found winning move, return immediately
                return f"{r+1},{c+1},{q},{d}"
            # If opponent already has 5 after our move (and we don't), this move is immediately losing; skip but record
            if opp_win and (not our_win):
                losing_moves.append((r,c,q,d))
                continue
            # Otherwise compute heuristic and safety
            h = heuristic(b)
            # small center bonus based on placement
            h += int(center_bonus[r,c])
            # Check if opponent has a winning reply to this board (depth-2 check)
            vulnerable = opponent_has_winning_reply(b)
            if vulnerable:
                # Deprioritize heavily
                h -= 20000
            # Choose best by score; prefer non-vulnerable moves in tie-breaker
            if (best_move is None) or (h > best_score) or (h == best_score and (best_vulnerable and not vulnerable)):
                best_score = h
                best_move = (r,c,q,d)
                best_vulnerable = vulnerable

    # If no non-immediately-losing move found, pick a losing move if present
    if best_move is None:
        # Choose first legal losing move (or any legal move if none)
        if losing_moves:
            r,c,q,d = losing_moves[0]
            return f"{r+1},{c+1},{q},{d}"
        else:
            # Fallback: pick first empty and first rotation
            r,c = empties[0]
            q,d = 0,'L'
            return f"{r+1},{c+1},{q},{d}"
    else:
        r,c,q,d = best_move
        return f"{r+1},{c+1},{q},{d}"

# If this module is run standalone, provide a small test to ensure format (not executed during evaluation)
if __name__ == "__main__":
    # Empty board test: choose a center-ish move
    you = [[0]*6 for _ in range(6)]
    opp = [[0]*6 for _ in range(6)]
    print(policy(you, opp))
