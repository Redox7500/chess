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
    return int(rank) - 1

def square_to_position(square):
    x = file_to_int(square[0])
    if x < 0 or x >= 8:
        raise ValueError(f"file {x} outside of range [0, 8)")
    y = rank_to_int(square[1])
    if y < 0 or y >= 8:
        raise ValueError(f"rank {y} outside of range [0, 8)")
    
    return [x, y]

class Game:
    def __init__(self, fen_string="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"):
        self.fen_string = fen_string
        self.move_history = []

    @property
    def fen_string_parts(self):
        return self.fen_string.split(" ")
    
    def print(self):
        for i, row in enumerate(self.fen_string_parts[0].translate(fen_string_translation_table).split("/")):
            print(f"{8 - i} {"".join([f"\x1b[{"47" if (j + i) % 2 == 0 else "40"}m{cell} \x1b[0m" for j, cell in enumerate(row)])}")
        print("  a b c d e f g h\n")
    
    def get_fen_string_part_character_index(self, index):
        return len(" ".join(self.fen_string_parts[:index])) + 1
    
    def set_fen_string_part(self, index, value):
        self.fen_string = f"{self.fen_string[:self.get_fen_string_part_character_index(index)]}{value} {self.fen_string[self.get_fen_string_part_character_index(index + 1):]}"

    def get_position_index(self, position):
        current_x = 0
        current_y = 7
        for i, character in enumerate(self.fen_string_parts[0]):
            if character == "/":
                current_x = 0
                current_y -= 1
                continue

            if character.isnumeric():
                current_x += int(character) - 1

            if current_y == position[1] and current_x >= position[0]:
                return i
            
            current_x += 1

    def get_piece_at_position(self, position):
        cell = self.fen_string[self.get_position_index(position)]
        return " " if cell.isnumeric() else cell
    
    def get_piece_at_square(self, square):
        return self.get_piece_at_position(square_to_position(square))
    
    def set_piece_at_position(self, position, piece):
        index = self.get_position_index(position)
        row = self.fen_string_parts[0].split("/")[7 - position[1]]

        current_x = 0
        i = 0
        for i, character in enumerate(row):
            int_character = int(character) if character.isnumeric() else None
            current_x += int_character - 1 if int_character is not None else 0

            if current_x >= position[0]:
                empty_squares_after = current_x - position[0]
                character_before_is_numeric = False
                character_after_is_numeric = False
                if int_character is None:
                    character_before = row[i - 1] if i > 0 else "def not a number"
                    character_before_is_numeric = character_before.isnumeric()
                    empty_squares_before = int(character_before) if character_before_is_numeric else 0
                    character_after = row[i + 1] if i < len(row) - 1 else "def not a number"
                    character_after_is_numeric = character_after.isnumeric()
                    empty_squares_after += int(character_after) if character_after_is_numeric else 0
                else:
                    empty_squares_before = int_character - empty_squares_after - 1
                break
            
            current_x += 1
        
        if piece != " ":
            replacement = f"{empty_squares_before if empty_squares_before > 0 else ""}{piece}{empty_squares_after if empty_squares_after > 0 else ""}"
        else:
            replacement = f"{empty_squares_before + 1 + empty_squares_after}"
        
        self.fen_string = f"{self.fen_string[:index - (1 if character_before_is_numeric else 0)]}{replacement}{self.fen_string[index + 1 + (1 if character_after_is_numeric else 0):]}"
    
    def set_piece_at_square(self, square, piece):
        self.set_piece_at_position(square_to_position(square), piece)
    
    def change_piece_position(self, start_position, end_position):
        self.set_piece_at_position(end_position, self.get_piece_at_position(start_position))
        self.set_piece_at_position(start_position, " ")
    
    def change_piece_square(self, start_square, end_square):
        self.change_piece_position(square_to_position(start_square), square_to_position(end_square))

    def positions_are_empty(self, *positions):
        return all([self.get_piece_at_position(position) == " " for position in positions])

    def squares_are_empty(self, *squares):
        return self.positions_are_empty(*[square_to_position(square) for square in squares])
    
    def move(self, move):
        simplified_move = move.translate(simplify_move_translation_table)

        turn = self.fen_string_parts[1]

        piece = None
        suggested_start_position = None
        end_position = None
        castle = False
        castle_side = None
        # en_passant = False

        capture = "x" in move
        promotion = move[-1] if move[-1].isupper() else None
        check = "+" in move
        checkmate = "#" in move

        if promotion is not None:
            simplified_move = simplified_move[:-1]
            
        if simplified_move == "0-0":
            castle = True
            castle_side = "k"
        elif simplified_move == "0-0-0":
            castle = True
            castle_side = "q"
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
            if capture:
                suggested_start_position = [None, rank_to_int(simplified_move[1])] if simplified_move[1].isnumeric() else [file_to_int(simplified_move[1]), None]
            else:
                suggested_start_position = square_to_position(simplified_move[1:3])
        elif len(simplified_move) == 6:
            piece = simplified_move[0]
            suggested_start_position = square_to_position(simplified_move[1:3])
            end_position = square_to_position(simplified_move[4:])
        
        if promotion is not None:
            if (turn == "w" and end_position[1] != 0) or (turn == "b" and end_position[1] != 7):
                raise ValueError(f"Cannot perform move {move}: cannot promote on this rank")
        else:
            if piece in ["P", "p"] and ((turn == "w" and end_position[1] == 0) or (turn == "b" and end_position[1] == 7)):
                raise ValueError(f"Cannot perform move {move}: move should be written as a promotion")

        # shit i gotta add promotions later
        
        if check or checkmate:
            previous_fen_string = self.fen_string
       
        if castle:
            turn_castle_side = castle_side.upper() if turn == "w" else castle_side.lower()

            if turn_castle_side not in self.fen_string_parts[2]:
                raise ValueError(f"Cannot perform move {move}: cannot castle")
            
            if turn_castle_side == "K" and self.squares_are_empty("f1", "g1"):
                self.change_piece_square("e1", "g1")
                self.change_piece_square("h1", "f1")
            elif turn_castle_side == "Q" and self.squares_are_empty("d1", "c1"):
                self.change_piece_square("e1", "c1")
                self.change_piece_square("a1", "d1")
            elif turn_castle_side == "k" and self.squares_are_empty("f8", "g8"):
                self.change_piece_square("e8", "g8")
                self.change_piece_square("h8", "f8")
            elif turn_castle_side == "q" and self.squares_are_empty("d8", "c8"):
                self.change_piece_square("e8", "c8")
                self.change_piece_square("a8", "d8")
            else:
                raise ValueError(f"Cannot perform move {move}: cannot castle")
            
            if turn == "w":
                new_fen_string_part = self.fen_string_parts[2].replace("K", "").replace("Q", "")
            else:
                new_fen_string_part = self.fen_string_parts[2].replace("k", "").replace("q", "")
            if new_fen_string_part == "":
                new_fen_string_part = "-"
            self.set_fen_string_part(2, new_fen_string_part)
        else:
            piece_at_end_position = self.get_piece_at_position(end_position)

            if (capture and (piece_at_end_position == " " or (piece_at_end_position.isupper() and turn == "w") or (not (piece_at_end_position.isupper()) and turn == "b"))) or (not (capture) and piece_at_end_position != " "):
                raise ValueError(f"Cannot perform move {move}: end position is invalid for this move")
            
            piece = piece.upper() if turn == "w" else piece.lower()
            # en_passant_target = self.fen_string_parts[3]

            match piece:
                case "P" | "p":
                    direction = -1 if turn == "w" else 1
                    if capture:
                        possible_start_positions = [
                            [end_position[0] - 1, end_position[1] + direction],
                            [end_position[0] + 1, end_position[1] + direction]
                        ]
                    else :
                        possible_start_positions = [[end_position[0], end_position[1] + direction]]
                        if end_position[1] == (3 if turn == "w" else 4):
                            possible_start_positions.append([end_position[0], end_position[1] + direction * 2])
                case "B" | "b":
                    left, right, down, up = end_position[0], 7 - end_position[0], end_position[1], 7 - end_position[1]
                    possible_start_positions = [
                        *[[end_position[0] - i, end_position[1] - i] for i in range(1, min(left, down) + 1)],
                        *[[end_position[0] - i, end_position[1] + i] for i in range(1, min(left, up) + 1)],
                        *[[end_position[0] + i, end_position[1] - i] for i in range(1, min(right, down) + 1)],
                        *[[end_position[0] + i, end_position[1] + i] for i in range(1, min(right, up) + 1)]
                    ]
                case "N" | "n":
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
                case "R" | "r":
                    left, right, down, up = end_position[0], 7 - end_position[0], end_position[1], 7 - end_position[1]
                    possible_start_positions = [
                        *[[end_position[0] - i, end_position[1]] for i in range(1, left + 1)],
                        *[[end_position[0] + i, end_position[1]] for i in range(1, right + 1)],
                        *[[end_position[0], end_position[1] - i] for i in range(1, down + 1)],
                        *[[end_position[0], end_position[1] + i] for i in range(1, up + 1)],
                    ]
                case "Q" | "q":
                    left, right, down, up = end_position[0], 7 - end_position[0], end_position[1], 7 - end_position[1]
                    possible_start_positions = [
                        *[[end_position[0] - i, end_position[1] - i] for i in range(1, min(left, down) + 1)],
                        *[[end_position[0] - i, end_position[1] + i] for i in range(1, min(left, up) + 1)],
                        *[[end_position[0] + i, end_position[1] - i] for i in range(1, min(right, down) + 1)],
                        *[[end_position[0] + i, end_position[1] + i] for i in range(1, min(right, up) + 1)],
                        *[[end_position[0] - i, end_position[1]] for i in range(1, left + 1)],
                        *[[end_position[0] + i, end_position[1]] for i in range(1, right + 1)],
                        *[[end_position[0], end_position[1] - i] for i in range(1, down + 1)],
                        *[[end_position[0], end_position[1] + i] for i in range(1, up + 1)],
                    ]
                case "K" | "k":
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

            start_position = None
            for position in possible_start_positions:
                if (to_check == 1 and position[should_match] != suggested_start_position[should_match]) or (to_check == 2 and position != suggested_start_position) or self.get_piece_at_position(position) != piece:
                    continue

                if piece not in ["N", "n"]:
                    direction = [sign(end_position[0] - position[0]), sign(end_position[1] - position[1])]
                    should_be_empty = [
                        [x, y] for x, y in zip(range(position[0] + direction[0], end_position[0]), range(position[1] + direction[1], end_position[1]))
                    ] if capture else [
                        [x, y] for x, y in zip(range(position[0] + direction[0], end_position[0] - direction[0]), range(position[1] + direction[1], end_position[1] - direction[1]))
                    ]
                    if not self.positions_are_empty(*should_be_empty):
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
        
        self.set_fen_string_part(1, "b" if turn == "w" else "w")
        if piece == "R":
            if start_position == [7, 0]:
                self.set_fen_string_part(2, self.fen_string_parts[2].replace("K", ""))
            if start_position == [0, 0]:
                self.set_fen_string_part(2, self.fen_string_parts[2].replace("Q", ""))
        if piece == "r":
            if start_position == [7, 7]:
                self.set_fen_string_part(2, self.fen_string_parts[2].replace("k", ""))
            if start_position == [0, 7]:
                self.set_fen_string_part(2, self.fen_string_parts[2].replace("q", ""))
        self.set_fen_string_part(4, int(self.fen_string_parts[4]) + 1 if not (capture or piece in ["P", "p"]) else 0) # check if this goes over 100?
        if turn == "b":
            self.set_fen_string_part(5, int(self.fen_string_parts[5]) + 1)
        
        # if not check/checkmate but it should be according to the move, self.fen_string = previous_fen_string

        self.move_history.append(move)

game = Game(fen_string="r1bqkbnr/ppppppPp/2n5/8/8/8/PPPPPPP1/RNBQKBNR w KQkq - 1 5")

previous_moves = [
    "e4", "e5",
    "Nf3", "Nf6",
    "Bc4", "Bc5",
    # "0-0"
]
for move in previous_moves:
    game.move(move)

user_input = None
while True:
    game.print()
    user_input = input("move\n> ")

    if user_input == "stop":
        break

    match user_input:
        case "stop":
            break
        case "fen" | "history" | "draw" | "resign":
            print()
            match user_input:
                case "fen":
                    print(f"Current FEN string: {game.fen_string}")
                case "history":
                    print(f"Current game history:\n{"\n".join(game.move_history)}")
                case "draw":
                    print("Draw offered")
                    ...
                case "resign":
                    print("idk")
                    ...
            
            input("\nPress 'Enter' to continue")
        case _:
            try:
                game.move(user_input)
            except BaseException as error:
                print(f"Bad move: {error}")
    
    print("\x1b[1;1H\x1b[2J\x1b[3J", end="")

    # add 75 move rule