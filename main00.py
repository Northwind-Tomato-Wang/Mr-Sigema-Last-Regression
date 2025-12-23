import pygame
import sys
import os
import numpy as np
import pandas as pd
import matplotlib
# 设置非交互式后端，防止弹窗干扰 Pygame
matplotlib.use("Agg") 
import matplotlib.pyplot as plt
import statsmodels.api as sm
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

# --- 游戏配置常量 ---
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
FPS = 30

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (50, 50, 50)
BLUE = (70, 130, 180)
RED = (200, 50, 50)
GREEN = (50, 200, 50)
TEXT_BG_COLOR = (0, 0, 0, 180) # 半透明黑色

# --- 资源管理器 ---
class AssetManager:
    def __init__(self):
        self.images = {}
        
    def load_image(self, name, filename, fallback_color=(100, 100, 100)):
        # 兼容不同系统的路径拼接
        path = os.path.join("assets", filename)
        try:
            img = pygame.image.load(path)
            # 简单的自适应缩放背景
            if "bg_" in name:
                img = pygame.transform.scale(img, (SCREEN_WIDTH, SCREEN_HEIGHT))
            self.images[name] = img
        except Exception as e:
            # 这里静默失败，仅在控制台提示，保证游戏不崩
            print(f"Warning: Image {filename} not found or error loading. Using fallback block.")
            surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT) if "bg_" in name else (200, 400))
            surf.fill(fallback_color)
            # 如果是人物，画个简单的圆头示意
            if "char_" in name:
                pygame.draw.circle(surf, (200, 200, 200), (100, 50), 40)
            self.images[name] = surf

    def get_image(self, name):
        return self.images.get(name)

# --- 数据分析引擎 (核心统计逻辑) ---
class DataEngine:
    def __init__(self):
        pass

    def generate_plot_surface(self, fig):
        """
        修复版：将 Matplotlib 的图表转换为 Pygame 的 Surface
        兼容 Retina 屏幕和不同 DPI 设置
        """
        canvas = FigureCanvas(fig)
        canvas.draw()
        
        # 使用 buffer_rgba 获取原始 RGBA 数据 (比 tostring_rgb 更稳定)
        raw_data = canvas.buffer_rgba()
        # 获取 Canvas 渲染后的实际尺寸 (整数元组)
        size = canvas.get_width_height()
        
        # 将数据转换为 Pygame Surface
        # 注意：使用 RGBA 模式，而不是 RGB
        surf = pygame.image.frombuffer(raw_data, size, "RGBA")
        
        return surf

    def level_1_regression(self):
        """第一章：线性回归图"""
        np.random.seed(42)
        X = np.random.rand(100) * 10
        # 陷阱：截距是负的 (亏钱)
        y = 0.5 * X - 5 + np.random.randn(100) 
        
        fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
        # 设置图表背景透明以便融入游戏
        fig.patch.set_alpha(0.9) 
        
        ax.scatter(X, y, color='blue', alpha=0.5, label='Actual Returns')
        
        # 拟合
        X_const = sm.add_constant(X)
        model = sm.OLS(y, X_const).fit()
        pred = model.predict(X_const)
        
        ax.plot(X, pred, color='red', label=f'OLS: y={model.params[1]:.2f}x + {model.params[0]:.2f}')
        ax.set_title("Strategy Returns vs Market (Trap: Negative Alpha)")
        ax.set_xlabel("Market Return")
        ax.set_ylabel("Sigma Strategy Return")
        ax.legend()
        plt.tight_layout()
        
        surf = self.generate_plot_surface(fig)
        plt.close(fig) # 释放内存
        return surf, model.params[0] 

    def level_2_multicollinearity(self):
        """第二章：多重共线性"""
        np.random.seed(42)
        size = 100
        # X1: Mining Load, X2: Server Latency (高度相关)
        x1 = np.random.rand(size) * 10 
        x2 = x1 * 0.9 + np.random.normal(0, 0.5, size) 
        
        fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
        fig.patch.set_alpha(0.9)

        ax.scatter(x1, x2, color='green')
        ax.set_title("Server Latency vs Mining Load (Correlation!)")
        ax.set_xlabel("Mining Load")
        ax.set_ylabel("Server Latency")
        plt.tight_layout()
        
        surf = self.generate_plot_surface(fig)
        plt.close(fig)
        return surf

    def level_4_heteroscedasticity(self):
        """第四章：异方差"""
        np.random.seed(42)
        x = np.linspace(1, 100, 100)
        # 误差随着 x 增大而增大 (喇叭口)
        noise = np.random.normal(0, x * 0.5, 100)
        y = 3 * x + noise

        model = sm.OLS(y, sm.add_constant(x)).fit()
        resid = model.resid

        fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
        fig.patch.set_alpha(0.9)

        ax.scatter(x, resid, color='purple')
        ax.axhline(0, color='black', linestyle='--')
        ax.set_title("Residual Plot (Look for the Funnel Shape)")
        ax.set_xlabel("Transaction Amount")
        ax.set_ylabel("Residuals")
        plt.tight_layout()

        surf = self.generate_plot_surface(fig)
        plt.close(fig)
        return surf

# --- 游戏引擎与界面 ---
class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Dr. Sigma's Last Regression")
        self.clock = pygame.time.Clock()
        
        # 字体初始化
        self.font = pygame.font.SysFont("Arial", 24) 
        self.title_font = pygame.font.SysFont("Arial", 40, bold=True)
        
        self.assets = AssetManager()
        self.load_assets()
        self.data_engine = DataEngine()
        
        self.state = "INTRO" # INTRO, DIALOGUE, PUZZLE, VICTORY
        self.current_level = 1
        
        # 剧情状态
        self.dialogue_index = 0
        self.dialogues = []
        self.current_bg = "bg_office"
        
        # 解密状态
        self.puzzle_surf = None
        self.puzzle_options = [] 
        self.feedback_text = ""

        self.setup_level_data()

    def load_assets(self):
        """加载所有需要的图片资源"""
        self.assets.load_image("bg_office", "bg_office.jpg", (50, 50, 80))
        self.assets.load_image("bg_server", "bg_server.jpg", (20, 40, 20))
        self.assets.load_image("bg_lab", "bg_lab.jpg", (80, 80, 80))
        
        self.assets.load_image("char_detective", "char_detective.png", (0, 0, 150))
        self.assets.load_image("char_assistant", "char_assistant.png", (0, 150, 150))

    def setup_level_data(self):
        """定义每一章的剧情文本和解密逻辑"""
        self.dialogue_index = 0 # 重置对话进度
        
        if self.current_level == 1:
            self.current_bg = "bg_office"
            self.dialogues = [
                {"speaker": "Detective", "text": "Dr. Sigma died mysteriously. I need to check his data.", "img": "char_detective"},
                {"speaker": "Assistant", "text": "Sir, I recovered a file. It's his strategy performance vs the Market.", "img": "char_assistant"},
                {"speaker": "Detective", "text": "Let's run a Simple Linear Regression (OLS).", "img": "char_detective"},
            ]
        elif self.current_level == 2:
            self.current_bg = "bg_server"
            self.dialogues = [
                {"speaker": "Detective", "text": "Wait, the intercept was negative! He was losing money!", "img": "char_detective"},
                {"speaker": "Assistant", "text": "I found two new variables: Server Latency and Mining Load.", "img": "char_assistant"},
                {"speaker": "Detective", "text": "If I put both in the regression, the coefficients go crazy.", "img": "char_detective"},
            ]
        elif self.current_level == 3: # Skip level 3 for demo flow but keep logic
             self.current_level = 4
             self.setup_level_data()
             return
        elif self.current_level == 4:
            self.current_bg = "bg_lab"
            self.dialogues = [
                {"speaker": "Detective", "text": "We caught the miner, but money is still leaking.", "img": "char_detective"},
                {"speaker": "Assistant", "text": "Look at Suspect B's transfer records.", "img": "char_assistant"},
                {"speaker": "Detective", "text": "The regression looks okay, but something is wrong with the errors.", "img": "char_detective"},
            ]

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.state == "INTRO":
                    self.state = "DIALOGUE"
                    self.setup_level_data()
                
                elif self.state == "DIALOGUE":
                    if self.dialogue_index < len(self.dialogues) - 1:
                        self.dialogue_index += 1
                    else:
                        # 剧情结束，进入解密环节
                        self.state = "PUZZLE"
                        self.init_puzzle()
                
                elif self.state == "PUZZLE":
                    mx, my = pygame.mouse.get_pos()
                    btn_y = SCREEN_HEIGHT - 150
                    for i, opt in enumerate(self.puzzle_options):
                        rect = pygame.Rect(50 + i*320, btn_y, 300, 60)
                        if rect.collidepoint(mx, my):
                            if opt["correct"]:
                                self.feedback_text = "Correct! Analysis confirmed."
                                # 强制重绘一次显示正确提示
                                self.draw()
                                pygame.display.flip()
                                pygame.time.wait(1000) # 停顿1秒让玩家看到 Correct
                                
                                self.current_level += 1
                                if self.current_level > 4: 
                                    self.state = "VICTORY"
                                else:
                                    self.setup_level_data()
                                    self.state = "DIALOGUE"
                            else:
                                self.feedback_text = opt["fail_msg"]

    def init_puzzle(self):
        self.feedback_text = ""
        if self.current_level == 1:
            self.puzzle_surf, intercept = self.data_engine.level_1_regression()
            self.puzzle_options = [
                {"text": "Model looks good (High R2)", "correct": False, "fail_msg": "Look closer at the Intercept (Alpha). It's negative!"},
                {"text": "Intercept is Negative (Fraud?)", "correct": True, "fail_msg": ""},
                {"text": "Ignore Data", "correct": False, "fail_msg": "You can't ignore the evidence!"}
            ]
        elif self.current_level == 2:
            self.puzzle_surf = self.data_engine.level_2_multicollinearity()
            self.puzzle_options = [
                {"text": "Keep both variables", "correct": False, "fail_msg": "P-values are insignificant due to High VIF!"},
                {"text": "Check VIF & Drop One", "correct": True, "fail_msg": ""},
            ]
        elif self.current_level == 4:
            self.puzzle_surf = self.data_engine.level_4_heteroscedasticity()
            self.puzzle_options = [
                {"text": "Accept OLS Model", "correct": False, "fail_msg": "Residuals are funnel-shaped (Heteroscedasticity)!"},
                {"text": "Use WLS / Log Transform", "correct": True, "fail_msg": ""},
            ]

    def draw_text_box(self, text, speaker_name):
        # 绘制底部半透明对话框
        box_rect = pygame.Rect(20, SCREEN_HEIGHT - 200, SCREEN_WIDTH - 40, 180)
        s = pygame.Surface((box_rect.width, box_rect.height), pygame.SRCALPHA)
        s.fill(TEXT_BG_COLOR)
        self.screen.blit(s, box_rect)
        
        # 绘制名字
        name_surf = self.title_font.render(speaker_name, True, BLUE)
        self.screen.blit(name_surf, (box_rect.x + 20, box_rect.y + 10))
        
        # 绘制文本 (简单的换行处理)
        words = text.split(' ')
        lines = []
        current_line = []
        for word in words:
            current_line.append(word)
            test_surf = self.font.render(' '.join(current_line), True, WHITE)
            if test_surf.get_width() > box_rect.width - 40:
                current_line.pop()
                lines.append(' '.join(current_line))
                current_line = [word]
        lines.append(' '.join(current_line))
        
        for i, line in enumerate(lines):
            line_surf = self.font.render(line, True, WHITE)
            self.screen.blit(line_surf, (box_rect.x + 20, box_rect.y + 60 + i * 30))

    def draw(self):
        # 1. 绘制背景
        bg = self.assets.get_image(self.current_bg)
        if bg:
            self.screen.blit(bg, (0, 0))
        else:
            self.screen.fill(GRAY)
        
        if self.state == "INTRO":
            s_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            s_surf.fill((0,0,0,150)) # 蒙版
            self.screen.blit(s_surf, (0,0))

            title = self.title_font.render("Dr. Sigma's Last Regression", True, WHITE)
            start = self.font.render("Click anywhere to start investigation", True, WHITE)
            self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 300))
            self.screen.blit(start, (SCREEN_WIDTH//2 - start.get_width()//2, 400))
            
        elif self.state == "DIALOGUE":
            # 绘制当前说话人立绘
            if self.dialogues:
                data = self.dialogues[self.dialogue_index]
                char_img = self.assets.get_image(data["img"])
                if char_img:
                    # 侦探在左，其他人在右
                    x_pos = 100 if data["speaker"]=="Detective" else SCREEN_WIDTH-350
                    self.screen.blit(char_img, (x_pos, SCREEN_HEIGHT-500))
                
                self.draw_text_box(data["text"], data["speaker"])
            
        elif self.state == "PUZZLE":
            # 绘制图表
            if self.puzzle_surf:
                x = SCREEN_WIDTH//2 - self.puzzle_surf.get_width()//2
                y = 50
                self.screen.blit(self.puzzle_surf, (x, y))
            
            # 绘制问题提示
            hint = self.font.render("Analyst AI: How should we interpret this data?", True, WHITE)
            pygame.draw.rect(self.screen, BLACK, (SCREEN_WIDTH//2 - 250, 10, 500, 30))
            self.screen.blit(hint, (SCREEN_WIDTH//2 - hint.get_width()//2, 15))

            # 绘制反馈信息
            if self.feedback_text:
                color = GREEN if "Correct" in self.feedback_text else RED
                fb = self.font.render(self.feedback_text, True, color)
                pygame.draw.rect(self.screen, BLACK, (SCREEN_WIDTH//2 - 300, 480, 600, 40))
                self.screen.blit(fb, (SCREEN_WIDTH//2 - fb.get_width()//2, 490))

            # 绘制选项按钮
            btn_y = SCREEN_HEIGHT - 150
            for i, opt in enumerate(self.puzzle_options):
                rect = pygame.Rect(50 + i*320, btn_y, 300, 60)
                # 鼠标悬停效果
                mouse_pos = pygame.mouse.get_pos()
                btn_color = (100, 160, 210) if rect.collidepoint(mouse_pos) else BLUE
                
                pygame.draw.rect(self.screen, btn_color, rect, border_radius=10)
                pygame.draw.rect(self.screen, WHITE, rect, 2, border_radius=10)
                
                txt = self.font.render(opt["text"], True, WHITE)
                self.screen.blit(txt, (rect.centerx - txt.get_width()//2, rect.centery - txt.get_height()//2))

        elif self.state == "VICTORY":
            self.screen.fill(BLACK)
            t = self.title_font.render("CASE CLOSED", True, GREEN)
            sub = self.font.render("You solved the mystery using Statistics!", True, WHITE)
            self.screen.blit(t, (SCREEN_WIDTH//2 - t.get_width()//2, 300))
            self.screen.blit(sub, (SCREEN_WIDTH//2 - sub.get_width()//2, 400))

        pygame.display.flip()

    def run(self):
        while True:
            self.handle_input()
            self.draw()
            self.clock.tick(FPS)

if __name__ == "__main__":
    game = Game()
    game.run()