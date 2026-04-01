piece_emojis = {
    "P":"♙",
    "B":"♗",
    "N":"♘",
    "R":"♖",
    "Q":"♕",
    "K":"♔",
    "p":"♟",
    "b":"♝",
    "n":"♞",
    "r":"♜",
    "q":"♛",
    "k":"♚",
    " ":" "
}
fen_string_translation_table = str.maketrans({str(number):" " * number for number in range(1, 9)} | piece_emojis)

simplify_move_translation_table = str.maketrans({"+":"", "#":"", "=":""})

def sign(value):
    return (value > 0) - (value < 0)

def file_to_int(file):
    return ord(file) - 97
   
def rank_to_int(rank):
    return 8 - int(rank)

def square_to_position(square):
    x = file_to_int(square[0])
    if x < 0 or x >= 8:
        raise ValueError(f"file {x} outside of range [0, 8)")
    y = rank_to_int(square[1])
    if y < 0 or y >= 8:
        raise ValueError(f"rank {y} outside of range [0, 8)")
    
    return [x, y]

class Game:
    def __init__(self):
        self.board = [
            ["r", "n", "b", "q", "k", "b", "n", "r"],
            ["p", "p", "p", "p", "p", "p", "p", "p"],
            [" ", " ", " ", " ", " ", " ", " ", " "],
            [" ", " ", " ", " ", " ", " ", " ", " "],
            [" ", " ", " ", " ", " ", " ", " ", " "],
            [" ", " ", " ", " ", " ", " ", " ", " "],
            ["P", "P", "P", "P", "P", "P", "P", "P"],
            ["R", "N", "B", "Q", "K", "B", "N", "R"]
        ]
        self.turn = "w"
        self.castle_rights = {
            "K":True,
            "Q":True,
            "k":True,
            "q":True
        }
        self.en_passant_target = None
        self.halfmove_clock = 0
        self.move_history = []
    
    @property
    def flipped_board(self):
        return [row[::-1] for row in self.board[::-1]]
    
    def print(self, flip=False):
        if not flip:
            for i, row in enumerate(self.board):
                print(f"{8 - i} {"".join([f"\x1b[{"47" if (j + i) % 2 == 0 else "40"}m{cell} \x1b[0m" for j, cell in enumerate("".join(row).translate(fen_string_translation_table))])}")
            print("  a b c d e f g h")
        else:
            for i, row in enumerate(self.flipped_board):
                print(f"{i + 1} {"".join([f"\x1b[{"47" if (j + i) % 2 == 0 else "40"}m{cell} \x1b[0m" for j, cell in enumerate("".join(row).translate(fen_string_translation_table))])}")
            print("  h g f e d c b a")
    
    def change_piece_position(self, start_position, end_position):
        self.board[end_position[1]][end_position[0]] = self.board[start_position[1]][start_position[0]]
        self.board[start_position[1]][start_position[0]] = " "
    
    def change_piece_square(self, start_square, end_square):
        self.change_piece_position(square_to_position(start_square), square_to_position(end_square))
    
    def move(self, move):
        simplified_move = move.translate(simplify_move_translation_table)

        piece = None
        suggested_start_position = None
        end_position = None
        castle = None
        # en_passant = False

        capture = "x" in move
        promotion = move[-1] if move[-1].isupper() else None
        check = "+" in move
        checkmate = "#" in move

        if promotion is not None:
            simplified_move = simplified_move[:-1]
            
        if simplified_move == "0-0":
            castle = "k"
        elif simplified_move == "0-0-0":
            castle = "q"
        # elif simplified_move[5:] == "e.p.":
        #     piece = "p"
        #     en_passant = True
        #     start_position = [file_to_int(simplified_move[0]), rank_to_int(simplified_move[3]) - 1]
        elif len(simplified_move) == 2:
            piece = "p"
            end_position = square_to_position(simplified_move)
        elif len(simplified_move) == 3:
            piece = simplified_move[0]
            end_position = square_to_position(simplified_move[1:])
        elif len(simplified_move) == 4:
            end_position = square_to_position(simplified_move[2:])
            if capture:
                if simplified_move[0].isupper():
                    piece = simplified_move[0]
                else:
                    piece = "p"
                    suggested_start_position = [file_to_int(simplified_move[0]), None]
            else:
                piece = simplified_move[0]
                suggested_start_position = [None, rank_to_int(simplified_move[1])] if simplified_move[1].isnumeric() else [file_to_int(simplified_move[1]), None]
        elif len(simplified_move) == 5:
            piece = simplified_move[0]
            end_position = square_to_position(simplified_move[3:])
            suggested_start_position = [None, rank_to_int(simplified_move[1])] if simplified_move[1].isnumeric() else [file_to_int(simplified_move[1]), None]
        
        if promotion is None:
            print(end_position[1])
            if piece.lower() == "p" and ((self.turn == "w" and end_position[1] == 0) or (self.turn == "b" and end_position[1] == 7)):
                raise ValueError(f"Cannot perform move {move}: move should be written as a promotion")
        else:
            if (self.turn == "w" and end_position[1] != 0) or (self.turn == "b" and end_position[1] != 7):
                raise ValueError(f"Cannot perform move {move}: cannot promote on this rank")
        
        if check or checkmate:
            previous_fen_string = self.fen_string
       
        if castle is not None:
            castle = castle.upper() if self.turn == "w" else castle.lower()

            if not self.castle_rights[castle]:
                raise ValueError(f"Cannot perform move {move}: cannot castle")
            
            if castle == "K" and " " == self.board[7][5] == self.board[7][6]:
                self.change_piece_position([4, 7], [6, 7])
                self.change_piece_position([7, 7], [5, 7])
            elif castle == "Q" and " " == self.board[7][3] == self.board[7][2]:
                self.change_piece_position([4, 7], [2, 7])
                self.change_piece_position([0, 7], [3, 7])
            elif castle == "k" and " " == self.board[0][5] == self.board[0][6]:
                self.change_piece_position([4, 0], [6, 0])
                self.change_piece_position([7, 0], [5, 0])
            elif castle == "q" and " " == self.board[0][3] == self.board[0][2]:
                self.change_piece_position([4, 0], [2, 0])
                self.change_piece_position([0, 0], [3, 0])
            else:
                raise ValueError(f"Cannot perform move {move}: cannot castle")
            
            if self.turn == "w":
                self.castle_rights["K"] = self.castle_rights["Q"] = False
            else:
                self.castle_rights["k"] = self.castle_rights["q"] = False
        else:
            piece_at_end_position = self.board[end_position[1]][end_position[0]]

            if (capture and (piece_at_end_position == " " or (self.turn == "w" and piece_at_end_position.isupper()) or (self.turn == "b" and piece_at_end_position.islower()))) or (not (capture) and piece_at_end_position != " "):
                raise ValueError(f"Cannot perform move {move}: end position is invalid for this move")
            
            # en_passant_target = self.fen_string_parts[3]
            piece = piece.upper() if self.turn == "w" else piece.lower()

            match piece.lower():
                case "p":
                    direction = 1 if self.turn == "w" else -1
                    if capture:
                        possible_start_positions = [
                            [end_position[0] - 1, end_position[1] + direction],
                            [end_position[0] + 1, end_position[1] + direction]
                        ]
                    else :
                        possible_start_positions = [[end_position[0], end_position[1] + direction]]
                        if end_position[1] == (4 if self.turn == "w" else 3):
                            possible_start_positions.append([end_position[0], end_position[1] + direction * 2])
                case "b":
                    left, right, up, down = end_position[0], 7 - end_position[0], end_position[1], 7 - end_position[1]
                    possible_start_positions = [
                        *[[end_position[0] - i, end_position[1] - i] for i in range(1, min(left, up) + 1)],
                        *[[end_position[0] - i, end_position[1] + i] for i in range(1, min(left, down) + 1)],
                        *[[end_position[0] + i, end_position[1] - i] for i in range(1, min(right, up) + 1)],
                        *[[end_position[0] + i, end_position[1] + i] for i in range(1, min(right, down) + 1)]
                    ]
                case "n":
                    possible_start_positions = []
                    for i in range(2):
                        dx = i % 2 + 1
                        dy = dx % 2 + 1
                        for j in range(2):
                            dx_sign = 1 if j == 0 else -1
                            new_x = end_position[0] + dx * dx_sign

                            if 0 > new_x or new_x > 7:
                                continue

                            for k in range(2):
                                dy_sign = 1 if k == 0 else -1
                                new_y = end_position[1] + dy * dy_sign
                                
                                if 0 > new_y or new_y > 7:
                                    continue

                                possible_start_positions.append([new_x, new_y])
                case "r":
                    left, right, up, down = end_position[0], 7 - end_position[0], end_position[1], 7 - end_position[1]
                    possible_start_positions = [
                        *[[end_position[0] - i, end_position[1]] for i in range(1, left + 1)],
                        *[[end_position[0] + i, end_position[1]] for i in range(1, right + 1)],
                        *[[end_position[0], end_position[1] - i] for i in range(1, up + 1)],
                        *[[end_position[0], end_position[1] + i] for i in range(1, down + 1)],
                    ]
                case "q":
                    left, right, up, down = end_position[0], 7 - end_position[0], end_position[1], 7 - end_position[1]
                    possible_start_positions = [
                        *[[end_position[0] - i, end_position[1] - i] for i in range(1, min(left, up) + 1)],
                        *[[end_position[0] - i, end_position[1] + i] for i in range(1, min(left, down) + 1)],
                        *[[end_position[0] + i, end_position[1] - i] for i in range(1, min(right, up) + 1)],
                        *[[end_position[0] + i, end_position[1] + i] for i in range(1, min(right, down) + 1)],
                        *[[end_position[0] - i, end_position[1]] for i in range(1, left + 1)],
                        *[[end_position[0] + i, end_position[1]] for i in range(1, right + 1)],
                        *[[end_position[0], end_position[1] - i] for i in range(1, up + 1)],
                        *[[end_position[0], end_position[1] + i] for i in range(1, down + 1)],
                    ]
                case "k":
                    possible_start_positions = []
                    for i in range(-1, 2):
                        new_x = end_position[0] + i

                        if 0 > new_x or new_x > 7:
                                continue
                        
                        for j in range(-1, 2):
                            new_y = end_position[1] + j

                            if 0 > new_y or new_y > 7:
                                continue
                            
                            possible_start_positions.append([new_x, new_y])

            # probably should write code that skips the searching stuff and just does things custom to each piece, but that's for later
            if isinstance(suggested_start_position, list):
                if None in suggested_start_position:
                    should_match = 0 if suggested_start_position[0] is not None else 1
                    to_check = 1
                else:
                    to_check = 2
            else:
                to_check = 0
            
            print(possible_start_positions)
            print(piece)

            start_position = None
            for position in possible_start_positions:
                if (to_check == 1 and position[should_match] != suggested_start_position[should_match]) or (to_check == 2 and position != suggested_start_position) or self.board[position[1]][position[0]] != piece:
                    continue

                if piece.lower() != "n":
                    direction = [sign(end_position[0] - position[0]), sign(end_position[1] - position[1])]
                    should_be_empty = [
                        [x, y] for x, y in zip(range(position[0] + direction[0], end_position[0]), range(position[1] + direction[1], end_position[1]))
                    ] if capture else [
                        [x, y] for x, y in zip(range(position[0] + direction[0], end_position[0] - direction[0]), range(position[1] + direction[1], end_position[1] - direction[1]))
                    ]
                    if not all(self.board[position[1]][position[0]] == " " for position in should_be_empty):
                        continue

                # add more checks ig
                # add checks for checks lol lmao hahahaha
                start_position = position
                break
            
            if start_position is None:
                raise ValueError(f"Cannot perform move {move}: no piece able to perform this move was found")

            if promotion is None:
                self.change_piece_position(start_position, end_position)
            else:
                self.set_piece_at_position(start_position, " ")
                self.set_piece_at_position(end_position, promotion)
        
        if piece is not None and piece.lower() == "r":
            if self.turn == "w":
                if start_position == [7, 0]:
                    self.castle_rights["K"] = False
                if start_position == [0, 0]:
                    self.castle_rights["Q"] = False
            else:
                if start_position == [7, 7]:
                    self.castle_rights["k"] = False
                if start_position == [0, 7]:
                    self.castle_rights["q"] = False

        if len(self.move_history) == 0:
            self.move_history.append([])
        self.move_history[-1].append(move)
        if self.turn == "b":
            self.move_history.append([])

        self.turn = "b" if self.turn == "w" else "w"

        self.halfmove_clock = self.halfmove_clock + 1 if (piece is None or piece.lower() != "p") and not capture else 0 # check if this goes over 100?
        
        # if not check/checkmate but it should be according to the move, self.fen_string = previous_fen_string

# game = Game(fen_string="r1bqkbnr/ppppppPp/2n5/8/8/8/PPPPPPP1/RNBQKBNR w KQkq - 1 5")
game = Game()

# previous_moves = [
#     "e4", "e5",
#     "Nf3", "Nf6",
#     "Bc4", "Bc5",
#     # "0-0"
# ]
# for move in previous_moves:
#     game.move(move)

user_input = None
while True:
    game.print()
    user_input = input("move\n> ")

    if user_input == "stop":
        break

    match user_input:
        case "stop":
            break
        case "history" | "draw" | "resign":
            print()
            match user_input:
                # case "history":
                #     print(f"Current game history:\n{"\n".join(game.move_history)}")
                case "draw":
                    print("Draw offered")
                    ...
                case "resign":
                    print("idk")
                    ...
            
            input("\nPress 'Enter' to continue")
        case _:
            # try:
                game.move(user_input)
            # except BaseException as error:
            #     print(f"Bad move: {error}")
    
    # print("\x1b[1;1H\x1b[2J\x1b[3J", end="")

    # add 75 move rule and 50 move rule ig