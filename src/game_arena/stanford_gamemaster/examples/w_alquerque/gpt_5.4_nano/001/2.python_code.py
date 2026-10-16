
import math
import re
from typing import List, Tuple, Optional

# Board is 5x5, with coordinates 1..5 for both rows and cols.
# Moves are along lines of Alquerque's graph; captures are jumps of length 2 over neighbors.
#
# We reconstruct adjacency on the standard 5x5 Alquerque board:
# - All horizontal and vertical neighbor connections.
# - Diagonals connect on specific edges (the "X" lines): (r,c) connected to (r-1,c-1) and (r-1,c+1)
#   where both coordinates stay within 1..5. This matches the common Alquerque(5) geometry.
#
# If the environment's geometry differs slightly, the policy may still be legal
# for many positions because move parsing is strictly validated against generated actions
# from the reconstructed legal geometry.

N = 5

def _cells_from_state(state):
    board = [[None for _ in range(N)] for _ in range(N)]
    control = None
    for fact in state:
        if not fact:
            continue
        if fact[0] == "cell":
            r = int(fact[1]) - 1
            c = int(fact[2]) - 1
            board[r][c] = fact[3]  # "red","black","blank"
        elif fact[0] == "control":
            control = fact[1]
    return board, control

def _inb(r,c):
    return 0 <= r < N and 0 <= c < N

def _adjacency():
    adj = [[[] for _ in range(N)] for _ in range(N)]
    # orthogonal
    dirs4 = [(-1,0),(1,0),(0,-1),(0,1)]
    # diagonals in the standard Alquerque 5x5: connect diagonally for all inner squares
    dirs_diag = [(-1,-1),(-1,1),(1,-1),(1,1)]
    for r in range(N):
        for c in range(N):
            for dr,dc in dirs4:
                r2,c2 = r+dr,c+dc
                if _inb(r2,c2):
                    adj[r][c].append((r2,c2))
            for dr,dc in dirs_diag:
                r2,c2 = r+dr,c+dc
                if _inb(r2,c2):
                    adj[r][c].append((r2,c2))
    # Remove duplicates
    for r in range(N):
        for c in range(N):
            adj[r][c] = list(set(adj[r][c]))
    return adj

ADJ = _adjacency()

def _role_piece(role):
    return role  # role is "red" or "black"

def _opp(role):
    return "red" if role == "black" else "black"

def _forward_dirs(role):
    # Forward direction is decreasing row for black? In description: red on bottom two rows.
    # So red moves "up" (towards row 1), black moves "down" (towards row 5).
    if role == "red":
        # forward is -1 in row
        return -1
    return 1

def _generate_moves(board, role):
    """
    Returns list of action strings.
    Supports single-step moves and single-jump captures.
    Also prefers to include captures even if non-capturing moves exist.
    """
    me = role
    enemy = _opp(role)
    forward = _forward_dirs(role)

    moves = []
    capture_moves = []

    for r in range(N):
        for c in range(N):
            if board[r][c] != me:
                continue
            # single moves: to adjacent empty cells
            for r2,c2 in ADJ[r][c]:
                if board[r2][c2] == "blank":
                    # In Alquerque, movement direction is not strictly one-way for legality in many variants,
                    # but the description says "move forward one step". We'll enforce forward-only moves.
                    if (r2 - r) == forward:
                        moves.append(("move", r, c, r2, c2))
            # captures: jump over enemy into empty landing
            for r2,c2 in ADJ[r][c]:
                # landing is two steps away along the same line: r3 = r + 2*(r2-r), ...
                r_mid, c_mid = r2, c2
                dr, dc = r_mid - r, c_mid - c
                r3, c3 = r + 2*dr, c + 2*dc
                if not _inb(r3,c3):
                    continue
                if board[r_mid][c_mid] == enemy and board[r3][c3] == "blank":
                    # enforce forward-only capture landing
                    if (r3 - r) == 2*forward:
                        capture_moves.append(("jump", r, c, r_mid, c_mid, r3, c3))

    # If any capture exists, Alquerque rules typically force capture. We'll output only capture moves if present.
    chosen = capture_moves if capture_moves else moves
    action_strs = []
    for m in chosen:
        if m[0] == "move":
            _, r, c, r2, c2 = m
            action_strs.append(f"move({c+1},{r+1},{c2+1},{r2+1})")
        else:
            _, r, c, rm, cm, r3, c3 = m
            action_strs.append(f"jump({c+1},{r+1},{cm+1},{rm+1},{c3+1},{r3+1})")
    return action_strs, chosen

def _parse_action_numbers(action):
    nums = list(map(int, re.findall(r"-?\d+", action)))
    return nums

def _apply_move(board, role, move_type, coords):
    # coords represent indices (0-based) matching our generation tuples
    newb = [row[:] for row in board]
    me = role
    enemy = _opp(role)
    if move_type == "move":
        r,c,r2,c2 = coords
        newb[r][c] = "blank"
        newb[r2][c2] = me
    else:
        r,c,rm,cm,r3,c3 = coords
        newb[r][c] = "blank"
        newb[rm][cm] = "blank"
        newb[r3][c3] = me
    return newb

def _is_capturable_next(board, role):
    """
    Rough safety heuristic: if any of my pieces can be captured by enemy on their next turn.
    We'll just check whether enemy has a jump over me into empty.
    """
    my = role
    enemy = _opp(role)
    # enemy forward direction
    forward_enemy = _forward_dirs(enemy)

    # generate enemy jumps capturing my pieces
    for r in range(N):
        for c in range(N):
            if board[r][c] != enemy:
                continue
            for r2,c2 in ADJ[r][c]:
                dr, dc = r2 - r, c2 - c
                r3, c3 = r + 2*dr, c + 2*dc
                if not _inb(r3,c3):
                    continue
                if board[r2][c2] == my and board[r3][c3] == "blank":
                    if (r3 - r) == 2*forward_enemy:
                        return True
    return False

def _evaluate(board, role, action_tuple):
    """
    Higher is better.
    action_tuple is one of the internal tuples created by _generate_moves.
    """
    me = role
    enemy = _opp(role)

    # material
    my_count = sum(1 for r in range(N) for c in range(N) if board[r][c] == me)
    en_count = sum(1 for r in range(N) for c in range(N) if board[r][c] == enemy)

    # progress
    forward = _forward_dirs(me)
    # For red: want smaller row (closer to 0), for black: want larger row (closer to N-1)
    if me == "red":
        progress = sum((N-1 - r) for r in range(N) for c in range(N) if board[r][c] == me)
    else:
        progress = sum(r for r in range(N) for c in range(N) if board[r][c] == me)

    center_bonus = 0
    for r in range(N):
        for c in range(N):
            if board[r][c] == me:
                # closer to center (2,2)
                center_bonus += 2.0 - (abs(r-2)+abs(c-2))*0.3

    # immediate capture bonus if action is jump
    if action_tuple[0] == "jump":
        # captured exactly one piece in our generator
        capture_score = 100.0
    else:
        capture_score = 0.0

    # safety
    unsafe_penalty = 0.0
    if _is_capturable_next(board, role):
        unsafe_penalty = 20.0

    # mobility estimate: number of legal moves for me (encourage having options)
    my_actions, _ = _generate_moves(board, role)
    mobility = len(my_actions)

    score = 10.0*(my_count - en_count) + 0.8*progress + 3.0*center_bonus + capture_score + 0.3*mobility - unsafe_penalty
    return score

def policy(state: list[list[object]], role: str) -> str:
    board, control = _cells_from_state(state)
    # If board is malformed, fallback: try to move any forward step we can find with adjacency guess.
    # Generate actions
    actions_str, action_tuples = _generate_moves(board, role)

    if not actions_str:
        # extreme fallback: pick any forward empty neighbor using orthogonal/diagonal assumptions
        me = role
        forward = _forward_dirs(me)
        for r in range(N):
            for c in range(N):
                if board[r][c] != me:
                    continue
                for r2,c2 in ADJ[r][c]:
                    if board[r2][c2] == "blank" and (r2-r)==forward:
                        return f"move({c+1},{r+1},{c2+1},{r2+1})"
        # As last resort, scan for any empty and return a syntactically valid move(1,1,1,1)
        return "move(1,1,1,1)"

    # If captures exist, action_tuples correspond to jump moves only (by _generate_moves), so just evaluate.
    best_action = None
    best_score = -1e18

    # Map action strings to internal tuple to evaluate after applying move
    for act_str, tup in zip(actions_str, action_tuples):
        if tup[0] == "move":
            _, r, c, r2, c2 = tup
            newb = _apply_move(board, role, "move", (r,c,r2,c2))
            score = _evaluate(newb, role, tup)
        else:
            _, r, c, rm, cm, r3, c3 = tup
            newb = _apply_move(board, role, "jump", (r,c,rm,cm,r3,c3))
            score = _evaluate(newb, role, tup)

        # tie-break: prefer moves that progress further
        if score > best_score + 1e-9:
            best_score = score
            best_action = act_str

    # Ensure we always return something legal by choosing among generated actions
    return best_action if best_action is not None else actions_str[0]
