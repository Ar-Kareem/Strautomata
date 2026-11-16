
import copy

def get_legal_moves(board, player):
    moves = []
    for r in range(8):
        for c in range(8):
            if board[r][c] != player:
                continue
            directions = [(0,1), (1,0), (0,-1), (-1,0), (1,1), (1,-1), (-1,1), (-1,-1)]
            for dr, dc in directions:
                # Calculate the line of movement
                line_cells = []
                # Positive direction
                step = 0
                while True:
                    nr = r + dr * step
                    nc = c + dc * step
                    if not (0 <= nr < 8 and 0 <= nc < 8):
                        break
                    line_cells.append((nr, nc))
                    step += 1
                # Negative direction
                step = -1
                while True:
                    nr = r + dr * step
                    nc = c + dc * step
                    if not (0 <= nr < 8 and 0 <= nc < 8):
                        break
                    line_cells.append((nr, nc))
                    step -= 1
                # Count total pieces in line
                total_pieces = sum(1 for (nr, nc) in line_cells if board[nr][nc] != 0)
                if total_pieces == 0:
                    continue
                # Check moves in both directions
                for direction in [1, -1]:
                    target_r = r + dr * total_pieces * direction
                    target_c = c + dc * total_pieces * direction
                    if not (0 <= target_r < 8 and 0 <= target_c < 8):
                        continue
                    if board[target_r][target_c] == player:
                        continue
                    # Validate path
                    valid = True
                    for step in range(1, total_pieces):
                        check_r = r + dr * step * direction
                        check_c = c + dc * step * direction
                        if not (0 <= check_r < 8 and 0 <= check_c < 8):
                            valid = False
                            break
                        if board[check_r][check_c] == -player:
                            valid = False
                            break
                    if valid:
                        moves.append(f"{r},{c}:{target_r},{target_c}")
    return moves

def apply_move(board, move_str, player):
    from_str, to_str = move_str.split(':')
    from_row, from_col = map(int, from_str.split(','))
    to_row, to_col = map(int, to_str.split(','))
    new_board = [row[:] for row in board]  # Deep copy
    new_board[from_row][from_col] = 0
    new_board[to_row][to_col] = player  # Captures opponent piece if present
    return new_board

def count_connected_components(board, player):
    visited = set()
    groups = 0
    for r in range(8):
        for c in range(8):
            if board[r][c] == player and (r, c) not in visited:
                groups += 1
                stack = [(r, c)]
                visited.add((r, c))
                while stack:
                    cr, cc = stack.pop()
                    for dr in [-1, 0, 1]:
                        for dc in [-1, 0, 1]:
                            if dr == 0 and dc == 0:
                                continue
                            nr, nc = cr + dr, cc + dc
                            if 0 <= nr < 8 and 0 <= nc < 8:
                                if board[nr][nc] == player and (nr, nc) not in visited:
                                    visited.add((nr, nc))
                                    stack.append((nr, nc))
    return groups

def evaluate(board, player):
    my_groups = count_connected_components(board, player)
    opp_groups = count_connected_components(board, -player)
    my_pieces = sum(row.count(player) for row in board)
    opp_pieces = sum(row.count(-player) for row in board)
    
    score = (1000.0 / my_groups) if my_groups != 0 else 10000.0  # Strong emphasis on connectivity
    score -= opp_groups * 50.0  # Disrupt opponent's connectivity
    score += (my_pieces - opp_pieces) * 100  # Significant reward for captures
    
    # Central control bonus
    center = 3.5
    for r in range(8):
        for c in range(8):
            if board[r][c] == player:
                dist = abs(r - center) + abs(c - center)
                score += (4 - dist) * 2  # Bonus up to 4 points per piece
    return score

def policy(board):
    my_moves = get_legal_moves(board, 1)
    if not my_moves:
        return None
    
    best_move = my_moves[0]
    best_score = -float('inf')
    
    for move in my_moves:
        new_board = apply_move(board, move, 1)
        opp_moves = get_legal_moves(new_board, -1)
        
        if not opp_moves:
            return move  # Immediate win if opponent has no moves
        
        min_score = float('inf')
        for opp_move in opp_moves:
            opp_board = apply_move(new_board, opp_move, -1)
            score = evaluate(opp_board, 1)
            if score < min_score:
                min_score = score
        
        if min_score > best_score:
            best_score = min_score
            best_move = move
    
    return best_move
