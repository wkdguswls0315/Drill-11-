from math import pi
import time

from pico2d import (
    SDL_KEYDOWN,
    SDL_KEYUP,
    SDLK_LEFT,
    SDLK_RIGHT,
    SDLK_SPACE,
    SDLK_a,
    load_image,
)
from transitions import Machine

SCREEN_WIDTH = 800
CHARACTER_WIDTH = 100
SLEEP_Y = 77
MOVE_SPEED = 5
AUTO_RUN_SPEED = MOVE_SPEED * 2
AUTO_RUN_SIZE = 150


class Boy:
    def __init__(self):
        self.x, self.y = 400, 90
        self.frame = 0
        self.face_dir = 1
        self.idle_started_at = time.monotonic()
        self.keys_down = set()
        self.image = load_image('animation_sheet.png')
        states = ['IDLE', 'RUN', 'SLEEP', 'AUTORUN']
        transitions = [
            {'trigger': 'fall_asleep', 'source': 'IDLE', 'dest': 'SLEEP'},
            {'trigger': 'start_running', 'source': 'IDLE', 'dest': 'RUN'},
            {'trigger': 'start_auto_run', 'source': 'IDLE', 'dest': 'AUTORUN'},
            {'trigger': 'wake_and_run', 'source': 'SLEEP', 'dest': 'RUN'},
            {
                'trigger': 'stop_running',
                'source': 'RUN',
                'dest': 'IDLE',
                'after': 'reset_idle_timer',
            },
            {
                'trigger': 'wake_up',
                'source': 'SLEEP',
                'dest': 'IDLE',
                'after': 'reset_idle_timer',
            },
        ]
        self.machine = Machine(
            model=self,
            states=states,
            transitions=transitions,
            initial='IDLE',
            auto_transitions=False,
        )

    def update(self):
        if self.state == 'IDLE':
            if time.monotonic() - self.idle_started_at >= 5:
                self.fall_asleep()
            else:
                self.frame = (self.frame + 1) % 8
        elif self.state == 'RUN':
            self.move_horizontally()
            self.frame = (self.frame + 1) % 8
        elif self.state == 'AUTORUN':
            self.x += self.face_dir * AUTO_RUN_SPEED
            self.frame = (self.frame + 1) % 8

    def move_horizontally(self):
        moving_left = SDLK_LEFT in self.keys_down
        moving_right = SDLK_RIGHT in self.keys_down

        if moving_left and not moving_right:
            self.face_dir = -1
            self.x = max(CHARACTER_WIDTH // 2, self.x - MOVE_SPEED)
        elif moving_right and not moving_left:
            self.face_dir = 1
            self.x = min(
                SCREEN_WIDTH - CHARACTER_WIDTH // 2,
                self.x + MOVE_SPEED,
            )

    def handle_event(self, event):
        if event.type == SDL_KEYUP:
            if event.key in (SDLK_LEFT, SDLK_RIGHT):
                self.keys_down.discard(event.key)
                if self.state == 'RUN':
                    if not self.keys_down:
                        self.stop_running()
                    elif SDLK_LEFT in self.keys_down:
                        self.face_dir = -1
                    else:
                        self.face_dir = 1
            return

        if event.type != SDL_KEYDOWN:
            return

        if event.key == SDLK_SPACE:
            if self.state == 'SLEEP':
                self.wake_up()
            return

        if event.key == SDLK_a:
            if self.state == 'IDLE':
                self.start_auto_run()
            return

        if event.key not in (SDLK_LEFT, SDLK_RIGHT):
            return

        if self.state == 'SLEEP':
            if event.key == SDLK_LEFT:
                self.face_dir = -1
            else:
                self.face_dir = 1
            self.keys_down.add(event.key)
            self.wake_and_run()
            return

        self.keys_down.add(event.key)
        if event.key == SDLK_LEFT:
            self.face_dir = -1
        else:
            self.face_dir = 1
        if self.state == 'IDLE':
            self.start_running()

    def reset_idle_timer(self):
        self.idle_started_at = time.monotonic()

    def draw(self):
        if self.state == 'SLEEP':
            bottom = 300 if self.face_dir == 1 else 200
            self.image.clip_composite_draw(
                0, bottom, 100, 100, -pi / 2, '', self.x, SLEEP_Y, 100, 100
            )
            return

        if self.state in ('RUN', 'AUTORUN'):
            bottom = 100 if self.face_dir == 1 else 0
        else:
            bottom = 300 if self.face_dir == 1 else 200
        if self.state == 'AUTORUN':
            self.image.clip_draw(
                self.frame * 100,
                bottom,
                100,
                100,
                self.x,
                self.y,
                AUTO_RUN_SIZE,
                AUTO_RUN_SIZE,
            )
        else:
            self.image.clip_draw(
                self.frame * 100, bottom, 100, 100, self.x, self.y
            )