
import copy

def get_moves(board_self, board_enemy):
    moves = []
    for r in range(5):
        for c in range(6):
            if board_self[r][c]:
                dirs = [(-1, 0, 'U'), (1, 0, 'D'), (0, -1, 'L'), (0, 1, 'R')]
                for dr, dc, d in dirs:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 5 and 0 <= nc < 6 and board_enemy[nr][nc]:
                        moves.append(f'{r},{c},{d}')
    return moves

def apply_move(board_you, board_opp, move_str):
    r, c, d = move_str.split(',')
    r, c = int(r), int(c)
    dr, dc = {'U': (-1, 0), 'D': (1, 0), 'L': (0, -1), 'R': (0, 1)}[d]
    nr, nc = r + dr, c + dc
    new_you = copy.deepcopy(board_you)
    new_opp = copy.deepcopy(board_opp)
    new_you[r][c] = 0
    new_you[nr][nc] = 1
    new_opp[nr][nc] = 0
    return new_you, new_opp

def policy(you: list[list[int]], opponent: list[list[int]]) -> str:
    all_moves = get_moves(you, opponent)
    if not all_moves:
        # This should not happen per problem constraints, but return arbitrary legal if forced
        # Assuming there is always a move, but to comply, pick the first possible if empty
        # In practice, game ends before, but here we assume.
        return all_moves[0] if all_moves else ""  # But must return legal, per problem.
    best_move = None
    min_opp_moves = float('inf')
    for move in all_moves:
        new_you, new_opp = apply_move(you, opponent, move)
        opp_moves = get_moves(new_opp, new_you)
        if len(opp_moves) < min_opp_moves:
            min_opp_moves = len(opp_moves)
            best_move = move
    return best_move if best_move else all_moves[0]  # Fallback, though unlikely
