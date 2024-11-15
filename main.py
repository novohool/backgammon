import pygame
import sys
import time
from enum import Enum
from typing import Tuple, List, Optional
from pydub import AudioSegment
import json
import os

# Game constants
SCREEN_WIDTH = 800  
SCREEN_HEIGHT = 600
BOARD_SIZE = 15
CELL_SIZE = 35

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
RED = (255, 0, 0)
BOARD_COLOR = (220, 179, 92)

class GameState(Enum):
    MENU = 1
    PLAYING = 2
    GAME_OVER = 3
    SETTINGS = 4

class PlayerType(Enum):
    HUMAN = 1
    AI = 2

class GameMode(Enum):
    PVP = 1
    PVE = 2

class Difficulty(Enum):
    EASY = 1
    MEDIUM = 2
    HARD = 3

class Stone:
    def __init__(self, x: int, y: int, color: Tuple[int, int, int]):
        self.x = x
        self.y = y
        self.color = color
        self.timestamp = time.time()

class Board:
    def __init__(self):
        self.size = BOARD_SIZE
        self.stones: List[Stone] = []
        self.last_move: Optional[Stone] = None
        
    def place_stone(self, x: int, y: int, color: Tuple[int, int, int]) -> bool:
        if self.is_valid_move(x, y):
            stone = Stone(x, y, color)
            self.stones.append(stone)
            self.last_move = stone
            return True
        return False
    
    def is_valid_move(self, x: int, y: int) -> bool:
        if x < 0 or x >= self.size or y < 0 or y >= self.size:
            return False
        return not any(stone.x == x and stone.y == y for stone in self.stones)
    
    def get_stone_at(self, x: int, y: int) -> Optional[Stone]:
        for stone in self.stones:
            if stone.x == x and stone.y == y:
                return stone
        return None
    
    def check_win(self, last_stone: Optional[Stone]) -> bool:
        if last_stone is None:
            return False
        
        directions = [(1,0), (0,1), (1,1), (1,-1)]
        for dx, dy in directions:
            count = 1
            # Check positive direction
            for i in range(1, 5):
                x, y = last_stone.x + dx*i, last_stone.y + dy*i
                stone = self.get_stone_at(x, y)
                if not stone or stone.color != last_stone.color:
                    break
                count += 1
            # Check negative direction    
            for i in range(1, 5):
                x, y = last_stone.x - dx*i, last_stone.y - dy*i
                stone = self.get_stone_at(x, y)
                if not stone or stone.color != last_stone.color:
                    break
                count += 1
            if count >= 5:
                return True
        return False

class AIPlayer:
    def __init__(self, difficulty: Difficulty):
        self.difficulty = difficulty
        # 评分标准，根据难度变化
        self.weights = {
            Difficulty.EASY: {"2": 10, "3": 50, "4": 1000, "5": 100000},
            Difficulty.MEDIUM: {"2": 20, "3": 100, "4": 2000, "5": 20000},
            Difficulty.HARD: {"2": 30, "3": 200, "4": 4000, "5": 40000}
        }
    
    def get_move(self, board: Board) -> Tuple[int, int]:
        best_score = float('-inf')
        best_move = None

        # 遍历棋盘空位，计算每个空位的评分
        for x in range(board.size):
            for y in range(board.size):
                if board.is_valid_move(x, y):
                    # 计算当前位置的总评分
                    score = self._evaluate_position(x, y, board, WHITE) + self._evaluate_position(x, y, board, BLACK)
                    if score > best_score:
                        best_score = score
                        best_move = (x, y)

        # 返回评分最高的位置
        return best_move if best_move else (board.size // 2, board.size // 2)
    
    def _evaluate_position(self, x: int, y: int, board: Board, color: Tuple[int, int, int]) -> int:
        """计算特定位置的评分"""
        total_score = 0
        directions = [(1, 0), (0, 1), (1, 1), (1, -1)]
        weights = self.weights[self.difficulty]  # 根据难度选择评分标准

        for dx, dy in directions:
            count = 1
            open_ends = 0

            # 正方向统计
            for i in range(1, 5):
                nx, ny = x + i * dx, y + i * dy
                stone = board.get_stone_at(nx, ny)
                if stone and stone.color == color:
                    count += 1
                else:
                    if not stone:
                        open_ends += 1
                    break

            # 反方向统计
            for i in range(1, 5):
                nx, ny = x - i * dx, y - i * dy
                stone = board.get_stone_at(nx, ny)
                if stone and stone.color == color:
                    count += 1
                else:
                    if not stone:
                        open_ends += 1
                    break

            # 根据棋型评分
            if count >= 5:
                total_score += weights["5"]  # 五连
            elif count == 4 and open_ends > 0:
                total_score += weights["4"]  # 活四
            elif count == 3 and open_ends > 0:
                total_score += weights["3"]  # 活三
            elif count == 2 and open_ends > 0:
                total_score += weights["2"]  # 活二

        return total_score


class SoundManager:
    def __init__(self):
        pygame.mixer.init()
        self.sounds = {
            'place': pygame.mixer.Sound('assets/stone_place.wav'),
            'win': pygame.mixer.Sound('assets/win.wav'),
            'click': pygame.mixer.Sound('assets/click.wav')
        }
    
    def play(self, sound_name: str):
        if sound_name in self.sounds:
            self.sounds[sound_name].play()

class Button:
    def __init__(self, x: int, y: int, width: int, height: int, text: str):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.is_hovered = False
        
    def draw(self, screen: pygame.Surface):
        color = GRAY if self.is_hovered else BLACK
        pygame.draw.rect(screen, color, self.rect, 2)
        
        font = pygame.font.Font(None, 36)
        text_surface = font.render(self.text, True, color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.is_hovered:
                return True
        return False

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Gomoku")
        
        self.state = GameState.MENU
        self.board = Board()
        self.sound_manager = SoundManager()
        self.game_mode = GameMode.PVE
        self.current_player = PlayerType.HUMAN
        self.ai = AIPlayer(Difficulty.MEDIUM)
        
        # Create menu buttons
        self.menu_buttons = [
            Button(300, 200, 200, 50, "Player vs AI"),
            Button(300, 270, 200, 50, "Player vs Player"),
            Button(300, 340, 200, 50, "Settings"),
            Button(300, 410, 200, 50, "Exit")
        ]
    
    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    self.handle_event(event)
            
            self.update()
            self.draw()
            
            pygame.display.flip()
        
        pygame.quit()
    
    def handle_event(self, event: pygame.event.Event):
        if self.state == GameState.MENU:
            self.handle_menu_event(event)
        elif self.state == GameState.PLAYING:
            self.handle_game_event(event)
        elif self.state == GameState.SETTINGS:
            self.handle_menu_event(event)
    
    def handle_menu_event(self, event: pygame.event.Event):
        for i, button in enumerate(self.menu_buttons):
            if button.handle_event(event):
                if i == 0:  # PvE
                    self.game_mode = GameMode.PVE
                    self.state = GameState.PLAYING
                elif i == 1:  # PvP
                    self.game_mode = GameMode.PVP
                    self.state = GameState.PLAYING
                elif i == 2:  # Settings
                    self.state = GameState.SETTINGS
                elif i == 3:  # Exit
                    pygame.event.post(pygame.event.Event(pygame.QUIT))
                
                self.sound_manager.play('click')
    
    def handle_game_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN and self.current_player == PlayerType.HUMAN:
            x, y = self.get_board_position(event.pos)
            if self.board.place_stone(x, y, BLACK):
                self.sound_manager.play('place')
                
                if self.board.last_move and self.board.check_win(self.board.last_move):
                    self.sound_manager.play('win')
                    self.state = GameState.GAME_OVER
                elif self.game_mode == GameMode.PVE:
                    self.current_player = PlayerType.AI
    
    def update(self):
        if self.state == GameState.PLAYING and self.current_player == PlayerType.AI:
            x, y = self.ai.get_move(self.board)
            if self.board.place_stone(x, y, WHITE):
                self.sound_manager.play('place')
                
                if self.board.check_win(self.board.last_move):
                    self.sound_manager.play('win')
                    self.state = GameState.GAME_OVER
                else:
                    self.current_player = PlayerType.HUMAN
    
    def draw(self):
        self.screen.fill(WHITE)
        
        if self.state == GameState.MENU:
            self.draw_menu()
        elif self.state == GameState.PLAYING or self.state == GameState.GAME_OVER:
            self.draw_game()
        elif self.state == GameState.SETTINGS:
            self.draw_settings()
    
    def draw_menu(self):
        title_font = pygame.font.Font(None, 72)
        title_text = title_font.render("Gomoku", True, BLACK)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, 100))
        self.screen.blit(title_text, title_rect)
        
        for button in self.menu_buttons:
            button.draw(self.screen)
    
    def draw_game(self):
        # Draw board background
        board_surface = pygame.Surface((BOARD_SIZE * CELL_SIZE, BOARD_SIZE * CELL_SIZE))
        board_surface.fill(BOARD_COLOR)
        
        # Draw grid lines
        for i in range(BOARD_SIZE):
            start_pos = (i * CELL_SIZE, 0)
            end_pos = (i * CELL_SIZE, BOARD_SIZE * CELL_SIZE)
            pygame.draw.line(board_surface, BLACK, start_pos, end_pos)
            
            start_pos = (0, i * CELL_SIZE)
            end_pos = (BOARD_SIZE * CELL_SIZE, i * CELL_SIZE)
            pygame.draw.line(board_surface, BLACK, start_pos, end_pos)
        
        # Draw stones
        for stone in self.board.stones:
            center = (stone.x * CELL_SIZE + CELL_SIZE//2, 
                     stone.y * CELL_SIZE + CELL_SIZE//2)
            pygame.draw.circle(board_surface, stone.color, center, CELL_SIZE//2 - 2)
            
            # Highlight last move
            if stone == self.board.last_move:
                pygame.draw.circle(board_surface, RED, center, CELL_SIZE//2 - 2, 2)
        
        # Center the board on screen
        board_x = (SCREEN_WIDTH - BOARD_SIZE * CELL_SIZE) // 2
        board_y = (SCREEN_HEIGHT - BOARD_SIZE * CELL_SIZE) // 2
        self.screen.blit(board_surface, (board_x, board_y))
        
        if self.state == GameState.GAME_OVER:
            self.draw_game_over()
    
    def draw_game_over(self):
        s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        s.fill((255, 255, 255, 128))
        self.screen.blit(s, (0,0))
        
        font = pygame.font.Font(None, 72)
        if self.board.last_move:
            winner = "Black" if self.board.last_move.color == BLACK else "White"
            text = font.render(f"{winner} Wins!", True, BLACK)
            text_rect = text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            self.screen.blit(text, text_rect)
    
    def draw_settings(self):
        # Settings UI implementation
        pass
    
    def get_board_position(self, pos: Tuple[int, int]) -> Tuple[int, int]:
        board_x = (SCREEN_WIDTH - BOARD_SIZE * CELL_SIZE) // 2
        board_y = (SCREEN_HEIGHT - BOARD_SIZE * CELL_SIZE) // 2
        x = (pos[0] - board_x) // CELL_SIZE
        y = (pos[1] - board_y) // CELL_SIZE
        return x, y

if __name__ == "__main__":
    game = Game()
    game.run()
