import unittest
from types import SimpleNamespace
from unittest.mock import patch

import boy


class FakeImage:
    def __init__(self):
        self.draw_calls = []

    def clip_composite_draw(self, *args):
        pass

    def clip_draw(self, *args):
        self.draw_calls.append(args)


class BoyRunTests(unittest.TestCase):
    def setUp(self):
        self.clock = patch('boy.time.monotonic', return_value=0.0)
        self.clock.start()
        self.addCleanup(self.clock.stop)
        self.image = patch('boy.load_image', return_value=FakeImage())
        self.image.start()
        self.addCleanup(self.image.stop)
        self.character = boy.Boy()

    def send_key(self, event_type, key):
        self.character.handle_event(
            SimpleNamespace(type=event_type, key=key)
        )

    def test_direction_keys_move_and_release_returns_to_idle(self):
        self.send_key(boy.SDL_KEYDOWN, boy.SDLK_RIGHT)
        self.assertEqual(self.character.state, 'RUN')
        self.character.update()
        self.assertEqual(self.character.x, 400 + boy.MOVE_SPEED)

        self.send_key(boy.SDL_KEYUP, boy.SDLK_RIGHT)
        self.assertEqual(self.character.state, 'IDLE')

        self.send_key(boy.SDL_KEYDOWN, boy.SDLK_LEFT)
        self.character.update()
        self.assertEqual(self.character.state, 'RUN')
        self.assertEqual(self.character.x, 400)
        self.send_key(boy.SDL_KEYUP, boy.SDLK_LEFT)
        self.assertEqual(self.character.state, 'IDLE')

    def test_releasing_one_key_keeps_run_while_other_is_held(self):
        self.send_key(boy.SDL_KEYDOWN, boy.SDLK_RIGHT)
        self.send_key(boy.SDL_KEYDOWN, boy.SDLK_LEFT)
        self.send_key(boy.SDL_KEYUP, boy.SDLK_LEFT)
        self.assertEqual(self.character.state, 'RUN')
        self.assertEqual(self.character.face_dir, 1)

        self.send_key(boy.SDL_KEYUP, boy.SDLK_RIGHT)
        self.assertEqual(self.character.state, 'IDLE')

    def test_autorun_state_class_moves_bounces_and_draws_larger(self):
        self.send_key(boy.SDL_KEYDOWN, boy.SDLK_a)
        self.assertIsInstance(self.character.auto_run, boy.AutoRun)
        self.assertEqual(self.character.state, 'AUTORUN')

        self.character.x = 721
        self.character.update()
        self.assertEqual(
            self.character.x,
            boy.SCREEN_WIDTH - boy.AUTO_RUN_SIZE // 2,
        )
        self.assertEqual(self.character.face_dir, -1)

        self.character.x = boy.AUTO_RUN_SIZE // 2 + 1
        self.character.update()
        self.assertEqual(self.character.x, boy.AUTO_RUN_SIZE // 2)
        self.assertEqual(self.character.face_dir, 1)

        self.character.draw()
        self.assertEqual(
            self.character.image.draw_calls[-1][-2:],
            (boy.AUTO_RUN_SIZE, boy.AUTO_RUN_SIZE),
        )

    def test_direction_key_interrupts_autorun_and_starts_normal_run(self):
        self.send_key(boy.SDL_KEYDOWN, boy.SDLK_a)
        self.send_key(boy.SDL_KEYDOWN, boy.SDLK_LEFT)
        self.assertEqual(self.character.state, 'RUN')
        self.assertEqual(self.character.face_dir, -1)

        self.character.update()
        self.assertEqual(self.character.x, 400 - boy.MOVE_SPEED)
        self.send_key(boy.SDL_KEYUP, boy.SDLK_LEFT)
        self.assertEqual(self.character.state, 'IDLE')

    def test_autorun_returns_to_idle_after_five_seconds(self):
        clock = SimpleNamespace(now=100.0)
        with patch('boy.time.monotonic', side_effect=lambda: clock.now):
            character = boy.Boy()
            character.handle_event(
                SimpleNamespace(type=boy.SDL_KEYDOWN, key=boy.SDLK_a)
            )
            clock.now += boy.AUTO_RUN_DURATION
            character.update()
            self.assertEqual(character.state, 'IDLE')
            self.assertEqual(character.idle_started_at, clock.now)


if __name__ == '__main__':
    unittest.main()
