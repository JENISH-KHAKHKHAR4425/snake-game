import pygame
import random
import sys
import os
import math

# Try to import numpy for sound generation. If it's missing, the game
# still runs perfectly fine -- it just runs silently.
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

# -----------------------------
# Initialize pygame
# -----------------------------
pygame.init()

try:
    pygame.mixer.init()
    MIXER_AVAILABLE = True
except pygame.error:
    MIXER_AVAILABLE = False

# -----------------------------
# Screen Settings
# -----------------------------
WIDTH = 600
HEIGHT = 700          # extra space at bottom for touch controls / HUD
BOARD_HEIGHT = 600    # actual play area (must stay multiple of GRID_SIZE)
GRID_SIZE = 20

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Snake Game")

clock = pygame.time.Clock()
FPS = 60

# -----------------------------
# Colors
# -----------------------------
BLACK = (20, 20, 20)
BOARD_BG = (25, 25, 25)
WHITE = (255, 255, 255)
GREEN = (0, 220, 0)
DARK_GREEN = (0, 150, 0)
RED = (255, 60, 60)
BLUE = (0, 180, 255)
GRAY = (120, 120, 120)
DARK_GRAY = (55, 55, 55)
YELLOW = (255, 220, 0)
LEAF_GREEN = (40, 170, 60)
PANEL = (35, 35, 40)
PANEL_LIGHT = (55, 55, 65)

# -----------------------------
# Fonts
# -----------------------------
font = pygame.font.SysFont("arial", 26)
small_font = pygame.font.SysFont("arial", 20)
big_font = pygame.font.SysFont("arial", 50, bold=True)

HIGH_SCORE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "highscore.txt")


# -----------------------------
# High score persistence
# -----------------------------
def load_high_score():
    try:
        with open(HIGH_SCORE_FILE, "r") as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return 0


def save_high_score(value):
    try:
        with open(HIGH_SCORE_FILE, "w") as f:
            f.write(str(value))
    except OSError:
        pass


# -----------------------------
# Sound generation (no external files needed)
# -----------------------------
def make_tone(frequency=440, duration=0.12, volume=0.3):
    if not (NUMPY_AVAILABLE and MIXER_AVAILABLE):
        return None
    sample_rate = 44100
    n_samples = int(sample_rate * duration)
    t = np.linspace(0, duration, n_samples, False)
    wave = np.sin(frequency * t * 2 * np.pi)
    # simple fade out to avoid clicks
    fade = np.linspace(1, 0, n_samples)
    wave = wave * fade * volume
    audio = np.int16(wave * 32767)
    stereo = np.column_stack((audio, audio))
    stereo = np.ascontiguousarray(stereo)
    try:
        return pygame.sndarray.make_sound(stereo)
    except Exception:
        return None


eat_sound = make_tone(660, 0.10, 0.35)
gameover_sound = make_tone(160, 0.35, 0.35)
click_sound = make_tone(880, 0.06, 0.25)


def play_sound(sound):
    if sound is not None:
        try:
            sound.play()
        except Exception:
            pass


# -----------------------------
# Helpers
# -----------------------------
def draw_text(text, font_obj, color, x, y, center=False):
    img = font_obj.render(text, True, color)
    rect = img.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    screen.blit(img, rect)
    return rect


def random_food(snake):
    max_x = WIDTH // GRID_SIZE
    max_y = BOARD_HEIGHT // GRID_SIZE
    while True:
        x = random.randrange(0, max_x) * GRID_SIZE
        y = random.randrange(0, max_y) * GRID_SIZE
        if (x, y) not in snake:
            return (x, y)


def draw_grid():
    for x in range(0, WIDTH, GRID_SIZE):
        pygame.draw.line(screen, (40, 40, 40), (x, 0), (x, BOARD_HEIGHT))
    for y in range(0, BOARD_HEIGHT, GRID_SIZE):
        pygame.draw.line(screen, (40, 40, 40), (0, y), (WIDTH, y))


def lerp(a, b, t):
    return a + (b - a) * t


def draw_food(food, pulse):
    cx = food[0] + GRID_SIZE // 2
    cy = food[1] + GRID_SIZE // 2
    radius = GRID_SIZE // 2 + int(1 * math.sin(pulse))
    # apple body
    pygame.draw.circle(screen, RED, (cx, cy), radius)
    # highlight
    pygame.draw.circle(screen, (255, 160, 160), (cx - 3, cy - 3), max(2, radius // 3))
    # stem
    pygame.draw.line(screen, (100, 60, 20), (cx, cy - radius), (cx + 2, cy - radius - 5), 2)
    # leaf
    leaf_rect = pygame.Rect(cx + 1, cy - radius - 6, 8, 5)
    pygame.draw.ellipse(screen, LEAF_GREEN, leaf_rect)


# -----------------------------
# Touch / on-screen controls
# -----------------------------
BTN_SIZE = 55
CTRL_CENTER_X = WIDTH // 2
CTRL_CENTER_Y = BOARD_HEIGHT + 70

btn_up = pygame.Rect(0, 0, BTN_SIZE, BTN_SIZE)
btn_down = pygame.Rect(0, 0, BTN_SIZE, BTN_SIZE)
btn_left = pygame.Rect(0, 0, BTN_SIZE, BTN_SIZE)
btn_right = pygame.Rect(0, 0, BTN_SIZE, BTN_SIZE)

btn_up.center = (CTRL_CENTER_X, CTRL_CENTER_Y - BTN_SIZE - 5)
btn_down.center = (CTRL_CENTER_X, CTRL_CENTER_Y + BTN_SIZE + 5)
btn_left.center = (CTRL_CENTER_X - BTN_SIZE - 5, CTRL_CENTER_Y)
btn_right.center = (CTRL_CENTER_X + BTN_SIZE + 5, CTRL_CENTER_Y)

pause_btn = pygame.Rect(WIDTH - 90, 15, 70, 32)


def draw_arrow_button(rect, direction, pressed=False):
    color = PANEL_LIGHT if not pressed else BLUE
    pygame.draw.rect(screen, color, rect, border_radius=10)
    pygame.draw.rect(screen, GRAY, rect, width=2, border_radius=10)
    cx, cy = rect.center
    s = 10
    if direction == "up":
        points = [(cx, cy - s), (cx - s, cy + s), (cx + s, cy + s)]
    elif direction == "down":
        points = [(cx, cy + s), (cx - s, cy - s), (cx + s, cy - s)]
    elif direction == "left":
        points = [(cx - s, cy), (cx + s, cy - s), (cx + s, cy + s)]
    else:  # right
        points = [(cx + s, cy), (cx - s, cy - s), (cx - s, cy + s)]
    pygame.draw.polygon(screen, WHITE, points)


def draw_touch_controls():
    draw_arrow_button(btn_up, "up")
    draw_arrow_button(btn_down, "down")
    draw_arrow_button(btn_left, "left")
    draw_arrow_button(btn_right, "right")


def draw_pause_button(paused):
    pygame.draw.rect(screen, PANEL_LIGHT, pause_btn, border_radius=8)
    pygame.draw.rect(screen, GRAY, pause_btn, width=2, border_radius=8)
    label = "Resume" if paused else "Pause"
    draw_text(label, small_font, WHITE, pause_btn.centerx, pause_btn.centery, center=True)


# -----------------------------
# Start / Menu Screen
# -----------------------------
def start_screen(high_score):
    play_btn = pygame.Rect(0, 0, 220, 60)
    play_btn.center = (WIDTH // 2, HEIGHT // 2 + 40)

    while True:
        screen.fill(BLACK)

        draw_text("SNAKE", big_font, GREEN, WIDTH // 2, HEIGHT // 2 - 100, center=True)
        draw_text(f"High Score : {high_score}", font, YELLOW, WIDTH // 2, HEIGHT // 2 - 40, center=True)

        mouse_pos = pygame.mouse.get_pos()
        hovered = play_btn.collidepoint(mouse_pos)
        pygame.draw.rect(screen, GREEN if hovered else DARK_GREEN, play_btn, border_radius=12)
        draw_text("PLAY", font, BLACK, play_btn.centerx, play_btn.centery, center=True)

        draw_text("Arrow keys / WASD / on-screen buttons to move",
                   small_font, GRAY, WIDTH // 2, HEIGHT // 2 + 120, center=True)
        draw_text("SPACE to pause  |  Click PLAY or press ENTER to start",
                   small_font, GRAY, WIDTH // 2, HEIGHT // 2 + 150, center=True)

        pygame.display.update()
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    play_sound(click_sound)
                    return

            if event.type in (pygame.MOUSEBUTTONDOWN, pygame.FINGERDOWN):
                pos = mouse_pos
                if event.type == pygame.FINGERDOWN:
                    pos = (event.x * WIDTH, event.y * HEIGHT)
                if play_btn.collidepoint(pos):
                    play_sound(click_sound)
                    return


# -----------------------------
# Game Function
# -----------------------------
def game(high_score):

    snake = [(100, 100), (80, 100), (60, 100)]
    prev_snake = list(snake)

    dx, dy = GRID_SIZE, 0
    next_dx, next_dy = dx, dy

    food = random_food(snake)

    score = 0
    move_interval = 110  # ms per grid step; lower = faster
    min_interval = 55

    move_timer = 0.0
    pulse_timer = 0.0
    paused = False

    running = True

    while running:
        dt = clock.tick(FPS)

        # -----------------------------
        # Events
        # -----------------------------
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_SPACE:
                    paused = not paused
                    play_sound(click_sound)

                elif event.key in (pygame.K_UP, pygame.K_w) and dy == 0:
                    next_dx, next_dy = 0, -GRID_SIZE

                elif event.key in (pygame.K_DOWN, pygame.K_s) and dy == 0:
                    next_dx, next_dy = 0, GRID_SIZE

                elif event.key in (pygame.K_LEFT, pygame.K_a) and dx == 0:
                    next_dx, next_dy = -GRID_SIZE, 0

                elif event.key in (pygame.K_RIGHT, pygame.K_d) and dx == 0:
                    next_dx, next_dy = GRID_SIZE, 0

            if event.type in (pygame.MOUSEBUTTONDOWN, pygame.FINGERDOWN):
                if event.type == pygame.FINGERDOWN:
                    pos = (event.x * WIDTH, event.y * HEIGHT)
                else:
                    pos = event.pos

                if pause_btn.collidepoint(pos):
                    paused = not paused
                    play_sound(click_sound)
                elif btn_up.collidepoint(pos) and dy == 0:
                    next_dx, next_dy = 0, -GRID_SIZE
                elif btn_down.collidepoint(pos) and dy == 0:
                    next_dx, next_dy = 0, GRID_SIZE
                elif btn_left.collidepoint(pos) and dx == 0:
                    next_dx, next_dy = -GRID_SIZE, 0
                elif btn_right.collidepoint(pos) and dx == 0:
                    next_dx, next_dy = GRID_SIZE, 0

        if not paused:
            move_timer += dt
            pulse_timer += dt * 0.01

            # -----------------------------
            # Fixed-step movement (kept separate from render FPS
            # so the animation stays smooth no matter the snake speed)
            # -----------------------------
            while move_timer >= move_interval:
                move_timer -= move_interval

                dx, dy = next_dx, next_dy
                prev_snake = list(snake)

                head_x = snake[0][0] + dx
                head_y = snake[0][1] + dy
                new_head = (head_x, head_y)

                # Collision
                if (
                    head_x < 0
                    or head_x >= WIDTH
                    or head_y < 0
                    or head_y >= BOARD_HEIGHT
                    or new_head in snake
                ):
                    play_sound(gameover_sound)
                    if score > high_score:
                        high_score = score
                        save_high_score(high_score)
                    game_over(score, high_score)
                    return

                snake.insert(0, new_head)

                if new_head == food:
                    score += 1
                    play_sound(eat_sound)
                    if score % 5 == 0 and move_interval > min_interval:
                        move_interval -= 6
                    food = random_food(snake)
                else:
                    snake.pop()

        # -----------------------------
        # Draw Everything
        # -----------------------------
        screen.fill(BLACK)
        pygame.draw.rect(screen, BOARD_BG, (0, 0, WIDTH, BOARD_HEIGHT))
        draw_grid()

        progress = 0 if move_interval == 0 else min(move_timer / move_interval, 1.0)

        # Snake (interpolated for smooth movement)
        for index, segment in enumerate(snake):
            if index < len(prev_snake):
                prev_seg = prev_snake[index]
            elif prev_snake:
                prev_seg = prev_snake[-1]
            else:
                prev_seg = segment

            draw_x = lerp(prev_seg[0], segment[0], progress) if not paused else segment[0]
            draw_y = lerp(prev_seg[1], segment[1], progress) if not paused else segment[1]

            color = GREEN if index == 0 else DARK_GREEN
            radius = 6 if index == 0 else 5
            pygame.draw.rect(
                screen, color,
                (draw_x, draw_y, GRID_SIZE, GRID_SIZE),
                border_radius=radius,
            )

            if index == 0:
                # simple eyes on the head for a bit of polish
                eye_offset = 5
                pygame.draw.circle(screen, WHITE, (int(draw_x) + eye_offset, int(draw_y) + eye_offset), 2)
                pygame.draw.circle(screen, WHITE, (int(draw_x) + GRID_SIZE - eye_offset, int(draw_y) + eye_offset), 2)

        # Food
        draw_food(food, pulse_timer)

        # HUD panel
        pygame.draw.rect(screen, PANEL, (0, BOARD_HEIGHT, WIDTH, HEIGHT - BOARD_HEIGHT))
        draw_text(f"Score : {score}", font, WHITE, 15, BOARD_HEIGHT + 12)
        draw_text(f"High Score : {high_score}", font, YELLOW, 15, BOARD_HEIGHT + 42)
        draw_text(f"Speed : {round(1000 / move_interval, 1)}", font, BLUE, WIDTH - 220, BOARD_HEIGHT + 12)

        draw_pause_button(paused)
        draw_touch_controls()

        if paused:
            overlay = pygame.Surface((WIDTH, BOARD_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (0, 0))
            draw_text("PAUSED", big_font, WHITE, WIDTH // 2, BOARD_HEIGHT // 2, center=True)
            draw_text("Press SPACE to resume", font, GRAY, WIDTH // 2, BOARD_HEIGHT // 2 + 55, center=True)

        pygame.display.update()


# -----------------------------
# Game Over Screen
# -----------------------------
def game_over(score, high_score):

    restart_btn = pygame.Rect(0, 0, 220, 55)
    restart_btn.center = (WIDTH // 2, HEIGHT // 2 + 90)
    quit_btn = pygame.Rect(0, 0, 220, 55)
    quit_btn.center = (WIDTH // 2, HEIGHT // 2 + 160)

    while True:
        screen.fill((15, 15, 15))

        draw_text("GAME OVER", big_font, RED, WIDTH // 2, HEIGHT // 2 - 130, center=True)
        draw_text(f"Final Score : {score}", font, WHITE, WIDTH // 2, HEIGHT // 2 - 60, center=True)
        draw_text(f"High Score : {high_score}", font, YELLOW, WIDTH // 2, HEIGHT // 2 - 25, center=True)

        mouse_pos = pygame.mouse.get_pos()

        hover_r = restart_btn.collidepoint(mouse_pos)
        pygame.draw.rect(screen, GREEN if hover_r else DARK_GREEN, restart_btn, border_radius=12)
        draw_text("RESTART (R)", font, BLACK, restart_btn.centerx, restart_btn.centery, center=True)

        hover_q = quit_btn.collidepoint(mouse_pos)
        pygame.draw.rect(screen, (200, 60, 60) if hover_q else (140, 40, 40), quit_btn, border_radius=12)
        draw_text("QUIT (Q)", font, WHITE, quit_btn.centerx, quit_btn.centery, center=True)

        pygame.display.update()
        clock.tick(FPS)

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    play_sound(click_sound)
                    game(high_score)
                    return
                elif event.key == pygame.K_q:
                    pygame.quit()
                    sys.exit()

            if event.type in (pygame.MOUSEBUTTONDOWN, pygame.FINGERDOWN):
                pos = mouse_pos
                if event.type == pygame.FINGERDOWN:
                    pos = (event.x * WIDTH, event.y * HEIGHT)

                if restart_btn.collidepoint(pos):
                    play_sound(click_sound)
                    game(high_score)
                    return
                elif quit_btn.collidepoint(pos):
                    pygame.quit()
                    sys.exit()


# -----------------------------
# Main
# -----------------------------
def main():
    high_score = load_high_score()
    start_screen(high_score)
    game(high_score)


if __name__ == "__main__":
    main()
