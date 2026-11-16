
import random
from typing import List, Tuple

# Precompute all winning lines (triples of coordinates)
LINES = [
    [(0, 0), (0, 1), (0, 2)],
    [(1, 0), (1, 1), (1, 2)],
    [(2, 0), (2, 1), (2, 2)],
    [(0, 0), (1, 0), (2, 0)],
    [(0, 1), (1, 1), (2, 1)],
    [(0, 2), (1, 2), (2, 2)],
    [(0, 0), (1, 1), (2, 2)],
    [(0, 2), (1, 1), (2, 0)],
]

CORNERS = [(0, 0), (0, 2), (2, 0), (2, 2)]
EDGES = [(0, 1), (1, 0), (1, 2), (2, 1)]
CENTER = (1, 1)

def legal_moves(board: List[List[int]]) -> List[Tuple[int, int]]:
    moves = []
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                moves.append((r, c))
    return moves

def lines_through(cell: Tuple[int, int]) -> List[List[Tuple[int, int]]]:
    r, c = cell
    return [line for line in LINES if (r, c) in line]

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Choose a move (row, col) on a 3x3 Phantom Tic Tac Toe board.
    Board values:
      1 -> confirmed our mark
      0 -> unknown (may be empty or opponent)
    Strategy:
      1) Immediate win: if any line has two 1s and a 0, pick that 0.
      2) Fork creation: pick a cell that would create multiple lines with two 1s.
      3) Favor center, then corners, then edges.
      4) Break ties randomly.
    Always returns a valid coordinate tuple in 0..2.
    """
    # Collect legal moves (cells with 0)
    moves = legal_moves(board)
    if not moves:
        # Fallback: if none reported as 0 (unlikely), pick any cell not 1 or (0,0)
        for r in range(3):
            for c in range(3):
                if board[r][c] != 1:
                    return (r, c)
        return (0, 0)

    # 1) Immediate win: any line with two 1s and one 0
    for line in LINES:
        ones = [(r, c) for (r, c) in line if board[r][c] == 1]
        zeros = [(r, c) for (r, c) in line if board[r][c] == 0]
        if len(ones) == 2 and len(zeros) == 1:
            # Attempt the winning cell
            return zeros[0]

    # Evaluate each legal move with heuristics
    best_score = -1e9
    best_moves = []

    for mv in moves:
        r, c = mv
        score = 0

        # If center, small bonus
        if mv == CENTER:
            score += 30

        # Corner bonus
        if mv in CORNERS:
            score += 10

        # Edge smaller bonus
        if mv in EDGES:
            score += 5

        # Count how many lines through mv would become "two-in-a-row" (i.e., placing here combined with existing 1s)
        two_in_row_after = 0
        for line in lines_through(mv):
            cnt_ones = sum(1 for (lr, lc) in line if board[lr][lc] == 1)
            cnt_zeros = sum(1 for (lr, lc) in line if board[lr][lc] == 0)
            # If after placing here, how many ones would be in this line?
            if cnt_ones + 1 >= 2 and cnt_zeros >= 1:
                two_in_row_after += 1

        # If this move would immediately create a win in the next own attempt (i.e., two lines become two-in-a-row),
        # that's a fork potential; heavy bonus.
        if two_in_row_after >= 2:
            score += 80
        else:
            score += two_in_row_after * 20

        # Also prefer moves that increase the count of lines we are present in
        # Count number of lines that contain at least one of our current marks and this cell is part of them
        proximity = 0
        for line in lines_through(mv):
            if any(board[lr][lc] == 1 for (lr, lc) in line):
                proximity += 1
        score += proximity * 3

        # Small random tie-breaker to reduce predictability
        score += random.random() * 1e-3

        if score > best_score:
            best_score = score
            best_moves = [mv]
        elif score == best_score:
            best_moves.append(mv)

    # Choose randomly among best moves
    choice = random.choice(best_moves)
    return choice

# If this module is run directly, provide a simple self-test demonstration
if __name__ == "__main__":
    # Example boards for quick sanity testing
    tests = [
        [[0,0,0],[0,1,0],[0,0,0]],  # center already ours -> pick a corner
        [[1,1,0],[0,0,0],[0,0,0]],  # immediate win at (0,2)
        [[0,0,0],[0,0,0],[0,0,0]],  # empty board -> pick center
        [[0,1,0],[0,0,0],[0,0,1]],  # try to create fork or pick center
    ]
    for b in tests:
        mv = policy(b)
        print("Board:", b, "-> move:", mv)
