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
TYPE_SPEED = 20 

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
CYAN = (0, 255, 255)
TRANS_BG = (0, 0, 0, 180) 
TRANS_HIGHLIGHT = (255, 165, 0, 100)
BRIEFING_BG_COLOR = (20, 30, 40)

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
        "continue_hint": ">>> 模型已修正 (点击任意处查看真相)",
        "correct": "分析正确！数据模型已重构完成。",
        "failed": "流程错误。剩余尝试次数: ",
        "game_over": "次数耗尽，自动载入正确方案...",
        "briefing_title": "【 战术分析简报 】",
        "conclusion_title": "【 案件还原与推理日志 】",
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
        img = None
        try:
            if os.path.exists(path):
                img = pygame.image.load(path)
            elif os.path.exists(path.replace(".jpg", ".png")):
                img = pygame.image.load(path.replace(".jpg", ".png"))
            
            if img:
                if size:
                    img = pygame.transform.smoothscale(img, size)
                self.images[name] = img
                return
        except:
            pass
            
        surf = pygame.Surface(size if size else (100, 100))
        color = (100, 100, 100)
        if "detective" in name: color = (50, 50, 150)
        if "assistant" in name: color = (50, 150, 150)
        if "suspect" in name: color = (150, 50, 50)
        if "bg_server" in name: color = (20, 40, 20)
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

# --- UI 组件 ---
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
        assets.load_image("bg_server", "bg_server.jpg", (SCREEN_WIDTH, SCREEN_HEIGHT)) 
        
        assets.load_image("char_detective", "char_detective.png", (600, 600))
        assets.load_image("char_assistant", "char_assistant.png", (600, 600))
        assets.load_image("char_suspect", "char_suspect.png", (600, 600))
        
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
        self.current_formula_surf = None
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
            # Ch1
            {
                "title": "Ch1: 线性的谎言",
                "bg": "bg_office",
                "dialogue": [
                    ("Detective", "终端解锁了。这上面的数据曲线完美得像个谎言。"),
                    ("Assistant", "老板，我导出了策略收益(Y)和大盘(X)。相关系数 0.98！这绝对是摇钱树啊。"),
                    ("Detective", "摇钱树？在金融圈，完美的直线通常意味着庞氏骗局。你检查 Alpha 了吗？"),
                    ("Assistant", "Alpha...？我以为只要看 Beta 和 R方就够了..."),
                    ("Detective", "典型的菜鸟思维。如果 Alpha (截距) 显著为负，就算拟合再好，他也是在稳定地亏钱。"),
                    ("Assistant", "我懂了！我马上跑一个 OLS 回归。但是具体步骤是...？"),
                    ("Detective", "别急着敲代码。先定义变量，再建模，最后一定要看 summary 里的截距项。")
                ],
                "briefing": {
                    "problem": "验证投资策略是否真正产生了超额收益 (Alpha)。",
                    "method": "普通最小二乘法 (OLS 线性回归)",
                    "logic": "通过最小化预测值与真实值之间的误差平方和，找到最佳拟合直线。",
                    "expected": "得到 Y = βX + α + ε。关注 α 的符号和显著性。",
                    "steps": ["1. 定义因变量 Y (Returns) 和自变量 X (Market)。", "2. 添加常数项 (Add Constant)。", "3. 拟合 OLS 模型。", "4. 检验 Alpha (截距) 系数的 P 值。"]
                },
                "conclusion": """回归模型像一把无情的手术刀，切开了 AlphaGo Capital 华丽的财报外衣，暴露了里面溃烂的伤口。

那条刺眼的红色拟合线之下，隐藏着一个冰冷的事实：截距项 (Alpha) 显著为负。这在金融学上判了死刑——这不仅仅是“业绩不佳”那么简单，这是系统性的、刻意为之的资金失血。Dr. Sigma 设计的核心算法并没有在战胜市场，而是在以一种极度隐蔽的数学方式，稳定地将资金“输”给特定的对手方。

那个完美的 R-Squared 值不是为了展示能力，而是为了掩盖失血的伤口。Sigma 不是在赚钱，他是在被迫洗钱。而这，仅仅是冰山一角。""",
                "pool": [{"id": "def_y_x", "text": "1. 定义变量 Y, X", "type": "correct"}, {"id": "add_const", "text": "2. 添加常数项", "type": "correct"}, {"id": "fit_ols", "text": "3. 拟合 OLS 模型", "type": "correct"}, {"id": "check_alpha", "text": "4. 检验 Alpha 系数", "type": "correct"}, {"id": "random_forest", "text": "随机森林分类", "type": "wrong"}, {"id": "ignore_p", "text": "忽略 P 值", "type": "wrong"}],
                "correct_order": ["def_y_x", "add_const", "fit_ols", "check_alpha"],
                "plot_pre": self.plot_ch1_pre,
                "plot_post": self.plot_ch1_post
            },
            # Ch2
            {
                "title": "Ch2: 共线性的迷雾",
                "bg": "bg_server",
                "dialogue": [
                    ("Detective", "果然是负 Alpha。他在亏钱。但公司财报显示他在盈利，这钱哪来的？"),
                    ("Assistant", "我在服务器日志里发现了两个隐藏变量：'Server_Latency' (延迟) 和 'Crypto_Mining_Load' (挖矿负载)。"),
                    ("Detective", "有人在利用公司的服务器挖矿？把这两个变量都扔进回归模型里看看。"),
                    ("Assistant", "好的... 咦？报错了？或者系数变得非常奇怪... 正负号完全反了！"),
                    ("Detective", "因为你在给自己挖坑。挖矿负载越高，服务器延迟自然越高。这两个变量在说同一件事。"),
                    ("Assistant", "这就是传说中的... 多重共线性？"),
                    ("Detective", "没错。模型无法区分谁才是罪魁祸首。我们需要计算 VIF (方差膨胀因子) 来去伪存真。")
                ],
                "briefing": {
                    "problem": "自变量高度相关，导致系数估计不稳定。",
                    "method": "方差膨胀因子 (VIF)",
                    "logic": "通过将某个自变量对其他所有自变量进行回归，判断其冗余程度。VIF 越高，多重共线性越严重。",
                    "expected": "识别 VIF > 10 的变量并剔除。",
                    "steps": ["1. 选中变量 Xi 作为因变量。", "2. 对其他所有变量 Xj 进行回归。", "3. 计算 R平方并代入 VIF 公式 (1/(1-R^2))。", "4. 剔除 VIF > 10 的变量。"]
                },
                "conclusion": """方差膨胀因子 (VIF) 的警报声，就像深夜里的火灾警铃，响彻了整个服务器机房。

'服务器延迟' 和 '挖矿负载' 的 VIF 值均疯狂飙升超过了 100，它们是共生的幽灵。当我们剔除冗余变量重新建模后，真相终于浮出水面：公司引以为傲的高频交易服务器，实际上被植入了底层的挖矿脚本。

这就是为什么 Sigma 的策略会亏损——毫秒级的交易优势被繁重的挖矿程序拖慢了。而利用公司电力和硬件挖出的巨额比特币，从未进入公司账户，而是直接流向了一个加密的离岸钱包。这是一场“寄生虫”式的完美犯罪，既吸干了宿主，又掩盖了踪迹。""",
                "pool": [{"id": "reg_xi", "text": "1. Xi 对其他变量回归", "type": "correct"}, {"id": "calc_r2", "text": "2. 计算 R平方", "type": "correct"}, {"id": "calc_vif", "text": "3. 计算 VIF = 1/(1-R^2)", "type": "correct"}, {"id": "drop_var", "text": "4. 剔除高 VIF 变量", "type": "correct"}, {"id": "reg_y_x", "text": "Y 对 X 回归", "type": "wrong"}, {"id": "pearson", "text": "皮尔逊相关系数", "type": "wrong"}],
                "correct_order": ["reg_xi", "calc_r2", "calc_vif", "drop_var"],
                "plot_pre": self.plot_ch2_pre,
                "plot_post": self.plot_ch2_post
            },
            # Ch3
            {
                "title": "Ch3: 嫌疑人的对抗",
                "bg": "bg_server",
                "dialogue": [
                    ("Detective", "挖矿确实在进行。现在我们要找出是谁干的。嫌疑人A（运维）和嫌疑人B（分析师）。"),
                    ("Assistant", "我拉了他们的异常登录次数。看起来嫌疑人 A 的平均次数比 B 高一点点？A 是凶手？"),
                    ("Detective", "光看平均值（Mean）是外行的做法。如果 A 只是某一天数据异常，而 B 是持续性异常呢？"),
                    ("Suspect B", "喂！你们在查什么？我这几天只是在加班做模型！数据波动是随机的！"),
                    ("Detective", "是不是随机的，你说了不算，统计学说了算。我们需要验证这组数据的差异是否显著。"),
                    ("Assistant", "我明白了！不能只比大小，要做假设检验。T检验！"),
                    ("Detective", "正是。我们要用 P 值来堵住他的嘴。")
                ],
                "briefing": {
                    "problem": "判断两组数据的均值差异是否具有统计学意义，而非随机波动。",
                    "method": "独立样本 T 检验 (T-Test)",
                    "logic": "计算信号(均值差)与噪音(标准误)的比率。P值越小，说明'纯属巧合'的概率越低，差异越显著。",
                    "expected": "计算 T 统计量与 P 值。若 P < 0.05，则差异显著。",
                    "steps": ["1. 计算两组数据的均值 (Mean)。", "2. 计算两组数据的方差 (Variance)。", "3. 计算 T 统计量。", "4. 查表或计算 P 值判断显著性。"]
                },
                "conclusion": """T 检验的结果像一记重锤，狠狠地击碎了嫌疑人 B 傲慢的谎言。

虽然运维主管 A 的平均登录次数略高，但其方差极大，P 值显示差异完全不显著——那只是因为服务器故障导致的偶尔加班。而嫌疑人 B 的数据在案发前一周呈现出极低方差的持续性高位，T 统计量高达 5.4，P 值远小于 0.01。在统计学里，这意味着'随机发生'的概率比中彩票还低。

'加班'？不，这是蓄意为之的入侵。B 就是那个在服务器植入后门的人。但一个初级分析师，哪来这么大的胆子？除非，他背后有更大的保护伞。""",
                "pool": [{"id": "calc_mean", "text": "1. 计算均值", "type": "correct"}, {"id": "calc_var", "text": "2. 计算方差", "type": "correct"}, {"id": "calc_t", "text": "3. 计算 T 统计量", "type": "correct"}, {"id": "check_p", "text": "4. 检查 P 值", "type": "correct"}, {"id": "vif", "text": "计算 VIF", "type": "wrong"}, {"id": "ols", "text": "做线性回归", "type": "wrong"}],
                "correct_order": ["calc_mean", "calc_var", "calc_t", "check_p"],
                "plot_pre": self.plot_ch3_pre,
                "plot_post": self.plot_ch3_post
            },
            # Ch4
            {
                "title": "Ch4: 不均匀的罪证",
                "bg": "bg_office",
                "dialogue": [
                    ("Detective", "B 嫌疑最大。我在查他的隐秘账户。我试图用线性模型预测他的'不明收入'。"),
                    ("Assistant", "这就来。模型跑通了！R平方还可以... 等等，这残差图怎么这么怪？"),
                    ("Detective", "像个喇叭口，对吧？小额转账很规律，金额越大，波动越剧烈。"),
                    ("Assistant", "这意味着误差不是恒定的... 普通 OLS 假设失效了？"),
                    ("Detective", "这就是'异方差性' (Heteroscedasticity)。他在试图用大量小额交易掩盖大额洗钱。"),
                    ("Assistant", "那之前的证据都不可靠了？"),
                    ("Detective", "必须修正。给变量取个对数，或者用加权最小二乘法 (WLS) 把这个喇叭口压平。")
                ],
                "briefing": {
                    "problem": "残差方差不恒定（呈喇叭状），违反 OLS 同方差假设。",
                    "method": "加权最小二乘法 (WLS)",
                    "logic": "给波动大的数据赋予较小的权重，给稳定的数据赋予较大的权重。以此消除异方差，恢复模型可靠性。",
                    "expected": "消除异方差，使残差均匀分布，恢复检验有效性。",
                    "steps": ["1. 提取普通回归的残差。", "2. 拟合残差与自变量的关系。", "3. 计算权重 (1/方差)。", "4. 进行加权回归 (WLS)。"]
                },
                "conclusion": """加权最小二乘法 (WLS) 成功压平了那些躁动的残差，也彻底压垮了 B 的心理防线。

那个喇叭口形状的残差图，正是 B 试图通过'拆分转账'（Structuring/Smurfing）来规避银行风控系统的铁证。小额资金像涓涓细流，大额资金则伪装成市场波动的噪音。但数学不会被这种拙劣的伪装欺骗。修正异方差后，模型精准地锁定了每一笔非法资金的去向。

B 崩溃了。他承认自己只是一个执行者。这笔巨额的比特币洗钱资金，最终流向了一个在开曼群岛的离岸账户，而该账户的实际控制人，指向了这栋大楼里最有权势的人——CEO。""",
                "pool": [{"id": "get_resid", "text": "1. 提取残差", "type": "correct"}, {"id": "fit_var", "text": "2. 拟合残差方差", "type": "correct"}, {"id": "calc_weight", "text": "3. 计算权重", "type": "correct"}, {"id": "wls", "text": "4. 加权回归", "type": "correct"}, {"id": "ttest", "text": "运行 T-Test", "type": "wrong"}, {"id": "alpha", "text": "检查 Alpha", "type": "wrong"}],
                "correct_order": ["get_resid", "fit_var", "calc_weight", "wls"],
                "plot_pre": self.plot_ch4_pre,
                "plot_post": self.plot_ch4_post
            },
            # Ch5
            {
                "title": "Ch5: 时间的预言",
                "bg": "bg_office",
                "dialogue": [
                    ("Suspect B", "好吧，我承认洗钱。但 Sigma 不是我杀的！他发现了一个大秘密..."),
                    ("Detective", "关于那个核心算法？"),
                    ("Suspect B", "那是庞氏骗局！它会在某个时间点崩盘。Sigma 留下了一串代码，那是核心基金的净值序列。"),
                    ("Assistant", "我试试用之前的线性回归预测崩盘时间... 咦？Durbin-Watson 统计量很低。"),
                    ("Detective", "别傻了。今天的股价受昨天影响，这是时间序列，存在'自相关'。普通回归根本处理不了。"),
                    ("Assistant", "那我们需要... ARIMA 模型？"),
                    ("Detective", "对。差分及平稳化，找到那个断崖式下跌的'奇点'。那是 Sigma 用生命换来的预警。")
                ],
                "briefing": {
                    "problem": "数据存在序列自相关，普通回归失效。",
                    "method": "ARIMA 时间序列模型",
                    "logic": "将非平稳数据通过差分变平稳，利用数据的自回归(AR)和移动平均(MA)特性，让过去的数据'预测'未来。",
                    "expected": "预测未来的崩盘点 (置信区间穿透)。",
                    "steps": ["1. ADF 检验判断平稳性。", "2. 进行差分 (d) 使序列平稳。", "3. 观察 ACF/PACF 确定 p, q。", "4. 拟合 ARIMA(p,d,q) 模型。"]
                },
                "conclusion": """ARIMA 模型在屏幕上缓缓画出了一条令人胆寒的红色曲线。

经过差分和平稳化处理后，时间序列模型指向了一个确定的、灾难性的未来：明天上午 10:00，由于流动性枯竭，'AlphaGo' 核心基金的净值将发生断崖式归零。Dr. Sigma 发现了这个数学上的必然，并试图阻止这场将摧毁无数家庭的灾难，因此被 CEO 灭口。

我们及时向证监会发送了这份预测报告。CEO 在准备登机逃往苏黎世前被捕。数理统计不会撒谎，它不仅预测了市场的崩盘，也还原了迟到的正义。

案件结束。但数据背后的贪婪，似乎永远无法被模型拟合。""",
                "pool": [{"id": "adf", "text": "1. ADF 检验", "type": "correct"}, {"id": "diff", "text": "2. 差分处理", "type": "correct"}, {"id": "定阶", "text": "3. ACF/PACF 定阶", "type": "correct"}, {"id": "arima", "text": "4. 拟合 ARIMA", "type": "correct"}, {"id": "log", "text": "对变量取 Log", "type": "wrong"}, {"id": "ols", "text": "直接线性外推", "type": "wrong"}],
                "correct_order": ["adf", "diff", "定阶", "arima"],
                "plot_pre": self.plot_ch5_pre,
                "plot_post": self.plot_ch5_post
            }
        ]

    def plot_to_surf(self, fig):
        canvas = FigureCanvas(fig)
        canvas.draw()
        raw_data = canvas.buffer_rgba()
        s = pygame.image.frombuffer(raw_data, canvas.get_width_height(), "RGBA")
        plt.close(fig)
        return s

    # --- 绘图函数 (Pre/Post) ---
    def plot_ch1_pre(self):
        fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
        fig.patch.set_alpha(0.8)
        x = np.random.rand(50) * 10
        y = 0.5 * x - 2 + np.random.randn(50) 
        ax.scatter(x, y, c='blue', alpha=0.6)
        ax.set_title("Strategy vs Market (Raw Data)")
        plt.tight_layout()
        return self.plot_to_surf(fig)

    def plot_ch1_post(self):
        fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
        fig.patch.set_alpha(0.8)
        x = np.random.rand(50) * 10
        y = 0.5 * x - 2 + np.random.randn(50) 
        ax.scatter(x, y, c='blue', alpha=0.6)
        ax.plot(x, 0.5*x-2, c='red', lw=2, label='OLS Fit')
        ax.axhline(-2, color='green', linestyle='--', label='Alpha < 0')
        ax.legend()
        ax.set_title("Regression Result: Negative Alpha", color='green', weight='bold')
        plt.tight_layout()
        return self.plot_to_surf(fig)

    def plot_ch2_pre(self):
        fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
        fig.patch.set_alpha(0.8)
        data = np.random.multivariate_normal([0, 0], [[1, 0.95], [0.95, 1]], 100)
        ax.scatter(data[:,0], data[:,1], c='red', alpha=0.6)
        ax.set_title("Problem: High Correlation (r=0.95)")
        ax.set_xlabel("Latency")
        ax.set_ylabel("Mining Load")
        plt.tight_layout()
        return self.plot_to_surf(fig)

    def plot_ch2_post(self):
        fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
        fig.patch.set_alpha(0.8)
        x = np.random.rand(50) * 10
        y = -0.5 * x + np.random.randn(50) 
        ax.scatter(x, y, c='green', alpha=0.6)
        ax.plot(x, -0.5*x, c='orange', lw=2)
        ax.set_title("FIXED: Mining Load -> Loss", color='green', weight='bold')
        ax.set_xlabel("Mining Load")
        plt.tight_layout()
        return self.plot_to_surf(fig)

    def plot_ch3_pre(self):
        fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
        fig.patch.set_alpha(0.8)
        data_a = np.random.normal(10, 2, 50)
        data_b = np.random.normal(15, 3, 50)
        ax.hist(data_a, alpha=0.5, label='A')
        ax.hist(data_b, alpha=0.5, label='B')
        ax.set_title("Raw Data: Hard to distinguish")
        ax.legend()
        plt.tight_layout()
        return self.plot_to_surf(fig)

    def plot_ch3_post(self):
        fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
        fig.patch.set_alpha(0.8)
        data_a = np.random.normal(10, 2, 50)
        data_b = np.random.normal(15, 3, 50)
        ax.boxplot([data_a, data_b], labels=['Suspect A', 'Suspect B'])
        ax.set_title("RESULT: Significant Difference (P<0.01)", color='green', weight='bold')
        plt.tight_layout()
        return self.plot_to_surf(fig)

    def plot_ch4_pre(self):
        fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
        fig.patch.set_alpha(0.8)
        x = np.linspace(1, 100, 100)
        noise = np.random.normal(0, x * 0.1, 100) 
        ax.scatter(x, noise, c='purple', alpha=0.6)
        ax.set_title("Residuals: Funnel Shape (Heteroscedasticity)")
        plt.tight_layout()
        return self.plot_to_surf(fig)

    def plot_ch4_post(self):
        fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
        fig.patch.set_alpha(0.8)
        x = np.linspace(1, 100, 100)
        noise = np.random.normal(0, 2, 100) 
        ax.scatter(x, noise, c='green', alpha=0.6)
        ax.axhline(0, color='black', linestyle='--')
        ax.set_title("WLS FIXED: Uniform Residuals", color='green', weight='bold')
        plt.tight_layout()
        return self.plot_to_surf(fig)

    def plot_ch5_pre(self):
        fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
        fig.patch.set_alpha(0.8)
        steps = np.random.normal(0, 1, 100)
        price = 100 + np.cumsum(steps)
        ax.plot(price, c='gray')
        ax.set_title("Raw Time Series (Non-stationary)")
        plt.tight_layout()
        return self.plot_to_surf(fig)

    def plot_ch5_post(self):
        fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
        fig.patch.set_alpha(0.8)
        steps = np.random.normal(0, 1, 100)
        price = 100 + np.cumsum(steps)
        future = np.arange(100, 120)
        future_price = price[-1] - np.arange(20) * 2 
        ax.plot(np.arange(100), price, label='History')
        ax.plot(future, future_price, color='red', linestyle='--', label='Crash Forecast')
        ax.fill_between(future, future_price - 5, future_price + 5, color='red', alpha=0.2)
        ax.set_title("FORECAST: The Crash", color='red', weight='bold')
        ax.legend()
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
        
        # 加载初始图 (Pre)
        if "plot_pre" in data:
            self.current_plot_surf = data["plot_pre"]()

    def handle_puzzle_click(self, pos):
        if pygame.Rect(900, 600, 200, 60).collidepoint(pos):
            self.check_puzzle()
            return
        
        # 判定新状态 PUZZLE_SOLVED
        if self.state == "PUZZLE_SOLVED":
             self.ai_popup_msg = TEXTS["CN"]["correct"]
             self.show_ai_popup = True
             self.state = "VICTORY_WAIT"
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
            # 成功：切换到 Post 图，进入中间状态供玩家观看
            data = self.chapters[self.current_chapter]
            if "plot_post" in data:
                self.current_plot_surf = data["plot_post"]()
            
            # 标记为已解决，改变界面提示，等待点击
            self.state = "PUZZLE_SOLVED"
            
        else:
            self.puzzle_attempts -= 1
            if self.puzzle_attempts <= 0:
                self.ai_popup_msg = TEXTS["CN"]["game_over"]
                self.show_ai_popup = True
                self.auto_solve()
                data = self.chapters[self.current_chapter]
                if "plot_post" in data:
                    self.current_plot_surf = data["plot_post"]()
                self.state = "VICTORY_WAIT" # 失败后自动通过，直接进结算
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
                    b.rect.topleft = (340, 150 + i*80)
                    break

    # --- 渲染逻辑 ---
    def draw_menu(self):
        bg = assets.images.get("bg_menu")
        if bg: self.screen.blit(bg, (0,0))
        
        font_t1 = assets.get_font(85) 
        s1 = font_t1.render("Dr. Sigma's", True, BLACK) 
        self.screen.blit(s1, (SCREEN_WIDTH//2 - s1.get_width()//2 + 4, 74))
        t1 = font_t1.render("Dr. Sigma's", True, YELLOW) 
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

    def draw_conclusion(self):
        self.screen.fill(BLACK)
        self.update_typewriter()
        t = assets.get_font(40).render(TEXTS["CN"]["conclusion_title"], True, RED)
        self.screen.blit(t, (SCREEN_WIDTH//2 - t.get_width()//2, 50))
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
        y = 120
        for line in lines:
            if line.strip() == "": y += 20; continue
            s = font.render(line, True, WHITE)
            self.screen.blit(s, (100, y))
            y += 40
        if self.type_idx >= len(self.target_text):
            hint = assets.get_font(20).render(">>> 点击进入下一章", True, LIGHT_GRAY)
            self.screen.blit(hint, (SCREEN_WIDTH - 300, SCREEN_HEIGHT - 60))

    def draw_the_end(self):
        self.screen.fill(BLACK)
        self.update_typewriter()
        font = assets.get_font(80)
        text_surf = font.render(self.current_text, True, WHITE)
        self.screen.blit(text_surf, (SCREEN_WIDTH//2 - text_surf.get_width()//2, SCREEN_HEIGHT//2 - 50))
        if self.type_idx >= len(self.target_text):
            sub = assets.get_font(24).render("Click anywhere to exit", True, GRAY)
            self.screen.blit(sub, (SCREEN_WIDTH//2 - sub.get_width()//2, SCREEN_HEIGHT//2 + 80))

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
        chapter_bg_name = self.chapters[self.current_chapter].get("bg", "bg_office")
        bg = assets.images.get(chapter_bg_name)
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
        elif "Suspect" in speaker:
            sus_img = assets.images.get("char_suspect")
            if sus_img: self.screen.blit(sus_img, (SCREEN_WIDTH - sus_img.get_width(), SCREEN_HEIGHT - sus_img.get_height()))
        box = pygame.Rect(50, SCREEN_HEIGHT-220, SCREEN_WIDTH-100, 200)
        s = pygame.Surface((box.width, box.height), pygame.SRCALPHA)
        s.fill(TRANS_BG)
        self.screen.blit(s, box)
        if speaker == "Detective": name_color = YELLOW
        elif speaker == "Assistant": name_color = (0, 255, 255)
        else: name_color = RED 
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
        self.screen.fill(BRIEFING_BG_COLOR)
        info = self.chapters[self.current_chapter]["briefing"]
        t = assets.get_font(48).render(TEXTS["CN"]["briefing_title"], True, YELLOW)
        self.screen.blit(t, (SCREEN_WIDTH//2 - t.get_width()//2, 50))
        start_y = 150
        gap = 15 # 大幅减小 Gap
        font_head = assets.get_font(30)
        font_body = assets.get_font(24)
        def draw_section(title, content, y):
            head = font_head.render(f"■ {title}:", True, ORANGE)
            self.screen.blit(head, (100, y))
            if isinstance(content, list):
                for i, line in enumerate(content):
                    body = font_body.render(line, True, WHITE)
                    self.screen.blit(body, (140, y + 35 + i*28)) # 减小行间距
                return y + 35 + len(content)*28 + gap
            else:
                words = content
                lines = []
                current_line = ""
                for char in words:
                    if font_body.size(current_line + char)[0] < 900:
                        current_line += char
                    else:
                        lines.append(current_line)
                        current_line = char
                lines.append(current_line)
                for i, line in enumerate(lines):
                    body = font_body.render(line, True, CYAN if title=="核心逻辑" else WHITE)
                    self.screen.blit(body, (140, y + 35 + i*28))
                return y + 35 + len(lines)*28 + gap
        
        cur_y = draw_section("面临问题", info["problem"], start_y)
        cur_y = draw_section("统计方法", info["method"], cur_y)
        cur_y = draw_section("核心逻辑", info["logic"], cur_y)
        cur_y = draw_section("预期目标", info["expected"], cur_y)
        cur_y = draw_section("执行步骤 (提示)", info["steps"], cur_y)
        Button(SCREEN_WIDTH - 250, SCREEN_HEIGHT - 100, 200, 60, TEXTS["CN"]["btn_start_puzzle"], self.enter_puzzle, GREEN).draw(self.screen)

    def draw_puzzle(self):
        pygame.draw.rect(self.screen, (30,30,30), (0,0, 320, SCREEN_HEIGHT))
        pygame.draw.rect(self.screen, (50,50,50), (320,0, 340, SCREEN_HEIGHT))
        pygame.draw.rect(self.screen, (70,70,70), (660,0, SCREEN_WIDTH-660, SCREEN_HEIGHT))
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
            self.screen.blit(self.current_plot_surf, (660, 150))
        for b in self.puzzle_blocks:
            b.draw(self.screen)
            
        if self.state == "PUZZLE_SOLVED":
            hint = assets.get_font(24).render(TEXTS["CN"]["continue_hint"], True, GREEN)
            pygame.draw.rect(self.screen, BLACK, (900, 600, 350, 60)) 
            self.screen.blit(hint, (800, 615)) 
        else:
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
        btn_ai_help = Button(20, 20, 120, 40, TEXTS["CN"]["ai_btn"], lambda: setattr(self, 'show_ai_dialog', True), YELLOW, BLACK)

        while True:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                
                if self.show_ai_answer_overlay:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        panel_right = 200 + 880
                        panel_top = 150
                        close_btn_rect = pygame.Rect(panel_right - 50, panel_top + 20, 30, 30)
                        if close_btn_rect.collidepoint(event.pos):
                            self.show_ai_answer_overlay = False
                    continue

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

                if self.show_ai_popup:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        self.show_ai_popup = False
                        if self.state == "VICTORY_WAIT":
                            self.state = "CONCLUSION"
                            self.reset_typewriter(self.chapters[self.current_chapter]["conclusion"])
                    continue
                
                if self.state == "SETTINGS":
                    self.input_url.handle_event(event)
                    self.input_key.handle_event(event)
                    self.input_model.handle_event(event)

                if event.type == pygame.MOUSEBUTTONDOWN:
                    pos = event.pos
                    
                    if self.state not in ["MENU", "SETTINGS", "STORY_INTRO", "THE_END"]:
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
                    
                    elif self.state == "PUZZLE_SOLVED":
                        # 点击任意处进入 VICTORY_WAIT 触发弹窗
                        self.ai_popup_msg = TEXTS["CN"]["correct"]
                        self.show_ai_popup = True
                        self.state = "VICTORY_WAIT"
                    
                    elif self.state == "CONCLUSION":
                        if self.type_idx < len(self.target_text):
                            self.type_idx = len(self.target_text)
                            self.current_text = self.target_text
                        else:
                            self.current_chapter += 1
                            if self.current_chapter >= len(self.chapters):
                                self.state = "THE_END"
                                self.reset_typewriter("The End")
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
                    
                    elif self.state == "THE_END":
                        if self.type_idx >= len(self.target_text):
                            pygame.quit()
                            sys.exit()

            if self.state == "MENU": self.draw_menu()
            elif self.state == "SETTINGS": self.draw_settings()
            elif self.state == "STORY_INTRO": self.draw_story_intro()
            elif self.state == "SCENE": self.comp_rect_cache = self.draw_scene()
            elif self.state == "DESKTOP": self.file_rect_cache = self.draw_desktop()
            elif self.state == "DIALOGUE": self.draw_dialogue()
            elif self.state == "BRIEFING": self.draw_briefing()
            elif self.state == "PUZZLE": self.draw_puzzle()
            elif self.state == "PUZZLE_SOLVED": self.draw_puzzle()
            elif self.state == "CONCLUSION": self.draw_conclusion()
            elif self.state == "THE_END": self.draw_the_end()
            
            if self.state not in ["MENU", "SETTINGS", "STORY_INTRO", "THE_END"] and not self.show_ai_dialog and not self.show_ai_answer_overlay:
                btn_ai_help.draw(self.screen)
            
            if self.show_ai_dialog:
                self.draw_ai_dialog()
            
            self.draw_ai_popup()
            self.draw_ai_answer_overlay()
            
            pygame.display.flip()
            self.clock.tick(FPS)

if __name__ == "__main__":
    game = Game()
    game.run()