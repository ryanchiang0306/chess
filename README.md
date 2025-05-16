# Chess 遊戲

---

## 專案簡介

本專案為以 Python 開發的國際象棋遊戲，整合了 AI 對弈與本機雙人對戰模式。採用 `pygame` 作為圖形介面，並利用 `python-chess` 套件處理棋盤邏輯與走法判斷。

---

## 主要特色

* **單人對 AI**：內建多種難度（Easy、Medium、Hard、Master），採用 Minimax + Alpha-Beta 剪枝與靜態搜索（Quiescence Search），AI 擁有思考提示與評估分數顯示。
* **雙人對弈**：同螢幕下與好友進行回合制對戰。
* **動態提示**：選中棋子後，自動高亮合法移動路徑與最後一步走位。
* **悔棋功能**：雙人模式可回退一步；AI 模式則同時回退玩家與 AI 的兩步。
* **即時評估**：侧邊欄顯示當前棋盤的評估分數，幫助掌握局勢。
* **結果呈現**：遊戲結束後顯示勝負或和局訊息，並可按 `R` 或點擊「Restart」按鈕重啟遊戲。

---

## 安裝需求

* Python 3.8 以上版本
* `pygame`
* `python-chess`

可透過下列指令一次安裝：

```bash
pip install pygame python-chess
```

---

## 使用說明

1. **選擇棋子**：滑鼠左鍵點擊棋盤上的己方棋子。
2. **移動棋子**：點擊合法目標格完成移動。
3. **悔棋**：點擊側邊欄「Undo Move」按鈕。
4. **重新開始**：按鍵盤 `R` 或側邊欄「Restart」按鈕。
5. **切換難度**：於側邊欄點擊對應難度按鈕。
6. **切換模式**：於側邊欄點擊「AI Battle」或「Two-player Battle」按鈕。

---

## 專案結構

```text
├── main.py          # 程式入口  
├── chess_game.py    # 遊戲邏輯（ChessGame 類）  
├── chess_ui.py      # 使用者介面（ChessUI 類）  
├── assets/          # 棋子圖片資源（PNG）  
└── README.md        # 專案說明
```

---

## 貢獻與回饋

歡迎發送 Issue 或 Pull Request，無論是錯誤回報、功能建議，或是程式優化，都非常感謝您的貢獻。

---

## 授權聲明

本專案以 MIT License 授權，詳見 `LICENSE`。
