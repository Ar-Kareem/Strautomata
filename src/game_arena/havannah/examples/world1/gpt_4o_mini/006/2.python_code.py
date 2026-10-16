
import numpy as np

def can_win(board, player):
    # Implement logic to check for winning structure: ring, bridge, fork
    # Here we will check the existence of winning patterns for the given player
    # This is a problem of hexagonal pathfinding which requires comprehensive checking
    pass  # Placeholder for actual win-check implementation

def possible_moves(me, opp, valid_mask):
    moves = []
    for row in range(len(valid_mask)):
        for col in range(len(valid_mask[row])):
            if valid_mask[row][col] and (row, col) not in me and (row, col) not in opp:
                moves.append((row, col))
    return moves

def is_blocking_move(move, opp, valid_mask):
    # Check if the move blocks an immediate winning condition for the opponent
    opp_plays = opp + [move]  # Simulate placing the stone
    return can_win(valid_mask, opp_plays)

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    # Create a potential moves list
    moves = possible_moves(me, opp, valid_mask)
    
    # First, check for immediate wins
    for move in moves:
        if can_win(valid_mask, me + [move]):
            return move  # Winning move found
    
    # Check to block the opponent if they have a potential win
    for move in moves:
        if is_blocking_move(move, opp, valid_mask):
            return move  # Block move found

    # If no immediate moves, select a strategic move or a random valid move
    # Here we could prioritize further strategic play but as a fallback:
    if moves:
        return moves[0]  # Fallback to the first valid move found

    raise RuntimeError("No valid moves available.")  # This should never happen with proper input
