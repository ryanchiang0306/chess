import pygame
import chess
import random
import time
import sys
import os
import threading

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

# ===== 建立視窗 =====
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("簡易西洋棋")

# ===== 字體 =====ntry:
try:
    font = pygame.font.SysFont('Arial', 24)
    small_font = pygame.font.SysFont('Arial', 18)
except:
    font = pygame.font.Font(None, 24)
    small_font = pygame.font.Font(None, 18)

# ===== 載入棋子圖片 =====
def load_piece_images():
    images = {}
    pieces = ['wP','wR','wN','wB','wQ','wK','bP','bR','bN','bB','bQ','bK']
    asset_dir = os.path.join(os.path.dirname(__file__), 'assets')
    for p in pieces:
        path = os.path.join(asset_dir, f"{p}.png")
        if os.path.isfile(path):
            img = pygame.image.load(path)
            images[p] = pygame.transform.scale(img, (SQUARE_SIZE, SQUARE_SIZE))
        else:
            raise FileNotFoundError(f"Cannot find asset: {path}")
    return images

piece_images = load_piece_images()

# ===== 繪製棋盤與棋子 =====
def draw_board(board, selected_sq=None, moves_highlight=None):
    for row in range(8):
        for col in range(8):
            sq = chess.square(col, 7 - row)
            color = LIGHT_SQ_COLOR if (row + col) % 2 == 0 else DARK_SQ_COLOR
            pygame.draw.rect(screen, color, (col*SQUARE_SIZE, row*SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
            # 選中方格
            if selected_sq == sq:
                s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                s.fill((255, 255, 0, 100))
                screen.blit(s, (col*SQUARE_SIZE, row*SQUARE_SIZE))
            # 可走位置
            if moves_highlight and any(m.to_square == sq for m in moves_highlight):
                s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                s.fill((0, 255, 0, 100))
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
        rank_txt = small_font.render(str(8-i), True, (200,200,200))
        screen.blit(file_txt, (i*SQUARE_SIZE + SQUARE_SIZE - 15, BOARD_SIZE - 15))
        screen.blit(rank_txt, (5, i*SQUARE_SIZE + 5))

# ===== 處理遊戲結束訊息 =====
def show_game_over(result):
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(180)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))
    if result == '1-0':
        msg = '白方勝利!'
    elif result == '0-1':
        msg = '黑方勝利!'
    else:
        msg = '和局!'
    text = font.render(msg, True, (255,255,255))
    rect = text.get_rect(center=(WIDTH//2, HEIGHT//2))
    screen.blit(text, rect)
    restart = small_font.render('按 R 重新開始', True, (255,255,255))
    rs_rect = restart.get_rect(center=(WIDTH//2, HEIGHT//2+30))
    screen.blit(restart, rs_rect)
    pygame.display.flip()

# ===== 極小化極大 + αβ 搜尋 =====
PIECE_VALS = {chess.PAWN:100, chess.KNIGHT:320, chess.BISHOP:330, chess.ROOK:500, chess.QUEEN:900, chess.KING:20000}
def evaluate_board(board):
    if board.is_checkmate():
        return -9999 if board.turn else 9999
    if board.is_stalemate():
        return 0
    w = sum(len(board.pieces(pt, chess.WHITE))*v for pt,v in PIECE_VALS.items())
    b = sum(len(board.pieces(pt, chess.BLACK))*v for pt,v in PIECE_VALS.items())
    return w - b

def minimax(board, depth, alpha, beta, maxP):
    if depth==0 or board.is_game_over(): return evaluate_board(board)
    if maxP:
        val = -float('inf')
        for m in board.legal_moves:
            board.push(m)
            val = max(val, minimax(board, depth-1, alpha, beta, False))
            board.pop()
            alpha = max(alpha,val)
            if beta<=alpha: break
        return val
    else:
        val = float('inf')
        for m in board.legal_moves:
            board.push(m)
            val = min(val, minimax(board, depth-1, alpha, beta, True))
            board.pop()
            beta = min(beta,val)
            if beta<=alpha: break
        return val

def find_best_move(board, depth):
    best=None
    best_eval = -float('inf') if board.turn==chess.WHITE else float('inf')
    for m in board.legal_moves:
        board.push(m)
        score = minimax(board, depth-1, -float('inf'), float('inf'), board.turn==chess.WHITE)
        board.pop()
        if (board.turn==chess.WHITE and score>best_eval) or (board.turn==chess.BLACK and score<best_eval):
            best_eval, best = score, m
    if not best and list(board.legal_moves): best = random.choice(list(board.legal_moves))
    return best

# ===== 主程式 =====
def main():
    board = chess.Board()
    selected = None
    ai_thinking=False
    game_over=False
    ai_depth=2
    running=True
    # AI 首次思考
    def ai_thread():
        nonlocal ai_thinking
        time.sleep(0.5)
        move = find_best_move(board, ai_depth)
        if move: board.push(move)
        ai_thinking=False
    while running:
        for e in pygame.event.get():
            if e.type==pygame.QUIT: running=False
            if e.type==pygame.KEYDOWN and e.key==pygame.K_r:
                board=chess.Board(); selected=None; game_over=False
            if e.type==pygame.MOUSEBUTTONDOWN and board.turn==chess.WHITE and not ai_thinking and not game_over:
                x,y=e.pos; col=x//SQUARE_SIZE; row=7-(y//SQUARE_SIZE)
                sq=chess.square(col,row)
                if selected is None:
                    p=board.piece_at(sq)
                    if p and p.color==chess.WHITE: selected=sq
                else:
                    mv=chess.Move(selected,sq)
                    if board.piece_at(selected).piece_type==chess.PAWN and ((sq//8==7) or (sq//8==0)):
                        mv=chess.Move(selected,sq,promotion=chess.QUEEN)
                    if mv in board.legal_moves:
                        board.push(mv)
                        ai_thinking=True
                        threading.Thread(target=ai_thread, daemon=True).start()
                    selected=None
        if not game_over and board.is_game_over(): game_over=True
        screen.fill(BG_COLOR)
        moves=[m for m in board.legal_moves if selected and m.from_square==selected]
        draw_board(board, selected, moves)
        if ai_thinking:
            t=small_font.render('AI THINKING...',True,(255,255,255))
            screen.blit(t,(10,HEIGHT-30))
        if game_over: show_game_over(board.result())
        pygame.display.flip() ; pygame.time.wait(50)
    pygame.quit(); sys.exit()

if __name__=='__main__':
    main()