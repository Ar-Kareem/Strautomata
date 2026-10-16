
import random
import collections

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    n = len(board)
    empty_cells = []
    for z in range(n):
        for y in range(n):
            for x in range(n):
                if board[z][y][x] == 0:
                    empty_cells.append((z, y, x))

    if not empty_cells:
        raise ValueError("No empty cells available on the board.")

    # Check for immediate winning move
    for z, y, x in empty_cells:
        board[z][y][x] = 1  # Try placing our piece
        if check_win(board, 1):
            return z, y, x
        board[z][y][x] = 0  # Undo
    
    # Check for opponent's immediate winning move and block it
    for z, y, x in empty_cells:
        board[z][y][x] = -1  # Try placing opponent's piece
        if check_win(board, -1):
            return z, y, x
        board[z][y][x] = 0  # Undo

    # Minimax (simplified - look ahead one step for maximizing win potential)
    best_move_score = -float('inf')
    best_moves = []

    for z, y, x in empty_cells:
        board[z][y][x] = 1  # Try our move
        
        current_score = calculate_score(board, 1, n) - calculate_score(board, -1, n)  # Our score minus opponent's score
        
        # Consider opponent's response for a slightly better minimax
        opponent_empty_cells = []
        for oz in range(n):
            for oy in range(n):
                for ox in range(n):
                    if board[oz][oy][ox] == 0:
                        opponent_empty_cells.append((oz, oy, ox))

        if opponent_empty_cells:
            min_opponent_score = float('inf')
            for oz, oy, ox in opponent_empty_cells:
                board[oz][oy][ox] = -1
                opponent_response_score = calculate_score(board, 1, n) - calculate_score(board, -1, n)
                min_opponent_score = min(min_opponent_score, opponent_response_score)
                board[oz][oy][ox] = 0
            current_score = min(current_score, min_opponent_score) # Opponent will choose move that minimizes our score
        
        board[z][y][x] = 0 # Undo our move

        if current_score > best_move_score:
            best_move_score = current_score
            best_moves = [(z, y, x)]
        elif current_score == best_move_score:
            best_moves.append((z, y, x))

    if best_moves:
        return random.choice(best_moves)

    # If no strategic move found, pick a random empty cell
    return random.choice(empty_cells)


def check_win(board: list[list[list[int]]], player: int) -> bool:
    n = len(board)
    
    # Check all 2D planes (XY, XZ, YZ)
    for z in range(n):
        if check_win_2d(board[z], player): return True  # XY plane
    for y in range(n):
        plane_xz = [[board[z][y][x] for x in range(n)] for z in range(n)]
        if check_win_2d(plane_xz, player): return True  # XZ plane
    for x in range(n):
        plane_yz = [[board[z][y][x] for y in range(n)] for z in range(n)]
        if check_win_2d(plane_yz, player): return True  # YZ plane
        
    # Check 3D lines
    # Columns along Z-axis
    for y in range(n):
        for x in range(n):
            if all(board[z][y][x] == player for z in range(n)): return True
    
    # Main 3D diagonals
    if all(board[i][i][i] == player for i in range(n)): return True
    if all(board[i][i][n-1-i] == player for i in range(n)): return True
    if all(board[i][n-1-i][i] == player for i in range(n)): return True
    if all(board[n-1-i][i][i] == player for i in range(n)): return True
    
    # Other 3D diagonals (going across different dimensions)
    if all(board[i][n-1-i][n-1-i] == player for i in range(n)): return True
    if all(board[n-1-i][i][n-1-i] == player for i in range(n)): return True
    if all(board[n-1-i][n-1-i][i] == player for i in range(n)): return True
    if all(board[n-1-i][n-1-i][n-1-i] == player for i in range(n)): return True
            
    return False

def check_win_2d(plane: list[list[int]], player: int) -> bool:
    n = len(plane)
    # Check rows
    for row in plane:
        if all(cell == player for cell in row): return True
    # Check columns
    for col_idx in range(n):
        if all(plane[row_idx][col_idx] == player for row_idx in range(n)): return True
    # Check diagonals
    if all(plane[i][i] == player for i in range(n)): return True
    if all(plane[i][n - 1 - i] == player for i in range(n)): return True
    return False

def calculate_score(board: list[list[list[int]]], player: int, n: int) -> int:
    score = 0
    opponent = -player

    # Iterate through all possible lines (rows, columns, diagonals in 3D)
    
    # 2D Planes
    for z in range(n):
        score += evaluate_plane(board[z], player, opponent, n)  # XY plane
    for y in range(n):
        plane_xz = [[board[z][y][x] for x in range(n)] for z in range(n)]
        score += evaluate_plane(plane_xz, player, opponent, n)  # XZ plane
    for x in range(n):
        plane_yz = [[board[z][y][x] for y in range(n)] for z in range(n)]
        score += evaluate_plane(plane_yz, player, opponent, n)  # YZ plane
    
    # 3D lines
    # Columns along Z-axis
    for y in range(n):
        for x in range(n):
            line = [board[z][y][x] for z in range(n)]
            score += evaluate_line(line, player, opponent)
    
    # Main 3D diagonals
    score += evaluate_line([board[i][i][i] for i in range(n)], player, opponent)
    score += evaluate_line([board[i][i][n-1-i] for i in range(n)], player, opponent)
    score += evaluate_line([board[i][n-1-i][i] for i in range(n)], player, opponent)
    score += evaluate_line([board[n-1-i][i][i] for i in range(n)], player, opponent)
    
    # Other 3D diagonals
    score += evaluate_line([board[i][n-1-i][n-1-i] for i in range(n)], player, opponent)
    score += evaluate_line([board[n-1-i][i][n-1-i] for i in range(n)], player, opponent)
    score += evaluate_line([board[n-1-i][n-1-i][i] for i in range(n)], player, opponent)
    score += evaluate_line([board[n-1-i][n-1-i][n-1-i] for i in range(n)], player, opponent)

    return score

def evaluate_plane(plane: list[list[int]], player: int, opponent: int, n: int) -> int:
    plane_score = 0
    # Rows
    for row in plane:
        plane_score += evaluate_line(row, player, opponent)
    # Columns
    for col_idx in range(n):
        col = [plane[row_idx][col_idx] for row_idx in range(n)]
        plane_score += evaluate_line(col, player, opponent)
    # Diagonals
    diag1 = [plane[i][i] for i in range(n)]
    diag2 = [plane[i][n - 1 - i] for i in range(n)]
    plane_score += evaluate_line(diag1, player, opponent)
    plane_score += evaluate_line(diag2, player, opponent)
    return plane_score

def evaluate_line(line: list[int], player: int, opponent: int) -> int:
    player_count = line.count(player)
    opponent_count = line.count(opponent)
    empty_count = line.count(0)

    if opponent_count > 0 and player_count > 0:
        return 0  # Blocked line

    if player_count == len(line):
        return 1000  # Winning line
    
    if opponent_count == len(line):
        return -1000 # Opponent winning line

    if player_count > 0 and empty_count > 0:
        return player_count  # Potential line for player

    if opponent_count > 0 and empty_count > 0:
        return -opponent_count # Potential line for opponent (negative value)

    return 0
