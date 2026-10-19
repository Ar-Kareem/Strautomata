
from typing import List, Tuple, Dict

# 3x3x3 Tic Tac Toe policy
# board is a 3x3x3 list: board[x][y][z] in {0, 1, -1}
# Return (x, y, z) coordinates (each 0..2) of chosen empty cell.


# Precompute all winning lines (each as triple of flat indices)
N = 3
# Map (x,y,z) -> flat index
def idx(x: int, y: int, z: int) -> int:
    return x * (N * N) + y * N + z

_all_lines: List[Tuple[int,int,int]] = []

def _generate_lines():
    lines = []
    for x in range(N):
        for y in range(N):
            for z in range(N):
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        for dz in (-1, 0, 1):
                            if dx == 0 and dy == 0 and dz == 0:
                                continue
                            # ensure this is the "start" of the line (previous step outside bounds)
                            px, py, pz = x - dx, y - dy, z - dz
                            if 0 <= px < N and 0 <= py < N and 0 <= pz < N:
                                continue
                            # build line of length N
                            coords = []
                            ok = True
                            for t in range(N):
                                nx, ny, nz = x + t*dx, y + t*dy, z + t*dz
                                if not (0 <= nx < N and 0 <= ny < N and 0 <= nz < N):
                                    ok = False
                                    break
                                coords.append((nx, ny, nz))
                            if not ok:
                                continue
                            # convert to flat indices
                            flat = tuple(idx(a,b,c) for (a,b,c) in coords)
                            # keep unique lines
                            if flat not in lines:
                                lines.append(flat)
    return lines

_all_lines = _generate_lines()


def _flatten_board(board: List[List[List[int]]]) -> List[int]:
    flat = [0] * (N * N * N)
    for x in range(N):
        for y in range(N):
            for z in range(N):
                flat[idx(x,y,z)] = int(board[x][y][z])
    return flat

def _unflatten_index(flat_index: int) -> Tuple[int,int,int]:
    x = flat_index // (N * N)
    rem = flat_index % (N * N)
    y = rem // N
    z = rem % N
    return (x, y, z)

def _check_winner_flat(flat_board: List[int]) -> int:
    # returns 1 if player 1 wins, -1 if opponent wins, 0 otherwise
    for a,b,c in _all_lines:
        s = flat_board[a] + flat_board[b] + flat_board[c]
        if s == 3:
            return 1
        if s == -3:
            return -1
    return 0

# Minimax with alpha-beta and memoization
from functools import lru_cache

def policy(board: List[List[List[int]]]) -> Tuple[int, int, int]:
    flat = _flatten_board(board)
    # Determine whose turn it is. We assume 1 (us) moves when count(1) == count(-1).
    ones = sum(1 for v in flat if v == 1)
    negs = sum(1 for v in flat if v == -1)
    # If ones == negs -> our turn (1). If ones < negs -> our turn too (we are behind) but that is unlikely.
    # If ones > negs -> technically opponent to move, but we still return a move; assume it's our turn only when ones <= negs.
    # For search we will assume next player is 1.
    next_player = 1

    # Quick: if we have an immediate winning move, take it
    empties = [i for i,v in enumerate(flat) if v == 0]
    for i in empties:
        flat[i] = 1
        if _check_winner_flat(flat) == 1:
            flat[i] = 0
            return _unflatten_index(i)
        flat[i] = 0

    # Quick: block immediate opponent win
    for i in empties:
        flat[i] = -1
        if _check_winner_flat(flat) == -1:
            flat[i] = 0
            return _unflatten_index(i)
        flat[i] = 0

    # Convert list to tuple for caching
    start_state = tuple(flat)

    @lru_cache(maxsize=None)
    def minimax(state: Tuple[int,...], player: int, alpha: int, beta: int) -> int:
        # returns score from perspective of player 1: +1 win for 1, -1 loss for 1, 0 draw
        state_list = list(state)
        winner = _check_winner_flat(state_list)
        if winner != 0:
            return winner  # 1 or -1
        if all(v != 0 for v in state):
            return 0  # draw

        empties_local = [i for i,v in enumerate(state) if v == 0]

        if player == 1:
            # maximizing for player 1
            value = -2
            for i in empties_local:
                state_list[i] = 1
                val = minimax(tuple(state_list), -1, alpha, beta)
                state_list[i] = 0
                if val > value:
                    value = val
                if value > alpha:
                    alpha = value
                if alpha >= beta:
                    break
                # immediate win shortcut
                if value == 1:
                    break
            return value
        else:
            # minimizing (opponent tries to make result -1)
            value = 2
            for i in empties_local:
                state_list[i] = -1
                val = minimax(tuple(state_list), 1, alpha, beta)
                state_list[i] = 0
                if val < value:
                    value = val
                if value < beta:
                    beta = value
                if alpha >= beta:
                    break
                if value == -1:
                    break
            return value

    # Choose best move by running minimax on each empty
    best_score = -2
    best_move = None
    # Try to order moves: center first, corners, edges (heuristic)
    center = idx(1,1,1)
    corners = [idx(x,y,z) for x in (0,2) for y in (0,2) for z in (0,2)]
    edges = [i for i in range(N*N*N) if i not in corners and i != center]
    ordering = []
    if center in empties:
        ordering.append(center)
    ordering.extend([c for c in corners if c in empties])
    ordering.extend([e for e in edges if e in empties])
    if not ordering:
        ordering = empties

    for i in ordering:
        flat_list = list(start_state)
        flat_list[i] = 1
        score = minimax(tuple(flat_list), -1, -2, 2)
        # We want the move maximizing player's outcome for player 1
        if score > best_score:
            best_score = score
            best_move = i
            # immediate win
            if best_score == 1:
                break

    # If nothing selected (shouldn't happen), pick first empty
    if best_move is None:
        if not empties:
            # No moves left; return arbitrary invalid -> but to be safe return (0,0,0)
            return (0,0,0)
        best_move = empties[0]

    return _unflatten_index(best_move)


# For quick testing when run as script (not required by arena but helpful)
if __name__ == "__main__":
    # empty board example
    b = [[[0 for _ in range(3)] for _ in range(3)] for _ in range(3)]
    move = policy(b)
    print("Chosen move on empty board:", move)
