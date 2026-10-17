
from typing import List, Tuple
import copy

def generate_lines() -> List[List[Tuple[int,int,int]]]:
    """Generate all 49 winning lines in a 3x3x3 cube.
    Coordinates are (z, y, x) with each in 0..2.
    """
    lines = []

    # Rows along x for each (z,y)
    for z in range(3):
        for y in range(3):
            lines.append([(z, y, x) for x in range(3)])

    # Columns along y for each (z,x)
    for z in range(3):
        for x in range(3):
            lines.append([(z, y, x) for y in range(3)])

    # Pillars along z for each (y,x)
    for y in range(3):
        for x in range(3):
            lines.append([(z, y, x) for z in range(3)])

    # Face diagonals in z-planes (for each z)
    for z in range(3):
        lines.append([(z, i, i) for i in range(3)])
        lines.append([(z, i, 2 - i) for i in range(3)])

    # Face diagonals in y-planes (for each y)
    for y in range(3):
        lines.append([(i, y, i) for i in range(3)])
        lines.append([(i, y, 2 - i) for i in range(3)])

    # Face diagonals in x-planes (for each x)
    for x in range(3):
        lines.append([(i, i, x) for i in range(3)])
        lines.append([(i, 2 - i, x) for i in range(3)])

    # Space diagonals (4)
    lines.append([(0,0,0), (1,1,1), (2,2,2)])
    lines.append([(0,0,2), (1,1,1), (2,2,0)])
    lines.append([(0,2,0), (1,1,1), (2,0,2)])
    lines.append([(0,2,2), (1,1,1), (2,0,0)])

    # There should be 49 lines
    # (Optional assert)
    # assert len(lines) == 49
    return lines

LINES = generate_lines()

def get_cell(board: List[List[List[int]]], coord: Tuple[int,int,int]) -> int:
    z,y,x = coord
    return board[z][y][x]

def set_cell(board: List[List[List[int]]], coord: Tuple[int,int,int], val: int) -> None:
    z,y,x = coord
    board[z][y][x] = val

def board_sum_on_line(board: List[List[List[int]]], line: List[Tuple[int,int,int]]) -> int:
    return sum(get_cell(board, c) for c in line)

def empty_cells(board: List[List[List[int]]]) -> List[Tuple[int,int,int]]:
    empties = []
    for z in range(3):
        for y in range(3):
            for x in range(3):
                if board[z][y][x] == 0:
                    empties.append((z,y,x))
    return empties

def count_potential_threats(board: List[List[List[int]]], player: int) -> int:
    """Count lines where player has exactly 2 marks and one empty (immediate threat)."""
    cnt = 0
    for line in LINES:
        s = board_sum_on_line(board, line)
        if s == 2 * player:
            # ensure there's an empty in that line
            if any(get_cell(board, c) == 0 for c in line):
                cnt += 1
    return cnt

def policy(board: List[List[List[int]]]) -> Tuple[int,int,int]:
    """
    Return the chosen empty cell (z, y, x) as a tuple of ints 0..2.
    Player is represented by 1, opponent by -1.
    """
    me = 1
    opp = -1

    empties = empty_cells(board)
    if not empties:
        # no move possible, return a default valid coord (shouldn't happen)
        return (0,0,0)

    # 1. Immediate win: find move that makes us win
    for c in empties:
        b2 = copy.deepcopy(board)
        set_cell(b2, c, me)
        # check if any line is complete for us
        if any(board_sum_on_line(b2, line) == 3 for line in LINES):
            return c

    # 2. Immediate block: opponent would win next turn, block it
    for c in empties:
        b2 = copy.deepcopy(board)
        set_cell(b2, c, opp)
        if any(board_sum_on_line(b2, line) == -3 for line in LINES):
            # placing at c would let opponent win, so blocking requires we play in the empty that opponent would use;
            # but we can detect opponent imminent wins directly: look for lines with sum == -2 and take their empty cell
            pass
    # Direct detection of opponent immediate winning squares:
    for line in LINES:
        s = board_sum_on_line(board, line)
        if s == -2:
            # find empty in this line and block it
            for c in line:
                if get_cell(board, c) == 0:
                    return c

    # 3. Create a fork: move that creates two or more immediate threats
    fork_moves = []
    for c in empties:
        b2 = copy.deepcopy(board)
        set_cell(b2, c, me)
        # Count potential threats (lines with sum == 2)
        threats = 0
        for line in LINES:
            s = board_sum_on_line(b2, line)
            if s == 2 and any(get_cell(b2, cc) == 0 for cc in line):
                threats += 1
        if threats >= 2:
            fork_moves.append((threats, c))
    if fork_moves:
        # choose one with highest threats (deterministic by order)
        fork_moves.sort(reverse=True)
        return fork_moves[0][1]

    # 4. Block opponent fork: try to pick a move that leaves opponent with no immediate wins
    # Detect opponent fork moves (cells where opponent could create >=2 threats)
    opp_fork_cells = []
    for c in empties:
        b2 = copy.deepcopy(board)
        set_cell(b2, c, opp)
        threats = 0
        for line in LINES:
            s = board_sum_on_line(b2, line)
            if s == -2 and any(get_cell(b2, cc) == 0 for cc in line):
                threats += 1
        if threats >= 2:
            opp_fork_cells.append(c)

    if opp_fork_cells:
        # If we can play in any of those fork cells, do it (blocks directly)
        for c in opp_fork_cells:
            if get_cell(board, c) == 0:
                return c
        # Otherwise try moves that after our play leave opponent with no immediate win moves
        good_moves = []
        for c in empties:
            b2 = copy.deepcopy(board)
            set_cell(b2, c, me)
            # count opponent immediate winning moves after this
            opp_immediates = 0
            for line in LINES:
                s = board_sum_on_line(b2, line)
                if s == -2 and any(get_cell(b2, cc) == 0 for cc in line):
                    opp_immediates += 1
            if opp_immediates == 0:
                good_moves.append(c)
        if good_moves:
            return good_moves[0]

    # 5. Take center if available
    center = (1,1,1)
    if get_cell(board, center) == 0:
        return center

    # 6. Opposite corner: if opponent is in a corner, take the opposite corner
    corners = [(z,y,x) for z in (0,2) for y in (0,2) for x in (0,2)]
    for cor in corners:
        z,y,x = cor
        opp_z = 2 - z
        opp_y = 2 - y
        opp_x = 2 - x
        if get_cell(board, (opp_z,opp_y,opp_x)) == opp and get_cell(board, cor) == 0:
            return cor

    # 7. Heuristic: choose the empty cell that lies on the largest number of potential (non-blocked) lines
    best_cell = None
    best_score = -1
    for c in empties:
        score = 0
        for line in LINES:
            if c in line:
                # a line is potential for us if it has no opponent mark
                line_vals = [get_cell(board, cc) for cc in line]
                if -1 not in line_vals:
                    # prefer lines where we already have marks as well
                    score += 1 + line_vals.count(1)
        # break ties deterministically by ordering of empties
        if score > best_score:
            best_score = score
            best_cell = c

    if best_cell is not None:
        return best_cell

    # 8. Fallback: return first empty
    return empties[0]
