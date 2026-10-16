
import copy

# Directions for movement: [dr, dc]
DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]

def count_pieces_in_row(board, row):
    count = 0
    for col in range(8):
        if board[row][col] != 0:
            count += 1
    return count

def count_pieces_in_col(board, col):
    count = 0
    for row in range(8):
        if board[row][col] != 0:
            count += 1
    return count

def count_pieces_in_main_diag(board, diag):
    count = 0
    for r in range(8):
        c = r - diag
        if 0 <= c < 8 and board[r][c] != 0:
            count += 1
    return count

def count_pieces_in_anti_diag(board, anti):
    count = 0
    for r in range(8):
        c = anti - r
        if 0 <= c < 8 and board[r][c] != 0:
            count += 1
    return count

def count_pieces(board, player):
    count = 0
    for row in range(8):
        for col in range(8):
            if board[row][col] == player:
                count += 1
    return count

def get_largest_component(board, player):
    visited = [[False] * 8 for _ in range(8)]
    max_size = 0
    for r in range(8):
        for c in range(8):
            if not visited[r][c] and board[r][c] == player:
                stack = [(r, c)]
                size = 0
                while stack:
                    row, col = stack.pop()
                    if visited[row][col]:
                        continue
                    visited[row][col] = True
                    size += 1
                    for dr, dc in DIRECTIONS:
                        nr, nc = row + dr, col + dc
                        if 0 <= nr < 8 and 0 <= nc < 8 and not visited[nr][nc] and board[nr][nc] == player:
                            stack.append((nr, nc))
                if size > max_size:
                    max_size = size
    return max_size

def generate_legal_moves(board, player):
    legal_moves = []
    for r in range(8):
        for c in range(8):
            if board[r][c] == player:
                for dr, dc in DIRECTIONS:
                    total_pieces = 0
                    if dr == 0 and dc != 0:
                        total_pieces = count_pieces_in_row(board, r)
                    elif dr != 0 and dc == 0:
                        total_pieces = count_pieces_in_col(board, c)
                    elif dr != 0 and dc != 0 and abs(dr) == abs(dc):
                        if dr == dc:
                            total_pieces = count_pieces_in_main_diag(board, r - c)
                        else:
                            total_pieces = count_pieces_in_anti_diag(board, r + c)
                    else:
                        continue
                    if total_pieces == 0:
                        continue
                    target_r = r + total_pieces * dr
                    target_c = c + total_pieces * dc
                    if not (0 <= target_r < 8 and 0 <= target_c < 8):
                        continue
                    legal = True
                    for step in range(1, total_pieces):
                        rr = r + step * dr
                        cc = c + step * dc
                        if board[rr][cc] != 0:
                            if board[rr][cc] == -player:
                                legal = False
                                break
                    if not legal:
                        continue
                    if board[target_r][target_c] == -player or board[target_r][target_c] == 0:
                        legal_moves.append((r, c, target_r, target_c))
    return legal_moves

def apply_move(board, move):
    from_r, from_c, to_r, to_c = move
    new_board = [list(row) for row in board]
    new_board[from_r][from_c] = 0
    new_board[to_r][to_c] = 1
    return new_board

def evaluate(board):
    our_largest = get_largest_component(board, 1)
    opp_largest = get_largest_component(board, -1)
    our_pieces = count_pieces(board, 1)
    opp_pieces = count_pieces(board, -1)
    if our_pieces == 0:
        return -10000
    if opp_pieces == 0:
        return 10000
    if our_largest == our_pieces:
        return 10000
    if opp_largest == opp_pieces:
        return -10000
    opponent_moves = generate_legal_moves(board, 1)
    if len(opponent_moves) == 0:
        return 10000
    score = (our_largest / our_pieces) - (opp_largest / opp_pieces)
    return score

def policy(board):
    moves = generate_legal_moves(board, 1)
    if not moves:
        return "0,0:0,0"
    best_score = -10**9
    best_move = None
    for move in moves:
        new_board = apply_move(board, move)
        score = evaluate(new_board)
        if score > best_score:
            best_score = score
            best_move = move
    return f"{best_move[0]},{best_move[1]}:{best_move[2]},{best_move[3]}"
