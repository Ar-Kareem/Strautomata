
import numpy as np
import itertools

def policy(board):
    # Generate all legal moves for player 1
    moves = generate_all_moves(board, player=1)
    if not moves:
        # Should not happen, but fallback
        return "0,0:0,0:0,0"
    
    # Opening book: first few moves
    empty_count = np.sum(board == 0)
    if empty_count >= 30:  # early game
        best_move = opening_move(board, moves)
        if best_move:
            return format_move(best_move)
    
    # Evaluate moves with 1-step lookahead
    best_score = -float('inf')
    best_move = moves[0]
    for move in moves:
        # Apply move
        new_board = apply_move(board, move)
        # Evaluate
        score = evaluate_board(new_board)
        # Add small tie-breaker: prefer moving forward in rows for variety
        score += (move[2] - move[0]) * 0.01
        if score > best_score:
            best_score = score
            best_move = move
    
    return format_move(best_move)

def generate_all_moves(board, player):
    """Return list of (fr, fc, tr, tc, ar, ac) for player."""
    moves = []
    player_val = 1 if player == 1 else 2
    # Find all player's amazons
    amazon_pos = np.argwhere(board == player_val)
    for fr, fc in amazon_pos:
        # Generate queen moves from (fr, fc)
        for dr, dc in [(1,0), (-1,0), (0,1), (0,-1),
                       (1,1), (1,-1), (-1,1), (-1,-1)]:
            r, c = fr + dr, fc + dc
            while 0 <= r < 6 and 0 <= c < 6:
                if board[r, c] != 0:
                    break
                # (r, c) is valid 'to' position
                # Now shoot arrow from (r, c)
                for adr, adc in [(1,0), (-1,0), (0,1), (0,-1),
                                 (1,1), (1,-1), (-1,1), (-1,-1)]:
                    ar, ac = r + adr, c + adc
                    while 0 <= ar < 6 and 0 <= ac < 6:
                        if (ar == fr and ac == fc) or board[ar, ac] == 0:
                            # Vacated from square is passable
                            if not (ar == fr and ac == fc) and board[ar, ac] != 0:
                                break
                            # Valid arrow position
                            moves.append((fr, fc, r, c, ar, ac))
                        else:
                            break
                        ar += adr
                        ac += adc
                r += dr
                c += dc
    return moves

def apply_move(board, move):
    """Return new board after move, without modifying original."""
    fr, fc, tr, tc, ar, ac = move
    new_board = board.copy()
    new_board[fr, fc] = 0
    new_board[tr, tc] = 1   # our amazon
    new_board[ar, ac] = -1  # arrow
    return new_board

def evaluate_board(board):
    """Heuristic score: mobility diff + territory diff."""
    our_moves = len(generate_all_moves(board, player=1))
    # Opponent moves on same board
    opp_moves = len(generate_all_moves(board, player=2))
    mobility_diff = our_moves - opp_moves
    
    # Territory: number of squares reachable by each amazon
    our_territory = count_reachable_squares(board, player=1)
    opp_territory = count_reachable_squares(board, player=2)
    territory_diff = our_territory - opp_territory
    
    # Combine
    score = mobility_diff + 0.5 * territory_diff
    return score

def count_reachable_squares(board, player):
    """Number of distinct empty squares reachable by player's amazons in one queen move."""
    player_val = 1 if player == 1 else 2
    amazons = np.argwhere(board == player_val)
    reachable = set()
    for fr, fc in amazons:
        for dr, dc in [(1,0), (-1,0), (0,1), (0,-1),
                       (1,1), (1,-1), (-1,1), (-1,-1)]:
            r, c = fr + dr, fc + dc
            while 0 <= r < 6 and 0 <= c < 6:
                if board[r, c] != 0:
                    break
                reachable.add((r, c))
                r += dr
                c += dc
    return len(reachable)

def opening_move(board, moves):
    """Choose a good opening move from a small book."""
    # Try to move center-most amazon toward center, shoot to limit opponent
    # Prefer moves that place arrow near opponent's likely positions
    opponent_amazons = np.argwhere(board == 2)
    if len(opponent_amazons) == 0:
        # First move: move (0,2) to (2,4), shoot (3,5)
        for move in moves:
            if move[:2] == (0, 2) and move[2:4] == (2, 4) and move[4:] == (3, 5):
                return move
        # fallback
        return None
    
    # Otherwise, use heuristic in main search
    return None

def format_move(move):
    fr, fc, tr, tc, ar, ac = move
    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"
