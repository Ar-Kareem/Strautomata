
import time

def policy(you: list[int], opponent: list[int]) -> int:
    board = list(you) + list(opponent)  # 14 entries
    deadline = time.time() + 0.85

    legal = [m for m in range(6) if you[m] > 0]
    best_move = legal[0]

    def simulate(b_in, move):
        b = b_in[:]
        seeds = b[move]
        b[move] = 0
        pos = move
        while seeds > 0:
            pos += 1
            if pos == 13:
                pos = 0
            elif pos == 14:
                pos = 0
            b[pos] += 1
            seeds -= 1
        # Capture
        if pos < 6 and b[pos] == 1 and b[12 - pos] > 0:
            b[6] += 1 + b[12 - pos]
            b[pos] = 0
            b[12 - pos] = 0
        extra = (pos == 6)
        my_empty = (b[0]|b[1]|b[2]|b[3]|b[4]|b[5]) == 0
        opp_empty = (b[7]|b[8]|b[9]|b[10]|b[11]|b[12]) == 0
        over = my_empty or opp_empty
        if over:
            for i in range(6):
                b[6] += b[i]; b[i] = 0
            for i in range(7, 13):
                b[13] += b[i]; b[i] = 0
        return b, extra, over

    def order_moves(b):
        moves = []
        for m in range(6):
            if b[m] == 0: continue
            # Heuristic: prefer moves granting extra turn
            prio = 0
            if b[m] == 6 - m:
                prio = -2
            elif b[m] > 0 and (m + b[m]) == 6:
                prio = -2
            # Also prefer capture-potential moves
            landing = m + b[m]
            if landing < 6 and b[landing] == 0 and b[12 - landing] > 0 and b[m] <= 5 - m:
                prio -= 1
            moves.append((prio, m))
        moves.sort()
        return [m for _, m in moves]

    def negamax(b, depth, alpha, beta):
        if time.time() > deadline:
            return None
        my_empty = (b[0]|b[1]|b[2]|b[3]|b[4]|b[5]) == 0
        opp_empty = (b[7]|b[8]|b[9]|b[10]|b[11]|b[12]) == 0
        if my_empty or opp_empty:
            mstore = b[6] + b[0]+b[1]+b[2]+b[3]+b[4]+b[5]
            ostore = b[13] + b[7]+b[8]+b[9]+b[10]+b[11]+b[12]
            return (mstore - ostore) * 100
        if depth == 0:
            return b[6] - b[13]

        best = -10**9
        moves = order_moves(b)
        for m in moves:
            nb, extra, over = simulate(b, m)
            if extra and not over:
                val = negamax(nb, depth - 1, alpha, beta)
                if val is None: return None
            else:
                swapped = nb[7:14] + nb[0:7]
                v2 = negamax(swapped, depth - 1, -beta, -alpha)
                if v2 is None: return None
                val = -v2
            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
        return best

    def root_search(depth):
        alpha = -10**9
        beta = 10**9
        best_val = -10**9
        best = legal[0]
        moves = order_moves(board)
        for m in moves:
            nb, extra, over = simulate(board, m)
            if extra and not over:
                val = negamax(nb, depth - 1, alpha, beta)
            else:
                swapped = nb[7:14] + nb[0:7]
                v2 = negamax(swapped, depth - 1, -beta, -alpha)
                if v2 is None: return None, None
                val = -v2
            if val is None: return None, None
            if val > best_val:
                best_val = val
                best = m
            if best_val > alpha:
                alpha = best_val
        return best, best_val

    # Iterative deepening
    for depth in range(2, 30):
        if time.time() > deadline:
            break
        result = root_search(depth)
        if result[0] is None:
            break
        best_move = result[0]
        # If we've solved (huge value from terminal), we can stop
        if abs(result[1]) >= 100 * 48 - 100:
            # likely solved decisively
            pass

    if board[best_move] == 0:
        for m in range(6):
            if board[m] > 0:
                return m
    return best_move
