
import sys
from typing import List, Tuple, Optional

# The board representation:
#   indices 0-5: your houses
#   index 6: your store
#   indices 7-12: opponent's houses
#   index 13: opponent's store

MAX_DEPTH = 5  # Depth limit for the search (can be adjusted)

def apply_move(board: List[int], player: int, move: int) -> Tuple[List[int], bool, bool]:
    """
    Apply a move for the given player (0 for you, 1 for opponent) on the given board.
    Returns (new_board, extra_move, terminal).
    - extra_move: True if the move results in an extra turn (last seed landed in the player's store).
    - terminal: True if the move ends the game (one side has no seeds in houses).
    """
    # Create a copy of the board to avoid modifying the original.
    new_board = list(board)

    # Determine the start index for the move based on the player.
    if player == 0:
        start_idx = move  # your house index (0..5)
        order = list(range(0, 13))  # your houses (0..5), your store (6), opponent houses (7..12) - skipping opponent store (13)
    else:
        start_idx = 7 + move  # opponent house index (7..12)
        # Order: opponent houses (7..12), opponent store (13), your houses (0..5) - skipping your store (6)
        order = list(range(7, 13)) + [13] + list(range(0, 6))

    # Remove the seeds from the starting house.
    seeds = new_board[start_idx]
    if seeds == 0:
        # Should not happen if move is legal.
        return new_board, False, False
    new_board[start_idx] = 0

    # Find the position of the start_idx in the order list.
    try:
        pos_in_order = order.index(start_idx)
    except ValueError:
        raise ValueError(f"Start index {start_idx} not found in order list for player {player}")

    # Distribute the seeds.
    idx = (pos_in_order + 1) % len(order)
    last_idx = None
    last_prev = None
    for _ in range(seeds):
        board_idx = order[idx]
        prev = new_board[board_idx]
        new_board[board_idx] += 1
        last_idx = board_idx
        last_prev = prev
        idx = (idx + 1) % len(order)

    # Handle capture and extra move for the player.
    extra_move = False
    if player == 0:
        # Your turn.
        if last_idx == 6:
            extra_move = True
        # Capture: if last seed landed in your house that was empty and opposite opponent house is non-empty.
        if 0 <= last_idx <= 5 and last_prev == 0:
            opposite = 12 - last_idx
            if new_board[opposite] > 0:
                captured = new_board[last_idx] + new_board[opposite]
                new_board[6] += captured
                new_board[last_idx] = 0
                new_board[opposite] = 0
    else:
        # Opponent's turn.
        if last_idx == 13:
            extra_move = True
        # Capture: if last seed landed in opponent house that was empty and opposite your house is non-empty.
        if 7 <= last_idx <= 12 and last_prev == 0:
            opposite = 12 - last_idx
            if new_board[opposite] > 0:
                captured = new_board[last_idx] + new_board[opposite]
                new_board[13] += captured
                new_board[last_idx] = 0
                new_board[opposite] = 0

    # Check for terminal condition: one player has no seeds in any of their houses.
    you_houses_sum = sum(new_board[0:6])
    opp_houses_sum = sum(new_board[7:13])
    terminal = False
    if you_houses_sum == 0 or opp_houses_sum == 0:
        terminal = True
        if you_houses_sum == 0:
            total = opp_houses_sum
            new_board[13] += total
            new_board[7:13] = [0]*6
        else:
            total = you_houses_sum
            new_board[6] += total
            new_board[0:6] = [0]*6

    return new_board, extra_move, terminal

def has_legal_moves(board: List[int], player: int) -> bool:
    """Check if the player has any legal moves (non-empty houses)."""
    if player == 0:
        return any(board[i] > 0 for i in range(6))
    else:
        return any(board[i] > 0 for i in range(7,13))

def evaluate(board: List[int], is_you_turn: bool) -> int:
    """Evaluate the board from the perspective of the player to move (maximizing)."""
    diff = board[6] - board[13]  # your store minus opponent store
    return diff if is_you_turn else -diff

def negamax(board: List[int], depth: int, is_you_turn: bool, alpha: int, beta: int) -> Tuple[int, Optional[int]]:
    """
    Negamax with alpha-beta pruning.
    Returns (score, best_move) from the perspective of the player to move (maximizing).
    """
    # Base case: depth 0 or terminal
    if depth == 0:
        return evaluate(board, is_you_turn), None

    # Check for terminal condition (one side has no houses with seeds)
    if sum(board[0:6]) == 0 or sum(board[7:13]) == 0:
        return evaluate(board, is_you_turn), None

    # Generate legal moves
    if is_you_turn:
        moves = [i for i in range(6) if board[i] > 0]
    else:
        moves = [i for i in range(7,13) if board[i] > 0]

    # If there are no moves (should not happen due to terminal check), return evaluation.
    if not moves:
        return evaluate(board, is_you_turn), None

    best_score = -10**9
    best_move = None

    for move in moves:
        # Apply the move
        new_board, extra_move, terminal = apply_move(board, 0 if is_you_turn else 1, move)

        if terminal:
            score = evaluate(new_board, is_you_turn)
        else:
            if extra_move and has_legal_moves(new_board, 0 if is_you_turn else 1):
                # Same player, depth unchanged
                score, _ = negamax(new_board, depth, is_you_turn, -beta, -alpha)
            else:
                # Switch player, depth-1
                score, _ = negamax(new_board, depth-1, not is_you_turn, -beta, -alpha)
                # Invert sign because we are moving to opponent (minimizing) in a maximizing node
                score = -score

        # Update best move and score
        if score > best_score:
            best_score = score
            best_move = move

        # Alpha-beta pruning
        alpha = max(alpha, score)
        if beta <= alpha:
            break

    return best_score, best_move

def policy(you: List[int], opponent: List[int]) -> int:
    """Choose a move for the current player (you) on the given board state."""
    # Combine the two lists into one board representation
    board = you[:] + opponent[:]  # length 14

    # Perform the search
    _, best_move = negamax(board, MAX_DEPTH, True, -10**9, 10**9)

    # In case no move is found (should not happen), choose the first non-empty house.
    if best_move is None:
        for i in range(6):
            if you[i] > 0:
                return i
        # If there are no moves, but the problem states there will be at least one, we return 0 as a fallback.
        return 0

    return best_move
