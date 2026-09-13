from board import Board
from evaluate import Evaluate, PIECE_VALUES


INF = 100000000
MATE_SCORE = 1000000


class Search:
    def __init__(self, verbose=False, quiescence_depth=4):
        self.evaluate = Evaluate()
        self.verbose = verbose
        self.quiescence_depth = quiescence_depth
        self.transposition = {}
        self.nodes = 0

    def copy_board(self, board):
        new_board = Board()
        new_board.state = [r[:] for r in board.state]
        new_board.white_king_moved = board.white_king_moved
        new_board.black_king_moved = board.black_king_moved
        new_board.white_rook_a_moved = board.white_rook_a_moved
        new_board.white_rook_h_moved = board.white_rook_h_moved
        new_board.black_rook_a_moved = board.black_rook_a_moved
        new_board.black_rook_h_moved = board.black_rook_h_moved
        return new_board

    def board_key(self, board, team, depth):
        return (
            tuple(tuple(row) for row in board.state),
            board.white_king_moved,
            board.black_king_moved,
            board.white_rook_a_moved,
            board.white_rook_h_moved,
            board.black_rook_a_moved,
            board.black_rook_h_moved,
            team,
            depth,
        )

    @staticmethod
    def piece_value(piece):
        piece_type = abs(piece)
        if piece_type == 7:
            return PIECE_VALUES[1]
        return PIECE_VALUES.get(piece_type, 0)

    @staticmethod
    def is_castle(move):
        return abs(move[1] - move[3]) == 2

    @staticmethod
    def is_real_piece(piece):
        return piece != 0 and abs(piece) != 7

    def is_capture(self, board, move):
        moving_piece = board.state[move[0]][move[1]]
        target_piece = board.state[move[2]][move[3]]

        if abs(moving_piece) == 1 and abs(target_piece) == 7:
            return True

        return self.is_real_piece(target_piece)

    def is_tactical_move(self, board, move):
        return move[4] is not None or self.is_capture(board, move)

    def move_order_score(self, board, move):
        moving_piece = board.state[move[0]][move[1]]
        target_piece = board.state[move[2]][move[3]]
        score = 0

        if move[4] is not None:
            score += 10000 + PIECE_VALUES.get(move[4], 0)

        if self.is_capture(board, move):
            score += 5000 + self.piece_value(target_piece) * 10 - self.piece_value(moving_piece)

        if abs(moving_piece) == 6 and self.is_castle(move):
            score += 80

        if move[2] in (3, 4) and move[3] in (3, 4):
            score += 20

        return score

    def terminal_score(self, board, team, depth):
        white_in_check, black_in_check, white_king_pos, black_king_pos = board.king_check_check()

        if team == 1:
            if white_in_check:
                return -MATE_SCORE - depth
            return 0

        if black_in_check:
            return MATE_SCORE + depth

        return 0

    def minmax(self, board, team, depth, alpha=-INF, beta=INF):
        self.nodes += 1
        legal_moves = board.get_all_legal_moves(team)

        if len(legal_moves) == 0:
            return self.terminal_score(board, team, depth), None

        if depth == 0:
            return self.quiescence(board, team, alpha, beta, self.quiescence_depth), None

        cache_key = self.board_key(board, team, depth)
        if cache_key in self.transposition:
            return self.transposition[cache_key]

        legal_moves.sort(key=lambda move: self.move_order_score(board, move), reverse=True)
        searched_all_moves = True

        if team == 1:
            best_eval = -INF
            best_move = None

            for move in legal_moves:
                child_board = self.copy_board(board)
                child_board.move_piece(*move)
                eval_score, dont_need = self.minmax(child_board, -team, depth - 1, alpha, beta)

                if eval_score > best_eval:
                    best_eval = eval_score
                    best_move = move

                alpha = max(alpha, best_eval)

                if self.verbose:
                    print("move:", move, "eval:", eval_score)

                if beta <= alpha:
                    searched_all_moves = False
                    break

        else:
            best_eval = INF
            best_move = None

            for move in legal_moves:
                child_board = self.copy_board(board)
                child_board.move_piece(*move)
                eval_score, dont_need = self.minmax(child_board, -team, depth - 1, alpha, beta)

                if eval_score < best_eval:
                    best_eval = eval_score
                    best_move = move

                beta = min(beta, best_eval)

                if self.verbose:
                    print("move:", move, "eval:", eval_score)

                if beta <= alpha:
                    searched_all_moves = False
                    break

        if searched_all_moves:
            self.transposition[cache_key] = (best_eval, best_move)

        return best_eval, best_move

    def quiescence(self, board, team, alpha, beta, depth):
        self.nodes += 1
        legal_moves = board.get_all_legal_moves(team)

        if len(legal_moves) == 0:
            return self.terminal_score(board, team, depth)

        if depth <= 0:
            return self.evaluate.evaluate(board)

        white_in_check, black_in_check, white_king_pos, black_king_pos = board.king_check_check()
        in_check = white_in_check if team == 1 else black_in_check

        if in_check:
            candidate_moves = legal_moves
            best_eval = -INF if team == 1 else INF
        else:
            stand_pat = self.evaluate.evaluate(board)
            candidate_moves = [move for move in legal_moves if self.is_tactical_move(board, move)]

            if team == 1:
                if stand_pat >= beta:
                    return stand_pat
                alpha = max(alpha, stand_pat)
                best_eval = stand_pat
            else:
                if stand_pat <= alpha:
                    return stand_pat
                beta = min(beta, stand_pat)
                best_eval = stand_pat

        if not candidate_moves:
            return best_eval

        candidate_moves.sort(key=lambda move: self.move_order_score(board, move), reverse=True)

        for move in candidate_moves:
            child_board = self.copy_board(board)
            child_board.move_piece(*move)
            eval_score = self.quiescence(child_board, -team, alpha, beta, depth - 1)

            if team == 1:
                if eval_score > best_eval:
                    best_eval = eval_score
                alpha = max(alpha, best_eval)
            else:
                if eval_score < best_eval:
                    best_eval = eval_score
                beta = min(beta, best_eval)

            if beta <= alpha:
                break

        return best_eval
