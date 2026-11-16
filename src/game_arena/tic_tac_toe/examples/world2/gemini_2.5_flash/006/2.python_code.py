
import math

class TicTacToeAI:
    def __init__(self):
        self.ME = 1
        self.OPPONENT = -1
        self.EMPTY = 0

        self.WINNING_SCORE = 100000
        self.LOSE_SCORE = -100000

        # Max depth for minimax search.
        # A depth of 5 provides a good balance of strength and performance for a 4x4 board
        # within the 1-second time limit. Deepening this too much will exceed the time limit.
        self.MAX_DEPTH = 5 

        # Pre-compute all winning lines once to avoid repeated calculations.
        self._WINNING_LINES = self._generate_winning_lines()

    def _generate_winning_lines(self):
        """Generates all possible 4-in-a-row winning lines for a 4x4 board.
        A winning line consists of 4 cells in a row, column, or main diagonal.
        """
        lines = []
        # Rows
        for r in range(4):
            lines.append([(r, c) for c in range(4)])
        # Columns
        for c in range(4):
            lines.append([(r, c) for r in range(4)])
        # Main Diagonals
        lines.append([(i, i) for i in range(4)])        # Top-left to bottom-right
        lines.append([(i, 3 - i) for i in range(4)])   # Top-right to bottom-left
        return lines

    def _get_empty_cells(self, board):
        """Returns a list of all empty (row, col) coordinates on the board."""
        empty_cells = []
        for r in range(4):
            for c in range(4):
                if board[r][c] == self.EMPTY:
                    empty_cells.append((r, c))
        return empty_cells

    def _check_win(self, board, player):
        """Checks if the given player has won the game on the current board state."""
        for line in self._WINNING_LINES:
            if all(board[r][c] == player for r, c in line):
                return True
        return False

    def _board_is_full(self, board):
        """Checks if the board is completely filled."""
        # This is a faster check than iterating if _get_empty_cells is expensive
        # or if we need to quickly know if it's a draw state.
        for r in range(4):
            for c in range(4):
                if board[r][c] == self.EMPTY:
                    return False
        return True

    def _evaluate_board(self, board):
        """Evaluates the current board state from the perspective of self.ME (player 1).
           Returns a numeric score. Higher scores are favorable for self.ME, lower for the opponent.
           This heuristic is used when minimax search depth is reached or for draw scenarios.
        """
        score = 0

        for line in self._WINNING_LINES:
            my_pieces = 0
            opp_pieces = 0
            for r, c in line:
                if board[r][c] == self.ME:
                    my_pieces += 1
                elif board[r][c] == self.OPPONENT:
                    opp_pieces += 1
            
            # Immediately return a decisive score if a win/loss state is found.
            # This helps prune earlier in the minimax tree.
            if my_pieces == 4:
                return self.WINNING_SCORE
            if opp_pieces == 4:
                return self.LOSE_SCORE
                
            # Heuristic scoring: Prioritize lines that are closer to winning for ME,
            # and penalize lines where the opponent is closer to winning.
            # A line is only scored if it's not blocked by the other player.
            if opp_pieces == 0: # This line contains only my pieces or is empty
                if my_pieces == 3: score += 500  # 3 in a row, one move to win
                elif my_pieces == 2: score += 50   # 2 in a row
                elif my_pieces == 1: score += 5    # 1 in a row
            
            if my_pieces == 0: # This line contains only opponent's pieces or is empty
                if opp_pieces == 3: score -= 500  # Opponent has 3 in a row, urgent block!
                elif opp_pieces == 2: score -= 50
                elif opp_pieces == 1: score -= 5
                
        return score

    def _minimax(self, board, depth, is_maximizing_player, alpha, beta):
        """Minimax algorithm with Alpha-Beta pruning for optimal decision making."""

        # Base cases for recursion:
        # 1. Terminal states (win, loss, draw)
        if self._check_win(board, self.ME):
            # Prefer solutions that lead to a win faster (smaller depth)
            return self.WINNING_SCORE - depth 
        if self._check_win(board, self.OPPONENT):
            # Prefer solutions that lead to a loss slower (larger depth for opponent's win)
            return self.LOSE_SCORE + depth    
        if self._board_is_full(board):
            return 0  # Draw
        # 2. Search depth limit reached
        if depth == self.MAX_DEPTH:
            return self._evaluate_board(board)

        empty_cells = self._get_empty_cells(board)
        # Fallback for empty board, although _board_is_full should catch this first.
        if not empty_cells: 
            return 0

        if is_maximizing_player: # AI (ME) is trying to maximize the score
            max_eval = -math.inf
            for r, c in empty_cells:
                board[r][c] = self.ME # Make the move temporarily
                eval = self._minimax(board, depth + 1, False, alpha, beta)
                board[r][c] = self.EMPTY # Undo the move
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval) # Update alpha
                if beta <= alpha: # Alpha-Beta Pruning: no need to search further
                    break
            return max_eval
        else:  # Opponent is trying to minimize my score
            min_eval = math.inf
            for r, c in empty_cells:
                board[r][c] = self.OPPONENT # Make the opponent's move temporarily
                eval = self._minimax(board, depth + 1, True, alpha, beta)
                board[r][c] = self.EMPTY  # Undo the move
                min_eval = min(min_eval, eval)
                beta = min(beta, eval) # Update beta
                if beta <= alpha: # Alpha-Beta Pruning: no need to search further
                    break
            return min_eval

    def policy(self, board: list[list[int]]) -> tuple[int, int]:
        """
        The main function that determines the next best move for the AI (player 1).
        It prioritizes immediate wins, then immediate blocks, and finally uses 
        minimax with alpha-beta pruning for strategic depth.
        """
        
        empty_cells = self._get_empty_cells(board)
        if not empty_cells:
            # If no empty cells, the board is full. Return a default invalid move.
            # The game manager should ideally not call policy in this state.
            return (0, 0) 

        # 1. Check for immediate win: If I can win in the next move, take it.
        # This is the most crucial type of move.
        for r, c in empty_cells:
            board[r][c] = self.ME # Temporarily place my piece
            if self._check_win(board, self.ME):
                board[r][c] = self.EMPTY # Undo the temporary move
                return (r, c) # Return the winning move
            board[r][c] = self.EMPTY # Undo the temporary move

        # 2. Check for immediate block: If the opponent can win in their next move, block it.
        # This prevents the opponent from winning.
        for r, c in empty_cells:
            board[r][c] = self.OPPONENT # Temporarily place opponent's piece
            if self._check_win(board, self.OPPONENT):
                board[r][c] = self.EMPTY # Undo the temporary move
                return (r, c) # Return the blocking move
            board[r][c] = self.EMPTY # Undo the temporary move

        # 3. If no immediate wins or blocks, use Minimax with Alpha-Beta pruning 
        # to find the best strategic move.
        best_score = -math.inf
        # Initialize best_move with the first empty cell as a fallback.
        best_move = empty_cells[0] 

        # It can sometimes be beneficial to shuffle empty_cells to explore different 
        # branches first, potentially improving alpha-beta pruning effectiveness 
        # or introducing slight variation if multiple moves yield the same optimal score.
        # import random
        # random.shuffle(empty_cells)

        for r, c in empty_cells:
            board[r][c] = self.ME # Make the potential move
            # Call minimax for the opponent (minimizing player) from the new board state
            current_score = self._minimax(board, 0, False, -math.inf, math.inf)
            board[r][c] = self.EMPTY # Undo the potential move

            if current_score > best_score:
                best_score = current_score
                best_move = (r, c)
            # If scores are equal, we could also randomly pick, but current behavior is fine.

        return best_move

# Create a single instance of the TicTacToeAI class.
# This ensures that winning lines are generated only once, improving efficiency
# for repeated calls to the policy function.
_tic_tac_toe_ai_instance = TicTacToeAI()

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Public entry point for the AI's move decision.
    Delegates the call to the pre-initialized TicTacToeAI instance.
    """
    return _tic_tac_toe_ai_instance.policy(board)

