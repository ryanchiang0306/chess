# -*- coding: utf-8 -*-
import pygame
import chess
import random
import time
import sys
import os
import threading
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum, auto

# ===== 遊戲設置與常數 =====
class GameMode(Enum):
    PLAYER_VS_AI = auto()
    PLAYER_VS_PLAYER = auto()

class Difficulty(Enum):
    EASY = 2
    MEDIUM = 3
    HARD = 4
    MASTER = 5

class ChessGame:
    """國際象棋遊戲主類，處理遊戲狀態和邏輯"""
    
    # 棋子評估值常數
    PIECE_VALS = {
        chess.PAWN: 100, 
        chess.KNIGHT: 320, 
        chess.BISHOP: 330, 
        chess.ROOK: 500, 
        chess.QUEEN: 900, 
        chess.KING: 20000
    }
    
    # 位置評估表 - 鼓勵棋子佔據好位置
    POSITION_TABLES = {
        chess.PAWN: [#兵
            0,  0,  0,  0,  0,  0,  0,  0,
            50, 50, 50, 50, 50, 50, 50, 50,
            10, 10, 20, 30, 30, 20, 10, 10,
            5,  5, 10, 25, 25, 10,  5,  5,
            0,  0,  0, 20, 20,  0,  0,  0,
            5, -5,-10,  0,  0,-10, -5,  5,
            5, 10, 10,-20,-20, 10, 10,  5,
            0,  0,  0,  0,  0,  0,  0,  0
        ],
        chess.KNIGHT: [
            -50,-40,-30,-30,-30,-30,-40,-50,
            -40,-20,  0,  0,  0,  0,-20,-40,
            -30,  0, 10, 15, 15, 10,  0,-30,
            -30,  5, 15, 20, 20, 15,  5,-30,
            -30,  0, 15, 20, 20, 15,  0,-30,
            -30,  5, 10, 15, 15, 10,  5,-30,
            -40,-20,  0,  5,  5,  0,-20,-40,
            -50,-40,-30,-30,-30,-30,-40,-50
        ],
        chess.BISHOP: [#主教
            -20,-10,-10,-10,-10,-10,-10,-20,
            -10,  0,  0,  0,  0,  0,  0,-10,
            -10,  0, 10, 10, 10, 10,  0,-10,
            -10,  5,  5, 10, 10,  5,  5,-10,
            -10,  0,  5, 10, 10,  5,  0,-10,
            -10,  5,  5,  5,  5,  5,  5,-10,
            -10,  0,  5,  0,  0,  5,  0,-10,
            -20,-10,-10,-10,-10,-10,-10,-20
        ],
        chess.ROOK: [#車
            0,  0,  0,  0,  0,  0,  0,  0,
            5, 10, 10, 10, 10, 10, 10,  5,
            -5,  0,  0,  0,  0,  0,  0, -5,
            -5,  0,  0,  0,  0,  0,  0, -5,
            -5,  0,  0,  0,  0,  0,  0, -5,
            -5,  0,  0,  0,  0,  0,  0, -5,
            -5,  0,  0,  0,  0,  0,  0, -5,
            0,  0,  0,  5,  5,  0,  0,  0
        ],
        chess.QUEEN: [
            -20,-10,-10, -5, -5,-10,-10,-20,
            -10,  0,  0,  0,  0,  0,  0,-10,
            -10,  0,  5,  5,  5,  5,  0,-10,
            -5,  0,  5,  5,  5,  5,  0, -5,
            0,  0,  5,  5,  5,  5,  0, -5,
            -10,  5,  5,  5,  5,  5,  0,-10,
            -10,  0,  5,  0,  0,  0,  0,-10,
            -20,-10,-10, -5, -5,-10,-10,-20
        ],
        chess.KING: [  # 遊戲非尾聲的國王評估
            -30,-40,-40,-50,-50,-40,-40,-30,
            -30,-40,-40,-50,-50,-40,-40,-30,
            -30,-40,-40,-50,-50,-40,-40,-30,
            -30,-40,-40,-50,-50,-40,-40,-30,
            -20,-30,-30,-40,-40,-30,-30,-20,
            -10,-20,-20,-20,-20,-20,-20,-10,
            20, 20,  0,  0,  0,  0, 20, 20,
            20, 30, 10,  0,  0, 10, 30, 20
        ],
        chess.KING + 100: [  # 遊戲尾聲的國王評估（避免重複鍵）
            -50,-40,-30,-20,-20,-30,-40,-50,
            -30,-20,-10,  0,  0,-10,-20,-30,
            -30,-10, 20, 30, 30, 20,-10,-30,
            -30,-10, 30, 40, 40, 30,-10,-30,
            -30,-10, 30, 40, 40, 30,-10,-30,
            -30,-10, 20, 30, 30, 20,-10,-30,
            -30,-30,  0,  0,  0,  0,-30,-30,
            -50,-30,-30,-30,-30,-30,-30,-50
        ]
    }
    
    def __init__(self, mode: GameMode = GameMode.PLAYER_VS_AI, 
                 difficulty: Difficulty = Difficulty.MEDIUM):
        """初始化遊戲實例"""
        self.board = chess.Board()
        self.mode = mode  
        self.difficulty = difficulty
        self.selected_square = None
        self.is_game_over = False
        self.ai_thinking = False
        self.ai_move = None
        self.move_history = []
        self.mutex = threading.Lock()
        self.transposition_table = {}  # 重複位置緩存
        self.result_message = ""
    
    def reset(self) -> None:
        """重置遊戲狀態"""
        self.board = chess.Board()
        self.selected_square = None
        self.is_game_over = False
        self.ai_thinking = False
        self.ai_move = None
        self.move_history = []
        self.result_message = ""
        self.transposition_table.clear()
    
    def handle_square_selection(self, sq: int) -> Tuple[bool, List[chess.Move]]:
        """處理棋子選擇與移動，返回(是否移動了棋子, 可能的移動列表)"""
        made_move = False
        moves = []
        
        # 檢查玩家是否可以移動棋子
        if self.is_game_over or self.ai_thinking:
            return False, []
            
        # 在雙人模式中，任何顏色都可以移動
        # 在AI模式中，只有白方可以移動
        if self.mode == GameMode.PLAYER_VS_AI and self.board.turn != chess.WHITE:
            return False, []
        
        piece = self.board.piece_at(sq)
        
        # 若尚未選擇棋子，則選擇一個屬於當前玩家的棋子
        if self.selected_square is None:
            if piece and piece.color == self.board.turn:
                self.selected_square = sq
                # 計算所有可能的移動
                moves = [m for m in self.board.legal_moves if m.from_square == sq]
        else:
            # 如果點擊自己的棋子，更新選擇
            if piece and piece.color == self.board.turn:
                self.selected_square = sq
                moves = [m for m in self.board.legal_moves if m.from_square == sq]
            else:
                # 嘗試移動到目標位置
                move = self._create_move(self.selected_square, sq)
                    
                if move in self.board.legal_moves:
                    with self.mutex:
                        self._make_move(move)
                        made_move = True
                        
                # 無論如何，取消選中狀態
                self.selected_square = None
                
        return made_move, moves
    
    def _create_move(self, from_sq: int, to_sq: int) -> chess.Move:
        """創建移動，處理升變等特殊情況"""
        piece = self.board.piece_at(from_sq)
        
        # 處理升變 (例如兵變后)
        if (piece and piece.piece_type == chess.PAWN and 
            chess.square_rank(to_sq) in [0, 7]):
            # 可以添加一個UI讓玩家選擇升變
            return chess.Move(from_sq, to_sq, promotion=chess.QUEEN)
        else:
            return chess.Move(from_sq, to_sq)
    
    def _make_move(self, move: chess.Move) -> None:
        """執行一個移動，並更新遊戲狀態"""
        self.board.push(move)
        self.move_history.append(move)
        
        # 檢查遊戲是否結束
        if self.board.is_game_over():
            self.is_game_over = True
            self._update_result_message()
    
    def _update_result_message(self) -> None:
        """更新遊戲結果訊息"""
        result = self.board.result()
        if result == '1-0':
            self.result_message = '白方勝利!'
        elif result == '0-1':
            self.result_message = '黑方勝利!'
        elif result == '1/2-1/2':
            self.result_message = '和局!'
    
    def undo_move(self) -> bool:
        """撤銷上一步移動"""
        with self.mutex:
            if not self.is_game_over and self.move_history:
                if self.mode == GameMode.PLAYER_VS_AI:
                    # 在對弈AI時，需要撤銷兩步（玩家和AI的）
                    if len(self.move_history) >= 2:
                        self.board.pop()
                        self.board.pop()
                        self.move_history.pop()
                        self.move_history.pop()
                        return True
                else:
                    # 雙人模式只撤銷一步
                    self.board.pop()
                    self.move_history.pop()
                    return True
            return False
    
    def start_ai_move(self) -> None:
        """啟動AI思考線程"""
        if not self.is_game_over and not self.ai_thinking and self.mode == GameMode.PLAYER_VS_AI:
            self.ai_thinking = True
            threading.Thread(target=self._ai_thread, daemon=True).start()
            
    def _ai_thread(self) -> None:
        """AI思考線程函數"""
        time.sleep(0.5)  # 稍微延遲讓玩家看到自己的移動
        
        with self.mutex:
            if self.is_game_over or self.board.turn != chess.BLACK:
                self.ai_thinking = False
                return
                
            try:
                # 計算 AI 的移動
                depth = self.difficulty.value
                move = self.find_best_move(depth)
                
                # 如果找到合法移動就執行
                if move:
                    self._make_move(move)
                    self.ai_move = move
            except Exception as e:
                print(f"AI thinking wrong: {e}")
                
        self.ai_thinking = False
    
    def _is_endgame(self) -> bool:
        """判斷是否是殘局階段"""
        # 殘局定義: 雙方後都沒了，或者一方只剩國王和一些小子
        queens = len(self.board.pieces(chess.QUEEN, chess.WHITE)) + \
                 len(self.board.pieces(chess.QUEEN, chess.BLACK))
        total_pieces = sum(len(list(self.board.pieces(piece_type, color))) 
                          for piece_type in chess.PIECE_TYPES
                          for color in [chess.WHITE, chess.BLACK])
        return queens == 0 or total_pieces <= 10
    
    def evaluate_board(self) -> int:
        """評估當前棋盤局勢，返回分數（正值有利於白方，負值有利於黑方）"""
        # 檢查遊戲終結狀態
        if self.board.is_checkmate():
            return -10000 if self.board.turn else 10000
        if self.board.is_stalemate() or self.board.is_insufficient_material():
            return 0
            
        # 是否殘局
        is_endgame = self._is_endgame()
        
        # 1. 材料價值計算
        w_material = 0
        b_material = 0
        
        # 2. 位置評估計算
        w_position = 0
        b_position = 0
        
        # 遍歷棋盤上的每個棋子
        for sq in chess.SQUARES:
            piece = self.board.piece_at(sq)
            if not piece:
                continue
            
            piece_type = piece.piece_type
            piece_value = self.PIECE_VALS[piece_type]
            
            # 翻轉黑方的位置索引（因為位置表是從白方視角定義的）
            pos_idx = sq if piece.color == chess.WHITE else chess.square_mirror(sq)
            
            # 使用國王的殘局評估表
            if piece_type == chess.KING and is_endgame:
                position_value = self.POSITION_TABLES[chess.KING + 100][pos_idx]
            else:
                position_value = self.POSITION_TABLES.get(piece_type, [0] * 64)[pos_idx]
            
            if piece.color == chess.WHITE:
                w_material += piece_value
                w_position += position_value
            else:
                b_material += piece_value
                b_position += position_value
        
        # 3. 機動性（可移動選項數量）
        if self.board.turn == chess.WHITE:
            w_mobility = len(list(self.board.legal_moves)) * 5
            # 儲存當前局面
            current_state = self.board.fen()
            # 嘗試一個空移動來切換到黑方
            self.board.push(chess.Move.null())
            b_mobility = len(list(self.board.legal_moves)) * 5
            # 恢復到原始局面
            self.board.pop()
            assert self.board.fen() == current_state
        else:
            b_mobility = len(list(self.board.legal_moves)) * 5
            # 儲存當前局面
            current_state = self.board.fen()
            # 嘗試一個空移動來切換到白方
            self.board.push(chess.Move.null())
            w_mobility = len(list(self.board.legal_moves)) * 5
            # 恢復到原始局面
            self.board.pop()
            assert self.board.fen() == current_state
        
        # 4. 王車易位價值
        castling_value = 0
        if self.board.has_castling_rights(chess.WHITE):
            castling_value += 60
        if self.board.has_castling_rights(chess.BLACK):
            castling_value -= 60
            
        # 5. 雙兵懲罰 (penalty for doubled pawns)
        doubled_pawns_penalty = 15
        for file in range(8):
            w_pawns_in_file = 0
            b_pawns_in_file = 0
            for rank in range(8):
                sq = chess.square(file, rank)
                piece = self.board.piece_at(sq)
                if piece and piece.piece_type == chess.PAWN:
                    if piece.color == chess.WHITE:
                        w_pawns_in_file += 1
                    else:
                        b_pawns_in_file += 1
            
            # 懲罰雙兵
            if w_pawns_in_file > 1:
                w_position -= (w_pawns_in_file - 1) * doubled_pawns_penalty
            if b_pawns_in_file > 1:
                b_position -= (b_pawns_in_file - 1) * doubled_pawns_penalty
            
        # 綜合評分
        material_score = w_material - b_material
        position_score = w_position - b_position
        mobility_score = w_mobility - b_mobility
        
        total_score = material_score + position_score + mobility_score + castling_value
        
        # 加入隨機性，防止AI行為過於機械化
        total_score += random.randint(-10, 10)
        
        return total_score
    
    def minimax(self, depth: int, alpha: float, beta: float, maximizing: bool, 
               quiescence: bool = False) -> float:
        """使用極小化極大演算法搜尋最佳移動分數"""
        # 置換表查詢
        board_hash = self.board.fen()
        if not quiescence and board_hash in self.transposition_table and \
           self.transposition_table[board_hash][0] >= depth:
            return self.transposition_table[board_hash][1]
        
        # 基本情況：到達搜尋深度或遊戲結束
        if depth == 0 or self.board.is_game_over():
            if quiescence and not self.board.is_game_over():
                # 靜態評估 - 只考慮吃子移動
                return self._quiescence_search(alpha, beta, 3)  # 深度限制為3
            return self.evaluate_board()
            
        # 獲取合法移動並優先考慮可能更好的移動
        moves = list(self.board.legal_moves)
        moves = self._order_moves(moves) if not quiescence else moves
            
        # 最大化玩家（白方）
        if maximizing:
            max_eval = float('-inf')
            for move in moves:
                self.board.push(move)
                eval = self.minimax(depth-1, alpha, beta, False, quiescence)
                self.board.pop()
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:  # Alpha-Beta 剪枝
                    break
            
            # 儲存結果到置換表
            if not quiescence:
                self.transposition_table[board_hash] = (depth, max_eval)
                
            return max_eval
        # 最小化玩家（黑方）
        else:
            min_eval = float('inf')
            for move in moves:
                self.board.push(move)
                eval = self.minimax(depth-1, alpha, beta, True, quiescence)
                self.board.pop()
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:  # Alpha-Beta 剪枝
                    break
                    
            # 儲存結果到置換表
            if not quiescence:
                self.transposition_table[board_hash] = (depth, min_eval)
                
            return min_eval
    
    def _quiescence_search(self, alpha: float, beta: float, depth: int) -> float:
        """靜態搜尋 - 只看吃子移動，避免水平效應"""
        # 基本評估
        stand_pat = self.evaluate_board()
        
        # Beta剪枝
        if stand_pat >= beta:
            return beta
            
        # Alpha調整
        if alpha < stand_pat:
            alpha = stand_pat
            
        # 如果達到深度限制，返回評估值
        if depth == 0:
            return stand_pat
            
        # 只考慮吃子移動
        capturing_moves = [move for move in self.board.legal_moves if self.board.is_capture(move)]
        capturing_moves = self._order_moves(capturing_moves)
        
        for move in capturing_moves:
            self.board.push(move)
            score = -self._quiescence_search(-beta, -alpha, depth - 1)
            self.board.pop()
            
            if score >= beta:
                return beta
            if score > alpha:
                alpha = score
                
        return alpha
        
    def _order_moves(self, moves: List[chess.Move]) -> List[chess.Move]:
        """對移動進行排序，以提高Alpha-Beta剪枝效率"""
        scored_moves = []
        
        for move in moves:
            score = 0
            
            # 吃子移動評分
            if self.board.is_capture(move):
                # 計算 MVV-LVA (Most Valuable Victim - Least Valuable Aggressor)
                victim_piece = self.board.piece_at(move.to_square)
                aggressor_piece = self.board.piece_at(move.from_square)
                
                if victim_piece and aggressor_piece:
                    # 吃高價值棋子的低價值棋子得分更高
                    victim_value = self.PIECE_VALS[victim_piece.piece_type]
                    aggressor_value = self.PIECE_VALS[aggressor_piece.piece_type]
                    score = 10 * victim_value - aggressor_value
            
            # 升變移動
            if move.promotion:
                score += 900  # 升級為后的分數
                
            # 棋子移動到好位置（使用位置表）
            piece = self.board.piece_at(move.from_square)
            if piece:
                # 使用位置評估表來評估移動的好壞
                to_sq = move.to_square
                if piece.color == chess.BLACK:
                    to_sq = chess.square_mirror(to_sq)
                    
                position_score = self.POSITION_TABLES.get(piece.piece_type, [0] * 64)[to_sq]
                score += position_score
                
            scored_moves.append((move, score))
            
        # 根據分數降序排列移動
        scored_moves.sort(key=lambda x: x[1], reverse=True)
        return [move for move, _ in scored_moves]
    
    def find_best_move(self, depth: int) -> Optional[chess.Move]:
        """尋找目前局勢下的最佳移動"""
        # 如果遊戲已結束或沒有合法移動，返回 None
        if self.board.is_game_over():
            return None
            
        legal_moves = list(self.board.legal_moves)
        if not legal_moves:
            return None
            
        # 對移動進行排序，以提高搜尋效率
        legal_moves = self._order_moves(legal_moves)
        
        best_move = None
        best_value = float('-inf') if self.board.turn == chess.WHITE else float('inf')
        alpha = float('-inf')
        beta = float('inf')
        
        # 對每個可能的移動進行評估
        for move in legal_moves:
            self.board.push(move)
            
            # 使用帶靜態評估的極小化極大搜尋
            if self.board.turn == chess.WHITE:  # 黑方剛移動，現在是白方回合
                value = self.minimax(depth-1, alpha, beta, True, True)
                if value < best_value:
                    best_value = value
                    best_move = move
                beta = min(beta, value)
            else:  # 白方剛移動，現在是黑方回合
                value = self.minimax(depth-1, alpha, beta, False, True)
                if value > best_value:
                    best_value = value
                    best_move = move
                alpha = max(alpha, value)
                
            self.board.pop()
            
            # Alpha-Beta 剪枝
            if alpha >= beta:
                break
        
        # 如果沒找到最佳移動，返回評估值最好的移動
        if best_move is None and legal_moves:
            best_move = legal_moves[0]
            
        return best_move
        
    def get_board_evaluation(self) -> int:
        """獲取當前棋盤評估分數"""
        return self.evaluate_board()
        
    def get_possible_moves(self, sq: int) -> List[chess.Move]:
        """獲取特定棋子的所有可能移動"""
        if sq is None:
            return []
        return [m for m in self.board.legal_moves if m.from_square == sq]


class ChessUI:
    """國際象棋遊戲界面類，負責繪製和處理用戶輸入"""
    
    # UI常數
    WIDTH = 640
    HEIGHT = 640
    BOARD_SIZE = 512
    SIDEBAR_WIDTH = WIDTH - BOARD_SIZE
    SQUARE_SIZE = BOARD_SIZE // 8
    
    # 顏色常數
    LIGHT_SQ_COLOR = (240, 217, 181)
    DARK_SQ_COLOR = (181, 136, 99)
    BG_COLOR = (50, 50, 50)
    TEXT_COLOR = (255, 255, 255)
    BUTTON_COLOR = (100, 100, 100)
    BUTTON_HOVER_COLOR = (130, 130, 130)
    BUTTON_TEXT_COLOR = (255, 255, 255)
    SELECTED_COLOR = (255, 255, 0, 100)
    MOVE_COLOR = (124, 252, 0, 180)
    LAST_MOVE_COLOR = (0, 191, 255, 120)
    
    def __init__(self, game: ChessGame):
        """初始化UI"""
        pygame.init()
        self.game = game
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("Chess")
        
        # 載入字體
        try:
            self.font = pygame.font.SysFont('Arial', 20)
            self.small_font = pygame.font.SysFont('Arial', 16)
            self.large_font = pygame.font.SysFont('Arial', 24)
            self.title_font = pygame.font.SysFont('Arial', 28, bold=True)
        except:
            self.font = pygame.font.Font(None, 24)
            self.small_font = pygame.font.Font(None, 18)
            self.large_font = pygame.font.Font(None, 30)
            self.title_font = pygame.font.Font(None, 36)
        
        # 載入棋子圖片
        self.piece_images = self._load_piece_images()
        
        # UI元素
        self.buttons = []
        self._create_ui_elements()
        
        # 遊戲時鐘
        self.clock = pygame.time.Clock()
        
    def _load_piece_images(self) -> Dict[str, pygame.Surface]:
        """載入棋子圖片"""
        images = {}
        pieces = ['wP','wR','wN','wB','wQ','wK','bP','bR','bN','bB','bQ','bK']
        asset_dir = os.path.join(os.path.dirname(__file__), 'assets')
        
        try:
            for p in pieces:
                path = os.path.join(asset_dir, f"{p}.png")
                if os.path.isfile(path):
                    img = pygame.image.load(path)
                    images[p] = pygame.transform.scale(img, (self.SQUARE_SIZE, self.SQUARE_SIZE))
        except FileNotFoundError as e:
            print(f"錯誤: {e}")
            print("找不到棋子圖片，使用簡易顯示模式")
            # 創建棋子的簡易顯示方式（文字代替圖片）
            for p in pieces:
                # 創建一個空白表面
                surface = pygame.Surface((self.SQUARE_SIZE, self.SQUARE_SIZE), pygame.SRCALPHA)
                color = (255, 255, 255) if p.startswith('w') else (0, 0, 0)
                # 畫一個圓形
                pygame.draw.circle(surface, color, (self.SQUARE_SIZE//2, self.SQUARE_SIZE//2), self.SQUARE_SIZE//2 - 5)
                # 在圓形中寫入棋子類型
                piece_letter = self.font.render(p[1], True, (255-color[0], 255-color[1], 255-color[2]))
                rect = piece_letter.get_rect(center=(self.SQUARE_SIZE//2, self.SQUARE_SIZE//2))
                surface.blit(piece_letter, rect)
                images[p] = surface
        
        return images
    
    def _create_ui_elements(self) -> None:
        """創建UI元素如按鈕"""
        # 側邊欄按鈕
        button_width = self.SIDEBAR_WIDTH - 20
        button_height = 30
        button_x = self.BOARD_SIZE + 10
        button_y_start = 50
        spacing = 15
        
        # 重置遊戲按鈕
        self.buttons.append({
            'rect': pygame.Rect(button_x, button_y_start, button_width, button_height),
            'text': 'restart',
            'action': 'reset'
        })
        
        # 撤銷移動按鈕
        self.buttons.append({
            'rect': pygame.Rect(button_x, button_y_start + button_height + spacing, 
                               button_width, button_height),
            'text': 'Undo Move',
            'action': 'undo'
        })
        
        # 切換難度按鈕
        difficulties = ['Easy', 'Normal', 'Difficult', 'Master']
        for i, diff in enumerate(difficulties):
            self.buttons.append({
                'rect': pygame.Rect(button_x, button_y_start + (i+2)*(button_height + spacing), 
                                   button_width, button_height),
                'text': f'{diff}',
                'action': f'difficulty_{i+1}',
                'highlight': i+2 == self.game.difficulty.value  # 高亮顯示當前難度
            })
        
        # 切換模式按鈕
        self.buttons.append({
            'rect': pygame.Rect(button_x, button_y_start + 6*(button_height + spacing), 
                               button_width, button_height),
            'text': 'AI Battle' if self.game.mode == GameMode.PLAYER_VS_AI else 'Two-player battle',
            'action': 'toggle_mode'
        })
        
    def draw_board(self) -> None:
        """繪製棋盤、棋子和移動提示"""
        # 繪製棋盤格子
        for row in range(8):
            for col in range(8):
                sq = chess.square(col, 7 - row)
                color = self.LIGHT_SQ_COLOR if (row + col) % 2 == 0 else self.DARK_SQ_COLOR
                pygame.draw.rect(self.screen, color, (col*self.SQUARE_SIZE, row*self.SQUARE_SIZE, 
                                                     self.SQUARE_SIZE, self.SQUARE_SIZE))
                
        # 繪製最後一步移動的高亮
        if self.game.move_history:
            last_move = self.game.move_history[-1]
            # 高亮顯示起點和終點
            for sq in [last_move.from_square, last_move.to_square]:
                col, row = chess.square_file(sq), 7 - chess.square_rank(sq)
                s = pygame.Surface((self.SQUARE_SIZE, self.SQUARE_SIZE), pygame.SRCALPHA)
                s.fill(self.LAST_MOVE_COLOR)
                self.screen.blit(s, (col*self.SQUARE_SIZE, row*self.SQUARE_SIZE))
        
        # 繪製選中棋子的高亮
        if self.game.selected_square is not None:
            col = chess.square_file(self.game.selected_square)
            row = 7 - chess.square_rank(self.game.selected_square)
            s = pygame.Surface((self.SQUARE_SIZE, self.SQUARE_SIZE), pygame.SRCALPHA)
            s.fill(self.SELECTED_COLOR)
            self.screen.blit(s, (col*self.SQUARE_SIZE, row*self.SQUARE_SIZE))
            
        # 繪製可移動位置的高亮
        moves = self.game.get_possible_moves(self.game.selected_square)
        for move in moves:
            sq = move.to_square
            col, row = chess.square_file(sq), 7 - chess.square_rank(sq)
            s = pygame.Surface((self.SQUARE_SIZE, self.SQUARE_SIZE), pygame.SRCALPHA)
            s.fill(self.MOVE_COLOR)
            self.screen.blit(s, (col*self.SQUARE_SIZE, row*self.SQUARE_SIZE))
                
        # 繪製棋子
        for sq in chess.SQUARES:
            p = self.game.board.piece_at(sq)
            if p:
                col = chess.square_file(sq)
                row = 7 - chess.square_rank(sq)
                key = ('w' if p.color == chess.WHITE else 'b') + p.symbol().upper()
                self.screen.blit(self.piece_images[key], (col*self.SQUARE_SIZE, row*self.SQUARE_SIZE))
                
        # 繪製座標標籤
        for i in range(8):
            file_txt = self.small_font.render(chess.FILE_NAMES[i], True, (200,200,200))
            rank_txt = self.small_font.render(str(i+1), True, (200,200,200))
            self.screen.blit(file_txt, (i*self.SQUARE_SIZE + self.SQUARE_SIZE - 15, self.BOARD_SIZE - 15))
            self.screen.blit(rank_txt, (5, (7-i)*self.SQUARE_SIZE + 5))
    
    def draw_sidebar(self) -> None:
        """繪製側邊欄信息和按鈕"""
        # 填充側邊欄背景
        pygame.draw.rect(self.screen, self.BG_COLOR, 
                        (self.BOARD_SIZE, 0, self.SIDEBAR_WIDTH, self.HEIGHT))
        
        # 繪製遊戲狀態信息
        title = self.title_font.render("Chess", True, self.TEXT_COLOR)
        self.screen.blit(title, (self.BOARD_SIZE + 10, 10))
        
        # 繪製當前玩家
        turn_text = "White Round" if self.game.board.turn == chess.WHITE else "Black Round"
        turn_surface = self.font.render(turn_text, True, self.TEXT_COLOR)
        self.screen.blit(turn_surface, (self.BOARD_SIZE + 10, self.HEIGHT - 60))
        
        # 繪製AI思考狀態
        if self.game.ai_thinking:
            thinking_text = self.font.render("AI Thinking...", True, self.TEXT_COLOR)
            self.screen.blit(thinking_text, (self.BOARD_SIZE + 10, self.HEIGHT - 30))
        
        # 繪製評估分數
        if not self.game.is_game_over:
            eval_score = self.game.get_board_evaluation()
            eval_text = f"Evaluate: {eval_score:+}"
            eval_surface = self.font.render(eval_text, True, self.TEXT_COLOR)
            self.screen.blit(eval_surface, (self.BOARD_SIZE + 10, self.HEIGHT - 90))
        
        # 繪製按鈕
        mouse_pos = pygame.mouse.get_pos()
        for button in self.buttons:
            # 檢查滑鼠是否懸停在按鈕上
            if button['rect'].collidepoint(mouse_pos):
                color = self.BUTTON_HOVER_COLOR
            else:
                color = self.BUTTON_COLOR
            
            # 高亮當前選中的選項
            if button.get('highlight', False):
                color = (100, 150, 100)
                
            pygame.draw.rect(self.screen, color, button['rect'])
            pygame.draw.rect(self.screen, (200, 200, 200), button['rect'], 1)  # 邊框
            
            # 繪製按鈕文字
            text_surf = self.font.render(button['text'], True, self.BUTTON_TEXT_COLOR)
            text_rect = text_surf.get_rect(center=button['rect'].center)
            self.screen.blit(text_surf, text_rect)
    
    def show_game_over(self) -> None:
        """顯示遊戲結束信息"""
        # 半透明覆蓋層
        overlay = pygame.Surface((self.BOARD_SIZE, self.BOARD_SIZE))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # 顯示勝負結果
        text = self.large_font.render(self.game.result_message, True, (255,255,255))
        rect = text.get_rect(center=(self.BOARD_SIZE//2, self.BOARD_SIZE//2))
        self.screen.blit(text, rect)
        
        restart = self.font.render('Press R to restart', True, (255,255,255))
        rs_rect = restart.get_rect(center=(self.BOARD_SIZE//2, self.BOARD_SIZE//2+40))
        self.screen.blit(restart, rs_rect)
    
    def handle_click(self, pos: Tuple[int, int]) -> None:
        """處理滑鼠點擊事件"""
        x, y = pos
        
        # 點擊在棋盤上
        if x < self.BOARD_SIZE and y < self.BOARD_SIZE:
            col = x // self.SQUARE_SIZE
            row = 7 - (y // self.SQUARE_SIZE)
            
            # 確保座標在合法範圍內
            if 0 <= col < 8 and 0 <= row < 8:
                sq = chess.square(col, row)
                made_move, _ = self.game.handle_square_selection(sq)
                
                # 如果是AI模式且玩家剛移動，啟動AI思考
                if made_move and self.game.mode == GameMode.PLAYER_VS_AI and not self.game.is_game_over:
                    self.game.start_ai_move()
        
        # 點擊在側邊欄上
        else:
            # 檢查按鈕點擊
            for button in self.buttons:
                if button['rect'].collidepoint(pos):
                    self.handle_button_action(button['action'])
                    break
    
    def handle_button_action(self, action: str) -> None:
        """處理按鈕動作"""
        if action == 'reset':
            self.game.reset()
            self._create_ui_elements()  # 更新UI元素狀態
            
        elif action == 'undo':
            self.game.undo_move()
            
        elif action.startswith('difficulty_'):
            difficulty_level = int(action.split('_')[1])
            if difficulty_level == 1:
                self.game.difficulty = Difficulty.EASY
            elif difficulty_level == 2:
                self.game.difficulty = Difficulty.MEDIUM
            elif difficulty_level == 3:
                self.game.difficulty = Difficulty.HARD
            elif difficulty_level == 4:
                self.game.difficulty = Difficulty.MASTER
            self._create_ui_elements()  # 更新UI元素狀態
            
        elif action == 'toggle_mode':
            if self.game.mode == GameMode.PLAYER_VS_AI:
                self.game.mode = GameMode.PLAYER_VS_PLAYER
            else:
                self.game.mode = GameMode.PLAYER_VS_AI
            self._create_ui_elements()  # 更新UI元素狀態
    
    def draw(self) -> None:
        """繪製整個遊戲畫面"""
        # 清空畫面
        self.screen.fill(self.BG_COLOR)
        
        # 繪製棋盤和棋子
        self.draw_board()
        
        # 繪製側邊欄
        self.draw_sidebar()
        
        # 如果遊戲結束，顯示結果
        if self.game.is_game_over:
            self.show_game_over()
            
        # 更新畫面
        pygame.display.flip()
    
    def run(self) -> None:
        """執行遊戲主循環"""
        running = True
        
        while running:
            # 處理事件
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    
                # 重新開始遊戲
                if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                    self.game.reset()
                    self._create_ui_elements()
                    
                # 處理滑鼠點擊
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_click(event.pos)
            
            # 繪製畫面
            self.draw()
            
            # 控制幀率
            self.clock.tick(60)
        
        # 結束遊戲
        pygame.quit()
        sys.exit()


def main() -> None:
    """程式入口點"""
    # 創建遊戲實例
    game = ChessGame(mode=GameMode.PLAYER_VS_AI, difficulty=Difficulty.MEDIUM)
    
    # 創建UI實例
    ui = ChessUI(game)
    
    # 執行遊戲
    ui.run()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()
        pygame.quit()
        sys.exit(1)
