import ctypes, os, sys, time, math, threading
from collections import deque

os.add_dll_directory(r"C:\Program Files (x86)\sweep\lib")
ctypes.cdll.LoadLibrary(r"C:\Program Files (x86)\sweep\lib\libsweep.dll")
sys.path.insert(0, r"C:\Users\97450\sweep-sdk\sweeppy")
from sweeppy import Sweep

import pygame

# ── Settings — change these ───────────────────────────────────────────────────
PORT       = 'COM7'
RANGE_CM   = 500       # how many cm the grid covers (each axis: -RANGE to +RANGE)
GRID_LINES = 10        # how many grid divisions per axis
FADE_SCANS = 6         # how many scans to keep visible

# ── Window ────────────────────────────────────────────────────────────────────
W, H       = 800, 850
PLOT_X     = 40        # left margin
PLOT_Y     = 60        # top margin
PLOT_W     = W - 80
PLOT_H     = H - 120
CX         = PLOT_X + PLOT_W // 2   # center x (sensor position)
CY         = PLOT_Y + PLOT_H // 2   # center y

# ── Colors ────────────────────────────────────────────────────────────────────
BG         = (15, 15, 20)
GRID_COL   = (40, 40, 55)
AXIS_COL   = (70, 70, 90)
LABEL_COL  = (100, 100, 120)
DOT_NEW    = (0, 220, 80)
DOT_OLD    = (0, 60, 25)
SENSOR_COL = (255, 80, 80)
TEXT_COL   = (200, 200, 220)
BORDER_COL = (60, 60, 80)

# ── Shared state ──────────────────────────────────────────────────────────────
scan_history = deque(maxlen=FADE_SCANS)
status_msg   = "Connecting..."
lock         = threading.Lock()
running      = True

def sweep_thread():
    global status_msg, running
    time.sleep(3)
    attempt = 0
    while running:
        attempt += 1
        try:
            with lock:
                status_msg = f"Connecting... (attempt {attempt})"
            with Sweep(PORT) as sweep:
                sweep.set_motor_speed(1)
                sweep.set_sample_rate(500)
                with lock:
                    status_msg = "Motor spinning up..."
                deadline = time.time() + 10
                while running and time.time() < deadline:
                    try:
                        if sweep.get_motor_ready():
                            break
                    except Exception:
                        pass
                    time.sleep(0.3)
                sweep.start_scanning()
                attempt = 0
                with lock:
                    status_msg = f"Scanning — range: ±{RANGE_CM}cm"
                for scan in sweep.get_scans():
                    if not running:
                        return
                    samples = []
                    for s in scan.samples:
                        ang  = s.angle / 1000.0
                        dist = s.distance
                        sig  = s.signal_strength
                        if dist > 2 and dist <= RANGE_CM * 1.5 and sig > 15:
                            # Convert polar → cartesian (cm)
                            rad = math.radians(ang)
                            x   = dist * math.sin(rad)
                            y   = -dist * math.cos(rad)
                            samples.append((x, y))
                    with lock:
                        scan_history.append(samples)
        except Exception as e:
            wait = min(3 * attempt, 10)
            with lock:
                status_msg = f"Retrying in {wait}s... ({e})"
            for _ in range(wait * 10):
                if not running:
                    return
                time.sleep(0.1)

def cm_to_screen(x_cm, y_cm):
    """Convert real-world cm coordinates to screen pixels."""
    px = CX + int(x_cm * (PLOT_W / 2) / RANGE_CM)
    py = CY + int(y_cm * (PLOT_H / 2) / RANGE_CM)
    return px, py

def draw_grid(surf, font_sm):
    # Border
    pygame.draw.rect(surf, BORDER_COL, (PLOT_X, PLOT_Y, PLOT_W, PLOT_H), 1)

    step = RANGE_CM / GRID_LINES

    # Vertical and horizontal grid lines
    for i in range(-GRID_LINES, GRID_LINES + 1):
        val = i * step

        # Vertical line
        sx, _ = cm_to_screen(val, 0)
        color = AXIS_COL if i == 0 else GRID_COL
        pygame.draw.line(surf, color, (sx, PLOT_Y), (sx, PLOT_Y + PLOT_H), 1 if i != 0 else 2)

        # Horizontal line
        _, sy = cm_to_screen(0, val)
        pygame.draw.line(surf, color, (PLOT_X, sy), (PLOT_X + PLOT_W, sy), 1 if i != 0 else 2)

        # Axis labels
        if i != 0 and i % 2 == 0:
            lbl = font_sm.render(f"{int(val)}", True, LABEL_COL)
            surf.blit(lbl, (sx - lbl.get_width() // 2, PLOT_Y + PLOT_H + 4))
            surf.blit(lbl, (PLOT_X - lbl.get_width() - 4, sy - lbl.get_height() // 2))

    # Axis titles
    x_lbl = font_sm.render("X (cm)", True, LABEL_COL)
    y_lbl = font_sm.render("Y (cm)", True, LABEL_COL)
    surf.blit(x_lbl, (PLOT_X + PLOT_W - x_lbl.get_width(), PLOT_Y + PLOT_H + 18))
    surf.blit(y_lbl, (2, PLOT_Y))

def draw_points(surf, scans):
    n = len(scans)
    if n == 0:
        return
    for idx, scan in enumerate(scans):
        t = (idx + 1) / n  # 0=oldest 1=newest
        r = int(DOT_OLD[0] + (DOT_NEW[0] - DOT_OLD[0]) * t)
        g = int(DOT_OLD[1] + (DOT_NEW[1] - DOT_OLD[1]) * t)
        b = int(DOT_OLD[2] + (DOT_NEW[2] - DOT_OLD[2]) * t)
        size = 3 if t > 0.7 else 2
        for x_cm, y_cm in scan:
            px, py = cm_to_screen(x_cm, y_cm)
            if PLOT_X <= px <= PLOT_X + PLOT_W and PLOT_Y <= py <= PLOT_Y + PLOT_H:
                pygame.draw.circle(surf, (r, g, b), (px, py), size)

def main():
    global RANGE_CM, running, status_msg  # add status_msg here

    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Sweep Lidar — Grid View")
    clock = pygame.time.Clock()

    font    = pygame.font.SysFont("Courier New", 13)
    font_sm = pygame.font.SysFont("Courier New", 11)
    font_lg = pygame.font.SysFont("Courier New", 16, bold=True)

    t = threading.Thread(target=sweep_thread, daemon=True)
    t.start()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                # + / - to change range
                elif event.key == pygame.K_UP or event.key == pygame.K_EQUALS:
                    RANGE_CM = min(RANGE_CM + 100, 2000)
                    with lock:
                        status_msg = f"Scanning — range: ±{RANGE_CM}cm"
                elif event.key == pygame.K_DOWN or event.key == pygame.K_MINUS:
                    RANGE_CM = max(RANGE_CM - 100, 100)
                    with lock:
                        status_msg = f"Scanning — range: ±{RANGE_CM}cm"

        with lock:
            scans  = list(scan_history)
            status = status_msg

        screen.fill(BG)

        # Title
        title = font_lg.render("SWEEP LIDAR — GRID VIEW", True, TEXT_COL)
        screen.blit(title, (PLOT_X, 12))

        # Range hint
        hint = font_sm.render(f"↑↓ to change range   ESC to quit", True, LABEL_COL)
        screen.blit(hint, (W - hint.get_width() - 10, 16))

        draw_grid(screen, font_sm)
        draw_points(screen, scans)

        # Sensor dot at center
        pygame.draw.circle(screen, SENSOR_COL, (CX, CY), 5)
        lbl = font_sm.render("SENSOR", True, SENSOR_COL)
        screen.blit(lbl, (CX + 7, CY - 7))

        # Status bar
        pygame.draw.rect(screen, (20, 20, 28), (0, H - 28, W, 28))
        pygame.draw.line(screen, BORDER_COL, (0, H - 28), (W, H - 28), 1)
        s = font_sm.render(f"  ●  {status}   |   range ±{RANGE_CM}cm", True, TEXT_COL)
        screen.blit(s, (6, H - 20))

        pygame.display.flip()
        clock.tick(30)

    running = False
    pygame.quit()

if __name__ == "__main__":
    main()

