import tkinter as tk
import sys
import time

root = tk.Tk()
root.geometry("305x355")

# Initialize the board representation and piece locations.
board = [
    ['-', '-', '-', '-', '-', '-', '-', '-'],
    ['-', '-', '-', '-', '-', '-', '-', '-'],
    ['-', '-', '-', '-', '-', '-', '-', '-'],
    ['-', '-', '-', '-', '-', '-', '-', '-'],
    ['-', '-', '-', '-', '-', '-', '-', '-'],
    ['-', '-', '-', '-', '-', '-', '-', '-'],
    ['-', '-', '-', '-', '-', '-', '-', '-'],
    ['-', '-', '-', '-', '-', '-', '-', '-'],
]

board_length = len(board)

piece_locations = {
    (0, 0): '0', (0, 2): '0', (0, 4): '0', (0, 6): '0',
    (1, 1): '0', (1, 3): '0', (1, 5): '0', (1, 7): '0',
    (2, 0): '0', (2, 2): '0', (2, 4): '0', (2, 6): '0',
    (5, 1): 'X', (5, 3): 'X', (5, 5): 'X', (5, 7): 'X',
    (6, 0): 'X', (6, 2): 'X', (6, 4): 'X', (6, 6): 'X',
    (7, 1): 'X', (7, 3): 'X', (7, 5): 'X', (7, 7): 'X',
}

click_positions = []

# Variable to keep track of whose turn it is. '0' for one player, 'X' for the other.
current_turn = 'X'

# Define the possible moves for each piece type
directions = {
    '0': [(1, 1), (1, -1)],  # normal moves for '0'
    'X': [(-1, 1), (-1, -1)],  # normal moves for 'X'
    '@': [(1, 1), (1, -1), (-1, 1), (-1, -1)],  # king moves for '0'
    '+': [(1, 1), (1, -1), (-1, 1), (-1, -1)]  # king moves for 'X'
}

# Define the possible capture moves for each piece type
capture_directions = {
    '0': [(2, 2), (2, -2)],
    'X': [(-2, 2), (-2, -2)],
    '@': [(2, 2), (2, -2), (-2, 2), (-2, -2)],
    '+': [(2, 2), (2, -2), (-2, 2), (-2, -2)]
}

# Heuristic Function to evaluate the value of a board using the piece count of the players and the game outcome
def difficulty1heuristic(current_piece_locations):
    opponent = 'X'
    opponent_king = '+'
    player = '0'
    player_king = '@'

    # Check if the game is over and determine the outcome
    game_result = game_over(current_piece_locations, player)
    if game_result[0]:
        if game_result[1] == player:
            # Player wins
            return 36 # Significantly increase value to prioritize terminal nodes where player wins
        else:
            # Opponent wins
            return -36  # Significantly decrease value to ignore terminal nodes where opponent wins

    utility_value = 0

    # increase/decrease value for each player/opponent piece
    for _, piece in current_piece_locations.items(): # Iterate through all pieces
        if piece == opponent:
            utility_value -= 1
        elif piece == opponent_king:
            utility_value -= 12 # Kings are more valuable than normal pieces
        elif piece == player:
            utility_value += 1
        elif piece == player_king:
            utility_value += 12

    # Non-terminal nodes: Utility based on opponent's pieces
    return utility_value

# Heuristic Function to evaluate the value of a board using the piece count of the players, the game outcome, and potential kinging moves
def difficulty2heuristic(current_piece_locations):
    opponent = 'X'
    opponent_king = '+'
    player = '0'
    player_king = '@'

    # Check if the game is over and determine the outcome
    game_result = game_over(current_piece_locations, player)
    if game_result[0]:
        if game_result[1] == player:
            return 48  # Significantly increase value to prioritize terminal nodes where player wins
        else:
            return -48  # Significantly decrease value to ignore terminal nodes where opponent wins

    utility_value = 0

    # increase/decrease value for each player/opponent piece
    for _, piece in current_piece_locations.items():
        if piece == opponent:
            utility_value -= 1
        elif piece == opponent_king:
            utility_value -= 12
        elif piece == player:
            utility_value += 1
        elif piece == player_king:
            utility_value += 12

    # Check for possible kinging moves
    for position, piece in current_piece_locations.items():
        row, col = position
        if piece == player:
            # Check if the player piece can be kinged in the next move
            if row == board_length - 2 and ((row+1, col+1) not in current_piece_locations.keys() or (row+1, col-1) not in current_piece_locations.keys()):
                utility_value += 3  # Increase utility for potential kinging
            elif row == board_length - 3 and (((row+1, col+1), 'X') in current_piece_locations.keys() or ((row+1, col-1), 'X') not in current_piece_locations.keys()):
                utility_value += 4 # Increase utility more for potential kinging and capturing enemy piece
            elif row == board_length - 3 and ((row+1, col+1), '+') in current_piece_locations.keys() or ((row+1, col-1), '+') not in current_piece_locations.keys():
                utility_value += 5 # Increase utility even more for potential kinging and capturing enemy king
        else:
            # Check if the opponent's piece can be kinged in the next move
            if row == board_length - 2 and ((row+1, col+1) not in current_piece_locations.keys() or (row+1, col-1) not in current_piece_locations.keys()):
                utility_value -= 3  # Decrease utility for opponent's potential kinging
            elif row == board_length - 3 and (((row+1, col+1), '0') in current_piece_locations.keys() or ((row+1, col-1), '0') not in current_piece_locations.keys()):
                utility_value -= 4 # Decrease utility more for opponent's potential kinging and capturing player piece
            elif row == board_length - 3 and ((row+1, col+1), '@') in current_piece_locations.keys() or ((row+1, col-1), '@') not in current_piece_locations.keys():
                utility_value -= 5 # Decrease utility even more for opponent's potential kinging and capturing player king

    # Non-terminal nodes: Utility based on opponent's pieces
    return utility_value

# Function for MiniMax w/ alpha-beta pruning to build tree and get best utility value
def minimax(current_piece_locations, depth, player, alpha, beta, heuristic_function):
    if depth == 0: # Reached the maximum depth
        return heuristic_function(current_piece_locations) # Evaluate the board using the heuristic function

    opponent = '0' if player == 'X' else 'X'

    # Get all possible moves for the current player
    possible_moves, _ = get_possible_moves(current_piece_locations, player)

    # Check if the game is over
    if len(possible_moves) == 0:
        return heuristic_function(current_piece_locations)

    # Maximizing utility
    if player == '0':
        best_value = -sys.maxsize
        # Iterate over all possible moves
        for move in possible_moves:
            # Simulate the move
            temp_piece_locations = simulate_move(current_piece_locations, move[0], move[1], player, possible_moves)
            # Recursively call minimax on the updated board
            value = minimax(temp_piece_locations, depth - 1, opponent, alpha, beta, heuristic_function)
            best_value = max(best_value, value)
            alpha = max(alpha, best_value)
            if beta <= alpha:
                break
        return best_value
    else: # Minimizing utility
        best_value = sys.maxsize
        # Iterate over all possible moves
        for move in possible_moves:
            # Simulate the move
            temp_piece_locations = simulate_move(current_piece_locations, move[0], move[1], player, possible_moves)
            # Recursively call minimax on the updated board
            value = minimax(temp_piece_locations, depth - 1, opponent, alpha, beta, heuristic_function)
            best_value = min(best_value, value)
            beta = min(beta, best_value)
            if beta <= alpha:
                break
        return best_value

def get_ai_move(current_piece_locations, player, depth):
    best_move = None
    best_value = -sys.maxsize

    # Get all possible moves for the AI player
    possible_moves, capture_possible = get_possible_moves(current_piece_locations, player)

    for move in possible_moves:
        # Simulate the move
        temp_piece_locations = simulate_move(current_piece_locations, move[0], move[1], player, possible_moves)
        # Run minimax on the updated board
        value = minimax(current_piece_locations, depth - 1, '0' if player == 'X' else 'X', -sys.maxsize, sys.maxsize, selected_heuristic)

        if value > best_value:
            best_value = value
            best_move = move

    return best_move, possible_moves

def move_ai_piece(move, possible_moves):
    start_pos, end_pos = move
    piece = piece_locations.pop(start_pos)
    piece_locations[end_pos] = piece

    # Check for kinging
    piece_kinged = False
    if piece == '0' and end_pos[0] == board_length - 1:
        piece_locations[end_pos] = '@'
        piece_kinged = True

    # Handle capturing
    capture = False
    row_diff = end_pos[0] - start_pos[0]
    col_diff = abs(end_pos[1] - start_pos[1])
    if abs(row_diff) == 2:
        mid_row = (start_pos[0] + end_pos[0]) // 2
        mid_col = (start_pos[1] + end_pos[1]) // 2
        del piece_locations[(mid_row, mid_col)]
        capture = True

    print(f"AI made a move: {start_pos} -> {end_pos}")

    # Handle possible multicapture
    if (capture == True and piece_kinged == False):
        new_moves, new_capture_possible = get_possible_moves(piece_locations, '0')
        if new_capture_possible:
            for move in new_moves:
                if (move[0], move[1]) not in possible_moves:
                    move_ai_piece(move, possible_moves)
                    return

    switch_turn()
    create_board_gui()
    if (get_possible_moves(piece_locations, 'X')[1] == True):
        display_message("You Must Capture!")

# Function to check if the game is over
def game_over(current_piece_locations, player):
    opponent = 'X' if current_turn == '0' else '0'
    # Check if the current player has no more pieces or cannot make any legal moves
    player_possible_moves, _ = get_possible_moves(current_piece_locations, player)
    if (len(player_possible_moves) == 0):
        return True, opponent  # Current player loses, opponent wins

    # Check if the opponent has no more pieces or cannot make any legal moves
    opponent_possible_moves, _ = get_possible_moves(current_piece_locations, opponent)
    if (len(opponent_possible_moves) == 0):
        return True, current_turn  # Opponent loses, current player wins

    # Otherwise game is still going
    return False, None


# Function to get all possible moves for the current player
def get_possible_moves(current_piece_locations, current_turn):
    moves = []
    capture_moves = []

    # Local function to check if position is within the board boundaries
    def in_bounds(row, col):
        return 0 <= row < board_length and 0 <= col < len(board[0])

    # Iterate over all pieces for the current player
    for position, piece in current_piece_locations.items():
        if piece in [current_turn, '@' if current_turn == '0' else '+']:
            current_row, current_col = position

            # Check all possible moves
            for direction in directions[piece]:
                new_row = current_row + direction[0]
                new_col = current_col + direction[1]
                if in_bounds(new_row, new_col) and (new_row, new_col) not in current_piece_locations:
                    moves.append((position, (new_row, new_col)))

            # Check all possible capture moves
            for direction in capture_directions[piece]:
                jump_row = current_row + direction[0]
                jump_col = current_col + direction[1]
                mid_row = current_row + direction[0] // 2
                mid_col = current_col + direction[1] // 2
                if in_bounds(jump_row, jump_col) and (jump_row, jump_col) not in current_piece_locations:
                    if (mid_row, mid_col) in current_piece_locations and current_piece_locations[(mid_row, mid_col)] not in [current_turn, '@' if current_turn == '0' else '+']:
                        capture_moves.append((position, (jump_row, jump_col)))
    if (len(capture_moves) > 0):
        return capture_moves, True
    else:
        return moves, False

def simulate_move(current_piece_locations, start_pos, end_pos, player, capture_moves):
    # Copy the piece_locations to avoid modifying the original during simulation
    temp_locations = current_piece_locations.copy()

    # Perform the move
    piece = temp_locations.pop(start_pos)
    temp_locations[end_pos] = piece

    # Check for kinging
    piece_kinged = False
    if piece == '0' and end_pos[0] == board_length - 1:
        temp_locations[end_pos] = '@'
        piece_kinged = True
    elif piece == 'X' and end_pos[0] == 0:
        temp_locations[end_pos] = '+'
        piece_kinged = True

    # Handle capturing
    capture = False
    if abs(start_pos[0] - end_pos[0]) == 2:  # Indicates a capture move
        opponent = '0' if player == 'X' else 'X'
        opponent_king = '@' if player == 'X' else '+'
        mid_row = (start_pos[0] + end_pos[0]) // 2
        mid_col = (start_pos[1] + end_pos[1]) // 2
        if (mid_row, mid_col) in temp_locations and temp_locations[(mid_row, mid_col)] in [opponent, opponent_king]:
            del temp_locations[(mid_row, mid_col)]
            capture = True  # Opponent piece was captured

    # Handle possible multicapture
    if (capture == True and piece_kinged == False):
        new_moves, new_capture_possible = get_possible_moves(temp_locations, current_turn)
        if new_capture_possible:
            for move in new_moves:
                if (move[0], move[1]) not in capture_moves:
                    simulate_move(temp_locations, move[0], move[1], player, capture_moves)

    return temp_locations

def is_valid_move(current_piece_locations, start_pos, end_pos):
    if start_pos not in current_piece_locations or end_pos in current_piece_locations:
        return False

    start_piece = current_piece_locations[start_pos]
    player_king = '@' if current_turn == '0' else '+'
    opponent = 'X' if current_turn == '0' else '0'
    opponent_king = '+' if opponent == 'X' else '@'

    # Ensure the move is made by the current player or king
    if start_piece not in [current_turn, player_king]:
        return False

    row, col = end_pos
    if row < 0 or row >= board_length or col < 0 or col >= len(board[0]):
        return False

    row_diff = end_pos[0] - start_pos[0]
    col_diff = abs(end_pos[1] - start_pos[1])

    # Basic move (including kings moving backward)
    allowed_row_diffs = {
        '0': [1],  # normal '0' pieces move downwards
        'X': [-1], # normal 'X' pieces move upwards
        '@': [1, -1],  # '0' kings move any direction
        '+': [1, -1]  # 'X' kings move any direction
    }
    if col_diff == 1 and row_diff in allowed_row_diffs[start_piece]:
        return True

    # Capture move
    if col_diff == 2:
        mid_row = (start_pos[0] + end_pos[0]) // 2
        mid_col = (start_pos[1] + end_pos[1]) // 2
        if (mid_row, mid_col) in current_piece_locations and current_piece_locations[(mid_row, mid_col)] in [opponent, opponent_king]:
            return True

    return False

def switch_turn():
    global current_turn
    current_turn = 'X' if current_turn == '0' else '0'
    get_Move_Info()

def get_Move_Info():
    get_possible_moves(piece_locations, current_turn)  # Display possible moves right after switching turns

def on_tile_click(row, col):
    global current_turn, click_positions
    click_positions.append((row, col))

    if len(click_positions) == 2:
        start_pos = click_positions[0]
        end_pos = click_positions[1]
        possible_moves, capture_possible = get_possible_moves(piece_locations, current_turn)

        if is_valid_move(piece_locations, start_pos, end_pos):
            if(capture_possible == True and ((start_pos, end_pos) not in possible_moves)):
                print(f"Invalid move by {current_turn}: {start_pos} -> {end_pos}")
                display_message("Invalid Move! You Must Capture!")
            else:
                piece = piece_locations.pop(start_pos)
                piece_locations[end_pos] = piece

                # Check for kinging
                piece_kinged = False
                if piece == '0' and end_pos[0] == board_length - 1:
                    piece_locations[end_pos] = '@'
                    piece_kinged = True
                elif piece == 'X' and end_pos[0] == 0:
                    piece_locations[end_pos] = '+'
                    piece_kinged = True

                # Handle capturing
                capture = False
                row_diff = end_pos[0] - start_pos[0]
                col_diff = abs(end_pos[1] - start_pos[1])
                if abs(row_diff) == 2:
                    capture = True
                    mid_row = (start_pos[0] + end_pos[0]) // 2
                    mid_col = (start_pos[1] + end_pos[1]) // 2
                    del piece_locations[(mid_row, mid_col)]

                print(f"{current_turn} made a valid move: {start_pos} -> {end_pos}")

                # Handle possible multicapture
                if (capture == True and piece_kinged == False):
                    create_board_gui()
                    new_moves, new_capture_possible = get_possible_moves(piece_locations, current_turn)
                    if(new_capture_possible == False):
                        switch_turn()
                        create_board_gui()
                        display_message("")  # Clear any previous error messages
                        # After the player's move, determine the AI's move
                        ai_move, ai_possible_answers = get_ai_move(piece_locations, '0', depth=5)  # Depth can be adjusted to increase difficulty or help speed things up if it's too slow
                        if (ai_move == None):
                            display_message("AI has no more moves! You win!")
                            return # End the game
                        move_ai_piece(ai_move, ai_possible_answers)  # Function to execute AI's move
                        # Check if player loses after AI's move
                    else:
                        for move in new_moves:
                            if (move[0], move[1]) not in possible_moves:
                                display_message("You must capture again!")
                else:
                    switch_turn()
                    create_board_gui()
                    # After the player's move, determine the AI's move
                    ai_move, ai_possible_answers = get_ai_move(piece_locations, '0', depth=5)  # Depth can be adjusted to increase difficulty or help speed things up if it's too slow
                    if (ai_move == None):
                        display_message("AI has no more moves! You win!")
                        return # End the game
                    move_ai_piece(ai_move, ai_possible_answers)  # Function to execute AI's move


        else:
            print(f"Invalid move by {current_turn}: {start_pos} -> {end_pos}")
            display_message("Invalid move!")  # Display error message

        if (len(get_possible_moves(piece_locations, 'X')[0]) == 0):
            display_message("You Lose!")
            return
        click_positions.clear()

def create_board_gui():
    for widget in root.winfo_children():
        widget.destroy()

    # Create label for displaying messages
    global message_label
    message_label = tk.Label(root, text="", font=('Helvetica', 10), fg="red")
    message_label.grid(row=board_length, columnspan=len(board[0]))  # Display the message label below the turn label

    for row in range(board_length):
        for col in range(len(board[row])):
            tile_color = 'white' if (row + col) % 2 == 0 else 'black'
            piece = piece_locations.get((row, col), ' ')
            button_text = piece  # Use the piece value directly
            button_fg = 'red' if piece in ['X', '+'] else 'blue' if piece in ['0', '@'] else 'black'
            button = tk.Button(root, text=button_text, bg=tile_color, fg=button_fg, width=4, height=2, command=lambda r=row, c=col: on_tile_click(r, c))
            button.grid(row=row, column=col)

# Function to display an error message
def display_message(msg):
    message_label.config(text=msg)


def set_difficulty(difficulty):
    global selected_heuristic
    if difficulty == 'easy':
        selected_heuristic = difficulty1heuristic
    elif difficulty == 'hard':
        selected_heuristic = difficulty2heuristic
    get_Move_Info()
    create_board_gui()

def choose_difficulty():
    # Clear the board and piece locations
    for widget in root.winfo_children():
        widget.destroy()

    # Create label telling user to select difficulty at beginning of game
    select_label = tk.Label(root, text="Select Difficulty:", font=('Helvetica', 12))
    select_label.pack(pady=20)

    # Create easy and hard buttons for user to select difficulty
    easy_button = tk.Button(root, text="Easy", command=lambda: set_difficulty('easy'))
    easy_button.pack(pady=10)
    hard_button = tk.Button(root, text="Hard", command=lambda: set_difficulty('hard'))
    hard_button.pack(pady=10)

# Initialize GUI and prompt user to select difficulty before starting the game
choose_difficulty()
root.mainloop()  # Start the tkinter event loop
