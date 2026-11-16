
import random
import time

ROW_COUNT = 6
COLUMN_COUNT = 7

class TimeoutError(Exception):
    """Raised when the search time limit is exceeded."""
    pass

class Connect4AI:
    def __init__(self):
        self.time_limit = 0.95  # seconds allowed for search
        self.start_time = 0.0
        self.board = None

    def get_move(self, board: list[list[int]]) -> int:
        """Main entry point: return the column to play."""
        # Ensure we work on a mutable copy
        self.board = [row[:] for row in board]
        self.start_time = time.time()
        valid_moves = self.get_valid_locations()
        if not valid_moves:
            return random.randint(0, COLUMN_COUNT - 1)  # fallback

        # 1. Immediate win
        for col in valid_moves:
            row = self.get_next_open_row(col)
            self.drop_piece(row, col, 1)
            if self.winning_move(1):
                self.remove_piece(row, col)
                return col
            self.remove_piece(row, col)

        # 2. Block opponent's immediate win
        for col in valid_moves:
            row = self.get_next_open_row(col)
            self.drop_piece(row, col, -1)
            if self.winning_move(-1):
                self.remove_piece(row, col)
                return col
            self.remove_piece(row, col)

        # 3. Iterative deepening alpha-beta search
        best_move = valid_moves[0]  # fallback
        try:
            for depth in range(1, 43):  # max possible moves = 42
                if time.time() - self.start_time > self.time_limit:
                    break
                move, _ = self.minimax(depth, -float('inf'), float('inf'), True)
                if move is not None:
                    best_move = move
        except TimeoutError:
            pass
        return best_move

    def is_valid_location(self, col: int) -> bool:
        return self.board[0][col] == 0

    def get_valid_locations(self) -> list[int]:
        return [c for c in range(COLUMN_COUNT) if self.is_valid_location(c)]

    def get_next_open_row(self, col: int) -> int:
        for r in range(ROW_COUNT - 1, -1, -1):
            if self.board[r][col] == 0:
                return r
        return -1

    def drop_piece(self, row: int, col: int, piece: int) -> None:
        self.board[row][col] = piece

    def remove_piece(self, row: int, col: int) -> None:
        self.board[row][col] = 0

    def winning_move(self, piece: int) -> bool:
        """Check if the given piece has a connect 4."""
        b = self.board
        # Horizontal
        for r in range(ROW_COUNT):
            for c in range(COLUMN_COUNT - 3):
                if b[r][c] == piece and b[r][c+1] == piece and b[r][c+2] == piece and b[r][c+3] == piece:
                    return True
        # Vertical
        for r in range(ROW_COUNT - 3):
            for c in range(COLUMN_COUNT):
                if b[r][c] == piece and b[r+1][c] == piece and b[r+2][c] == piece and b[r+3][c] == piece:
                    return True
        # Diagonal /
        for r in range(3, ROW_COUNT):
            for c in range(COLUMN_COUNT - 3):
                if b[r][c] == piece and b[r-1][c+1] == piece and b[r-2][c+2] == piece and b[r-3][c+3] == piece:
                    return True
        # Diagonal \
        for r in range(ROW_COUNT - 3):
            for c in range(COLUMN_COUNT - 3):
                if b[r][c] == piece and b[r+1][c+1] == piece and b[r+2][c+2] == piece and b[r+3][c+3] == piece:
                    return True
        return False

    def is_terminal_node(self) -> bool:
        return (self.winning_move(1) or self.winning_move(-1) or
                len(self.get_valid_locations()) == 0)

    def evaluate_window(self, window: list[int], piece: int) -> int:
        """Score a segment of 4 cells."""
        opp_piece = -piece
        count_piece = window.count(piece)
        count_empty = window.count(0)
        count_opp = window.count(opp_piece)
        score = 0

        if count_piece == 4:
            score += 1000000
        elif count_piece == 3 and count_empty == 1:
            score += 5000
        elif count_piece == 2 and count_empty == 2:
            score += 200
        elif count_piece == 1 and count_empty == 3:
            score += 10

        if count_opp == 3 and count_empty == 1:
            score -= 5000
        elif count_opp == 2 and count_empty == 2:
            score -= 200

        return score

    def score_position(self, piece: int) -> int:
        """Heuristic evaluation of the board from the perspective of `piece`."""
        score = 0

        # Center column preference
        center_col = COLUMN_COUNT // 2
        center_array = [self.board[r][center_col] for r in range(ROW_COUNT)]
        center_count = center_array.count(piece)
        score += center_count * 6

        # Horizontal windows
        for r in range(ROW_COUNT):
            row_array = self.board[r]
            for c in range(COLUMN_COUNT - 3):
                window = row_array[c:c+4]
                score += self.evaluate_window(window, piece)

        # Vertical windows
        for c in range(COLUMN_COUNT):
            col_array = [self.board[r][c] for r in range(ROW_COUNT)]
            for r in range(ROW_COUNT - 3):
                window = col_array[r:r+4]
                score += self.evaluate_window(window, piece)

        # Diagonal / windows
        for r in range(3, ROW_COUNT):
            for c in range(COLUMN_COUNT - 3):
                window = [self.board[r-i][c+i] for i in range(4)]
                score += self.evaluate_window(window, piece)

        # Diagonal \ windows
        for r in range(ROW_COUNT - 3):
            for c in range(COLUMN_COUNT - 3):
                window = [self.board[r+i][c+i] for i in range(4)]
                score += self.evaluate_window(window, piece)

        return score

    def order_moves(self, moves: list[int]) -> list[int]:
        """Sort moves to improve alpha-beta pruning: center first."""
        center = COLUMN_COUNT // 2
        moves.sort(key=lambda x: abs(x - center))
        return moves

    def minimax(self, depth: int, alpha: float, beta: float,
                maximizing_player: bool) -> tuple[int | None, int]:
        """Minimax with alpha-beta pruning. Returns (best_col, score)."""
        if time.time() - self.start_time > self.time_limit:
            raise TimeoutError

        valid_locations = self.get_valid_locations()
        is_terminal = self.is_terminal_node()

        if depth == 0 or is_terminal:
            if is_terminal:
                if self.winning_move(1):
                    return (None, 1000000000)
                elif self.winning_move(-1):
                    return (None, -1000000000)
                else:  # draw
                    return (None, 0)
            else:
                return (None, self.score_position(1))

        moves = self.order_moves(valid_locations)

        if maximizing_player:
            value = -float('inf')
            best_col = moves[0]
            for col in moves:
                row = self.get_next_open_row(col)
                self.drop_piece(row, col, 1)
                _, new_score = self.minimax(depth - 1, alpha, beta, False)
                self.remove_piece(row, col)
                if new_score > value:
                    value = new_score
                    best_col = col
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return best_col, value
        else:
            value = float('inf')
            best_col = moves[0]
            for col in moves:
                row = self.get_next_open_row(col)
                self.drop_piece(row, col, -1)
                _, new_score = self.minimax(depth - 1, alpha, beta, True)
                self.remove_piece(row, col)
                if new_score < value:
                    value = new_score
                    best_col = col
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return best_col, value


def policy(board: list[list[int]]) -> int:
    """API entry point expected by the arena."""
    ai = Connect4AI()
    return ai.get_move(board)
