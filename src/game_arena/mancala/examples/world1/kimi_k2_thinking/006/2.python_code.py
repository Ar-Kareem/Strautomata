
import time
from typing import List

# ----------------------------------------------------------------------
# Constants
HOUSE_COUNT = 6
STORE_INDEX = 6               # index of the store for the player to move
BOARD_SIZE = 14               # 6 houses + store + 6 opponent houses + opponent store
INF = 10 ** 9

# ----------------------------------------------------------------------
def apply_move(board: List[int], move: int) -> (List[int], bool):
    """
    Apply a move (0‑5) on the given board.
    Returns (new_board, extra_move) where extra_move indicates that the
    player will move again immediately.
    """
    seeds = board[move]
    if seeds == 0:
        raise ValueError("Illegal move – empty house")

    new_board = board[:]                     # copy
    new_board[move] = 0

    cur = (move + 1) % BOARD_SIZE
    while seeds > 0:
        # skip opponent store (index 13)
        if cur == 13:
            cur = (cur + 1) % BOARD_SIZE
            continue
        new_board[cur] += 1
        seeds -= 1
        last = cur
        cur = (cur + 1) % BOARD_SIZE

    extra_move = (last == STORE_INDEX)

    # capture check (only if last seed fell in a house, not the store)
    if not extra_move and 0 <= last <= 5:
        opposite = 12 - last                  # opponent house opposite this house
        if new_board[last] == 1 and new_board[opposite] > 0:
            captured = new_board[last] + new_board[opposite]
            new_board[STORE_INDEX] += captured
            new_board[last] = 0
            new_board[opposite] = 0

    return new_board, extra_move


def swap_perspective(board: List[int]) -> List[int]:
    """Swap the two sides – the opponent becomes the player to move."""
    return board[7:14] + board[0:7]


def is_terminal(board: List[int]) -> bool:
    """True if one side has no seeds in its houses."""
    return sum(board[0:6]) == 0 or sum(board[7:13]) == 0


def terminal_value(board: List[int], root_perspective: bool) -> int:
    """Final evaluation when the game has finished."""
    side0_houses = sum(board[0:6])
    side1_houses = sum(board[7:13])
    side0_store = board[6] + side0_houses
    side1_store = board[13] + side1_houses

    if root_perspective:
        return side0_store - side1_store
    else:
        return side1_store - side0_store


def heuristic_value(board: List[int], root_perspective: bool) -> int:
    """
    Fast heuristic from the root player's point of view.
    Components:
    * store difference (weight 2)
    * house‑seed difference (weight 1)
    * net “capture potential” (player’s empty houses opposite opponent seeds
      minus opponent’s empty houses opposite player seeds, weight 1)
    """
    store_diff = board[6] - board[13]           # from player to move POV
    house_diff = sum(board[0:6]) - sum(board[7:13])

    # capture potential
    player_pot = 0
    opp_pot = 0
    for i in range(6):
        if board[i] == 0 and board[12 - i] > 0:
            player_pot += board[12 - i]        # can capture these seeds
        if board[12 - i] == 0 and board[i] > 0:
            opp_pot += board[i]                # opponent could capture these
    net_pot = player_pot - opp_pot

    value = store_diff * 2 + house_diff + net_pot

    if root_perspective:
        return value
    else:
        return -value


def search(board: List[int], depth: int, alpha: int, beta: int,
           root_perspective: bool) -> int:
    """
    Alpha‑beta recursion.
    `root_perspective` tells whether the board is seen from the original
    player's viewpoint (True → maximizing, False → minimizing).
    """
    if is_terminal(board):
        return terminal_value(board, root_perspective)
    if depth == 0:
        return heuristic_value(board, root_perspective)

    moves = [i for i in range(6) if board[i] > 0]

    # move ordering – evaluate children once and sort
    scored = []
    for mv in moves:
        child_board, extra = apply_move(board, mv)
        if not extra:
            child_board = swap_perspective(child_board)
        child_root = root_perspective if extra else (not root_perspective)
        scored.append((heuristic_value(child_board, child_root),
                       mv, child_board, extra))

    if root_perspective:
        scored.sort(key=lambda x: x[0], reverse=True)   # MAX
    else:
        scored.sort(key=lambda x: x[0])                  # MIN

    if root_perspective:                                 # MAX
        value = -INF
        for _, mv, child_board, extra in scored:
            child_root = root_perspective if extra else (not root_perspective)
            value = max(value,
                        search(child_board, depth - 1, alpha, beta, child_root))
            alpha = max(alpha, value)
            if beta <= alpha:
                break
        return value
    else:                                                # MIN
        value = INF
        for _, mv, child_board, extra in scored:
            child_root = root_perspective if extra else (not root_perspective)
            value = min(value,
                        search(child_board, depth - 1, alpha, beta, child_root))
            beta = min(beta, value)
            if beta <= alpha:
                break
        return value


def search_root(board: List[int], depth: int) -> (int, int):
    """
    Search from the root (original player to move).  Returns
    (best_move_index, best_value).
    """
    best_move = None
    best_val = -INF
    alpha = -INF
    beta = INF

    moves = [i for i in range(6) if board[i] > 0]

    # order the moves by heuristic value seen from the root
    scored = []
    for mv in moves:
        child_board, extra = apply_move(board, mv)
        child_root = True if extra else False          # perspective stays root / flips
        if not extra:
            child_board = swap_perspective(child_board)
        scored.append((heuristic_value(child_board, child_root),
                       mv, child_board, extra))

    scored.sort(key=lambda x: x[0], reverse=True)      # MAX‑ordering

    for _, mv, child_board, extra in scored:
        child_root = True if extra else False
        val = search(child_board, depth - 1, alpha, beta, child_root)
        if val > best_val:
            best_val = val
            best_move = mv
        alpha = max(alpha, val)
        if beta <= alpha:
            break

    return best_move, best_val


def policy(you: List[int], opponent: List[int]) -> int:
    """
    Public API – returns the chosen house index (0‑5).
    """
    # combine the two views into a single 14‑slot board
    board = you + opponent

    # a legal move must exist (guaranteed by the environment)
    legal = [i for i in range(6) if you[i] > 0]
    fallback = legal[0] if legal else 0

    start = time.time()
    best_move = None

    depth = 0
    while True:
        depth += 1
        move, _ = search_root(board, depth)
        if move is not None:
            best_move = move
        # time limit (leave a little safety margin)
        if time.time() - start > 0.85:
            break
        if depth >= 12:            # safety net, should never be hit
            break

    return best_move if best_move is not None else fallback
