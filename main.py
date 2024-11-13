import pygame
import sys

# 初始化 Pygame
pygame.init()

# 设置屏幕大小
screen_width = 600
screen_height = 600
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("五子棋")

# 定义颜色
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (200, 200, 200)  # 改为浅灰色，方便在白色背景上识别

# 棋盘参数
BOARD_SIZE = 15
CELL_SIZE = screen_width // BOARD_SIZE

# 全局变量
list1 = []  # AI
list2 = []  # human
list3 = []  # all
list_all = []  # 整个棋盘的点

# 每种棋型的分数
shape_score = {
    2: 10,   # 活二
    3: 50,   # 活三
    4: 1000, # 活四
    5: 100000 # 五连
}

def ai():
    best_score = -1
    best_move = None

    # 遍历所有空位置，计算该位置的评分
    for x in range(BOARD_SIZE):
        for y in range(BOARD_SIZE):
            if (x, y) in list3:
                continue  # 跳过已占用位置

            # 计算当前位置的评分
            score = evaluate_position(x, y, list1) + evaluate_position(x, y, list2)
            
            if score > best_score:
                best_score = score
                best_move = (x, y)

    return best_move if best_move else (BOARD_SIZE // 2, BOARD_SIZE // 2)  # 如果无最佳位置，则下在中心

def evaluate_position(x, y, stones):
    """计算在 (x, y) 位置下棋的得分"""
    total_score = 0
    directions = [(1, 0), (0, 1), (1, 1), (1, -1)]

    for dx, dy in directions:
        count = 1  # 当前位置已算一颗棋子
        open_ends = 0

        # 检查正方向
        for i in range(1, 5):
            nx, ny = x + i * dx, y + i * dy
            if (nx, ny) in stones:
                count += 1
            else:
                break
        if 0 <= x + 5 * dx < BOARD_SIZE and 0 <= y + 5 * dy < BOARD_SIZE:
            open_ends += 1

        # 检查反方向
        for i in range(1, 5):
            nx, ny = x - i * dx, y - i * dy
            if (nx, ny) in stones:
                count += 1
            else:
                break
        if 0 <= x - 5 * dx < BOARD_SIZE and 0 <= y - 5 * dy < BOARD_SIZE:
            open_ends += 1

        # 计算分数
        if count >= 5:
            total_score += shape_score[5]  # 五连
        elif count == 4 and open_ends > 0:
            total_score += shape_score[4]  # 活四
        elif count == 3 and open_ends > 0:
            total_score += shape_score[3]  # 活三
        elif count == 2 and open_ends > 0:
            total_score += shape_score[2]  # 活二

    return total_score

def game_win(list):
    for m in range(BOARD_SIZE):
        for n in range(BOARD_SIZE):
            if n < BOARD_SIZE - 4 and (m, n) in list and (m, n + 1) in list and (m, n + 2) in list and (m, n + 3) in list and (m, n + 4) in list:
                return True
            elif m < BOARD_SIZE - 4 and (m, n) in list and (m + 1, n) in list and (m + 2, n) in list and (m + 3, n) in list and (m + 4, n) in list:
                return True
            elif m < BOARD_SIZE - 4 and n < BOARD_SIZE - 4 and (m, n) in list and (m + 1, n + 1) in list and (m + 2, n + 2) in list and (m + 3, n + 3) in list and (m + 4, n + 4) in list:
                return True
            elif m < BOARD_SIZE - 4 and n > 3 and (m, n) in list and (m + 1, n - 1) in list and (m + 2, n - 2) in list and (m + 3, n - 3) in list and (m + 4, n - 4) in list:
                return True
    return False

def draw_board():
    screen.fill(WHITE)
    for x in range(1, BOARD_SIZE):
        pygame.draw.line(screen, BLACK, (x * CELL_SIZE, 0), (x * CELL_SIZE, screen_height))
        pygame.draw.line(screen, BLACK, (0, x * CELL_SIZE), (screen_width, x * CELL_SIZE))

def place_stone(x, y, color):
    # 绘制棋子，同时为白棋添加黑色边框
    pygame.draw.circle(screen, BLACK, (x * CELL_SIZE + CELL_SIZE // 2, y * CELL_SIZE + CELL_SIZE // 2), CELL_SIZE // 2 - 3)
    pygame.draw.circle(screen, color, (x * CELL_SIZE + CELL_SIZE // 2, y * CELL_SIZE + CELL_SIZE // 2), CELL_SIZE // 2 - 5)

def main():
    for i in range(BOARD_SIZE):
        for j in range(BOARD_SIZE):
            list_all.append((i, j))

    running = True
    turn = "black"
    winner = None

    while running:
        draw_board()

        # 绘制所有已下的棋子
        for stone in list1:
            place_stone(stone[1], stone[0], GRAY)
        for stone in list2:
            place_stone(stone[1], stone[0], BLACK)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if winner is None:
                    x, y = pygame.mouse.get_pos()
                    row, col = y // CELL_SIZE, x // CELL_SIZE

                    if (row, col) in list3:
                        continue

                    if turn == "black":
                        list2.append((row, col))
                        list3.append((row, col))
                        place_stone(col, row, BLACK)

                        if game_win(list2):
                            winner = "black"
                            print("黑棋获胜！")
                            running = False

                        turn = "white"
                    else:
                        pos = ai()
                        list1.append(pos)
                        list3.append(pos)
                        place_stone(pos[1], pos[0], GRAY)

                        if game_win(list1):
                            winner = "white"
                            print("白棋获胜！")
                            running = False

                        turn = "black"

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
