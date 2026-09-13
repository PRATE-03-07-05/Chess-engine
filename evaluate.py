PIECE_VALUES = {
    1: 100,
    2: 320,
    3: 330,
    4: 500,
    5: 900,
    6: 0,
}

PAWN_TABLE = [
    [0, 0, 0, 0, 0, 0, 0, 0],
    [50, 50, 50, 50, 50, 50, 50, 50],
    [10, 10, 20, 30, 30, 20, 10, 10],
    [5, 5, 10, 25, 25, 10, 5, 5],
    [0, 0, 0, 20, 20, 0, 0, 0],
    [5, -5, -10, 0, 0, -10, -5, 5],
    [5, 10, 10, -20, -20, 10, 10, 5],
    [0, 0, 0, 0, 0, 0, 0, 0],
]

KNIGHT_TABLE = [
    [-50, -40, -30, -30, -30, -30, -40, -50],
    [-40, -20, 0, 5, 5, 0, -20, -40],
    [-30, 5, 10, 15, 15, 10, 5, -30],
    [-30, 0, 15, 20, 20, 15, 0, -30],
    [-30, 5, 15, 20, 20, 15, 5, -30],
    [-30, 0, 10, 15, 15, 10, 0, -30],
    [-40, -20, 0, 0, 0, 0, -20, -40],
    [-50, -40, -30, -30, -30, -30, -40, -50],
]

BISHOP_TABLE = [
    [-20, -10, -10, -10, -10, -10, -10, -20],
    [-10, 5, 0, 0, 0, 0, 5, -10],
    [-10, 10, 10, 10, 10, 10, 10, -10],
    [-10, 0, 10, 15, 15, 10, 0, -10],
    [-10, 5, 5, 15, 15, 5, 5, -10],
    [-10, 0, 5, 10, 10, 5, 0, -10],
    [-10, 0, 0, 0, 0, 0, 0, -10],
    [-20, -10, -10, -10, -10, -10, -10, -20],
]

ROOK_TABLE = [
    [0, 0, 0, 5, 5, 0, 0, 0],
    [5, 10, 10, 10, 10, 10, 10, 5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [0, 0, 0, 5, 5, 0, 0, 0],
]

QUEEN_TABLE = [
    [-20, -10, -10, -5, -5, -10, -10, -20],
    [-10, 0, 5, 0, 0, 0, 0, -10],
    [-10, 5, 5, 5, 5, 5, 0, -10],
    [0, 0, 5, 5, 5, 5, 0, -5],
    [-5, 0, 5, 5, 5, 5, 0, -5],
    [-10, 0, 5, 5, 5, 5, 0, -10],
    [-10, 0, 0, 0, 0, 0, 0, -10],
    [-20, -10, -10, -5, -5, -10, -10, -20],
]

KING_MIDDLE_TABLE = [
    [20, 30, 10, 0, 0, 10, 30, 20],
    [20, 20, 0, 0, 0, 0, 20, 20],
    [-10, -20, -20, -20, -20, -20, -20, -10],
    [-20, -30, -30, -40, -40, -30, -30, -20],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
]

KING_END_TABLE = [
    [-50, -30, -30, -30, -30, -30, -30, -50],
    [-30, -30, 0, 0, 0, 0, -30, -30],
    [-30, -10, 20, 30, 30, 20, -10, -30],
    [-30, -10, 30, 40, 40, 30, -10, -30],
    [-30, -10, 30, 40, 40, 30, -10, -30],
    [-30, -10, 20, 30, 30, 20, -10, -30],
    [-30, -20, -10, 0, 0, -10, -20, -30],
    [-50, -40, -30, -20, -20, -30, -40, -50],
]

PIECE_SQUARE_TABLES = {
    1: PAWN_TABLE,
    2: KNIGHT_TABLE,
    3: BISHOP_TABLE,
    4: ROOK_TABLE,
    5: QUEEN_TABLE,
}

MOBILITY_WEIGHTS = {
    2: 4,
    3: 4,
    4: 2,
    5: 1,
}

KNIGHT_DIRECTIONS = (
    (2, 1),
    (2, -1),
    (-2, 1),
    (-2, -1),
    (1, 2),
    (1, -2),
    (-1, 2),
    (-1, -2),
)

BISHOP_DIRECTIONS = ((1, 1), (1, -1), (-1, 1), (-1, -1))
ROOK_DIRECTIONS = ((1, 0), (-1, 0), (0, 1), (0, -1))
QUEEN_DIRECTIONS = BISHOP_DIRECTIONS + ROOK_DIRECTIONS


class Evaluate:
    def evaluate(self, board):
        score = 0
        white_pawns_by_file = [0] * 8
        black_pawns_by_file = [0] * 8
        pawns = []
        rooks = []
        bishop_count = {1: 0, -1: 0}
        non_pawn_material = 0
        queens = 0
        kings = {}

        for row, board_row in enumerate(board.state):
            for col, piece in enumerate(board_row):
                team = self.team(piece)
                if team == 0:
                    continue

                piece_type = abs(piece)

                if piece_type == 1:
                    pawns.append((row, col, team))
                    if team == 1:
                        white_pawns_by_file[col] += 1
                    else:
                        black_pawns_by_file[col] += 1
                elif piece_type in PIECE_VALUES:
                    non_pawn_material += PIECE_VALUES[piece_type]

                if piece_type == 3:
                    bishop_count[team] += 1
                elif piece_type == 4:
                    rooks.append((row, col, team))
                elif piece_type == 5:
                    queens += 1
                elif piece_type == 6:
                    kings[team] = (row, col)

        endgame = queens == 0 or non_pawn_material <= 2400

        for row, board_row in enumerate(board.state):
            for col, piece in enumerate(board_row):
                team = self.team(piece)
                if team == 0:
                    continue

                piece_type = abs(piece)
                score += team * PIECE_VALUES[piece_type]
                score += team * self.piece_square_value(piece_type, team, row, col, endgame)
                score += team * self.mobility_value(board, row, col, piece_type, team)

                if not endgame:
                    score += team * self.development_value(row, col, piece_type, team)

        score += self.pawn_structure_score(
            pawns,
            white_pawns_by_file,
            black_pawns_by_file,
        )
        score += self.rook_file_score(rooks, white_pawns_by_file, black_pawns_by_file)
        score += self.bishop_pair_score(bishop_count)
        score += self.king_safety_score(board, kings, white_pawns_by_file, black_pawns_by_file, endgame)
        score += self.check_score(board)

        return score

    @staticmethod
    def team(piece):
        if piece in (0, 7, -7):
            return 0
        return 1 if piece > 0 else -1

    @staticmethod
    def in_bounds(row, col):
        return 0 <= row <= 7 and 0 <= col <= 7

    def team_at(self, board, row, col):
        return self.team(board.state[row][col])

    @staticmethod
    def piece_square_value(piece_type, team, row, col, endgame):
        if piece_type == 6:
            table = KING_END_TABLE if endgame else KING_MIDDLE_TABLE
        else:
            table = PIECE_SQUARE_TABLES.get(piece_type)

        if table is None:
            return 0

        table_row = row if team == 1 else 7 - row
        return table[table_row][col]

    def mobility_value(self, board, row, col, piece_type, team):
        if piece_type == 2:
            move_count = self.jump_mobility(board, row, col, team, KNIGHT_DIRECTIONS)
        elif piece_type == 3:
            move_count = self.ray_mobility(board, row, col, team, BISHOP_DIRECTIONS)
        elif piece_type == 4:
            move_count = self.ray_mobility(board, row, col, team, ROOK_DIRECTIONS)
        elif piece_type == 5:
            move_count = self.ray_mobility(board, row, col, team, QUEEN_DIRECTIONS)
        else:
            return 0

        return MOBILITY_WEIGHTS[piece_type] * move_count

    def jump_mobility(self, board, row, col, team, directions):
        move_count = 0
        for row_delta, col_delta in directions:
            next_row = row + row_delta
            next_col = col + col_delta
            if self.in_bounds(next_row, next_col) and self.team_at(board, next_row, next_col) != team:
                move_count += 1
        return move_count

    def ray_mobility(self, board, row, col, team, directions):
        move_count = 0
        for row_delta, col_delta in directions:
            next_row = row + row_delta
            next_col = col + col_delta

            while self.in_bounds(next_row, next_col):
                target_team = self.team_at(board, next_row, next_col)
                if target_team == team:
                    break

                move_count += 1
                if target_team == -team:
                    break

                next_row += row_delta
                next_col += col_delta

        return move_count

    @staticmethod
    def development_value(row, col, piece_type, team):
        if piece_type not in (2, 3):
            return 0

        if team == 1 and row == 7 and col in (1, 2, 5, 6):
            return -12

        if team == -1 and row == 0 and col in (1, 2, 5, 6):
            return -12

        return 0

    def pawn_structure_score(self, pawns, white_pawns_by_file, black_pawns_by_file):
        score = 0

        for count in white_pawns_by_file:
            if count > 1:
                score -= 18 * (count - 1)

        for count in black_pawns_by_file:
            if count > 1:
                score += 18 * (count - 1)

        for row, col, team in pawns:
            friendly_files = white_pawns_by_file if team == 1 else black_pawns_by_file
            enemy_pawns = [pawn for pawn in pawns if pawn[2] == -team]

            if self.is_isolated_pawn(col, friendly_files):
                score += team * -10

            if self.is_passed_pawn(row, col, team, enemy_pawns):
                score += team * self.passed_pawn_bonus(row, team)

        return score

    @staticmethod
    def is_isolated_pawn(col, friendly_files):
        left_file_has_pawn = col > 0 and friendly_files[col - 1] > 0
        right_file_has_pawn = col < 7 and friendly_files[col + 1] > 0
        return not left_file_has_pawn and not right_file_has_pawn

    @staticmethod
    def is_passed_pawn(row, col, team, enemy_pawns):
        checked_files = {file for file in (col - 1, col, col + 1) if 0 <= file <= 7}

        for enemy_row, enemy_col, enemy_team in enemy_pawns:
            if enemy_team != -team or enemy_col not in checked_files:
                continue

            if team == 1 and enemy_row < row:
                return False

            if team == -1 and enemy_row > row:
                return False

        return True

    @staticmethod
    def passed_pawn_bonus(row, team):
        advancement = 6 - row if team == 1 else row - 1
        return 20 + max(0, advancement) * 8

    @staticmethod
    def rook_file_score(rooks, white_pawns_by_file, black_pawns_by_file):
        score = 0

        for row, col, team in rooks:
            friendly_files = white_pawns_by_file if team == 1 else black_pawns_by_file
            enemy_files = black_pawns_by_file if team == 1 else white_pawns_by_file

            if friendly_files[col] == 0 and enemy_files[col] == 0:
                score += team * 25
            elif friendly_files[col] == 0:
                score += team * 12

            if (team == 1 and row == 1) or (team == -1 and row == 6):
                score += team * 20

        return score

    @staticmethod
    def bishop_pair_score(bishop_count):
        score = 0
        if bishop_count[1] >= 2:
            score += 30
        if bishop_count[-1] >= 2:
            score -= 30
        return score

    def king_safety_score(self, board, kings, white_pawns_by_file, black_pawns_by_file, endgame):
        if endgame:
            return 0

        score = 0

        for team, king_square in kings.items():
            row, col = king_square
            friendly_files = white_pawns_by_file if team == 1 else black_pawns_by_file
            enemy_files = black_pawns_by_file if team == 1 else white_pawns_by_file

            if (team == 1 and (row, col) in ((7, 2), (7, 6))) or (
                team == -1 and (row, col) in ((0, 2), (0, 6))
            ):
                score += team * 45
            elif (team == 1 and (row, col) in ((7, 1), (7, 7))) or (
                team == -1 and (row, col) in ((0, 1), (0, 7))
            ):
                score += team * 15

            score += team * self.king_pawn_shield_score(board, row, col, team)
            score += team * self.king_open_file_score(col, friendly_files, enemy_files)

        return score

    def king_pawn_shield_score(self, board, row, col, team):
        score = 0
        shield_row = row - 1 if team == 1 else row + 1

        if not 0 <= shield_row <= 7:
            return score

        for shield_col in (col - 1, col, col + 1):
            if self.in_bounds(shield_row, shield_col) and board.state[shield_row][shield_col] == team:
                score += 10

        return score

    @staticmethod
    def king_open_file_score(col, friendly_files, enemy_files):
        score = 0

        for file_index in (col - 1, col, col + 1):
            if not 0 <= file_index <= 7:
                continue

            if friendly_files[file_index] == 0 and enemy_files[file_index] == 0:
                score -= 12
            elif friendly_files[file_index] == 0:
                score -= 8

        return score

    @staticmethod
    def check_score(board):
        white_in_check, black_in_check, white_king_pos, black_king_pos = board.king_check_check()
        score = 0

        if white_in_check:
            score -= 35
        if black_in_check:
            score += 35

        return score
