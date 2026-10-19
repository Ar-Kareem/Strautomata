
import numpy as np
from typing import Optional

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    """
    3x3x3 Tic Tac Toe policy that attempts to win, block, or make strategic moves.
    """
    board_np = np.array(board)
    
    # Get all winning lines in 3x3x3 tic-tac-toe
    lines = get_all_lines()
    
    # 1. Check if we can win immediately
    move = find_winning_move(board_np, lines, player=1)
    if move is not None:
        return move
    
    # 2. Block opponent from winning
    move = find_winning_move(board_np, lines, player=-1)
    if move is not None:
        return move
    
    # 3. Try to create a fork (two winning threats)
    move = find_fork_move(board_np, lines, player=1)
    if move is not None:
        return move
    
    # 4. Block opponent's fork
    move = find_fork_move(board_np, lines, player=-1)
    if move is not None:
        return move
    
    # 5. Take center if available
    if board_np[1, 1, 1] == 0:
        return (1, 1, 1)
    
    # 6. Take strategic positions (corners, then edges)
    strategic_positions = [
        (0, 0, 0), (0, 0, 2), (0, 2, 0), (0, 2, 2),
        (2, 0, 0), (2, 0, 2), (2, 2, 0), (2, 2, 2),
        (1, 1, 0), (1, 1, 2), (1, 0, 1), (1, 2, 1),
        (0, 1, 1), (2, 1, 1)
    ]
    
    for pos in strategic_positions:
        if board_np[pos] == 0:
            return pos
    
    # 7. Take any available position
    empty_cells = np.argwhere(board_np == 0)
    if len(empty_cells) > 0:
        cell = empty_cells[0]
        return tuple(cell)
    
    return (0, 0, 0)  # Fallback


def get_all_lines():
    """Generate all possible winning lines in 3x3x3 tic-tac-toe."""
    lines = []
    
    # Lines parallel to axes
    for i in range(3):
        for j in range(3):
            # Lines parallel to x-axis
            lines.append([(i, j, k) for k in range(3)])
            # Lines parallel to y-axis
            lines.append([(i, k, j) for k in range(3)])
            # Lines parallel to z-axis
            lines.append([(k, i, j) for k in range(3)])
    
    # Diagonals on faces
    for i in range(3):
        # xy-plane diagonals
        lines.append([(j, j, i) for j in range(3)])
        lines.append([(j, 2-j, i) for j in range(3)])
        # xz-plane diagonals
        lines.append([(j, i, j) for j in range(3)])
        lines.append([(j, i, 2-j) for j in range(3)])
        # yz-plane diagonals
        lines.append([(i, j, j) for j in range(3)])
        lines.append([(i, j, 2-j) for j in range(3)])
    
    # Space diagonals (4 total)
    lines.append([(i, i, i) for i in range(3)])
    lines.append([(i, i, 2-i) for i in range(3)])
    lines.append([(i, 2-i, i) for i in range(3)])
    lines.append([(2-i, i, i) for i in range(3)])
    
    return lines


def find_winning_move(board: np.ndarray, lines: list, player: int) -> Optional[tuple]:
    """Find a move that wins (or blocks) immediately for the given player."""
    for line in lines:
        values = [board[pos] for pos in line]
        if values.count(player) == 2 and values.count(0) == 1:
            # Found a line with 2 of player's pieces and 1 empty
            for pos in line:
                if board[pos] == 0:
                    return pos
    return None


def find_fork_move(board: np.ndarray, lines: list, player: int) -> Optional[tuple]:
    """Find a move that creates multiple winning threats (fork)."""
    empty_cells = np.argwhere(board == 0)
    
    for cell in empty_cells:
        cell = tuple(cell)
        # Simulate placing the piece
        test_board = board.copy()
        test_board[cell] = player
        
        # Count how many lines now have 2 pieces and 1 empty
        threats = 0
        for line in lines:
            values = [test_board[pos] for pos in line]
            if values.count(player) == 2 and values.count(0) == 1:
                threats += 1
        
        # If this creates 2+ threats, it's a fork
        if threats >= 2:
            return cell
    
    return None
