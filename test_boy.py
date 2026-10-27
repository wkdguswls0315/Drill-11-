import unittest
from types import SimpleNamespace
from unittest.mock import patch

import boy


class FakeImage:
    def clip_composite_draw(self, *args):
        pass

    def clip_draw(self, *args):
        pass


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


if __name__ == '__main__':
    unittest.main()
