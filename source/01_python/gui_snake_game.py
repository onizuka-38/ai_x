import pygame
import random
import sys

# 초기화
pygame.init()

# 화면 크기
WIDTH, HEIGHT = 600, 400
BLOCK_SIZE = 20

# 색상
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
DARK_GREEN = (0, 155, 0)
RED = (255, 0, 0)
BLACK = (0, 0, 0)

# 화면 설정
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("🐍 Snake Game")

# 시계 설정
clock = pygame.time.Clock()
FPS = 10

font = pygame.font.SysFont(None, 35)

def draw_snake(snake):
    for block in snake:
        pygame.draw.rect(screen, DARK_GREEN, pygame.Rect(block[0], block[1], BLOCK_SIZE, BLOCK_SIZE))

def draw_food(position):
    pygame.draw.rect(screen, RED, pygame.Rect(position[0], position[1], BLOCK_SIZE, BLOCK_SIZE))

def show_message(msg, color):
    text = font.render(msg, True, color)
    screen.blit(text, [WIDTH // 6, HEIGHT // 3])

def main():
    x = WIDTH // 2
    y = HEIGHT // 2
    dx = None
    dy = None

    snake = [[x, y]]
    food = [random.randrange(0, WIDTH, BLOCK_SIZE), random.randrange(0, HEIGHT, BLOCK_SIZE)]

    score = 0
    game_over = False

    while True:
        screen.fill(WHITE)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP and dy != BLOCK_SIZE:
                    dx, dy = 0, -BLOCK_SIZE
                elif event.key == pygame.K_DOWN and dy != -BLOCK_SIZE:
                    dx, dy = 0, BLOCK_SIZE
                elif event.key == pygame.K_LEFT and dx != BLOCK_SIZE:
                    dx, dy = -BLOCK_SIZE, 0
                elif event.key == pygame.K_RIGHT and dx != -BLOCK_SIZE:
                    dx, dy = BLOCK_SIZE, 0
                elif event.key == pygame.K_r and game_over:
                    main()

        if not game_over and dx is not None and dy is not None:
            x += dx
            y += dy
            new_head = [x, y]

            # 충돌 검사
            if (
                x < 0 or x >= WIDTH or
                y < 0 or y >= HEIGHT or
                new_head in snake
            ):
                game_over = True

            snake.insert(0, new_head)
            if new_head == food:
                food = [random.randrange(0, WIDTH, BLOCK_SIZE), random.randrange(0, HEIGHT, BLOCK_SIZE)]
                score += 1
            else:
                snake.pop()

        # 그리기
        draw_snake(snake)
        draw_food(food)
        score_text = font.render(f"Score: {score}", True, BLACK)
        screen.blit(score_text, [10, 10])

        if game_over:
            show_message(f"Game Over! Score: {score} | Press R to Restart", RED)

        pygame.display.update()
        clock.tick(FPS)

if __name__ == "__main__":
    main()
