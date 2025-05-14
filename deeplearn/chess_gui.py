import pygame
import chess
import random
import time
import sys
import os
import threading
from typing import List, Optional, Tuple

# ===== 初始化 pygame =====
pygame.init()

# ===== 遊戲常數 =====
WIDTH, HEIGHT = 512, 512
BOARD_SIZE = WIDTH
SQUARE_SIZE = BOARD_SIZE // 8
LIGHT_SQ_COLOR = (240, 217, 181)
DARK_SQ_COLOR = (181, 136, 99)
HIGHLIGHT_COLOR = (124, 252, 0, 180)
BG_COLOR = (50, 50, 50)
SELECTED_COLOR = (255, 255, 0, 100)  # 選中格子的顏色
MOVE_COLOR = (0, 255, 0, 100)        # 可走位置的顏色

# ===== 建立視窗 =====
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("國際象棋")

# ===== 字體 =====
try:
    font = pygame.font.SysFont('Arial', 24)
    small_font = pygame.font.SysFont('Arial', 18)
except:
    font = pygame.font.Font(None, 24)
    small_font = pygame.font.Font(None, 18)

# ===== 棋子評估值 =====
PIECE_VALS = {
    chess.PAWN: 100, 
    chess.KNIGHT: 320, 
    chess.BISHOP: 330, 
    chess.ROOK: 500, 
    chess.QUEEN: 900, 
    chess.KING: 20000
}

# ===== 載入棋子圖片 =====
def load_piece_images() -> dict:
    """載入棋子圖片並返回包含所有棋子圖片的字典"""
    images = {}
    pieces = ['wP','wR','wN','wB','wQ','wK','bP','bR','bN','bB','bQ','bK']
    asset_dir = os.path.join(os.path.dirname(__file__), 'assets')
    
    for p in pieces:
        path = os.path.join(asset_dir, f"{p}.png")
        if os.path.isfile(path):
            img = pygame.image.load(path)
            images[p] = pygame.transform.scale(img, (SQUARE_SIZE, SQUARE_SIZE))
        else:
            raise FileNotFoundError(f"找不到資源檔案: {path}")
    return images

try:
    piece_images = load_piece_images()
except FileNotFoundError as e:
    print(f"錯誤: {e}")
    print("請確認 assets 資料夾中有所有必要的棋子圖片")
    pygame.quit()
    sys.exit(1)

# ===== 繪製棋盤與棋子 =====
def draw_board(board: chess.Board, selected_sq: Optional[int] = None, 
               moves_highlight: Optional[List[chess.Move]] = None) -> None:
    """繪製棋盤、棋子和高亮的移動選項"""
    # 繪製棋盤格子
    for row in range(8):
        for col in range(8):
            sq = chess.square(col, 7 - row)
            color = LIGHT_SQ_COLOR if (row + col) % 2 == 0 else DARK_SQ_COLOR
            pygame.draw.rect(screen, color, (col*SQUARE_SIZE, row*SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
    
    # 繪製高亮選項
    if selected_sq is not None:
        col, row = chess.square_file(selected_sq), 7 - chess.square_rank(selected_sq)
        s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
        s.fill(SELECTED_COLOR)
        screen.blit(s, (col*SQUARE_SIZE, row*SQUARE_SIZE))
        
    if moves_highlight:
        for move in moves_highlight:
            sq = move.to_square
            col, row = chess.square_file(sq), 7 - chess.square_rank(sq)
            s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            s.fill(MOVE_COLOR)
            screen.blit(s, (col*SQUARE_SIZE, row*SQUARE_SIZE))
                
    # 畫棋子
    for sq in chess.SQUARES:
        p = board.piece_at(sq)
        if p:
            col = chess.square_file(sq)
            row = 7 - chess.square_rank(sq)
            key = ('w' if p.color == chess.WHITE else 'b') + p.symbol().upper()
            screen.blit(piece_images[key], (col*SQUARE_SIZE, row*SQUARE_SIZE))
                
    # 畫座標標籤
    for i in range(8):
        file_txt = small_font.render(chess.FILE_NAMES[i], True, (200,200,200))
        rank_txt = small_font.render(str(i+1), True, (200,200,200))
        screen.blit(file_txt, (i*SQUARE_SIZE + SQUARE_SIZE - 15, BOARD_SIZE - 15))
        screen.blit(rank_txt, (5, (7-i)*SQUARE_SIZE + 5))

# ===== 處理遊戲結束訊息 =====
def show_game_over(result: str) -> None:
    """顯示遊戲結束訊息"""
    # 半透明覆蓋層
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(180)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))
    
    # 顯示勝負結果
    if result == '1-0':
        msg = '白方勝利!'
    elif result == '0-1':
        msg = '黑方勝利!'
    else:
        msg = '平局!'
        
    text = font.render(msg, True, (255,255,255))
    rect = text.get_rect(center=(WIDTH//2, HEIGHT//2))
    screen.blit(text, rect)
    
    restart = small_font.render('按 R 重新開始', True, (255,255,255))
    rs_rect = restart.get_rect(center=(WIDTH//2, HEIGHT//2+30))
    screen.blit(restart, rs_rect)

# ===== 評估棋盤局勢 =====
def evaluate_board(board: chess.Board) -> int:
    """評估當前棋盤局勢，返回分數（正值有利於白方，負值有利於黑方）"""
    if board.is_checkmate():
        return -10000 if board.turn else 10000
    if board.is_stalemate():
        return 0
        
    # 材料價值計算
    w_value = sum(len(board.pieces(pt, chess.WHITE)) * v for pt, v in PIECE_VALS.items())
    b_value = sum(len(board.pieces(pt, chess.BLACK)) * v for pt, v in PIECE_VALS.items())
    
    # 機動性（可移動選項數量）考量 - 給予額外分數
    mobility_bonus = 10
    w_mobility = len(list(board.generate_legal_moves())) if board.turn == chess.WHITE else 0
    b_mobility = len(list(board.generate_legal_moves())) if board.turn == chess.BLACK else 0
    
    # 中心控制考量
    center_squares = [chess.E4, chess.D4, chess.E5, chess.D5]
    w_center = sum(1 for sq in center_squares if board.piece_at(sq) and board.piece_at(sq).color == chess.WHITE)
    b_center = sum(1 for sq in center_squares if board.piece_at(sq) and board.piece_at(sq).color == chess.BLACK)
    center_bonus = 30  # 中心控制獎勵
    
    total_score = (w_value - b_value) + mobility_bonus * (w_mobility - b_mobility) + center_bonus * (w_center - b_center)
    return total_score

# ===== 極小化極大 + αβ 搜尋 =====
def minimax(board: chess.Board, depth: int, alpha: float, beta: float, maximizing: bool) -> float:
    """使用極小化極大演算法搜尋最佳移動分數"""
    # 基本情況：到達搜尋深度或遊戲結束
    if depth == 0 or board.is_game_over():
        return evaluate_board(board)
        
    # 最大化玩家（白方）
    if maximizing:
        max_eval = float('-inf')
        for move in board.legal_moves:
            board.push(move)
            eval = minimax(board, depth-1, alpha, beta, False)
            board.pop()
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:  # Alpha-Beta 剪枝
                break
        return max_eval
    # 最小化玩家（黑方）
    else:
        min_eval = float('inf')
        for move in board.legal_moves:
            board.push(move)
            eval = minimax(board, depth-1, alpha, beta, True)
            board.pop()
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:  # Alpha-Beta 剪枝
                break
        return min_eval

def find_best_move(board: chess.Board, depth: int) -> Optional[chess.Move]:
    """尋找目前局勢下的最佳移動"""
    # 如果遊戲已結束或沒有合法移動，返回 None
    if board.is_game_over():
        return None
        
    legal_moves = list(board.legal_moves)
    if not legal_moves:
        return None
        
    # 隨機打亂移動順序，避免AI每次都做相同的選擇
    random.shuffle(legal_moves)
    
    best_move = None
    best_value = float('-inf') if board.turn == chess.WHITE else float('inf')
    
    # 對每個可能的移動進行評估
    for move in legal_moves:
        board.push(move)
        # 根據當前玩家進行極小化極大搜尋
        if board.turn == chess.WHITE:  # 黑方剛移動，現在是白方回合
            value = minimax(board, depth-1, float('-inf'), float('inf'), True)
            if value < best_value:
                best_value = value
                best_move = move
        else:  # 白方剛移動，現在是黑方回合
            value = minimax(board, depth-1, float('-inf'), float('inf'), False)
            if value > best_value:
                best_value = value
                best_move = move
        board.pop()
    
    # 如果沒找到最佳移動，隨機選一個
    if best_move is None and legal_moves:
        best_move = random.choice(legal_moves)
        
    return best_move

# ===== 主程式 =====
def main() -> None:
    """遊戲主循環"""
    board = chess.Board()
    selected = None
    ai_thinking = False
    game_over = False
    ai_depth = 2  # 調整深度來平衡思考時間和強度
    running = True
    mutex = threading.Lock()
    
    # AI 思考線程
    def ai_thread() -> None:
        nonlocal ai_thinking, game_over, board
        
        time.sleep(0.3)  # 稍微延遲讓玩家看到自己的移動
        
        with mutex:
            if game_over or board.turn != chess.BLACK:
                ai_thinking = False
                return
                
            try:
                # 計算 AI 的移動
                move = find_best_move(board, ai_depth)
                
                # 如果找到合法移動就執行
                if move:
                    board.push(move)
                    
                    # AI 落子後檢查是否結束遊戲
                    if board.is_game_over():
                        game_over = True
            except Exception as e:
                print(f"AI 思考錯誤: {e}")
                
        ai_thinking = False
    
    # 記錄幀率和效能
    clock = pygame.time.Clock()
    
    # 主遊戲迴圈
    while running:
        # 處理事件
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            # 重新開始遊戲
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                with mutex:
                    board = chess.Board()
                    selected = None
                    game_over = False
                    ai_thinking = False
                    
            # 處理滑鼠點擊
            if (event.type == pygame.MOUSEBUTTONDOWN and 
                board.turn == chess.WHITE and 
                not ai_thinking and 
                not game_over):
                
                x, y = event.pos
                col = x // SQUARE_SIZE
                row = 7 - (y // SQUARE_SIZE)
                
                # 確保座標在合法範圍內
                if 0 <= col < 8 and 0 <= row < 8:
                    sq = chess.square(col, row)
                    
                    # 第一次點擊選擇棋子
                    if selected is None:
                        piece = board.piece_at(sq)
                        if piece and piece.color == chess.WHITE:
                            selected = sq
                            
                    # 第二次點擊移動棋子
                    else:
                        # 如果點擊自己的棋子，更新選擇
                        piece = board.piece_at(sq)
                        if piece and piece.color == chess.WHITE:
                            selected = sq
                            continue
                            
                        # 創建移動
                        move = None
                        
                        # 處理升變 (例如兵變后)
                        if (board.piece_at(selected) and 
                            board.piece_at(selected).piece_type == chess.PAWN and 
                            chess.square_rank(sq) in [0, 7]):
                            move = chess.Move(selected, sq, promotion=chess.QUEEN)
                        else:
                            move = chess.Move(selected, sq)
                            
                        # 如果移動合法，執行它
                        if move in board.legal_moves:
                            with mutex:
                                board.push(move)
                                
                                # 檢查遊戲是否結束
                                if board.is_game_over():
                                    game_over = True
                                else:
                                    # 觸發 AI 思考
                                    ai_thinking = True
                                    threading.Thread(target=ai_thread, daemon=True).start()
                                    
                        # 無論如何，取消選中狀態
                        selected = None
        
        # 檢查遊戲是否結束（在線程外再次檢查）
        with mutex:
            if not game_over and board.is_game_over():
                game_over = True
        
        # 繪製畫面
        screen.fill(BG_COLOR)
        
        # 計算選中棋子的可能移動
        moves = []
        if selected is not None:
            moves = [m for m in board.legal_moves if m.from_square == selected]
            
        # 繪製棋盤和棋子
        draw_board(board, selected, moves)
        
        # 顯示當前玩家
        turn_text = small_font.render('白方回合' if board.turn == chess.WHITE else '黑方回合', True, (255, 255, 255))
        screen.blit(turn_text, (10, HEIGHT - 50))
        
        # 如果 AI 正在思考，顯示提示
        if ai_thinking:
            thinking_text = small_font.render('AI 思考中...', True, (255, 255, 255))
            screen.blit(thinking_text, (10, HEIGHT - 30))
            
        # 如果遊戲結束，顯示結果
        if game_over:
            show_game_over(board.result())
            
        # 更新畫面並控制幀率
        pygame.display.flip()
        clock.tick(60)  # 限制最大幀率為60FPS
    
    # 結束遊戲
    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()
