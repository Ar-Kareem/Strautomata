
import numpy as np
from typing import List, Tuple, Optional
import sys

def policy(board) -> str:
    board = np.array(board)
    player = 1
    opponent = -1

    def get_my_pieces():
        return [(r, c) for r in range(8) for c in range(8) if board[r, c] == player]

    def get_directions():
        return [(dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if (dr, dc) != (0, 0)]

    def count_pieces_in_direction(r, c, dr, dc):
        cnt = 0
        while 0 <= r < 8 and 0 <= c < 8:
            if board[r, c] != 0:
                cnt += 1
            r += dr
            c += dc
        return cnt

    def is_path_clear(r, c, dr, dc, steps):
        # Check if we can move 'steps' steps in direction (dr,dc) from (r,c)
        # Can jump over own pieces, but not over opponent pieces
        for i in range(1, steps):
            nr, nc = r + i*dr, c + i*dc
            if not (0 <= nr < 8 and 0 <= nc < 8):
                return False
            if board[nr, nc] == opponent:  # cannot jump over opponent
                return False
        return True

    def get_legal_moves():
        moves = []
        my_pieces = get_my_pieces()
        directions = get_directions()
        for r, c in my_pieces:
            for dr, dc in directions:
                steps = count_pieces_in_direction(r, c, dr, dc)
                nr, nc = r + dr*steps, c + dc*steps
                if steps == 0:
                    continue
                if 0 <= nr < 8 and 0 <= nc < 8:
                    if is_path_clear(r, c, dr, dc, steps):
                        if board[nr, nc] == 0 or board[nr, nc] == opponent:
                            moves.append((r, c, nr, nc))
        return moves

    def get_connected_components(player_val):
        visited = np.zeros((8,8), dtype=bool)
        components = []
        def flood(r, c, comp):
            stack = [(r, c)]
            while stack:
                r, c = stack.pop()
                if not (0 <= r < 8 and 0 <= c < 8):
                    continue
                if visited[r, c] or board[r, c] != player_val:
                    continue
                visited[r, c] = True
                comp.append((r, c))
                for dr in (-1,0,1):
                    for dc in (-1,0,1):
                        if dr == 0 and dc == 0: continue
                        nr, nc = r+dr, c+dc
                        if 0 <= nr < 8 and 0 <= nc < 8 and not visited[nr, nc] and board[nr, nc] == player_val:
                            stack.append((nr, nc))
        for r in range(8):
            for c in range(8):
                if board[r, c] == player_val and not visited[r, c]:
                    comp = []
                    flood(r, c, comp)
                    components.append(comp)
        return components

    def evaluate():
        # Heuristic: size of largest connected component of my pieces
        my_comps = get_connected_components(player)
        if not my_comps:
            return -1000
        my_largest = max(len(comp) for comp in my_comps)
        # Bonus for having few components (closer to connected)
        component_penalty = -len(my_comps)
        # Also consider opponent's connectivity? Maybe not for 1-ply
        return my_largest * 10 + component_penalty

    def make_move_and_evaluate(move):
        # Apply move, evaluate, undo
        fr, fc, tr, tc = move
        captured = None
        # Save state
        piece = board[fr, fc]
        target = board[tr, tc]
        # Make move
        board[fr, fc] = 0
        board[tr, tc] = piece
        if target == opponent:
            captured = (tr, tc)
        # Evaluate
        score = evaluate()
        # Undo
        board[fr, fc] = piece
        board[tr, tc] = target
        return score

    # Get all legal moves
    legal_moves = get_legal_moves()
    if not legal_moves:
        # No moves? Just return a dummy (should not happen in normal play)
        return "0,0:0,0"

    # Find winning move: if any move results in a win, take it
    current_score = evaluate()
    my_count = len(get_my_pieces())
    for move in legal_moves:
        fr, fc, tr, tc = move
        captured = board[tr, tc] == opponent
        piece = board[fr, fc]
        target = board[tr, tc]
        board[fr, fc] = 0
        board[tr, tc] = piece
        # Check if after move, all my pieces are connected
        my_comps = get_connected_components(player)
        my_comp_count = len(my_comps)
        board_size = sum(len(comp) for comp in my_comps)
        if my_comp_count == 1 and board_size == (my_count - (1 if captured else 0)):
            # Win! Undo and return
            board[fr, fc] = piece
            board[tr, tc] = target
            return f"{fr},{fc}:{tr},{tc}"
        board[fr, fc] = piece
        board[tr, tc] = target

    # Otherwise, evaluate all moves
    best_score = -float('inf')
    best_move = legal_moves[0]
    for move in legal_moves:
        score = make_move_and_evaluate(move)
        if score > best_score:
            best_score = score
            best_move = move

    fr, fc, tr, tc = best_move
    return f"{fr},{fc}:{tr},{tc}"
