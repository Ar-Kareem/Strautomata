
def next_location(side, idx, player):
    """Return the next (side, index) after dropping a seed in location (side, idx)."""
    if side == player:
        if idx < 5:
            return side, idx + 1
        elif idx == 5:
            return side, 6
        elif idx == 6:  # after store, go to opponent's first house
            return 1 - player, 0
    else:
        if idx < 5:
            return side, idx + 1
        elif idx == 5:
            return player, 0
    # Should never reach here for valid calls
    return side, idx


def apply_move(board, player, move):
    """
    Apply a move for the given player (0 = you, 1 = opponent).
    Returns (new_board, extra_move, capture).
    Does *not* apply the game‑ending rule.
    """
    # Copy the board so the original stays unchanged
    new_board = [board[0][:], board[1][:]]
    if player == 0:
        houses = new_board[0]
        opp_houses = new_board[1]
    else:
        houses = new_board[1]
        opp_houses = new_board[0]
    store_idx = 6

    seeds = houses[move]
    if seeds == 0:                     # Should never happen for legal moves
        return new_board, False, False
    houses[move] = 0

    extra_move = False
    capture = False

    side = player
    idx = move + 1                     # start from the next house

    while seeds > 0:
        # Drop one seed
        if side == player:
            if idx == 6:               # player's store
                houses[store_idx] += 1
            else:
                houses[idx] += 1
        else:                           # opponent's house
            opp_houses[idx] += 1

        seeds -= 1

        if seeds == 0:                  # last seed dropped
            if side == player and idx == 6:
                extra_move = True
            else:
                extra_move = False
                # Capture check (only when landing on player's house)
                if side == player and idx != 6:
                    # house must have been empty before this drop
                    if houses[idx] == 1:
                        opp_idx = 5 - idx
                        if opp_houses[opp_idx] > 0:
                            capture = True
                            # move captured seeds to store
                            houses[store_idx] += 1 + opp_houses[opp_idx]
                            houses[idx] = 0
                            opp_houses[opp_idx] = 0
            break

        # Move to next location
        side, idx = next_location(side, idx, player)

    return new_board, extra_move, capture


def is_game_over(board):
    """Return True iff one side has no seeds in its houses."""
    you = board[0]
    opp = board[1]
    if all(you[i] == 0 for i in range(6)):
        return True
    if all(opp[i] == 0 for i in range(6)):
        return True
    return False


def final_scores(board):
    """Compute the final store counts when the game is over (without modifying the original board)."""
    you = board[0][:]
    opp = board[1][:]

    # If you have no seeds, opponent moves their house seeds to their store
    if all(you[i] == 0 for i in range(6)):
        opp_store = opp[6]
        for i in range(6):
            opp_store += opp[i]
            opp[i] = 0
        opp[6] = opp_store

    # If opponent has no seeds, you move your house seeds to your store
    if all(opp[i] == 0 for i in range(6)):
        you_store = you[6]
        for i in range(6):
            you_store += you[i]
            you[i] = 0
        you[6] = you_store

    return you[6], opp[6]


def evaluate(board):
    """Heuristic evaluation from the perspective of player 0 (you)."""
    if is_game_over(board):
        your_store, opp_store = final_scores(board)
        return your_store - opp_store

    your_store = board[0][6]
    opp_store = board[1][6]
    your_houses = sum(board[0][0:6])
    opp_houses = sum(board[1][0:6])

    # Store difference is primary; houses contribute a smaller weight
    return (your_store - opp_store) + 0.2 * (your_houses - opp_houses)


def minimax(board, player, depth, alpha, beta):
    """Alpha‑beta minimax. Returns (value, best_move)."""
    if depth == 0 or is_game_over(board):
        return evaluate(board), None

    # Legal moves for the current player
    moves = [i for i in range(6) if board[player][i] > 0]
    if not moves:
        return evaluate(board), None

    # Prepare move list with priority for ordering
    move_infos = []
    for mv in moves:
        new_board, extra_move, capture = apply_move(board, player, mv)
        # Prioritize: extra move > capture > normal
        priority = 0 if extra_move else (1 if capture else 2)
        move_infos.append((priority, mv, new_board, extra_move, capture))

    move_infos.sort(key=lambda x: x[0])

    best_move = None
    if player == 0:                     # maximizing player (you)
        best_value = -float('inf')
        for _, mv, new_board, extra_move, _ in move_infos:
            # Terminal after this move?
            if is_game_over(new_board):
                value = evaluate(new_board)
            else:
                if extra_move:
                    value, _ = minimax(new_board, player, depth - 1, alpha, beta)
                else:
                    value, _ = minimax(new_board, 1 - player, depth - 1, alpha, beta)

            if value > best_value:
                best_value = value
                best_move = mv
            if best_value > alpha:
                alpha = best_value
            if alpha >= beta:
                break
        return best_value, best_move
    else:                               # minimizing player (opponent)
        best_value = float('inf')
        for _, mv, new_board, extra_move, _ in move_infos:
            if is_game_over(new_board):
                value = evaluate(new_board)
            else:
                if extra_move:
                    value, _ = minimax(new_board, player, depth - 1, alpha, beta)
                else:
                    value, _ = minimax(new_board, 1 - player, depth - 1, alpha, beta)

            if value < best_value:
                best_value = value
                best_move = mv
            if best_value < beta:
                beta = best_value
            if beta <= alpha:
                break
        return best_value, best_move


def policy(you, opponent):
    """
    Return a legal move (0‑5) for the current player.
    The function implements a depth‑6 minimax search with alpha‑beta pruning.
    """
    # Copy the board to avoid mutating the input
    board = [you[:], opponent[:]]
    depth = 6

    _, best_move = minimax(board, 0, depth, -float('inf'), float('inf'))

    # Safety fallback: return the first legal house if something went wrong
    if best_move is not None and you[best_move] > 0:
        return best_move
    for i in range(6):
        if you[i] > 0:
            return i
