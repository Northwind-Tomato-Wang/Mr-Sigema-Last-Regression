import pygame
import pygame.scrap 
import sys
import os
import random
import numpy as np
import matplotlib
matplotlib.use("Agg") 
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import platform

# --- Windows 高分屏适配 ---
if platform.system() == "Windows":
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass

# --- 路径与配置 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

def get_windows_font():
    local_font = os.path.join(BASE_DIR, "simhei.ttf")
    if os.path.exists(local_font): return local_font
    fonts = ["msyh.ttc", "msyh.ttf", "simhei.ttf"]
    font_dir = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts")
    for f in fonts:
        path = os.path.join(font_dir, f)
        if os.path.exists(path): return path
    return None

FONT_PATH = get_windows_font()

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
TYPE_SPEED = 30 

# 颜色
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (50, 50, 50)
LIGHT_GRAY = (200, 200, 200)
BLUE = (70, 130, 180)
DARK_BLUE = (0, 50, 100)
RED = (220, 60, 60)
GREEN = (50, 200, 50)
YELLOW = (255, 215, 0) 
ORANGE = (255, 165, 0)
TRANS_BG = (0, 0, 0, 180) 
TRANS_HIGHLIGHT = (255, 165, 0, 100)

TEXTS = {
    "CN": {
        "start": "开始调查",
        "settings": "系统设置",
        "back": "返回",
        "save": "保存配置",
        "api_title": "LLM API 配置 (支持 Ctrl+V)",
        "scene_hint": "案发现场：寻找可疑的电子设备...",
        "comp_hint": "点击调查电脑",
        "desktop_hint": "Dr. Sigma 的远程桌面",
        "file_hint": "点击分析数据文件",
        "submit": "验证分析流程",
        "correct": "分析正确！正在生成报告...",
        "failed": "流程错误。剩余尝试次数: ",
        "game_over": "次数耗尽，自动载入正确方案...",
        "briefing_title": "【 战术分析简报 】",
        "btn_start_puzzle": "开始解密",
        "ai_btn": "AI 辅助",
        "ai_placeholder": "输入问题 (支持 Ctrl+V)...",
        "intro_text": """顶级量化对冲基金 "AlphaGo Capital" 的首席科学家 Dr. Sigma 在办公室离奇死亡。

警方初步判定为心脏骤停，但你——作为一名精通数据的私家侦探——发现他的电脑里留下了一个未完成的 Jupyter Notebook 和一系列加密的 .csv 数据文件。

Dr. Sigma 似乎在死前试图通过数学模型，揭露公司内部的一个巨大阴谋......"""
    }
}

# --- 资源管理 ---
class AssetManager:
    def __init__(self):
        self.images = {}
        self.font_cache = {}

    def load_image(self, name, filename, size=None):
        path = os.path.join(ASSETS_DIR, filename)
        try:
            img = pygame.image.load(path)
            if size:
                img = pygame.transform.smoothscale(img, size)
            self.images[name] = img
        except Exception:
            surf = pygame.Surface(size if size else (100, 100))
            color = (100, 100, 100)
            if "detective" in name: color = (50, 50, 150)
            if "assistant" in name: color = (50, 150, 150)
            surf.fill(color)
            self.images[name] = surf

    def get_font(self, size):
        if size not in self.font_cache:
            if FONT_PATH:
                try:
                    self.font_cache[size] = pygame.font.Font(FONT_PATH, size)
                except:
                    self.font_cache[size] = pygame.font.SysFont("Microsoft YaHei", size)
            else:
                self.font_cache[size] = pygame.font.SysFont("SimHei", size)
        return self.font_cache[size]

assets = AssetManager()

# --- Mock AI ---
class MockAIService:
    def __init__(self):
        self.kb = {
            "OLS": "普通最小二乘法 (OLS) 是一种线性回归方法，通过最小化预测值与真实值之差的平方和来寻找最佳拟合直线。",
            "ALPHA": "Alpha (α) 代表超额收益。如果 α < 0，说明策略在亏钱。",
            "VIF": "方差膨胀因子 (VIF) 用于检测多重共线性。如果 VIF > 10，应剔除该变量。",
            "P值": "P-value 用于假设检验。一般 P < 0.05 认为结果显著。",
            "多重共线性": "指自变量之间存在高度相关性，导致模型系数估计不稳定。"
        }
    
    def query(self, text):
        key = text.upper().strip()
        for k, v in self.kb.items():
            if k in key: return v
        return f"【AI】关于 '{text}' 的分析：\n(模拟API返回) 这是一个统计学概念。接入API后将显示详细解释。"

ai_service = MockAIService()

# --- UI 组件: 输入框 ---
class InputBox:
    def __init__(self, x, y, w, h, label, text='', font_size=24):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = GRAY
        self.text = text
        self.label = label
        self.active = False
        self.font_size = font_size
        self.bg_color = BLACK

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.active = not self.active
                pygame.key.start_text_input()
            else:
                self.active = False
                pygame.key.stop_text_input()
            self.color = GREEN if self.active else GRAY
            
        if event.type == pygame.TEXTINPUT and self.active:
            self.text += event.text

        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_v and (event.mod & pygame.KMOD_CTRL):
                try:
                    content = pygame.scrap.get(pygame.SCRAP_TEXT)
                    if content:
                        paste_text = ''.join(char for char in content.decode("utf-8") if 32 <= ord(char) <= 126 or ord(char) > 127)
                        self.text += paste_text
                except: pass
            elif event.key == pygame.K_RETURN:
                return "SUBMIT"
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
        return None

    def draw(self, screen):
        label_surf = assets.get_font(20).render(self.label, True, LIGHT_GRAY)
        screen.blit(label_surf, (self.rect.x, self.rect.y - 25))
        pygame.draw.rect(screen, self.bg_color, self.rect)
        pygame.draw.rect(screen, self.color, self.rect, 2)
        font = assets.get_font(self.font_size)
        display_text = self.text
        while font.size(display_text)[0] > self.rect.width - 20:
            display_text = display_text[1:]
        txt_surface = font.render(display_text, True, WHITE)
        screen.blit(txt_surface, (self.rect.x + 10, self.rect.centery - txt_surface.get_height()//2))

# --- UI 组件: 按钮 ---
class Button:
    def __init__(self, x, y, w, h, text, action, color=BLUE, text_color=WHITE):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.action = action
        self.color = color
        self.text_color = text_color
        self.hover = False

    def draw(self, screen):
        col = (min(self.color[0]+30, 255), min(self.color[1]+30, 255), min(self.color[2]+30, 255)) if self.hover else self.color
        pygame.draw.rect(screen, col, self.rect, border_radius=8)
        pygame.draw.rect(screen, WHITE, self.rect, 2, border_radius=8)
        font = assets.get_font(24)
        surf = font.render(self.text, True, self.text_color)
        screen.blit(surf, (self.rect.centerx - surf.get_width()//2, self.rect.centery - surf.get_height()//2))

# --- 拖拽块 ---
class DraggableBlock:
    def __init__(self, step_id, text, is_correct, x, y):
        self.step_id = step_id
        self.text = text
        self.rect = pygame.Rect(x, y, 280, 50)
        self.original_pos = (x, y) 
        self.in_slot = False 

    def draw(self, screen):
        color = DARK_BLUE if not self.in_slot else BLUE
        pygame.draw.rect(screen, color, self.rect, border_radius=5)
        pygame.draw.rect(screen, WHITE, self.rect, 2, border_radius=5)
        font = assets.get_font(18)
        disp_text = self.text if len(self.text) < 22 else self.text[:20] + "..."
        surf = font.render(disp_text, True, WHITE)
        screen.blit(surf, (self.rect.x + 10, self.rect.centery - surf.get_height()//2))

# --- 游戏主类 ---
class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.scrap.init() 
        pygame.display.set_caption("Dr. Sigma's Last Regression")
        self.clock = pygame.time.Clock()
        
        # 加载资源
        assets.load_image("bg_menu", "bg_menu.jpg", (SCREEN_WIDTH, SCREEN_HEIGHT))
        assets.load_image("bg_settings", "bg_settings.jpg", (SCREEN_WIDTH, SCREEN_HEIGHT))
        assets.load_image("bg_crime", "bg_crime_scene.jpg", (SCREEN_WIDTH, SCREEN_HEIGHT))
        assets.load_image("bg_desktop", "bg_desktop.png", (SCREEN_WIDTH, SCREEN_HEIGHT))
        assets.load_image("bg_office", "bg_office.jpg", (SCREEN_WIDTH, SCREEN_HEIGHT))
        assets.load_image("char_detective", "char_detective.png", (600, 600))
        assets.load_image("char_assistant", "char_assistant.png", (600, 600))
        
        self.state = "MENU"
        self.current_chapter = 0
        self.chapters = self.init_chapters()
        self.has_investigated = False 
        
        # API 设置
        self.api_config = {"url": "...", "key": "", "model": "qwen-turbo"}
        self.input_url = InputBox(300, 150, 600, 50, "API URL", self.api_config["url"])
        self.input_key = InputBox(300, 250, 600, 50, "API Key (Ctrl+V)", self.api_config["key"])
        self.input_model = InputBox(300, 350, 600, 50, "Model Name", self.api_config["model"])
        
        # 游戏变量
        self.puzzle_blocks = [] 
        self.puzzle_slots = [None] * 5 
        self.puzzle_attempts = 3
        self.dialogue_idx = 0
        self.current_plot_surf = None
        self.ai_popup_msg = ""
        self.show_ai_popup = False
        
        # 打字机
        self.target_text = ""
        self.current_text = ""
        self.type_idx = 0
        self.last_type_time = 0
        
        # AI 交互
        self.show_ai_dialog = False
        self.ai_dialog_input = InputBox(340, 300, 600, 50, TEXTS["CN"]["ai_placeholder"], font_size=24)
        self.show_ai_answer_overlay = False
        self.ai_answer_text = ""

    def init_chapters(self):
        return [
            {
                "title": "Ch1: 线性的谎言",
                "dialogue": [
                    ("Detective", "终端解锁了。这上面的数据曲线完美得像个谎言。"),
                    ("Assistant", "老板，我导出了策略收益(Y)和大盘(X)。看，一条漂亮的直线！"),
                    ("Detective", "漂亮？在金融里，漂亮的直线通常意味着诈骗。你检查 Alpha 了吗？"),
                    ("Assistant", "Alpha？我以为只要相关性高就够了..."),
                    ("Detective", "新手。如果 Alpha 为负，就算拟合再好，他也在稳定亏钱。"),
                    ("Assistant", "懂了！我马上准备 OLS 环境。具体怎么做？"),
                    ("Detective", "先别急着敲代码，看清楚你要解决什么问题。")
                ],
                "briefing": {
                    "problem": "验证投资策略是否真正产生了超额收益 (Alpha)。",
                    "method": "普通最小二乘法 (OLS 线性回归)",
                    "expected": "得到 Y = βX + α + ε。关注 α 的符号。",
                    "steps": ["1. 加载 Pandas 读取 CSV 数据。", "2. 清洗数据 (DropNA)。", "3. 建立 OLS 模型 (statsmodels)。", "4. 检查 Alpha (Const) 系数。"]
                },
                "pool": [{"id": "load", "text": "1. 读取 CSV 数据", "type": "correct"}, {"id": "clean", "text": "2. 清洗缺失值", "type": "correct"}, {"id": "model", "text": "3. 建立 OLS 回归模型", "type": "correct"}, {"id": "check", "text": "4. 检查截距项符号", "type": "correct"}, {"id": "wrong1", "text": "随机森林分类", "type": "wrong"}, {"id": "wrong2", "text": "忽略 P 值", "type": "wrong"}],
                "correct_order": ["load", "clean", "model", "check"],
                "plot_func": self.plot_ch1
            },
            {
                "title": "Ch2: 共线性的迷雾",
                "dialogue": [
                    ("Detective", "果然是负 Alpha。他在亏钱。但财报是盈利的，钱哪来的？"),
                    ("Assistant", "发现了隐藏日志：'延迟(ms)' 和 '负载(%)'。"),
                    ("Detective", "都扔进模型里看看。"),
                    ("Assistant", "等等，报错了？系数变得巨大而且反常..."),
                    ("Detective", "因为你在给自己挖坑。高负载必然高延迟，它们是一回事。"),
                    ("Assistant", "这就是... 多重共线性？"),
                    ("Detective", "没错。两个变量说同一件事，模型会疯掉。我们需要 VIF。")
                ],
                "briefing": {
                    "problem": "自变量高度相关，导致系数估计不稳定。",
                    "method": "方差膨胀因子 (VIF)",
                    "expected": "识别 VIF > 10 的变量并剔除。",
                    "steps": ["1. 计算相关矩阵 (Correlation)。", "2. 计算 VIF 值。", "3. 剔除高 VIF 变量。", "4. 重新拟合模型。"]
                },
                "pool": [{"id": "corr", "text": "1. 计算相关矩阵", "type": "correct"}, {"id": "vif", "text": "2. 计算 VIF 值", "type": "correct"}, {"id": "drop", "text": "3. 剔除高 VIF 变量", "type": "correct"}, {"id": "refit", "text": "4. 重新拟合模型", "type": "correct"}, {"id": "keep", "text": "保留所有变量", "type": "wrong"}],
                "correct_order": ["corr", "vif", "drop", "refit"],
                "plot_func": self.plot_ch2
            }
        ]

    def plot_to_surf(self, fig):
        canvas = FigureCanvas(fig)
        canvas.draw()
        raw_data = canvas.buffer_rgba()
        s = pygame.image.frombuffer(raw_data, canvas.get_width_height(), "RGBA")
        plt.close(fig)
        return s

    def plot_ch1(self):
        fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
        fig.patch.set_alpha(0.8)
        x = np.random.rand(50) * 10
        y = 0.5 * x - 2 + np.random.randn(50) 
        ax.scatter(x, y, c='blue', alpha=0.6)
        ax.plot(x, 0.5*x-2, c='red', lw=2)
        ax.set_title("Strategy vs Market (Alpha < 0)")
        plt.tight_layout()
        return self.plot_to_surf(fig)

    def plot_ch2(self):
        fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
        fig.patch.set_alpha(0.8)
        data = np.random.multivariate_normal([0, 0], [[1, 0.95], [0.95, 1]], 100)
        ax.scatter(data[:,0], data[:,1], c='green', alpha=0.6)
        ax.set_title("Correlation (r=0.95)")
        ax.set_xlabel("Latency")
        ax.set_ylabel("Load")
        plt.tight_layout()
        return self.plot_to_surf(fig)

    def reset_typewriter(self, text):
        self.target_text = text
        self.current_text = ""
        self.type_idx = 0
        self.last_type_time = pygame.time.get_ticks()

    def update_typewriter(self):
        if self.type_idx < len(self.target_text):
            now = pygame.time.get_ticks()
            if now - self.last_type_time > TYPE_SPEED:
                self.type_idx += 1
                self.current_text = self.target_text[:self.type_idx]
                self.last_type_time = now
        return self.type_idx >= len(self.target_text)

    # --- 状态逻辑 ---
    def start_game(self):
        self.current_chapter = 0
        self.has_investigated = False
        self.state = "STORY_INTRO" 
        self.reset_typewriter(TEXTS["CN"]["intro_text"])

    def enter_briefing(self):
        self.state = "BRIEFING"

    def enter_puzzle(self):
        self.state = "PUZZLE"
        data = self.chapters[self.current_chapter]
        self.puzzle_attempts = 3
        self.puzzle_blocks = []
        self.puzzle_slots = [None] * 5
        pool_data = data["pool"].copy()
        random.shuffle(pool_data)
        
        # 布局调整：Pool x=20
        for i, item in enumerate(pool_data):
            blk = DraggableBlock(item["id"], item["text"], True, 20, 150 + i*60)
            self.puzzle_blocks.append(blk)
        if "plot_func" in data:
            self.current_plot_surf = data["plot_func"]()

    def handle_puzzle_click(self, pos):
        if pygame.Rect(900, 600, 200, 60).collidepoint(pos):
            self.check_puzzle()
            return
        for b in self.puzzle_blocks:
            if b.rect.collidepoint(pos):
                if not b.in_slot:
                    try:
                        idx = self.puzzle_slots.index(None)
                        self.puzzle_slots[idx] = b
                        b.in_slot = True
                        # 布局调整：Slot x=340
                        b.rect.topleft = (340, 150 + idx * 80)
                    except ValueError: pass
                else:
                    if b in self.puzzle_slots:
                        idx = self.puzzle_slots.index(b)
                        self.puzzle_slots[idx] = None
                    b.in_slot = False
                    b.rect.topleft = b.original_pos
                break

    def check_puzzle(self):
        current_ids = [b.step_id for b in self.puzzle_slots if b is not None]
        correct_ids = self.chapters[self.current_chapter]["correct_order"]
        if current_ids == correct_ids:
            self.ai_popup_msg = TEXTS["CN"]["correct"]
            self.show_ai_popup = True
            self.state = "VICTORY_WAIT"
        else:
            self.puzzle_attempts -= 1
            if self.puzzle_attempts <= 0:
                self.ai_popup_msg = TEXTS["CN"]["game_over"]
                self.show_ai_popup = True
                self.auto_solve()
                self.state = "VICTORY_WAIT"
            else:
                self.ai_popup_msg = TEXTS["CN"]["failed"] + str(self.puzzle_attempts)
                self.show_ai_popup = True

    def auto_solve(self):
        correct_ids = self.chapters[self.current_chapter]["correct_order"]
        self.puzzle_slots = [None] * 5
        for b in self.puzzle_blocks:
            b.in_slot = False
            b.rect.topleft = b.original_pos
        for i, cid in enumerate(correct_ids):
            for b in self.puzzle_blocks:
                if b.step_id == cid:
                    self.puzzle_slots[i] = b
                    b.in_slot = True
                    # 布局调整：Slot x=340
                    b.rect.topleft = (340, 150 + i*80)
                    break

    # --- 渲染逻辑 ---
    def draw_menu(self):
        bg = assets.images.get("bg_menu")
        if bg: self.screen.blit(bg, (0,0))
        
        # 标题修改：第一行也变大、加粗(阴影)、黄色
        font_t1 = assets.get_font(85) # 字号变大
        s1 = font_t1.render("Dr. Sigma's", True, BLACK) # 阴影
        self.screen.blit(s1, (SCREEN_WIDTH//2 - s1.get_width()//2 + 4, 74))
        
        t1 = font_t1.render("Dr. Sigma's", True, YELLOW) # 黄色
        self.screen.blit(t1, (SCREEN_WIDTH//2 - t1.get_width()//2, 70))
        
        font_t2 = assets.get_font(110)
        s2 = font_t2.render("Last Regression", True, BLACK)
        self.screen.blit(s2, (SCREEN_WIDTH//2 - s2.get_width()//2 + 4, 174))
        
        t2 = font_t2.render("Last Regression", True, YELLOW)
        self.screen.blit(t2, (SCREEN_WIDTH//2 - t2.get_width()//2, 170))
        
        Button(SCREEN_WIDTH//2 - 100, 350, 200, 60, TEXTS["CN"]["start"], self.start_game).draw(self.screen)
        Button(SCREEN_WIDTH//2 - 100, 450, 200, 60, TEXTS["CN"]["settings"], lambda: setattr(self, 'state', 'SETTINGS')).draw(self.screen)

    def draw_settings(self):
        bg = assets.images.get("bg_settings")
        if not bg: bg = assets.images.get("bg_menu")
        if bg: self.screen.blit(bg, (0,0))
        else: self.screen.fill(DARK_BLUE)
        t = assets.get_font(40).render(TEXTS["CN"]["api_title"], True, YELLOW)
        self.screen.blit(t, (100, 50))
        self.input_url.draw(self.screen)
        self.input_key.draw(self.screen)
        self.input_model.draw(self.screen)
        Button(100, 600, 150, 50, TEXTS["CN"]["back"], lambda: setattr(self, 'state', 'MENU'), GRAY).draw(self.screen)
        def save_config():
            self.api_config["url"] = self.input_url.text
            self.api_config["key"] = self.input_key.text
            self.state = "MENU"
        Button(1000, 600, 150, 50, TEXTS["CN"]["save"], save_config, GREEN).draw(self.screen)

    def draw_story_intro(self):
        self.screen.fill(BLACK)
        self.update_typewriter()
        font = assets.get_font(28)
        lines = []
        full_paras = self.current_text.split('\n')
        for p in full_paras:
            current_line = ""
            for char in p:
                test_line = current_line + char
                if font.size(test_line)[0] < SCREEN_WIDTH - 200:
                    current_line = test_line
                else:
                    lines.append(current_line)
                    current_line = char
            lines.append(current_line)
        y = 100
        for line in lines:
            if line.strip() == "": y += 20; continue
            s = font.render(line, True, WHITE)
            self.screen.blit(s, (100, y))
            y += 40
        if self.type_idx >= len(self.target_text):
            hint = assets.get_font(20).render(">>> 点击任意处继续", True, LIGHT_GRAY)
            self.screen.blit(hint, (SCREEN_WIDTH - 300, SCREEN_HEIGHT - 60))

    def draw_scene(self):
        bg = assets.images.get("bg_crime")
        if bg: self.screen.blit(bg, (0,0))
        if not self.has_investigated:
            comp_rect = pygame.Rect(SCREEN_WIDTH - 250, 50, 200, 150)
            s = pygame.Surface((200, 150), pygame.SRCALPHA)
            s.fill(TRANS_HIGHLIGHT)
            self.screen.blit(s, comp_rect.topleft)
            pygame.draw.rect(self.screen, ORANGE, comp_rect, 3)
            msg_rect = pygame.Rect(comp_rect.x, comp_rect.bottom + 10, 200, 40)
            pygame.draw.rect(self.screen, BLACK, msg_rect, border_radius=5)
            txt = assets.get_font(20).render(TEXTS["CN"]["comp_hint"], True, WHITE)
            self.screen.blit(txt, (msg_rect.centerx - txt.get_width()//2, msg_rect.centery - txt.get_height()//2))
            return comp_rect
        else: return pygame.Rect(0,0,SCREEN_WIDTH,SCREEN_HEIGHT)

    def draw_desktop(self):
        bg = assets.images.get("bg_desktop")
        if bg: self.screen.blit(bg, (0,0))
        else: self.screen.fill(BLUE)
        if not self.has_investigated:
            file_rect = pygame.Rect(100, 100, 120, 140)
            s = pygame.Surface((120, 140), pygame.SRCALPHA)
            s.fill(TRANS_HIGHLIGHT)
            self.screen.blit(s, file_rect.topleft)
            pygame.draw.rect(self.screen, ORANGE, file_rect, 2)
            msg_rect = pygame.Rect(file_rect.x, file_rect.bottom + 10, 150, 30)
            pygame.draw.rect(self.screen, DARK_BLUE, msg_rect, border_radius=5)
            txt = assets.get_font(16).render(TEXTS["CN"]["file_hint"], True, WHITE)
            self.screen.blit(txt, (msg_rect.centerx - txt.get_width()//2, msg_rect.centery - txt.get_height()//2))
            return file_rect
        else: return pygame.Rect(0,0,SCREEN_WIDTH,SCREEN_HEIGHT)

    def draw_dialogue(self):
        bg = assets.images.get("bg_office")
        if bg: self.screen.blit(bg, (0,0))
        else: self.screen.fill(GRAY)
        data = self.chapters[self.current_chapter]["dialogue"][self.dialogue_idx]
        speaker, text = data
        self.update_typewriter()
        if speaker == "Detective":
            det_img = assets.images.get("char_detective")
            if det_img: self.screen.blit(det_img, (0, SCREEN_HEIGHT - det_img.get_height()))
        elif speaker == "Assistant":
            asst_img = assets.images.get("char_assistant")
            if asst_img: self.screen.blit(asst_img, (SCREEN_WIDTH - asst_img.get_width(), SCREEN_HEIGHT - asst_img.get_height()))
        box = pygame.Rect(50, SCREEN_HEIGHT-220, SCREEN_WIDTH-100, 200)
        s = pygame.Surface((box.width, box.height), pygame.SRCALPHA)
        s.fill(TRANS_BG)
        self.screen.blit(s, box)
        name_color = YELLOW if speaker == "Detective" else (0, 255, 255)
        n_txt = assets.get_font(32).render(speaker, True, name_color)
        self.screen.blit(n_txt, (box.x+30, box.y+20))
        font = assets.get_font(26)
        line1 = self.current_text[:38]
        line2 = self.current_text[38:]
        self.screen.blit(font.render(line1, True, WHITE), (box.x+30, box.y+70))
        if line2: self.screen.blit(font.render(line2, True, WHITE), (box.x+30, box.y+110))
        if self.type_idx >= len(self.target_text):
            hint = assets.get_font(20).render(">>> 点击继续", True, LIGHT_GRAY)
            self.screen.blit(hint, (box.right-150, box.bottom-40))

    def draw_briefing(self):
        self.screen.fill((20, 30, 40))
        info = self.chapters[self.current_chapter]["briefing"]
        t = assets.get_font(48).render(TEXTS["CN"]["briefing_title"], True, YELLOW)
        self.screen.blit(t, (SCREEN_WIDTH//2 - t.get_width()//2, 50))
        start_y = 150
        gap = 50
        font_head = assets.get_font(30)
        font_body = assets.get_font(24)
        def draw_section(title, content, y):
            head = font_head.render(f"■ {title}:", True, ORANGE)
            self.screen.blit(head, (100, y))
            if isinstance(content, list):
                for i, line in enumerate(content):
                    body = font_body.render(line, True, WHITE)
                    self.screen.blit(body, (140, y + 40 + i*35))
                return y + 40 + len(content)*35 + gap
            else:
                body = font_body.render(content, True, WHITE)
                self.screen.blit(body, (140, y + 40))
                return y + 40 + 35 + gap
        cur_y = draw_section("面临问题", info["problem"], start_y)
        cur_y = draw_section("统计方法", info["method"], cur_y)
        cur_y = draw_section("预期目标", info["expected"], cur_y)
        cur_y = draw_section("执行步骤 (提示)", info["steps"], cur_y)
        Button(SCREEN_WIDTH - 250, SCREEN_HEIGHT - 100, 200, 60, TEXTS["CN"]["btn_start_puzzle"], self.enter_puzzle, GREEN).draw(self.screen)

    def draw_puzzle(self):
        # 绘制分区背景 (GRID SYSTEM)
        pygame.draw.rect(self.screen, (30,30,30), (0,0, 320, SCREEN_HEIGHT)) # 左侧
        pygame.draw.rect(self.screen, (50,50,50), (320,0, 340, SCREEN_HEIGHT)) # 中间
        pygame.draw.rect(self.screen, (70,70,70), (660,0, SCREEN_WIDTH-660, SCREEN_HEIGHT)) # 右侧
        
        t1 = assets.get_font(30).render("步骤池", True, LIGHT_GRAY)
        self.screen.blit(t1, (30, 20))
        
        msg = f"剩余尝试: {self.puzzle_attempts}"
        t2 = assets.get_font(30).render(msg, True, RED if self.puzzle_attempts==1 else WHITE)
        self.screen.blit(t2, (340, 20))
        
        for i in range(5):
            r = pygame.Rect(340, 150 + i*80, 300, 60)
            pygame.draw.rect(self.screen, (80,80,80), r, 2, border_radius=5)
            num = assets.get_font(20).render(f"Step {i+1}", True, (120,120,120))
            self.screen.blit(num, (r.x - 70, r.centery - 10))
            
        if self.current_plot_surf:
            # 图表左移到 660，确保完整显示
            self.screen.blit(self.current_plot_surf, (660, 150))
            
        for b in self.puzzle_blocks:
            b.draw(self.screen)
        Button(900, 600, 200, 60, TEXTS["CN"]["submit"], self.check_puzzle, GREEN).draw(self.screen)

    def draw_ai_popup(self):
        if not self.show_ai_popup: return
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0,0,0,180))
        self.screen.blit(overlay, (0,0))
        panel = pygame.Rect(340, 250, 600, 200)
        pygame.draw.rect(self.screen, DARK_BLUE, panel, border_radius=10)
        pygame.draw.rect(self.screen, WHITE, panel, 2, border_radius=10)
        t = assets.get_font(28).render("系统通知", True, YELLOW)
        self.screen.blit(t, (panel.x+20, panel.y+20))
        c = assets.get_font(24).render(self.ai_popup_msg, True, WHITE)
        self.screen.blit(c, (panel.x+20, panel.y+80))
        hint = assets.get_font(20).render("[点击任意处关闭]", True, LIGHT_GRAY)
        self.screen.blit(hint, (panel.centerx - hint.get_width()//2, panel.bottom - 40))

    def draw_ai_dialog(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))
        
        panel = pygame.Rect(280, 200, 720, 250)
        pygame.draw.rect(self.screen, DARK_BLUE, panel, border_radius=15)
        pygame.draw.rect(self.screen, YELLOW, panel, 2, border_radius=15)
        
        t = assets.get_font(32).render("AI 统计学助手", True, YELLOW)
        self.screen.blit(t, (panel.x + 30, panel.y + 30))
        
        self.ai_dialog_input.draw(self.screen)
        
        Button(panel.right - 120, panel.bottom - 70, 100, 50, "提问", lambda: None, GREEN).draw(self.screen)
        
        hint = assets.get_font(18).render("输入问题后按回车发送 (支持 Ctrl+V)", True, LIGHT_GRAY)
        self.screen.blit(hint, (panel.x + 30, panel.bottom - 40))

        close_btn_rect = pygame.Rect(panel.right - 40, panel.top + 10, 30, 30)
        pygame.draw.line(self.screen, RED, (close_btn_rect.left, close_btn_rect.top), (close_btn_rect.right, close_btn_rect.bottom), 3)
        pygame.draw.line(self.screen, RED, (close_btn_rect.left, close_btn_rect.bottom), (close_btn_rect.right, close_btn_rect.top), 3)
        return close_btn_rect, pygame.Rect(panel.right - 120, panel.bottom - 70, 100, 50)

    def draw_ai_answer_overlay(self):
        if not self.show_ai_answer_overlay: return
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 220))
        self.screen.blit(overlay, (0, 0))
        panel = pygame.Rect(200, 150, 880, 420)
        pygame.draw.rect(self.screen, (40, 44, 52), panel, border_radius=15)
        pygame.draw.rect(self.screen, BLUE, panel, 2, border_radius=15)
        t = assets.get_font(32).render("AI 知识库解答", True, YELLOW)
        self.screen.blit(t, (panel.x + 30, panel.y + 30))
        font = assets.get_font(24)
        words = self.ai_answer_text
        lines = []
        current_line = ""
        for char in words:
            if font.size(current_line + char)[0] < 820:
                current_line += char
            else:
                lines.append(current_line)
                current_line = char
        lines.append(current_line)
        for i, line in enumerate(lines):
            s = font.render(line, True, WHITE)
            self.screen.blit(s, (panel.x + 30, panel.y + 90 + i * 35))
        close_btn_rect = pygame.Rect(panel.right - 50, panel.top + 20, 30, 30)
        pygame.draw.line(self.screen, RED, (close_btn_rect.left, close_btn_rect.top), (close_btn_rect.right, close_btn_rect.bottom), 3)
        pygame.draw.line(self.screen, RED, (close_btn_rect.left, close_btn_rect.bottom), (close_btn_rect.right, close_btn_rect.top), 3)
        return close_btn_rect

    # --- 游戏主循环 ---
    def run(self):
        # 左上角 AI 按钮
        btn_ai_help = Button(20, 20, 120, 40, TEXTS["CN"]["ai_btn"], lambda: setattr(self, 'show_ai_dialog', True), YELLOW, BLACK)

        while True:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                
                # 1. 优先处理 AI 结果展示遮罩
                if self.show_ai_answer_overlay:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        panel_right = 200 + 880
                        panel_top = 150
                        close_btn_rect = pygame.Rect(panel_right - 50, panel_top + 20, 30, 30)
                        if close_btn_rect.collidepoint(event.pos):
                            self.show_ai_answer_overlay = False
                    continue

                # 2. 处理 AI 提问输入遮罩
                if self.show_ai_dialog:
                    res = self.ai_dialog_input.handle_event(event)
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        close_rect, send_rect = self.draw_ai_dialog()
                        if close_rect.collidepoint(event.pos):
                            self.show_ai_dialog = False
                            self.ai_dialog_input.active = False
                        if send_rect.collidepoint(event.pos):
                            res = "SUBMIT"
                    if res == "SUBMIT":
                        question = self.ai_dialog_input.text
                        if question.strip():
                            self.ai_answer_text = ai_service.query(question)
                            self.show_ai_answer_overlay = True
                            self.show_ai_dialog = False 
                            self.ai_dialog_input.text = ""
                            self.ai_dialog_input.active = False
                    continue

                # 3. 游戏内通知
                if self.show_ai_popup:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        self.show_ai_popup = False
                        if self.state == "VICTORY_WAIT":
                            self.current_chapter += 1
                            if self.current_chapter >= len(self.chapters):
                                self.state = "MENU"
                            else:
                                if self.has_investigated:
                                    self.state = "DIALOGUE"
                                    self.dialogue_idx = 0
                                    self.reset_typewriter(self.chapters[self.current_chapter]["dialogue"][0][1])
                                else:
                                    self.has_investigated = True 
                                    self.state = "DIALOGUE"
                                    self.dialogue_idx = 0
                                    self.reset_typewriter(self.chapters[self.current_chapter]["dialogue"][0][1])
                    continue
                
                # 4. 常规状态
                if self.state == "SETTINGS":
                    self.input_url.handle_event(event)
                    self.input_key.handle_event(event)
                    self.input_model.handle_event(event)

                if event.type == pygame.MOUSEBUTTONDOWN:
                    pos = event.pos
                    
                    if self.state not in ["MENU", "SETTINGS", "STORY_INTRO"]:
                        if btn_ai_help.rect.collidepoint(pos):
                            self.show_ai_dialog = True
                            self.ai_dialog_input.active = True
                            continue

                    if self.state == "MENU":
                        if pygame.Rect(SCREEN_WIDTH//2 - 100, 350, 200, 60).collidepoint(pos):
                            self.start_game()
                        if pygame.Rect(SCREEN_WIDTH//2 - 100, 450, 200, 60).collidepoint(pos):
                            self.state = "SETTINGS"
                            
                    elif self.state == "SETTINGS":
                        if pygame.Rect(100, 600, 150, 50).collidepoint(pos): self.state = "MENU"
                        if pygame.Rect(1000, 600, 150, 50).collidepoint(pos): 
                            self.api_config["url"] = self.input_url.text
                            self.api_config["key"] = self.input_key.text
                            self.state = "MENU"

                    elif self.state == "STORY_INTRO":
                        if self.type_idx < len(self.target_text):
                            self.type_idx = len(self.target_text)
                            self.current_text = self.target_text
                        else:
                            self.state = "SCENE"

                    elif self.state == "SCENE":
                        if self.comp_rect_cache.collidepoint(pos):
                            self.state = "DESKTOP"
                            
                    elif self.state == "DESKTOP":
                        if self.file_rect_cache.collidepoint(pos):
                            self.state = "DIALOGUE"
                            self.dialogue_idx = 0
                            self.has_investigated = True 
                            self.reset_typewriter(self.chapters[self.current_chapter]["dialogue"][0][1])
                            
                    elif self.state == "DIALOGUE":
                        if self.type_idx < len(self.target_text):
                            self.type_idx = len(self.target_text)
                            self.current_text = self.target_text
                        else:
                            self.dialogue_idx += 1
                            if self.dialogue_idx >= len(self.chapters[self.current_chapter]["dialogue"]):
                                self.enter_briefing()
                            else:
                                self.reset_typewriter(self.chapters[self.current_chapter]["dialogue"][self.dialogue_idx][1])

                    elif self.state == "BRIEFING":
                        if pygame.Rect(SCREEN_WIDTH - 250, SCREEN_HEIGHT - 100, 200, 60).collidepoint(pos):
                            self.enter_puzzle()
                            
                    elif self.state == "PUZZLE":
                        self.handle_puzzle_click(pos)

            if self.state == "MENU": self.draw_menu()
            elif self.state == "SETTINGS": self.draw_settings()
            elif self.state == "STORY_INTRO": self.draw_story_intro()
            elif self.state == "SCENE": self.comp_rect_cache = self.draw_scene()
            elif self.state == "DESKTOP": self.file_rect_cache = self.draw_desktop()
            elif self.state == "DIALOGUE": self.draw_dialogue()
            elif self.state == "BRIEFING": self.draw_briefing()
            elif self.state == "PUZZLE": self.draw_puzzle()
            
            # 绘制 AI 按钮
            if self.state not in ["MENU", "SETTINGS", "STORY_INTRO"] and not self.show_ai_dialog and not self.show_ai_answer_overlay:
                btn_ai_help.draw(self.screen)
            
            # 绘制 AI 遮罩层 (放在最上层)
            if self.show_ai_dialog:
                self.draw_ai_dialog()
            
            self.draw_ai_popup()
            self.draw_ai_answer_overlay()
            
            pygame.display.flip()
            self.clock.tick(FPS)

if __name__ == "__main__":
    game = Game()
    game.run()