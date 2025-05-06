import curses
import time
import random

UI_HEIGHT = 4

PLANE = [
    "  ------",
    "  | | # \\                                      |",
    "  | ____ \\_________|----^\"|\"\"\"\"\"|\"\\___________ |",
    "   \\___\\   FO + 94 >>    `\"\"\"\"\"\"\"     =====  \"|D",
    "      ^^-------____--\"\"\"\"\"\"\"\"+\"\"--_  __--\"|",
    "                  `\"\"|\"-->####)+---|`\"\"     |",
    "                                \\  \\",
    "                               <- O -)",
    "                                 `'\""
]

CLOUD_TEMPLATE = [
    "          .-~~~-.",
    "  .- ~ ~-(       )_ _",
    " /                     ~ -.",
    "|                           \\",
    " \\                         .'",
    "   ~- . _____________ . -~"
]

def check_collision(plane_y, plane_height, plane_x, cloud):
    cloud_height = len(cloud.cloud)
    cloud_width = max(len(line) for line in cloud.cloud)
    
    cloud_top = cloud.y
    cloud_bottom = cloud.y + cloud_height
    plane_bottom = plane_y + plane_height

    y_overlap = (cloud_top < plane_bottom) and (cloud_bottom > plane_y)
    x_overlap = (cloud.x < plane_x + 10) and (cloud.x + cloud_width > plane_x)

    return y_overlap and x_overlap

class Cloud:
    def __init__(self, max_y, max_x):
        self.cloud = CLOUD_TEMPLATE[:random.randint(3, len(CLOUD_TEMPLATE))]
        self.y = random.randint(UI_HEIGHT + 1, max_y - len(self.cloud) - 2)
        self.x = max_x
        self.scored = False
        self.collided = False

    def move(self):
        self.x -= 1

    def is_off_screen(self):
        return self.x + max(len(line) for line in self.cloud) < 0

    def draw(self, stdscr):
        max_y, max_x = stdscr.getmaxyx()
        for i, line in enumerate(self.cloud):
            row = self.y + i
            col = self.x
            if 0 <= row < max_y and col < max_x:
                visible_line = line[:max_x - col] if col >= 0 else line[abs(col):max_x]
                try:
                    stdscr.addstr(row, max(0, col), visible_line)
                except curses.error:
                    pass  # Still handle edge cases safely

def draw_plane(stdscr, y, x):
    for i, line in enumerate(PLANE):
        if 0 <= y + i < curses.LINES:
            stdscr.addstr(y + i, x, line[:curses.COLS - x])


def main(stdscr):
    title = "ASCII Flight Sim"
    subtitle = "Fly the plane with the arrows (up, down) to avoid the stormy clouds. At the third storm, you loose. Use 'q' to quit."
    credit_assets = "Game developed by Luis Natera. Plane by: Clarence Speer Padilla // Cloud by: https://www.asciiart.eu/nature/clouds"
    frame_delay = 0.05      # initial delay (slower)
    score = 0
    storm_count = 0
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(1)
    curses.use_default_colors()

    max_y, max_x = stdscr.getmaxyx()
    plane_height = len(PLANE)
    y = max_y // 2 - plane_height // 2
    x = 10
    center_x = max_x // 2

    clouds = []
    last_cloud_time = time.time()

    while True:
        stdscr.erase()  # Less aggressive than clear(), helps reduce flicker
        # stdscr.addstr(0, 0, f"Score: {score}  |  Use ↑ ↓ to fly, 'q' to quit.")
        try:
            score_text = f"Score: {score} // Storms: {storm_count}"
            stdscr.addstr(0, center_x - len(title) // 2, title, curses.A_BOLD)
            stdscr.addstr(1, center_x - len(subtitle) // 2, subtitle)
            stdscr.addstr(3, center_x - len(score_text) // 2, score_text, curses.A_BOLD)
            # Add credits at the bottom left
            stdscr.addstr(max_y - 1, 0, credit_assets)
        except curses.error:
            pass  # In case terminal is too small

        # Input handling
        key = stdscr.getch()
        if key == curses.KEY_UP and y > UI_HEIGHT:
            y -= 1
        elif key == curses.KEY_DOWN and y < max_y - plane_height - 1:
            y += 1
        elif key == ord('q'):
            break

        # Clouds management
        if time.time() - last_cloud_time > random.uniform(2, 4):
            clouds.append(Cloud(max_y, max_x))
            last_cloud_time = time.time()

        for cloud in clouds:
            cloud.move()
            cloud.draw(stdscr)
        # ✅ Score for dodged clouds
        for cloud in clouds:
            # Mark collided clouds
            if not cloud.collided and check_collision(y, plane_height, x, cloud):
                cloud.collided = True
                storm_count += 1

            # Score only clouds that passed without collision
            if not cloud.scored and not cloud.collided and cloud.x + 10 < x:
                score += 1
                cloud.scored = True
        clouds = [cloud for cloud in clouds if not cloud.is_off_screen()]

        draw_plane(stdscr, y, x)
        # Check for game over condition
        if storm_count >= 3:
            stdscr.addstr(max_y // 2, center_x - len("Game Over") // 2, "Game Over", curses.A_BOLD)
            stdscr.addstr(max_y // 2 + 1, center_x - len("Press any key to restart") // 2, "Press any key to restart")
            stdscr.addstr(max_y // 2 + 2, center_x - len("Press 'q' to quit") // 2, "Press 'q' to quit")
            
            stdscr.refresh()
            while True:
                key = stdscr.getch()
                if key == ord('q'):
                    return
                elif key != -1:
                    # Reset game state
                    score = 0
                    storm_count = 0
                    clouds.clear()
                    y = max_y // 2 - plane_height // 2
                    break



        stdscr.refresh()
        time.sleep(frame_delay)
        frame_delay = max(0.01, 0.05 - score * 0.001)

if __name__ == '__main__':
    curses.wrapper(main)

