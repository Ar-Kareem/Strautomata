
import random

def possible_lines():
    lines = []
    # Along z-direction (pillars)
    for x in range(3):
        for y in range(3):
            lines.append([(x, y, z) for z in range(3)])
    # Along y-direction (rows in xz planes, y fixed)
    for y in range(3):
        for z in range(3):
            lines.append([(x, y, z) for x in range(3)])
    # Along x-direction (columns in yz planes, x fixed)
    for x in range(3):
        for z in range(3):
            lines.append([(x, y, z) for y in range(3)])
    # Diagonals in xz planes (y fixed)
    for y in range(3):
        lines.append([(x, y, x) for x in range(3)])
        lines.append([(2 - x, y, x) for x in range(3)])
    # Diagonals in yz planes (x fixed)
    for x in range(3):
        lines.append([(x, y, y) for y in range(3)])
        lines.append([(x, 2 - y, y) for y in range(3)])
    # Diagonals in xy planes (z fixed)
    for z in range(3):
        lines.append([(x, x, z) for x in range(3)])
        lines.append([(2 - x, x, z) for x in range(3)])
    # Space diagonals
    lines.append([(i, i, i) for i in range(3)])
    lines.append([(i, i, 2 - i) for i in range(3)])
    lines.append([(2 - i, i, i) for i in range(3)])
    lines.append([(2 - i, i, 2 - i) for i in range(3)])
    return lines

LINES = possible_lines()

def get_move(board, player):
    for line in LINES:
        owned = 0
        empty_pos = None
        opponent_count = 0
        for x, y, z in line:
            val = board[z][y][x]
            if val == player:
                owned += 1
            elif val == 0:
                empty_pos = (x, y, z)
            else:
                opponent_count += 1
        if owned == 2 and empty_pos and opponent_count == 0:
            return empty_pos
    return None

def get_score(board, pos, player):
    score = 0
    for line in LINES:
        if pos in line:
            mine = 0
            opponent = 0
            empty = 0
            for x, y, z in line:
                val = board[z][y][x]
                if val == player:
                    mine += 1
                elif val == -player:
                    opponent += 1
                else:
                    empty += 1
            if mine == 1 and opponent == 0 and empty == 2:
                score += 1
    return score

def policy(board):
    empties = []
    preferred = [(1, 1, 1)]  # center
    # Face centers
    for d in range(3):
        for s in [0, 2]:
            if d == 0:
                preferred.append((s, 1, 1))
            elif d == 1:
                preferred.append((1, s, 1))
            else:
                preferred.append((1, 1, s))
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board[z][y][x] == 0:
                    empties.append((x, y, z))
    if not empties:
        raise ValueError("No empty cells")
    # Check for win
    win_move = get_move(board, 1)
    if win_move:
        return win_move
    # Check for block
    block_move = get_move(board, -1)
    if block_move:
        return block_move
    # Evaluate based on opening threats
    max_score = -1
    best_pos = None
    for pos in empties:
        score = get_score(board, pos, 1)
        if score > max_score:
            max_score = score
            best_pos = pos
        elif score == max_score and random.random() > 0.5:  # tie breaker
            best_pos = pos
    if best_pos:
        return best_pos
    # Fallback to preferred
    for pos in preferred:
        if pos in empties:
            return pos
    # Random
    return random.choice(empties)
