
import collections
from typing import List, Tuple

# This file implements a strategic agent for 3x3x3 Tic Tac Toe.
# The strategy is based on a well-known heuristic hierarchy for Tic Tac Toe,
# adapted for the 3D board.

# ---- Pre-computation of Winning Lines and Cell-to-Line Mapping ----

def _create_winning_lines() -> list[list[tuple[int, int, int]]]:
    """
    Generates and returns all 49 possible winning lines on a 3x3x3 board.
    Each line is a list of 3 (z, y, x) coordinate tuples.
    """
    lines = []
    
    # 27 axis-aligned lines (rows, columns, and pillars)
    for i in range(3):
        for j in range(3):
            lines.append([(i, j, k) for k in range(3)])  # Line along x-axis
            lines.append([(i, k, j) for k in range(3)])  # Line along y-axis
            lines.append([(k, i, j) for k in range(3)])  # Line along z-axis

    # 18 planar diagonals
    for i in range(3):
        lines.append([(i, d, d) for d in range(3)])      # XY plane, z=i
        lines.append([(i, d, 2 - d) for d in range(3)])  # XY plane, z=i
        lines.append([(d, i, d) for d in range(3)])      # XZ plane, y=i
        lines.append([(d, i, 2 - d) for d in range(3)])  # XZ plane, y=i
        lines.append([(d, d, i) for d in range(3)])      # YZ plane, x=i
        lines.append([(d, 2 - d, i) for d in range(3)])  # YZ plane, x=i
        
    # 4 major space diagonals
    lines.append([(d, d, d) for d in range(3)])
    lines.append([(d, d, 2 - d) for d in range(3)])
    lines.append([(d, 2 - d, d) for d in range(3)])
    lines.append([(2 - d, d, d) for d in range(3)])
    
    return lines

# A global constant holding all winning lines, computed once on module load.
WINNING_LINES = _create_winning_lines()

# A dictionary to map a cell to all winning lines it belongs to.
# This is an optimization to avoid iterating all 49 lines for fork checks.
CELL_TO_LINES_MAP = collections.defaultdict(list)
for line in WINNING_LINES:
    for cell in line:
        CELL_TO_LINES_MAP[cell].append(line)


def policy(board: List[List[List[int]]]) -> Tuple[int, int, int]:
    """
    Determines the next best move for a 3x3x3 Tic Tac Toe game.

    The agent follows a deterministic, heuristic-based strategy with the
    following priority:
    1.  Win: Complete a line of three.
    2.  Block: Block the opponent from completing a line of three.
    3.  Fork: Create two simultaneous winning threats.
    4.  Block Fork: Prevent the opponent from creating a fork.
    5.  Center: Occupy the center cell if available.
    6.  Opposite Corner: If the opponent is in a corner, take the opposite one.
    7.  Empty Corner: Take any available corner.
    8.  Empty Side: Take any available side cell (face or edge center).

    Args:
        board: A 3x3x3 list of lists representing the game state.
               - `1`: This AI player.
               - `-1`: The opponent.
               - `0`: Empty cell.
        The coordinates are assumed to be in (z, y, x) format.

    Returns:
        A tuple (z, y, x) representing the coordinates of the chosen move.
    """
    MY_PLAYER = 1
    OPPONENT = -1

    empty_cells = []
    for z in range(3):
        for y in range(3):
            for x in range(3):
                if board[z][y][x] == 0:
                    empty_cells.append((z, y, x))
    
    # If board is empty, take the center (best opening move).
    if len(empty_cells) == 27:
        return (1, 1, 1)

    def find_immediate_threat(player: int) -> None:
        """Finds a move to complete a line for the given player."""
        for line in WINNING_LINES:
            values = [board[c[0]][c[1]][c[2]] for c in line]
            if values.count(player) == 2 and values.count(0) == 1:
                empty_index = values.index(0)
                return line[empty_index]
        return None

    # 1. Win: Check if we can make a winning move.
    my_win_move = find_immediate_threat(MY_PLAYER)
    if my_win_move:
        return my_win_move

    # 2. Block: Check if the opponent has a winning move and block it.
    opponent_win_move = find_immediate_threat(OPPONENT)
    if opponent_win_move:
        return opponent_win_move
        
    def find_fork_moves(player: int) -> list[tuple[int, int, int]]:
        """Finds all moves that create at least two threats for the player."""
        forks = []
        for move in empty_cells:
            board[move[0]][move[1]][move[2]] = player
            threats_created = 0
            for line in CELL_TO_LINES_MAP[move]:
                values = [board[c[0]][c[1]][c[2]] for c in line]
                if values.count(player) == 2 and values.count(0) == 1:
                    threats_created += 1
            board[move[0]][move[1]][move[2]] = 0
            if threats_created >= 2:
                forks.append(move)
        return forks

    # 3. Fork: Try to create a fork for ourselves.
    my_forks = find_fork_moves(MY_PLAYER)
    if my_forks:
        return my_forks[0]

    # 4. Block Opponent's Fork
    opponent_forks = find_fork_moves(OPPONENT)
    if len(opponent_forks) == 1:
        return opponent_forks[0]
    elif len(opponent_forks) > 1:
        # Opponent has multiple forks. We must make a move that forces them
        # to defend, which means creating an immediate threat of our own.
        for move in empty_cells:
            if move in opponent_forks: continue
            board[move[0]][move[1]][move[2]] = MY_PLAYER
            is_forcing = any(
                [board[c[0]][c[1]][c[2]] for c in line].count(MY_PLAYER) == 2 and
                [board[c[0]][c[1]][c[2]] for c in line].count(0) == 1
                for line in CELL_TO_LINES_MAP[move]
            )
            board[move[0]][move[1]][move[2]] = 0
            if is_forcing:
                return move
        # If no forcing move is found, we're in a losing position.
        # Play in one of their fork spots to delay the loss.
        return opponent_forks[0]

    # --- Positional Play Heuristics (if no critical moves exist) ---
    
    # 5. Center: Play the center if available.
    if board[1][1][1] == 0:
        return (1, 1, 1)

    # 6. Opposite Corner: If opp is in a corner, play the opposite one.
    corners = {(0,0,0): (2,2,2), (0,0,2): (2,2,0), (0,2,0): (2,0,2), (0,2,2): (2,0,0)}
    corners.update({v: k for k, v in corners.items()})
    for corner, opposite in corners.items():
        if board[corner[0]][corner[1]][corner[2]] == OPPONENT and board[opposite[0]][opposite[1]][opposite[2]] == 0:
            return opposite

    # 7. Empty Corner: Play in any available corner.
    for corner in sorted(list(corners.keys())): # Sort for determinism
        if board[corner[0]][corner[1]][corner[2]] == 0:
            return corner

    # 8. Empty Side: Play on any remaining empty cell.
    if empty_cells:
        return empty_cells[0]
    
    # Fallback for robustness. Should not be reached in a valid game.
    raise RuntimeError("No valid moves available, but the game is not over.")

