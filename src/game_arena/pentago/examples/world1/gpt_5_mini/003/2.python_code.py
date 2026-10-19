
#!/usr/bin/env python3
# Pentago move selection policy
# Defines: policy(you, opponent) -> str
#
# Strategy:
# 1. Try to find an immediate winning move for us (we have 5+ in a row after our move).
# 2. Otherwise choose a move that does not give the opponent an immediate 5 after our move
#    and also leaves no immediate winning response for the opponent.
# 3. If none found, return the first legal move.

from copy import deepcopy

def _rotate_quadrant(board, quad, dir):
    # board: 6x6 list of lists (modified in place)
    # quad: 0..3, dir: 'L' or 'R'
    r0 = 0 if quad < 2 else 3
    c0 = 0 if (quad % 2) == 0 else 3
    # extract 3x3
    old = [[board[r0 + i][c0 + j] for j in range(3)] for i in range(3)]
    new = [[0]*3 for _ in range(3)]
    if dir == 'R':
        # clockwise: new[i][j] = old[2-j][i]
        for i in range(3):
            for j in range(3):
                new[i][j] = old[2-j][i]
    else:
        # 'L' anticlockwise: new[i][j] = old[j][2-i]
        for i in range(3):
            for j in range(3):
                new[i][j] = old[j][2-i]
    # write back
    for i in range(3):
        for j in range(3):
            board[r0 + i][c0 + j] = new[i][j]

def _apply_move(you_board, opp_board, r, c, quad, dir):
    # r,c are 0-indexed. Returns new (you,opp) boards after placing and rotating.
    y = [list(row) for row in you_board]
    o = [list(row) for row in opp_board]
    y[r][c] = 1
    # rotate both boards' quadrants
    _rotate_quadrant(y, quad, dir)
    _rotate_quadrant(o, quad, dir)
    return y, o

def _has_five(board):
    # board: 6x6 with 1 for player's stones, 0 otherwise
    # return True if there exists 5 or more in a straight line
    dirs = [(0,1), (1,0), (1,1), (-1,1)]
    for r in range(6):
        for c in range(6):
            if board[r][c] != 1:
                continue
            for dr, dc in dirs:
                count = 1
                # forward
                i = 1
                while True:
                    rr = r + dr*i
                    cc = c + dc*i
                    if 0 <= rr < 6 and 0 <= cc < 6 and board[rr][cc] == 1:
                        count += 1
                        i += 1
                    else:
                        break
                # backward
                i = 1
                while True:
                    rr = r - dr*i
                    cc = c - dc*i
                    if 0 <= rr < 6 and 0 <= cc < 6 and board[rr][cc] == 1:
                        count += 1
                        i += 1
                    else:
                        break
                if count >= 5:
                    return True
    return False

def _opponent_can_win_after(you_board, opp_board):
    # Given board state after our move, check if opponent has any legal move that results
    # in them having 5 in a row after their placement+rotation.
    empties = [(r,c) for r in range(6) for c in range(6) if you_board[r][c] == 0 and opp_board[r][c] == 0]
    if not empties:
        return False
    for (r,c) in empties:
        for quad in range(4):
            for dir in ('L','R'):
                new_opp, new_you = _apply_move(opp_board, you_board, r, c, quad, dir)
                # new_opp is opponent after their move
                if _has_five(new_opp):
                    return True
    return False

def policy(you, opponent) -> str:
    # Convert inputs to normal Python lists of ints for safety (handles numpy/other sequences)
    you_board = [[int(you[r][c]) for c in range(6)] for r in range(6)]
    opp_board = [[int(opponent[r][c]) for c in range(6)] for r in range(6)]

    empties = [(r,c) for r in range(6) for c in range(6) if you_board[r][c] == 0 and opp_board[r][c] == 0]

    # 1) Try immediate winning move for us
    for (r,c) in empties:
        for quad in range(4):
            for dir in ('L','R'):
                new_you, new_opp = _apply_move(you_board, opp_board, r, c, quad, dir)
                if _has_five(new_you) and not _has_five(new_opp):
                    # return winning move
                    return f"{r+1},{c+1},{quad},{dir}"

    # 2) Try safe moves: after our move the opponent does not already have 5, and opponent has no immediate winning reply
    safe_moves = []
    for (r,c) in empties:
        for quad in range(4):
            for dir in ('L','R'):
                new_you, new_opp = _apply_move(you_board, opp_board, r, c, quad, dir)
                # avoid moves that already give opponent 5 (they would at least draw)
                if _has_five(new_opp):
                    continue
                # avoid moves where opponent can win immediately next turn
                if _opponent_can_win_after(new_you, new_opp):
                    continue
                safe_moves.append((r,c,quad,dir))
    if safe_moves:
        r,c,quad,dir = safe_moves[0]
        return f"{r+1},{c+1},{quad},{dir}"

    # 3) If no safe move or win found, just return the first legal move (deterministic order)
    r,c = empties[0]
    return f"{r+1},{c+1},0,L"

# If this file is executed directly, provide a small sanity test (not required).
if __name__ == "__main__":
    # empty boards -> should place at 1,1,0,L
    you = [[0]*6 for _ in range(6)]
    opp = [[0]*6 for _ in range(6)]
    print(policy(you, opp))
