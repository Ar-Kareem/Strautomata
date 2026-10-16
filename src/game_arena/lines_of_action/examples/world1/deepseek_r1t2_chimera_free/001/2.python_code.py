
import collections
import copy

# Centrality grid to prioritize central positions
CENTRALITY_GRID = [
    [1, 1, 2, 2, 2, 2, 1, 1],
    [1, 2, 3, 3, 3, 3, 2, 1],
    [2, 3, 4, 4, 4, 4, 3, 2],
    [2, 3, 4, 5, 5, 4, 3, 2],
    [2, 3, 4, 5, 5, 4, 3, 2],
    [2, 3, 4, 4, 4, 4, 3, 2],
    [1, 2, 3, 3, 3, 3, 2, 1],
    [1, 1, 2, 2, 2, 2, 1, 1],
]

def count_connected_components(board, player):
    """Count the number of connected components for the given player using BFS."""
    visited = set()
    component_count = 0
    rows = len(board)
    cols = len(board[0])
    for r in range(rows):
        for c in range(cols):
            if board[r][c] == player and (r, c) not in visited:
                # BFS to mark all connected pieces
                queue = collections.deque([(r, c)])
                visited.add((r, c))
                while queue:
                    x, y = queue.popleft()
                    for dx in [-1, 0, 1]:
                        for dy in [-1, 0, 1]:
                            if dx == 0 and dy == 0:
                                continue
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < rows and 0 <= ny < cols:
                                if board[nx][ny] == player and (nx, ny) not in visited:
                                    visited.add((nx, ny))
                                    queue.append((nx, ny))
                component_count += 1
    return component_count

def get_line_count(board, r, c, direction_type):
    """Count the number of pieces in the specified line (row, column, or diagonal)."""
    count = 0
    if direction_type == 'row':
        count = sum(1 for cell in board[r] if cell != 0)
    elif direction_type == 'col':
        count = sum(1 for row in board if row[c] != 0)
    elif direction_type == 'diag1':  # \ diagonal
        k = r + c
        for i in range(8):
            j = k - i
            if 0 <= i < 8 and 0 <= j < 8:
                if board[i][j] != 0:
                    count += 1
    elif direction_type == 'diag2':  # / diagonal
        k = r - c
        for i in range(8):
            j = i - k
            if 0 <= i < 8 and 0 <= j < 8:
                if board[i][j] != 0:
                    count += 1
    return count

def generate_moves(board, player):
    """Generate all valid moves for the given player."""
    moves = []
    directions = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
    for r in range(8):
        for c in range(8):
            if board[r][c] != player:
                continue
            for dr, dc in directions:
                # Determine direction type for line count
                if dr == 0 and dc != 0:
                    direction_type = 'row'
                elif dc == 0 and dr != 0:
                    direction_type = 'col'
                else:
                    direction_type = 'diag1' if dr == dc else 'diag2'
                line_count = get_line_count(board, r, c, direction_type)
                # Check if line_count is 0 (shouldn't happen as current cell is counted)
                if line_count == 0:
                    continue
                nr = r + dr * line_count
                nc = c + dc * line_count
                # Check if destination is within bounds
                if 0 <= nr < 8 and 0 <= nc < 8:
                    valid = True
                    # Check if any opponent pieces are jumped over (excluding destination)
                    for step in range(1, line_count):
                        tr = r + dr * step
                        tc = c + dc * step
                        if board[tr][tc] == -player:
                            valid = False
                            break
                    if not valid:
                        continue
                    # Check destination is not own piece
                    if board[nr][nc] == player:
                        continue
                    moves.append((r, c, nr, nc))
    return moves

def apply_move(board, move, player):
    """Apply the move to the board and return a new board."""
    new_board = [list(row) for row in board]
    r, c, nr, nc = move
    new_board[r][c] = 0
    new_board[nr][nc] = player
    return new_board

def evaluate(board):
    """Evaluate the board from the perspective of player 1 (maximizing player)."""
    my_components = count_connected_components(board, 1)
    opp_components = count_connected_components(board, -1)
    my_pieces = sum(row.count(1) for row in board)
    opp_pieces = sum(row.count(-1) for row in board)
    my_centrality = sum(CENTRALITY_GRID[r][c] for r in range(8) for c in range(8) if board[r][c] == 1)
    opp_centrality = sum(CENTRALITY_GRID[r][c] for r in range(8) for c in range(8) if board[r][c] == -1)
    
    # Primary factors
    score = (opp_components - my_components) * 1000  # Minimize own components
    score += (my_centrality - opp_centrality) * 10    # Central control
    score += (my_pieces - opp_pieces) * 100           # Piece differential
    
    return score

def policy(board):
    # Check if we have any immediate winning move
    my_moves = generate_moves(board, 1)
    if not my_moves:
        # Shouldn't happen as policy is called only when there's a move
        return "0,0:0,0"  # Fallback
    
    best_move = None
    best_score = float('-inf')
    
    for move in my_moves:
        new_board = apply_move(board, move, 1)
        # Check if this move wins the game
        if count_connected_components(new_board, 1) == 1:
            return f"{move[0]},{move[1]}:{move[2]},{move[3]}"
        
        # Generate opponent's moves and find the worst-case scenario
        opp_moves = generate_moves(new_board, -1)
        min_score = float('inf')
        if len(opp_moves) == 0:
            # Opponent can't move; evaluate the board
            current_score = evaluate(new_board)
            if current_score > best_score:
                best_score = current_score
                best_move = move
        else:
            for opp_move in opp_moves:
                opp_board = apply_move(new_board, opp_move, -1)
                current_score = evaluate(opp_board)
                if current_score < min_score:
                    min_score = current_score
            if min_score > best_score:
                best_score = min_score
                best_move = move
    
    # Format the best move found
    if best_move is None:
        # Fallback: pick first move if no move selected
        best_move = my_moves[0]
    return f"{best_move[0]},{best_move[1]}:{best_move[2]},{best_move[3]}"
