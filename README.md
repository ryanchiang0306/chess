# Chess 遊戲 README

## 專案介紹

這是一款以 Python 開發的國際象棋遊戲，結合了 AI 與雙人對弈功能，使用 `pygame` 作為圖形介面，並利用 `python-chess` 庫處理棋盤邏輯與走法判斷。

## 功能特色

* **單人對 AI**：內建多種難度（Easy、Medium、Hard、Master），採用 Minimax + Alpha-Beta 剪枝與靜態搜索（Quiescence Search）。
* **雙人對弈**：同螢幕下雙人對戰模式。
* **走步提示**：玩家選中棋子後，自動高亮可行走的步數。
* **悔棋功能**：支援在雙人模式上一手悔棋，AI 模式悔棋會同時回退玩家與 AI 的兩步。
* **遊戲評估**：即時顯示棋盤評估分數，幫助玩家掌握局勢。
* **結果顯示**：遊戲結束後顯示勝負或和局訊息，並支援重新開始。

## 安裝需求

* Python 3.8 以上
* `pygame`
* `python-chess`

可透過以下指令一次安裝：

```bash
pip install pygame python-chess
```

## 快速上手

1. 下載或 Clone 本專案至本機：

   ```bash
   https://github.com/ryanchiang0306/chess.git
   ```

git clone [https://github.com/yourname/chess-game.git](https://github.com/yourname/chess-game.git)
cd chess-game

````
2. 安裝相依套件（見上方）。
3. 在專案根目錄執行：
   ```bash
python main.py
````

或者：

```bash
python chess_game.py
```

4. 遊戲介面啟動後，根據提示選擇遊戲模式與難度，開始對弈！

## 操作說明

* **選擇棋子**：滑鼠左鍵點擊棋盤上的棋子。
* **移動棋子**：再度點擊合法目標格。
* **悔棋**：點擊側邊欄「Undo Move」按鈕。
* **重新開始**：點擊「restart」按鈕或按鍵盤 R。
* **切換難度**：點擊側邊欄難度按鈕。
* **切換模式**：點擊 AI Battle / Two-player battle 按鈕。

## 程式結構

```
├── main.py           # 程式進入點
├── chess_game.py     # 遊戲邏輯（ChessGame 類）
├── chess_ui.py       # 介面繪製與事件處理（ChessUI 類）
├── assets/           # 棋子圖片資源（PNG）
└── README.md         # 專案說明
```

## 開發與貢獻

歡迎提交 Issue 或 Pull Request，分享改進建議或新功能！

## 授權

本專案採用 MIT License，詳見 `LICENSE`。
