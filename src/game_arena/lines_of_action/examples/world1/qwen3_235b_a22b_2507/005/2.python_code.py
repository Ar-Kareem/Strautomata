
import numpy as np
import time
from typing import List, Tuple, Set, Optional

def policy(board) -> str:
    # Constants
    BOARD_SIZE = 8
    EMPTY = 0
    CURRENT_PLAYER = 1
    OPPONENT_PLAYER = -1
    INF = 1000000

    # Convert to numpy array for easier manipulation
    board = np.array(board)

    def in_bounds(r: int, c: int) -> bool:
        return 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE

    def count_pieces_in_direction(r: int, c: int, dr: int, dc: int) -> int:
        count = 0
        while in_bounds(r + dr, c + dc):
            r += dr
            c += dc
            count += 1
        return count

    def get_line_length(r: int, c: int, dr: int, dc: int) -> int:
        # Count total pieces (both players) in the given line of action
        count = 0
        while in_bounds(r, c):
            if board[r, c] != EMPTY:
                count += 1
            r += dr
            c += dc
        return count

    def get_possible_moves(r: int, c: int) -> List[Tuple[int, int]]:
        if board[r, c] != CURRENT_PLAYER:
            return []
        move_options = []
        directions = [(0,1),(1,0),(0,-1),(-1,0),(1,1),(-1,-1),(1,-1),(-1,1)]
        for dr, dc in directions:
            line_count = get_line_length(r - dr * 7, c - dc * 7, dr, dc)
            if line_count == 0:
                continue  # No pieces in this line
            steps = line_count
            nr, nc = r + dr * steps, c + dc * steps
            if not in_bounds(nr, nc):
                continue

            # Check if path is clear (can jump over own, not over opponent)
            blocked = False
            for i in range(1, steps):
                ir, ic = r + dr * i, c + dc * i
                if board[ir, ic] == OPPONENT_PLAYER:
                    blocked = True
                    break
            if blocked:
                continue

            # Landing cell can be empty or opponent
            if board[nr, nc] != OPPONENT_PLAYER:
                if board[nr, nc] == CURRENT_PLAYER:
                    continue  # cannot capture own piece
            # Valid move
            move_options.append((nr, nc))
        return move_options

    def get_all_legal_moves(player: int) -> List[Tuple[int, int, int, int]]:
        moves = []
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if board[r, c] == player:
                    for nr, nc in get_possible_moves(r, c):
                        moves.append((r, c, nr, nc))
        return moves

    def make_move(board: np.ndarray, move: Tuple[int,int,int,int]):
        r, c, nr, nc = move
        new_board = board.copy()
        new_board[r, c] = EMPTY
        new_board[nr, nc] = CURRENT_PLAYER  # assuming current player moves
        return new_board

    def flood_fill_connected(board: np.ndarray, r: int, c: int, visited: Set, player: int) -> Set:
        stack = [(r, c)]
        component = set()
        while stack:
            cr, cc = stack.pop()
            if (cr, cc) in visited or not in_bounds(cr, cc) or board[cr, cc] != player:
                continue
            visited.add((cr, cc))
            component.add((cr, cc))
            for dr in [-1,0,1]:
                for dc in [-1,0,1]:
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = cr + dr, cc + dc
                    if (nr, nc) not in visited and in_bounds(nr, nc) and board[nr, nc] == player:
                        stack.append((nr, nc))
        return component

    def get_connected_components(board: np.ndarray, player: int) -> List[Set]:
        visited = set()
        components = []
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if (r, c) not in visited and board[r, c] == player:
                    comp = flood_fill_connected(board, r, c, visited, player)
                    components.append(comp)
        return components

    def evaluate(board: np.ndarray) -> float:
        # Heuristic evaluation
        my_pieces = np.sum(board == CURRENT_PLAYER)
        opp_pieces = np.sum(board == OPPONENT_PLAYER)

        my_comp = get_connected_components(board, CURRENT_PLAYER)
        opp_comp = get_connected_components(board, OPPONENT_PLAYER)

        # Reward: fewer and larger components (better connected)
        my_comp_score = -len(my_comp) * 10 + sum(len(c)**2 for c in my_comp) / (my_pieces + 1e-5)
        opp_comp_score = -len(opp_comp) * 10 + sum(len(c)**2 for c in opp_comp) / (opp_pieces + 1e-5)

        # Mobility: number of legal moves
        my_moves = len(get_all_legal_moves(CURRENT_PLAYER))
        opp_moves = len(get_all_legal_moves(OPPONENT_PLAYER))
        mobility_score = my_moves - opp_moves * 0.5

        # Win conditions: if I connected, big positive. If opponent connected, big negative.
        if len(my_comp) == 1 and my_pieces > 0:
            return INF - 100
        if len(opp_comp) == 1 and opp_pieces > 0:
            return -INF + 100

        # Prefer captures
        capture_bonus = (7 - opp_pieces) * 5  # more captures = better

        # Central control - sum of inverse distance to center
        center_r, center_c = 3.5, 3.5
        my_center_score = 0
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if board[r, c] == CURRENT_PLAYER:
                    dist = ((r - center_r)**2 + (c - center_c)**2)
                    my_center_score += 1 / (dist + 1)

        total_score = (
            my_comp_score * 8 +
            mobility_score * 0.5 +
            capture_bonus +
            my_center_score * 2 +
            (-opp_comp_score) * 4
        )
        return total_score

    def minimax(board: np.ndarray, depth: int, alpha: float, beta: float, maximizing: bool) -> float:
        if depth == 0 or time.time() - start_time > 0.9:
            return evaluate(board)

        # Switch player
        original_player = CURRENT_PLAYER
        current_player = -original_player if not maximizing else original_player

        moves = get_all_legal_moves(current_player)
        if not moves:
            # No moves — could be loss or draw
            comp_me = len(get_connected_components(board, original_player))
            comp_opp = len(get_connected_components(board, -original_player))
            if comp_me == 1:
                return INF - depth
            if comp_opp == 1:
                return -INF + depth
            return -1000  # losing

        # Move ordering: by capture and evaluation heuristic
        scored_moves = []
        for move in moves:
            new_b = board.copy()
            r, c, nr, nc = move
            new_b[r, c] = EMPTY
            new_b[nr, nc] = current_player
            score = evaluate(new_b) if current_player == original_player else -evaluate(new_b)
            scored_moves.append((score, move))
        scored_moves.sort(key=lambda x: x[0], reverse=maximizing)

        if maximizing:
            max_eval = -INF
            for _, move in scored_moves:
                new_b = board.copy()
                r, c, nr, nc = move
                new_b[r, c] = EMPTY
                new_b[nr, nc] = CURRENT_PLAYER
                eval_score = minimax(new_b, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = INF
            for _, move in scored_moves:
                new_b = board.copy()
                r, c, nr, nc = move
                new_b[r, c] = EMPTY
                new_b[nr, nc] = -CURRENT_PLAYER  # opponent moves
                eval_score = minimax(new_b, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval

    def find_best_move():
        legal_moves = get_all_legal_moves(CURRENT_PLAYER)
        if not legal_moves:
            # Fallback: scan for any valid move (unlikely)
            for r in range(BOARD_SIZE):
                for c in range(BOARD_SIZE):
                    if board[r, c] == CURRENT_PLAYER:
                        for nr, nc in get_possible_moves(r, c):
                            return f"{r},{c}:{nr},{nc}"
            # Should not happen
            return "0,0:0,0"
        
        # If only one move, return it
        if len(legal_moves) == 1:
            r, c, nr, nc = legal_moves[0]
            return f"{r},{c}:{nr},{nc}"

        # Start timing
        global start_time
        start_time = time.time()

        # Iterative deepening up to depth 2 or 3
        best_move_str = f"{legal_moves[0][0]},{legal_moves[0][1]}:{legal_moves[0][2]},{legal_moves[0][3]}"
        for depth in [1, 2, 3]:
            if time.time() - start_time > 0.8:
                break
            best_value = -INF
            best_move = legal_moves[0]
            for move in legal_moves:
                r, c, nr, nc = move
                new_board = board.copy()
                new_board[r, c] = EMPTY
                new_board[nr, nc] = CURRENT_PLAYER
                value = minimax(new_board, depth - 1, -INF, INF, False)
                if value > best_value:
                    best_value = value
                    best_move = move
                if time.time() - start_time > 0.85:
                    break
            r, c, nr, nc = best_move
            best_move_str = f"{r},{c}:{nr},{nc}"
            if time.time() - start_time > 0.9:
                break
        return best_move_str

    # Ensure we always return a legal move
    try:
        return find_best_move()
    except:
        # Fallback: return first legal move
        for r in range(8):
            for c in range(8):
                if board[r, c] == CURRENT_PLAYER:
                    for nr, nc in get_possible_moves(r, c):
                        return f"{r},{c}:{nr},{nc}"
        return "0,0:0,0"  # absolute fallback

