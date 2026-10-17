```python
def get_winner_flat(board):
    def cell(r, c):
        return board[r * 4 + c]
    # rows
    for r in range(4):
        s = cell(r, 0