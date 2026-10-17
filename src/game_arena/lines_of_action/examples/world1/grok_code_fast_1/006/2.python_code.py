
import copy

def get_line_piece_count(board, r, c, dr, dc):
    if dr == 0:  # vertical, line is column c
        return sum(1 for i in range(8) if board[i][c] != 0)
    elif dc == 0:  # horizontal, line is row r
        return sum(1 for j in range(8) if board[r][j] != 0)
    else:  # diagonal
        if dr * dc > 0:  # same sign, r - c constant
            const = r - c
            count = 0
            for i in range(8):
                j = i - const
                if 0 <= j < 8 and board[i][j] != 0:
                    count += 1
            return count
        else:  # opposite sign, r + c constant
            const = r + c
            count = 0
            for i in range(8):
                j = const - i
                if 0 <= j < 8 and board[i][j] != 0:
                    count += 1
            return count

def is_legal_move(board, r, c, tr, tc, dr, dc, piece_count):
    # Check path: no opponent in between
    for k in range(1, piece_count):
        nr, nc = r + k * dr, c + k * dc
        if board[nr][nc] == -1:
            return False
    # Target must not be own piece
    if board[tr][tc] == 1:
        return False
    return True

def get_legal_moves(board):
    moves = []
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
    for r in range(8):
        for c in range(8):
            if board[r][c] == 1:
                for dr, dc in directions:
                    piece_count = get_line_piece_count(board, r, c, dr, dc)
                    tr, tc = r + dr * piece_count, c + dc * piece_count
                    if 0 <= tr < 8 and 0 <= tc < 8 and is_legal_move(board, r, c, tr, tc, dr, dc, piece_count):
                        moves.append((r, c, tr, tc))
    return moves

def apply_move(board, r, c, tr, tc):
    new_board = copy.deepcopy(board)
    new_board[r][c] = 0
    if new_board[tr][tc] == -1:
        new_board[tr][tc] = 1  # capture and capture, but since moving to it, set to 1
    else:
        new_board[tr][tc] = 1
    return new_board

def count_components(board):
    visited = [[False]*8 for _ in range(8)]
    components = 0
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
    for r in range(8):
        for c in range(8):
            if board[r][c] == 1 and not visited[r][c]:
                components += 1
                stack = [(r, c)]
                visited[r][c] = True
                while stack:
                    cr, cc = stack.pop()
                    for dr, dc in directions:
                        nr, nc = cr + dr, cc + dc
                        if 0 <= nr < 8 and 0 <= nc < 8 and board[nr][nc] == 1 and not visited[nr][nc]:
                            visited[nr][nc] = True
                            stack.append((nr, nc))
    return components

def policy(board):
    legal_moves = get_legal_moves(board)
    if not legal_moves:
        # Though unlikely, ensure something is returned
        return "0,0:0,1"  # Dummy, but shouldn't happen
    best_move = None
    min_components = 9  # Max possible is 12
    for r, c, tr, tc in legal_moves:
        new_board = apply_move(board, r, c, tr, tc)
        comp = count_components(new_board)
        if comp < min_components:
            min_components = comp
            best_move = (r, c, tr, tc)
    if best_move:
        r, c, tr, tc = best_move
        return f"{r},{c}:{tr},{tc}"
    else:
        # Fallback, take first move
        r, c, tr, tc = legal_moves[0]
        return f"{r},{c}:{tr},{tc}"
