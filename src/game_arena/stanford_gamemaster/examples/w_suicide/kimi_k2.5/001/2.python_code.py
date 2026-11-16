
import functools

# Define all winning lines (rows, columns, diagonals)
LINES = [
    [(0, 0), (0, 1), (0, 2)], [(1, 0), (1, 1), (1, 2)], [(2, 0), (2, 1), (2, 2)],  # rows
    [(0, 0), (1, 0), (2, 0)], [(0, 1), (1, 1), (2, 1)], [(0, 2), (1, 2), (2, 2)],  # cols
    [(0, 0), (1, 1), (2, 2)], [(0, 2), (1, 1), (2, 0)]  # diagonals
]

def check_win(board, player):
    """Return True if player has three marks in a row (which means they lose in Suicide)."""
    for line in LINES:
        if all(board[r][c] == player for r, c in line):
            return True
    return False

@functools.lru_cache(maxsize=None)
def minimax(board_tuple, player):
    """
    Minimax value for the current player from this state.
    Returns: 1 (win for current player), 0 (draw), -1 (loss for current player).
    A win occurs when the opponent is forced to complete three in a row.
    """
    board = [list(row) for row in board_tuple]
    
    # Check if previous player just lost (made a line)
    prev_player = "o" if player == "x" else "x"
    if check_win(board, prev_player):
        return 1  # Previous player lost, current player wins
    
    # Check for draw (full board)
    if all(board[r][c] != "b" for r in range(3) for c in range(3)):
        return 0
    
    next_player = "o" if player == "x" else "x"
    best_score = -2
    
    for r in range(3):
        for c in range(3):
            if board[r][c] == "b":
                # Make move
                board[r][c] = player
                
                if check_win(board, player):
                    # Current player completes a line and loses immediately
                    score = -1
                else:
                    # Recurse; opponent's win is our loss
                    score = -minimax(tuple(tuple(row) for row in board), next_player)
                
                # Undo move
                board[r][c] = "b"
                
                if score > best_score:
                    best_score = score
                    if best_score == 1:
                        return 1  # Alpha pruning: found a winning move
    
    return best_score

def policy(state: list[list[object]], role: str) -> str:
    # Parse state into 3x3 board
    board = [[None for _ in range(3)] for _ in range(3)]
    for fact in state:
        if fact[0] == "cell":
            r, c = int(fact[1]) - 1, int(fact[2]) - 1
            board[r][c] = fact[3]
    
    board_tuple = tuple(tuple(row) for row in board)
    best_score = -2
    best_moves = []
    
    for r in range(3):
        for c in range(3):
            if board[r][c] == "b":
                # Simulate move
                new_board = [list(row) for row in board_tuple]
                new_board[r][c] = role
                
                if check_win(new_board, role):
                    # Immediate loss, avoid if possible
                    score = -1
                else:
                    next_role = "o" if role == "x" else "x"
                    score = -minimax(tuple(tuple(row) for row in new_board), next_role)
                
                if score > best_score:
                    best_score = score
                    best_moves = [(r, c)]
                elif score == best_score:
                    best_moves.append((r, c))
    
    if not best_moves:
        # Fallback: return first available empty cell (should only happen if error)
        for r in range(3):
            for c in range(3):
                if board[r][c] == "b":
                    return f"mark({r+1},{c+1})"
        return "mark(1,1)"
    
    # Tie-breaking: prefer center > corners > edges for deterministic play
    def move_priority(move):
        r, c = move
        if r == 1 and c == 1:
            return 0  # Center
        if (r, c) in [(0, 0), (0, 2), (2, 0), (2, 2)]:
            return 1  # Corner
        return 2  # Edge
    
    best_moves.sort(key=move_priority)
    chosen_r, chosen_c = best_moves[0]
    return f"mark({chosen_r+1},{chosen_c+1})"
