
import time
import math
from typing import Optional, List, Tuple

class TicTacToe4x4:
    def __init__(self, board: List[List[int]]):
        self.board = board
        self.size = 4
        self.winning_lines = self._generate_winning_lines()
    
    def _generate_winning_lines(self) -> List[List[Tuple[int, int]]]:
        """Generate all winning lines: rows, columns, diagonals."""
        lines = []
        # rows
        for r in range(self.size):
            lines.append([(r, c) for c in range(self.size)])
        # columns
        for c in range(self.size):
            lines.append([(r, c) for r in range(self.size)])
        # main diagonals
        lines.append([(i, i) for i in range(self.size)])
        lines.append([(i, self.size - 1 - i) for i in range(self.size)])
        return lines
    
    def check_winner(self) -> Optional[int]:
        """Return 1 if player 1 wins, -1 if player -1 wins, 0 for draw, None if game not over."""
        for line in self.winning_lines:
            values = [self.board[r][c] for (r, c) in line]
            if values[0] != 0 and all(v == values[0] for v in values):
                return values[0]
        # check for draw
        if all(self.board[r][c] != 0 for r in range(self.size) for c in range(self.size)):
            return 0
        return None
    
    def evaluate(self) -> float:
        """Heuristic evaluation for non-terminal state."""
        score = 0
        for line in self.winning_lines:
            count1 = 0
            count_neg1 = 0
            for (r, c) in line:
                if self.board[r][c] == 1:
                    count1 += 1
                elif self.board[r][c] == -1:
                    count_neg1 += 1
            if count1 > 0 and count_neg1 > 0:
                continue  # blocked line
            if count1 > 0:
                score += 10 ** (count1 - 1)
            if count_neg1 > 0:
                score -= 10 ** (count_neg1 - 1)
        return score
    
    def get_possible_moves(self) -> List[Tuple[int, int]]:
        moves = []
        for r in range(self.size):
            for c in range(self.size):
                if self.board[r][c] == 0:
                    moves.append((r, c))
        return moves
    
    def make_move(self, move: Tuple[int, int], player: int) -> None:
        r, c = move
        self.board[r][c] = player
    
    def undo_move(self, move: Tuple[int, int]) -> None:
        r, c = move
        self.board[r][c] = 0
    
    def is_terminal(self) -> bool:
        return self.check_winner() is not None

def minimax(game: TicTacToe4x4, depth: int, alpha: float, beta: float, maximizing_player: bool) -> float:
    """Minimax with alpha-beta pruning, depth limited."""
    winner = game.check_winner()
    if winner is not None:
        if winner == 1:
            return 10000  # win for us
        elif winner == -1:
            return -10000  # win for opponent
        else:
            return 0  # draw
    if depth == 0:
        return game.evaluate()
    
    moves = game.get_possible_moves()
    if maximizing_player:
        max_eval = -math.inf
        for move in moves:
            game.make_move(move, 1)
            eval = minimax(game, depth - 1, alpha, beta, False)
            game.undo_move(move)
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = math.inf
        for move in moves:
            game.make_move(move, -1)
            eval = minimax(game, depth - 1, alpha, beta, True)
            game.undo_move(move)
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval

def policy(board: List[List[int]]) -> Tuple[int, int]:
    # Time management: iterative deepening with time limit
    start_time = time.perf_counter()
    time_limit = 0.9  # seconds, leave some margin
    best_move = None
    game = TicTacToe4x4([row[:] for row in board])  # copy
    
    # If it's the first move, we can pick a corner or center? But we'll let minimax decide.
    # However, to speed up, we can pick a reasonable first move if board is empty.
    # Check if board is empty
    empty_count = sum(cell == 0 for row in board for cell in row)
    if empty_count == 16:
        # first move: choose center or corner? In 4x4, center is not a single cell.
        # We can choose (1,1) as a good starting point.
        return (1, 1)
    
    depth = 1
    while time.perf_counter() - start_time < time_limit:
        current_best = None
        best_score = -math.inf
        moves = game.get_possible_moves()
        # Order moves by heuristic? Not implemented for simplicity.
        for move in moves:
            game.make_move(move, 1)
            score = minimax(game, depth, -math.inf, math.inf, False)
            game.undo_move(move)
            if score > best_score:
                best_score = score
                current_best = move
            # break if time is running out
            if time.perf_counter() - start_time > time_limit:
                break
        if current_best is not None:
            best_move = current_best
        depth += 1
        if depth > 16:  # max depth
            break
    
    # fallback: if no move found (should not happen), pick first available
    if best_move is None:
        moves = game.get_possible_moves()
        best_move = moves[0]
    return best_move
