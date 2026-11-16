
def policy(state: list[list[object]], role: str) -> str:
    # Parse the board state
    board = {}
    for prop in state:
        if prop[0] == "cell":
            row, col, color = int(prop[1]), int(prop[2]), prop[3]
            board[(row, col)] = color
    
    # Determine direction: red moves up (decreasing row), black moves down (increasing row)
    is_red = role == "red"
    direction = -1 if is_red else 1
    opponent = "black" if is_red else "red"
    
    # Find all pieces of current role
    my_pieces = [(r, c) for (r, c), color in board.items() if color == role]
    
    # Generate all possible moves and jumps
    legal_moves = []
    
    # Check for jumps first (they are often mandatory)
    for r, c in my_pieces:
        jumps = find_jumps(board, r, c, role, opponent)
        legal_moves.extend(jumps)
    
    # If jumps exist, prioritize them
    if legal_moves:
        # Sort by length of jump sequence (longer chains first for maximum capture)
        legal_moves.sort(key=lambda x: -len(x.split('(')))
        return legal_moves[0]
    
    # Otherwise look for regular moves
    for r, c in my_pieces:
        moves = find_regular_moves(board, r, c, role, direction)
        legal_moves.extend(moves)
    
    # Return first available move
    if legal_moves:
        return legal_moves[0]
    
    # Fallback (shouldn't reach here if game is legal)
    return "move(5,1,4,1)" if is_red else "move(1,1,2,1)"

def find_jumps(board, row, col, role, opponent, visited=None):
    """Find all possible jump sequences from a position"""
    if visited is None:
        visited = set()
    
    jumps = []
    visited_local = visited.copy()
    visited_local.add((row, col))
    
    # Check all 4 diagonal directions
    for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
        adj_r, adj_c = row + dr, col + dc
        jump_r, jump_c = row + 2*dr, col + 2*dc
        
        # Check if jump is valid
        if 1 <= jump_r <= 5 and 1 <= jump_c <= 5:
            # Check if adjacent has opponent piece and landing is empty
            if (adj_r, adj_c) in board and board[(adj_r, adj_c)] == opponent:
                if (jump_r, jump_c) not in board:
                    # Valid jump
                    jump_move = f"jump({row},{col},{adj_r},{adj_c},{jump_r},{jump_c})"
                    jumps.append(jump_move)
                    
                    # Look for chained jumps
                    board_copy = board.copy()
                    board_copy[(row, col)] = "blank"
                    del board_copy[(row, col)]
                    board_copy[(adj_r, adj_c)] = "blank"
                    del board_copy[(adj_r, adj_c)]
                    board_copy[(jump_r, jump_c)] = role
                    
                    chained = find_jumps(board_copy, jump_r, jump_c, role, opponent, visited_local)
                    if chained:
                        # Extend jump sequences
                        jumps.extend([jump_move + " " + c for c in chained])
    
    return jumps if jumps else []

def find_regular_moves(board, row, col, role, direction):
    """Find all regular (non-jump) moves from a position"""
    moves = []
    
    # Can move diagonally forward
    for dc in [-1, 1]:
        new_r = row + direction
        new_c = col + dc
        
        # Check bounds
        if 1 <= new_r <= 5 and 1 <= new_c <= 5:
            # Check if destination is empty
            if (new_r, new_c) not in board:
                moves.append(f"move({row},{col},{new_r},{new_c})")
    
    return moves
