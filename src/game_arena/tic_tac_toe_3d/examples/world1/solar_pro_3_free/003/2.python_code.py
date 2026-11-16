
#!/usr/bin/env python3
"""
Policy for a 3×3×3 three‑dimensional Tic‑Tac‑Toe.
Returns a legal move (i, j, k) that wins if possible,
blocks opponent’s winning threat if possible, otherwise
chooses the move with the highest minimax score using
alpha‑beta pruning.
"""

from typing import List, Tuple, Optional
import copy

# Fixed board size
SIZE = 3

# All winning lines in a 3×3×3 cube (49 lines total)
WINNING_LINES = [
    # Orthogonal rows (x‑direction)
    [[ (x, y, z) for x in range(SIZE) ] for y in range(SIZE) for z in range(SIZE)],
    # Orthogonal rows (y‑direction)
    [[ (x, y, z) for y in range(SIZE) ] for x in range(SIZE) for z in range(SIZE)],
    # Orthogonal rows (z‑direction)
    [[ (x, y, z) for z in range(SIZE) ] for x in range(SIZE) for y in range(SIZE)],
    # Diagonals on xy‑planes (fixed z)
    [[ (i, i, z) for i in range(SIZE) ] for z in range(SIZE)],
    [[ (i, 2 - i, z) for i in range(SIZE) ] for z in range(SIZE)],
    # Diagonals on xz‑planes (fixed y)
    [[ (i, j, i) for i in range(SIZE) ] for j in range(SIZE)],
    [[ (i, j, 2 - i) for i in range(SIZE) ] for j in range(SIZE)],
    # Diagonals on yz‑planes (fixed x)
    [[ (i, i, j) for i in range(SIZE) ] for j in range(SIZE)],
    [[ (i, 2 - i, j) for i in range(SIZE) ] for j in range(SIZE)],
    # Space diagonals (through the centre)
    [(0, 0, 0), (1, 1, 1), (2, 2, 2)],
    [(0, 0, 2), (1, 1, 1), (2, 2, 0)],
    [(0, 2, 0), (1, 1, 1), (2, 0, 2)],
    [(0, 2, 2), (1, 1, 1), (2, 0, 0)],
]

def has_winning_line(board: List[List[List[int]]], player: int) -> bool:
    """Return True if *player* has any complete line on the board."""
    for line in WINNING_LINES:
        # flatten the line into (i,j,k) coordinates
        coords = [(board[x][y][z] == player) for x, y, z in line]
        if all(coords):
            return True
    return False

def has_threat(board: List[List[List[int]]], player: int) -> List[Tuple[int, int, int]]:
    """
    Find empty cells that, if filled with *player*, would create a win.
    Returns a list of positions sorted by distance from the centre.
    """
    centre = (SIZE // 2, SIZE // 2, SIZE // 2)   # (1,1,1)
    moves: List[Tuple[int, int, int]] = []

    # Gather all empty cells
    for i in range(SIZE):
        for j in range(SIZE):
            for k in range(SIZE):
                if board[i][j][k] == 0:
                    # simulate placing player at (i,j,k)
                    simulated = copy.deepcopy(board)
                    simulated[i][j][k] = player
                    if has_winning_line(simulated, player):
                        # This move would win instantly; rank it first
                        moves.append((i, j, k, 0))
                    else:
                        moves.append((i, j, k, manhattan(i, j, k)))
    # Add dummy key to differentiate immediate win (no distance) from regular moves
    # Then sort by distance ascending (smaller distance first)
    if moves:
        moves.sort(key=lambda m: m[1] if isinstance(m[1], int) else 0)  # immediate win first
    return [(move[0], move[1], move[2]) for move in moves]

def manhattan(coord: int) -> int:
    """Distance from centre (1,1,1) for coordinates 0‑2."""
    centre = (SIZE // 2, SIZE // 2, SIZE // 2)
    return sum(abs(c - centre[idx]) for idx, c in enumerate(coord))

def apply_move(board: List[List[List[int]]], move: Tuple[int, int, int], player: int) -> List[List[List[int]]]:
    """Return a new board with *player* placed at *move* (deep copy)."""
    new_board = [ [ row[:] for row in layer ] for layer in board ]
    new_board[move[0]][move[1]][move[2]] = player
    return new_board

def get_possible_moves(board: List[List[List[int]]]) -> List[Tuple[int, int, int]]:
    """All empty cells on the board."""
    moves = []
    for i in range(SIZE):
        for j in range(SIZE):
            for k in range(SIZE):
                if board[i][j][k] == 0:
                    moves.append((i, j, k))
    return moves

def evaluate(board: List[List[List[int]]]) -> int:
    """Return 10 for us winning, -10 for opponent winning, 0 for draw."""
    winner = None
    for line in WINNING_LINES:
        vals = [board[x][y][z] for x, y, z in line]
        if vals[0] == vals[1] == vals[2] and vals[0] != 0:
            winner = vals[0]
            break
    if winner == 1:
        return 10
    if winner == -1:
        return -10
    return 0

def minimax(board: List[List[List[int]]],
            player: int,
            alpha: float,
            beta: float,
            depth: int) -> Tuple[int, Tuple[int, int, int]]:
    """Return (score, best_move) for the given player using alpha‑beta pruning."""
    winner = None
    for line in WINNING_LINES:
        vals = [board[x][y][z] for x, y, z in line]
        if vals[0] == vals[1] == vals[2] and vals[0] != 0:
            winner = vals[0]
            break
    if winner is not None:
        # A terminal win/loss is forced regardless of depth
        if winner == player:
            return (10, None) if depth < 20 else (10, (0,0,0))   # win for player
        else:
            return (-10, None)                                 # loss

    # No immediate win/loss; check if board is full (draw)
    if len(get_possible_moves(board)) == 0:
        return (0, None)

    moves = get_possible_moves(board)
    # For deterministic behaviour we sort moves by manhattan distance from centre
    moves.sort(key=lambda m: sum(abs(coord - (SIZE//2) for coord in m)))

    if player == 1:      # Maximising player (us)
        best_score = -float('inf')
        best_move = None
        for move in moves:
            new_board = apply_move(board, move, player)
            # Check if this move itself is a winning move (fast win)
            if has_winning_line(new_board, player):
                return (10, move)
            score, _ = minimax(new_board, -player, alpha, beta, depth + 1)
            alpha = max(alpha, score)
            if score > best_score:
                best_score = score
                best_move = move
            if beta <= alpha:
                break
        return (best_score, best_move)
    else:                # Minimising player (opponent)
        best_score = float('inf')
        best_move = None
        for move in moves:
            new_board = apply_move(board, move, player)
            if has_winning_line(new_board, -player):
                # Opponent would win immediately, we must avoid this path.
                # But we cannot let it happen; block it later. The recursion will see that
                # and return a low score, prompting us to block. However to guarantee
                # blocking we directly stop the opponent from winning by choosing
                # the winning move ourselves.
                # So we treat immediate opponent win as a forced loss and prune.
                # The parent maximising call will see a score of -10 and select a
                # different move that blocks this threat.
                # Here we simply return a very low score.
                score = -10
                beta = min(beta, score)
                if beta <= alpha:
                    break
                continue
            score, _ = minimax(new_board, -player, alpha, beta, depth + 1)
            beta = min(beta, score)
            if score < best_score:
                best_score = score
                best_move = move
            if beta <= alpha:
                break
        return (best_score, best_move)

def policy(board: List[List[List[int]]]) -> Tuple[int, int, int]:
    """
    Implements the described strategy.
    Returns a legal (i, j, k) move for the current player.
    """
    # Determine whose turn we are (assume we start first, tie -> us)
    our_count = sum(cell == 1 for layer in board for row in layer for cell in row)
    opponent_count = sum(cell == -1 for layer in board for row in layer for cell in row)
    player = 1 if our_count <= opponent_count else -1

    # Immediate win?
    for move in get_possible_moves(board):
        new_board = apply_move(board, move, player)
        if has_winning_line(new_board, player):
            return move

    # Immediate opponent win (block it)
    for move in get_possible_moves(board):
        new_board = apply_move(board, move, -1)
        if has_winning_line(new_board, -1):
            return move

    # Otherwise use minimax (full search)
    _, best_move = minimax(board, player, float("-inf"), float("inf"), 0)
    # best_move is guaranteed to be a legal move
    return best_move

# If the file is executed directly, run a tiny sanity test.
if __name__ == "__main__":
    # Simple test: empty board, we expect the centre.
    empty = [[[[0] * SIZE for _ in range(SIZE)] for __ in range(SIZE)]]
    move = policy(empty)
    print("Policy move on empty board:", move)   # should be (1,1,1)
