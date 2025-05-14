強化西洋棋 AI

這是一個基於 Pygame 與 python-chess 的簡易西洋棋遊戲，結合強化評估函數與 Minimax + αβ 剪枝，實現人機對戰功能。

主要功能:

* 玩家與 AI 對戰，白方由玩家操作，黑方由 AI 控制
* 強化評估函數：整合物質價值、位置價值（PST）與流動性評分
* 搜尋演算法：Minimax 結合 αβ 剪枝，並優先處理吃子和升變走法
* 圖形化介面：使用 Pygame 繪製棋盤、棋子以及合法走法標示
* 重啟遊戲：按下 R 鍵可重新開始

檔案結構:

* assets 資料夾：存放所有棋子圖檔，檔名為 wP.png, bK.png 等共 12 種
* chess\_gui.py：遊戲主程式
* README（本檔）：專案說明

環境需求:

* Python 3.12 或更新版本
* Pygame
* python-chess

安裝步驟:

1. 進入專案資料夾
2. 執行 pip install pygame python-chess
3. 確認 assets 資料夾中含有 12 種棋子圖檔

執行方式:
使用對應 Python 直譯器執行 chess\_gui.py，例如：
python chess\_gui.py

操作說明:

* 移動棋子：先點擊要移動的棋子，再點擊目標格子
* 重啟棋局：按下 R 鍵
* 結束程式：關閉視窗

AI 強度調整:
在程式中修改 ai\_depth 參數，數值越大 AI 思考時間越長但棋力越強。

後續改進建議:

* 為所有棋子加入位置權重表（PST）
* 實作 Quiescence Search 以避免地平線效應
* 使用置換表（Transposition Table）降低重複計算
* 採用 Iterative Deepening，允許設定思考時間上限

歡迎提出建議和改進方案。
