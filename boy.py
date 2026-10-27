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
AUTO_RUN_DURATION = 5


class AutoRun:
    def __init__(self, boy):
        self.boy = boy
        self.started_at = None

    def enter(self):
        self.started_at = time.monotonic()

    def update(self):
        if self.started_at is None:
            raise RuntimeError('AutoRun must be entered before it is updated.')

        if time.monotonic() - self.started_at >= AUTO_RUN_DURATION:
            self.boy.end_auto_run()
            return

        next_x = self.boy.x + self.boy.face_dir * AUTO_RUN_SPEED
        half_width = AUTO_RUN_SIZE // 2
        if next_x <= half_width:
            self.boy.x = half_width
            self.boy.face_dir = 1
        elif next_x >= SCREEN_WIDTH - half_width:
            self.boy.x = SCREEN_WIDTH - half_width
            self.boy.face_dir = -1
        else:
            self.boy.x = next_x
        self.boy.frame = (self.boy.frame + 1) % 8

    def draw(self):
        bottom = 100 if self.boy.face_dir == 1 else 0
        self.boy.image.clip_draw(
            self.boy.frame * 100,
            bottom,
            100,
            100,
            self.boy.x,
            self.boy.y,
            AUTO_RUN_SIZE,
            AUTO_RUN_SIZE,
        )


class Boy:
    def __init__(self):
        self.x, self.y = 400, 90
        self.frame = 0
        self.face_dir = 1
        self.idle_started_at = time.monotonic()
        self.auto_run = AutoRun(self)
        self.keys_down = set()
        self.image = load_image('animation_sheet.png')
        states = ['IDLE', 'RUN', 'SLEEP', 'AUTORUN']
        transitions = [
            {'trigger': 'fall_asleep', 'source': 'IDLE', 'dest': 'SLEEP'},
            {'trigger': 'start_running', 'source': 'IDLE', 'dest': 'RUN'},
            {
                'trigger': 'start_auto_run',
                'source': 'IDLE',
                'dest': 'AUTORUN',
                'after': 'begin_auto_run',
            },
            {
                'trigger': 'end_auto_run',
                'source': 'AUTORUN',
                'dest': 'IDLE',
                'after': 'reset_idle_timer',
            },
            {
                'trigger': 'interrupt_auto_run',
                'source': 'AUTORUN',
                'dest': 'RUN',
            },
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
            self.auto_run.update()

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
        elif self.state == 'AUTORUN':
            self.interrupt_auto_run()

    def reset_idle_timer(self):
        self.idle_started_at = time.monotonic()

    def begin_auto_run(self):
        self.auto_run.enter()

    def draw(self):
        if self.state == 'AUTORUN':
            self.auto_run.draw()
            return

        if self.state == 'SLEEP':
            bottom = 300 if self.face_dir == 1 else 200
            self.image.clip_composite_draw(
                0, bottom, 100, 100, -pi / 2, '', self.x, SLEEP_Y, 100, 100
            )
            return

        if self.state == 'RUN':
            bottom = 100 if self.face_dir == 1 else 0
        else:
            bottom = 300 if self.face_dir == 1 else 200
        self.image.clip_draw(
            self.frame * 100, bottom, 100, 100, self.x, self.y
        )