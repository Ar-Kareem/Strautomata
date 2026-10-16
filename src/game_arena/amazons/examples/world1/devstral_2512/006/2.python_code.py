
import numpy as np
import random
from typing import List, Tuple, Optional

def policy(board: np.ndarray) -> str:
    # Directions for queen-like movement (8 directions)
    DIRECTIONS = [(-1, -1), (-1, 0), (-1, 1),
                  (0, -1),          (0, 1),
                  (1, -1),  (1, 0), (1, 1)]

    def is_valid_position(row: int, col: int) -> bool:
        return 0 <= row < 6 and 0 <= col < 6

    def get_legal_moves(board: np.ndarray, player: int) -> List[Tuple[Tuple[int, int], Tuple[int, int], Tuple[int, int]]]:
        """Returns all legal moves for the given player (1 or 2)"""
        moves = []
        opponent = 3 - player

        for r in range(6):
            for c in range(6):
                if board[r, c] == player:
                    # Find all possible move destinations
                    for dr, dc in DIRECTIONS:
                        for step in range(1, 6):
                            nr, nc = r + dr * step, c + dc * step
                            if not is_valid_position(nr, nc):
                                break
                            if board[nr, nc] != 0:
                                break
                            # Found a valid move destination
                            # Now find all possible arrow shots from this position
                            for adr, adc in DIRECTIONS:
                                for astep in range(1, 6):
                                    ar, ac = nr + adr * astep, nc + adc * astep
                                    if not is_valid_position(ar, ac):
                                        break
                                    if board[ar, ac] != 0:
                                        break
                                    # Check if arrow path is clear (can pass through original position)
                                    clear = True
                                    for s in range(1, astep):
                                        ir, ic = nr + adr * s, nc + adc * s
                                        if board[ir, ic] != 0 and (ir != r or ic != c):
                                            clear = False
                                            break
                                    if clear:
                                        moves.append(((r, c), (nr, nc), (ar, ac)))
        return moves

    def evaluate_board(board: np.ndarray) -> float:
        """Evaluates the board position from the perspective of player 1"""
        # Count legal moves for both players
        player1_moves = len(get_legal_moves(board, 1))
        player2_moves = len(get_legal_moves(board, 2))

        if player2_moves == 0:
            return float('inf')  # Player 1 wins
        if player1_moves == 0:
            return float('-inf')  # Player 1 loses

        # Center control (weight 2.0)
        center = [(2, 2), (2, 3), (3, 2), (3, 3)]
        center_score = 0
        for r, c in center:
            if board[r, c] == 1:
                center_score += 1
            elif board[r, c] == 2:
                center_score -= 1

        # Mobility difference (weight 1.0)
        mobility_score = (player1_moves - player2_moves) / max(player1_moves + player2_moves, 1)

        # Amazon spread (weight 0.5) - prefer spread out amazons
        player1_positions = [(r, c) for r in range(6) for c in range(6) if board[r, c] == 1]
        player2_positions = [(r, c) for r in range(6) for c in range(6) if board[r, c] == 2]

        def calculate_spread(positions):
            if len(positions) < 2:
                return 0
            total_dist = 0
            for i in range(len(positions)):
                for j in range(i+1, len(positions)):
                    total_dist += abs(positions[i][0] - positions[j][0]) + abs(positions[i][1] - positions[j][1])
            return total_dist / (len(positions) * (len(positions) - 1) / 2)

        spread_score = calculate_spread(player1_positions) - calculate_spread(player2_positions)

        # Arrow blocking potential (weight 0.5)
        arrow_block_score = 0
        for r in range(6):
            for c in range(6):
                if board[r, c] == -1:
                    # Check if arrow is between opponent amazons
                    for dr, dc in DIRECTIONS:
                        count = 0
                        for step in range(1, 6):
                            nr, nc = r + dr * step, c + dc * step
                            if not is_valid_position(nr, nc):
                                break
                            if board[nr, nc] == 2:
                                count += 1
                            if board[nr, nc] != 0 and board[nr, nc] != 2:
                                break
                        if count >= 2:
                            arrow_block_score += 0.5

        total_score = (2.0 * center_score +
                       1.0 * mobility_score +
                       0.5 * spread_score +
                       0.5 * arrow_block_score)
        return total_score

    def minimax(board: np.ndarray, depth: int, alpha: float, beta: float, maximizing_player: bool) -> Tuple[float, Optional[Tuple[Tuple[int, int], Tuple[int, int], Tuple[int, int]]]]:
        if depth == 0:
            return evaluate_board(board), None

        legal_moves = get_legal_moves(board, 1 if maximizing_player else 2)

        if not legal_moves:
            return float('-inf') if maximizing_player else float('inf'), None

        if maximizing_player:
            best_score = float('-inf')
            best_move = None
            for move in legal_moves:
                (fr, fc), (tr, tc), (ar, ac) = move
                # Make the move
                new_board = board.copy()
                new_board[fr, fc] = 0
                new_board[tr, tc] = 1
                new_board[ar, ac] = -1

                score, _ = minimax(new_board, depth - 1, alpha, beta, False)
                if score > best_score:
                    best_score = score
                    best_move = move
                alpha = max(alpha, best_score)
                if beta <= alpha:
                    break
            return best_score, best_move
        else:
            best_score = float('inf')
            best_move = None
            for move in legal_moves:
                (fr, fc), (tr, tc), (ar, ac) = move
                # Make the move
                new_board = board.copy()
                new_board[fr, fc] = 0
                new_board[tr, tc] = 2
                new_board[ar, ac] = -1

                score, _ = minimax(new_board, depth - 1, alpha, beta, True)
                if score < best_score:
                    best_score = score
                    best_move = move
                beta = min(beta, best_score)
                if beta <= alpha:
                    break
            return best_score, best_move

    # Get all legal moves for the current player (player 1)
    legal_moves = get_legal_moves(board, 1)

    if not legal_moves:
        # Shouldn't happen per problem statement, but return a dummy move if it does
        return "0,0:1,0:2,0"

    # Try to find a winning move first
    for move in legal_moves:
        (fr, fc), (tr, tc), (ar, ac) = move
        new_board = board.copy()
        new_board[fr, fc] = 0
        new_board[tr, tc] = 1
        new_board[ar, ac] = -1

        opponent_moves = get_legal_moves(new_board, 2)
        if not opponent_moves:
            return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"

    # Use minimax with depth 2 to find the best move
    try:
        _, best_move = minimax(board, depth=2, alpha=float('-inf'), beta=float('inf'), maximizing_player=True)
        if best_move:
            (fr, fc), (tr, tc), (ar, ac) = best_move
            return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"
    except:
        pass

    # Fallback to random legal move if minimax fails or times out
    move = random.choice(legal_moves)
    (fr, fc), (tr, tc), (ar, ac) = move
    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"
