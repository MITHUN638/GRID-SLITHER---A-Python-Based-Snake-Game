# ============================================================
#  SNAKE GAME  –  Python + Pygame
#  Student : MITHUN RAJ R
#  Project : Snake Game (Pygame)
# ============================================================
#
#  HOW TO RUN:
#    pip install pygame
#    python snake_game.py
#
#  CONTROLS:
#    Arrow Keys / W A S D  →  Move
#    P                     →  Pause / Resume
#    R  (game over screen) →  Restart
#    Q / ESC               →  Quit
# ============================================================

import pygame
import sys
import random
import time

# ── Initialise pygame ───────────────────────────────────────
pygame.init()
pygame.display.set_caption("Snake Game – MITHUN RAJ R")

# ── Constants ───────────────────────────────────────────────
CELL        = 24          # Size of each grid cell in pixels
COLS        = 25          # Number of columns
ROWS        = 22          # Number of rows
WIDTH       = COLS * CELL          # 600 px
HEIGHT      = ROWS * CELL + 100    # 628 px  (extra 100 for HUD)
FPS         = 10          # Game speed (ticks per second)

# ── Colour palette ───────────────────────────────────────────
BG          = (245, 244, 240)   # Page background
GRID_COL    = (235, 232, 226)   # Subtle grid lines
SURFACE     = (255, 255, 255)   # Card / board surface
BORDER      = (210, 205, 198)   # Border colour

HEAD_COL    = ( 27,  67,  50)   # Dark green  — snake head
BODY_COL    = ( 45, 106,  79)   # Medium green — body even
BODY_ALT    = ( 64, 145, 108)   # Light green  — body odd
FOOD_COL    = (230,  57,  70)   # Red          — food
EYE_COL     = (255, 255, 255)   # White        — eyes

TEXT_DARK   = ( 26,  26,  26)   # Primary text
TEXT_MUTED  = (136, 136, 136)   # Muted / label text
ACCENT      = ( 45, 106,  79)   # Green accent (score)
SCORE_GOLD  = (255, 200,   0)   # Best score gold

OVERLAY_BG  = (255, 255, 255, 230)  # Semi-transparent overlay
DANGER      = (230,  57,  70)   # Red (game over / cause)
PAUSE_COL   = ( 45, 106,  79)

# ── Screen ───────────────────────────────────────────────────
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock  = pygame.time.Clock()

# ── Fonts ────────────────────────────────────────────────────
FONT_BIG    = pygame.font.SysFont("Arial", 42, bold=True)
FONT_MED    = pygame.font.SysFont("Arial", 26, bold=True)
FONT_SMALL  = pygame.font.SysFont("Arial", 18)
FONT_MONO   = pygame.font.SysFont("Courier New", 17)
FONT_TINY   = pygame.font.SysFont("Arial", 14)

# ── Load / create assets ─────────────────────────────────────
# We generate images programmatically (no external files needed)
# But we also save them as PNGs so the /assets/ folder is populated

def make_food_surface():
    """Red circle food sprite 24×24."""
    s = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
    pygame.draw.ellipse(s, FOOD_COL, (2, 2, CELL-4, CELL-4))
    # shine
    pygame.draw.ellipse(s, (255, 120, 120), (6, 4, 8, 5))
    return s

def make_head_surface():
    """Dark green rounded square with eyes 24×24."""
    s = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
    pygame.draw.rect(s, HEAD_COL, (1, 1, CELL-2, CELL-2), border_radius=6)
    # eyes
    pygame.draw.circle(s, EYE_COL, (16, 8),  3)
    pygame.draw.circle(s, EYE_COL, (16, 16), 3)
    pygame.draw.circle(s, (0,0,0), (17, 8),  1)
    pygame.draw.circle(s, (0,0,0), (17, 16), 1)
    return s

def make_body_surface(alt=False):
    """Body segment sprite 24×24."""
    s = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
    col = BODY_ALT if alt else BODY_COL
    pygame.draw.rect(s, col, (2, 2, CELL-4, CELL-4), border_radius=5)
    return s

# Pre-render sprite surfaces
FOOD_IMG  = make_food_surface()
HEAD_IMG  = make_head_surface()
BODY_IMG  = make_body_surface(False)
BODY_AIMG = make_body_surface(True)

# ── Direction vectors ────────────────────────────────────────
UP    = ( 0, -1)
DOWN  = ( 0,  1)
LEFT  = (-1,  0)
RIGHT = ( 1,  0)

# ═══════════════════════════════════════════════════════════
#  GAME STATE CLASS
# ═══════════════════════════════════════════════════════════
class SnakeGame:
    def __init__(self):
        self.best = 0          # persists across restarts
        self.reset()

    # ── Reset / initialise all game variables ───────────────
    def reset(self):
        # Snake: list of (col, row) tuples. Index 0 = head.
        self.snake      = [(COLS // 2, ROWS // 2)]
        self.direction  = RIGHT       # current direction
        self.next_dir   = RIGHT       # queued from keypress
        self.score      = 0
        self.food_eaten = 0
        self.running    = True        # True = game active
        self.paused     = False
        self.game_over  = False
        self.cause      = ""          # cause of death string
        self.place_food()

    # ── Place food on a free cell ───────────────────────────
    def place_food(self):
        while True:
            pos = (random.randint(0, COLS-1), random.randint(0, ROWS-1))
            if pos not in self.snake:
                self.food = pos
                break

    # ── Handle one keypress ─────────────────────────────────
    def handle_key(self, key):
        # Direction map: key → direction vector
        dir_map = {
            pygame.K_UP:    UP,    pygame.K_w: UP,
            pygame.K_DOWN:  DOWN,  pygame.K_s: DOWN,
            pygame.K_LEFT:  LEFT,  pygame.K_a: LEFT,
            pygame.K_RIGHT: RIGHT, pygame.K_d: RIGHT,
        }
        if key in dir_map:
            nd = dir_map[key]
            # Prevent 180° reversal: opposite vectors sum to (0,0)
            if nd[0] + self.direction[0] != 0 or nd[1] + self.direction[1] != 0:
                self.next_dir = nd
        elif key == pygame.K_p:
            self.paused = not self.paused

    # ── One game tick ───────────────────────────────────────
    def tick(self):
        if self.paused or self.game_over:
            return

        # 1. Apply queued direction
        self.direction = self.next_dir

        # 2. Calculate new head position
        hx, hy = self.snake[0]
        dx, dy = self.direction
        nx, ny = hx + dx, hy + dy

        # 3. Wall collision → game over
        if nx < 0 or nx >= COLS or ny < 0 or ny >= ROWS:
            self._end("Hit the Wall")
            return

        # 4. Self collision → game over
        if (nx, ny) in self.snake:
            self._end("Hit Itself")
            return

        # 5. Move: add new head at front
        self.snake.insert(0, (nx, ny))

        # 6. Food eaten?
        if (nx, ny) == self.food:
            self.score      += 10
            self.food_eaten += 1
            self.place_food()
            # Don't remove tail → snake grows
        else:
            self.snake.pop()   # Remove tail → forward movement

    def _end(self, cause):
        self.game_over = True
        self.cause     = cause
        if self.score > self.best:
            self.best = self.score


# ═══════════════════════════════════════════════════════════
#  DRAWING FUNCTIONS
# ═══════════════════════════════════════════════════════════

def draw_board(game):
    """Draw background, grid, food, and snake onto screen."""
    # Board area (below HUD)
    board_rect = pygame.Rect(0, 100, WIDTH, ROWS * CELL)
    pygame.draw.rect(screen, SURFACE, board_rect)

    # Grid lines
    for x in range(0, WIDTH, CELL):
        pygame.draw.line(screen, GRID_COL, (x, 100), (x, HEIGHT), 1)
    for y in range(100, HEIGHT, CELL):
        pygame.draw.line(screen, GRID_COL, (0, y), (WIDTH, y), 1)

    # Board border
    pygame.draw.rect(screen, BORDER, board_rect, 2)

    # Food
    fx, fy = game.food
    screen.blit(FOOD_IMG, (fx * CELL, 100 + fy * CELL))

    # Snake
    for i, (sx, sy) in enumerate(game.snake):
        if i == 0:
            # Head — rotate eyes based on direction
            head = rotate_head(game.direction)
            screen.blit(head, (sx * CELL, 100 + sy * CELL))
        else:
            img = BODY_IMG if i % 2 == 0 else BODY_AIMG
            screen.blit(img, (sx * CELL, 100 + sy * CELL))


def rotate_head(direction):
    """Rotate head sprite so eyes face the movement direction."""
    # Base head has eyes on the right side (facing RIGHT)
    angles = { RIGHT: 0, LEFT: 180, UP: 90, DOWN: 270 }
    return pygame.transform.rotate(HEAD_IMG, angles.get(direction, 0))


def draw_hud(game):
    """Draw the top HUD bar: title + score cards."""
    pygame.draw.rect(screen, BG, (0, 0, WIDTH, 100))
    pygame.draw.line(screen, BORDER, (0, 100), (WIDTH, 100), 2)

    # Title
    title = FONT_MED.render("🐍 Snake Game", True, TEXT_DARK)
    screen.blit(title, (16, 14))

    by_line = FONT_TINY.render("MITHUN RAJ R", True, TEXT_MUTED)
    screen.blit(by_line, (18, 44))

    # Score card
    draw_card(screen, WIDTH - 260, 10, 115, 80, "SCORE", str(game.score), ACCENT)
    draw_card(screen, WIDTH - 135, 10, 115, 80, "BEST",  str(game.best),  TEXT_DARK)


def draw_card(surf, x, y, w, h, label, value, val_color):
    """Draw a small score card."""
    pygame.draw.rect(surf, SURFACE, (x, y, w, h), border_radius=8)
    pygame.draw.rect(surf, BORDER,  (x, y, w, h), 1, border_radius=8)
    lbl = FONT_TINY.render(label, True, TEXT_MUTED)
    val = FONT_BIG.render(value, True, val_color)
    surf.blit(lbl, (x + w//2 - lbl.get_width()//2, y + 10))
    surf.blit(val, (x + w//2 - val.get_width()//2,  y + 30))


def draw_overlay_start(game):
    """Start screen overlay."""
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((255, 255, 255, 220))
    screen.blit(overlay, (0, 0))

    cy = HEIGHT // 2 - 80

    t1 = FONT_BIG.render("🐍  Snake Game", True, HEAD_COL)
    screen.blit(t1, (WIDTH//2 - t1.get_width()//2, cy))

    t2 = FONT_SMALL.render("Arrow Keys / WASD to move", True, TEXT_MUTED)
    screen.blit(t2, (WIDTH//2 - t2.get_width()//2, cy + 60))

    t3 = FONT_SMALL.render("Hit the wall = Game Over", True, DANGER)
    screen.blit(t3, (WIDTH//2 - t3.get_width()//2, cy + 90))

    btn = draw_button(screen, WIDTH//2, cy + 150, "PRESS ENTER TO START", HEAD_COL)


def draw_overlay_gameover(game):
    """Game over overlay with scorecard."""
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((255, 255, 255, 230))
    screen.blit(overlay, (0, 0))

    cx = WIDTH  // 2
    cy = HEIGHT // 2 - 140

    # Title
    t1 = FONT_BIG.render("💀  GAME OVER", True, DANGER)
    screen.blit(t1, (cx - t1.get_width()//2, cy))

    # Final score
    t2 = FONT_BIG.render(str(game.score), True, ACCENT)
    screen.blit(t2, (cx - t2.get_width()//2, cy + 55))

    # Scorecard box
    bx, by, bw, bh = cx - 130, cy + 110, 260, 170
    pygame.draw.rect(screen, BG,     (bx, by, bw, bh), border_radius=10)
    pygame.draw.rect(screen, BORDER, (bx, by, bw, bh), 1, border_radius=10)

    rows = [
        ("Score",      str(game.score),      ACCENT),
        ("Best",       str(game.best),        TEXT_DARK),
        ("Length",     str(len(game.snake)),  TEXT_DARK),
        ("Food Eaten", str(game.food_eaten),  TEXT_DARK),
        ("Cause",      game.cause,            DANGER),
    ]
    for i, (lbl, val, vcol) in enumerate(rows):
        ry = by + 12 + i * 30
        l_surf = FONT_MONO.render(lbl, True, TEXT_MUTED)
        v_surf = FONT_MONO.render(val, True, vcol)
        screen.blit(l_surf, (bx + 12,  ry))
        screen.blit(v_surf, (bx + bw - v_surf.get_width() - 12, ry))
        if i < len(rows) - 1:
            pygame.draw.line(screen, BORDER,
                             (bx + 8, ry + 26), (bx + bw - 8, ry + 26), 1)

    # Buttons hint
    hint = FONT_SMALL.render("R = Restart     Q = Quit", True, TEXT_MUTED)
    screen.blit(hint, (cx - hint.get_width()//2, cy + 295))


def draw_overlay_paused():
    """Pause screen."""
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((255, 255, 255, 180))
    screen.blit(overlay, (0, 0))
    t = FONT_BIG.render("⏸  PAUSED", True, PAUSE_COL)
    screen.blit(t, (WIDTH//2 - t.get_width()//2, HEIGHT//2 - 30))
    t2 = FONT_SMALL.render("Press P to resume", True, TEXT_MUTED)
    screen.blit(t2, (WIDTH//2 - t2.get_width()//2, HEIGHT//2 + 30))


def draw_button(surf, cx, y, text, color):
    t = FONT_SMALL.render(text, True, color)
    bx = cx - t.get_width()//2 - 20
    bw = t.get_width() + 40
    bh = 40
    pygame.draw.rect(surf, color,   (bx, y, bw, bh), border_radius=8)
    pygame.draw.rect(surf, color,   (bx, y, bw, bh), 2, border_radius=8)
    twhite = FONT_SMALL.render(text, True, SURFACE)
    surf.blit(twhite, (cx - twhite.get_width()//2, y + 10))


# ═══════════════════════════════════════════════════════════
#  SAVE ASSETS  (runs once — creates PNG files in /assets/)
# ═══════════════════════════════════════════════════════════
def save_assets():
    try:
        pygame.image.save(FOOD_IMG,  "assets/food.png")
        pygame.image.save(HEAD_IMG,  "assets/snake_head.png")
        pygame.image.save(BODY_IMG,  "assets/snake_body.png")
        pygame.image.save(BODY_AIMG, "assets/snake_body_alt.png")
    except Exception:
        pass   # If assets/ folder doesn't exist, skip silently


# ═══════════════════════════════════════════════════════════
#  MAIN  –  game loop
# ═══════════════════════════════════════════════════════════
def main():
    game      = SnakeGame()
    started   = False    # Shows start screen first

    save_assets()        # Write sprite PNGs to assets/ folder

    while True:
        # ── Event handling ─────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if not started:
                    if event.key == pygame.K_RETURN:
                        started = True
                elif game.game_over:
                    if event.key == pygame.K_r:
                        game.reset()
                    elif event.key in (pygame.K_q, pygame.K_ESCAPE):
                        pygame.quit()
                        sys.exit()
                else:
                    if event.key in (pygame.K_q, pygame.K_ESCAPE):
                        pygame.quit()
                        sys.exit()
                    game.handle_key(event.key)

        # ── Game tick ──────────────────────────────────────
        if started and not game.game_over:
            game.tick()

        # ── Drawing ────────────────────────────────────────
        screen.fill(BG)
        draw_hud(game)
        draw_board(game)

        if not started:
            draw_overlay_start(game)
        elif game.paused:
            draw_overlay_paused()
        elif game.game_over:
            draw_overlay_gameover(game)

        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    main()
