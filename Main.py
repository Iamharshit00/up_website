from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.graphics import Rectangle, Color
from kivy.core.audio import SoundLoader
from kivy.properties import NumericProperty, BooleanProperty
import random
import os

# Screen size
Window.size = (400, 600)

# Constants
WIDTH = 400
HEIGHT = 600
GRAVITY = 0.5
JUMP_POWER = -12
MOVE_SPEED = 5
JUMP_GAP = 120
PLATFORM_WIDTH = 80
PLATFORM_HEIGHT = 15


def load_high_score():
    try:
        with open('High_score.txt', 'r') as f:
            return int(f.read())
    except:
        return 0


def save_high_score(score):
    hs = load_high_score()
    if score > hs:
        try:
            with open('High_score.txt', 'w') as f:
                f.write(str(score))
        except:
            pass


class GameWidget(Widget):
    """Main game canvas widget"""
    pass


class MenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.button_sound = SoundLoader.load('select_button.mp3')
        if self.button_sound:
            self.button_sound.volume = 0.5
        self._build_ui()

    def _build_ui(self):
        self.layout = FloatLayout(size=self.size, pos=self.pos)
        self.bind(size=self._update_layout, pos=self._update_layout)

        # Background
        self.bg = Image(source='A serene sky over lish cliffs.png',
                        size=self.size, pos=self.pos,
                        allow_stretch=True, keep_ratio=False)
        self.layout.add_widget(self.bg)

        # Logo
        self.logo = Image(source='logo.png', size=(100, 100), pos=(150, 400))
        self.layout.add_widget(self.logo)

        # High score label
        hs = load_high_score()
        self.hs_label = Label(text=f'High Score: {hs}',
                              pos=(10, 570), size=(200, 30),
                              color=(1, 0, 0, 1), font_size=18)
        self.layout.add_widget(self.hs_label)

        # Credits
        self.credit = Label(text='Made by: Harshit Singh',
                            pos=(200, 10), size=(200, 30),
                            color=(1, 0, 0, 1), font_size=14)
        self.layout.add_widget(self.credit)

        # Play button
        self.play_btn = Button(size=(150, 60), pos=(125, 250),
                               background_normal='play button.png',
                               background_down='play button.png',
                               border=[0, 0, 0, 0])
        self.play_btn.bind(on_press=self.start_game)
        self.layout.add_widget(self.play_btn)

        # Exit button
        self.exit_btn = Button(size=(150, 60), pos=(125, 170),
                               background_normal='Exit button.png',
                               background_down='Exit button.png',
                               border=[0, 0, 0, 0])
        self.exit_btn.bind(on_press=self.exit_app)
        self.layout.add_widget(self.exit_btn)

        self.add_widget(self.layout)

    def _update_layout(self, instance, value):
        self.layout.size = instance.size
        self.layout.pos = instance.pos
        self.bg.size = instance.size
        self.bg.pos = instance.pos

    def play_sound(self):
        if self.button_sound:
            self.button_sound.play()

    def start_game(self, instance):
        self.play_sound()
        # Refresh high score display
        hs = load_high_score()
        self.hs_label.text = f'High Score: {hs}'
        self.manager.current = 'game'
        game_screen = self.manager.get_screen('game')
        game_screen.start_new_game()

    def exit_app(self, instance):
        self.play_sound()
        App.get_running_app().stop()
        Window.close()


class GameScreen(Screen):
    score = NumericProperty(0)
    game_over = BooleanProperty(False)
    game_paused = BooleanProperty(False)
    cheat_mode = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Game state
        self.player_x = 200
        self.player_y = 500
        self.player_w = 30
        self.player_h = 50
        self.velocity_y = 0
        self.on_ground = False
        self.facing_right = True
        self.move_left_active = False
        self.move_right_active = False
        self.platforms = []
        self.game_started_once = False
        self._keyboard = None

        # Load sounds
        self.jump_sound = SoundLoader.load('jump.mp3')
        self.game_over_sound = SoundLoader.load('game-over.mp3')
        self.button_sound = SoundLoader.load('select_button.mp3')
        self.game_start_sound = SoundLoader.load('foxboytails-game-start-317318.mp3')
        self.bg_music = SoundLoader.load('music.mp3')

        if self.jump_sound:
            self.jump_sound.volume = 0.6
        if self.game_over_sound:
            self.game_over_sound.volume = 0.8
        if self.button_sound:
            self.button_sound.volume = 0.5

        self._build_ui()
        self._init_platforms()

        # Bind keyboard
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(keyboard_key_down=self._on_key_down,
                           keyboard_key_up=self._on_key_up)

    def _keyboard_closed(self):
        if self._keyboard:
            self._keyboard.unbind(keyboard_key_down=self._on_key_down,
                                  keyboard_key_up=self._on_key_up)
            self._keyboard = None

    def _on_key_down(self, keyboard, keycode, text, modifiers):
        if keycode[1] == 'left':
            self.move_left_active = True
        elif keycode[1] == 'right':
            self.move_right_active = True
        elif keycode[1] == 'space':
            self._do_jump()
        elif keycode[1] == 'c':
            self.cheat_mode = not self.cheat_mode
        elif keycode[1] == 'escape':
            if not self.game_over:
                self._pause_game()
        return True

    def _on_key_up(self, keyboard, keycode):
        if keycode[1] == 'left':
            self.move_left_active = False
        elif keycode[1] == 'right':
            self.move_right_active = False
        return True

    def _build_ui(self):
        self.layout = FloatLayout(size=self.size, pos=self.pos)
        self.bind(size=self._update_layout, pos=self._update_layout)

        # Background
        self.bg = Image(source='A serene sky over lush cliffs.png',
                        size=self.size, pos=self.pos,
                        allow_stretch=True, keep_ratio=False)
        self.layout.add_widget(self.bg)

        # Game canvas
        self.game_canvas = Widget(size=self.size, pos=self.pos)
        self.layout.add_widget(self.game_canvas)

        # Score label
        self.score_label = Label(text='Score: 0',
                                 pos=(280, 565), size=(120, 30),
                                 color=(0, 0, 0, 1), font_size=18)
        self.layout.add_widget(self.score_label)

        # Credits
        self.credit_label = Label(text='Made by: Harshit Singh',
                                  pos=(200, 5), size=(200, 25),
                                  color=(1, 0, 0, 1), font_size=12)
        self.layout.add_widget(self.credit_label)

        # Control buttons
        self.stop_btn = Button(size=(40, 40), pos=(350, 555),
                               background_normal='stop.png',
                               background_down='stop.png',
                               border=[0, 0, 0, 0])
        self.stop_btn.bind(on_press=self._pause_game)
        self.layout.add_widget(self.stop_btn)

        # Left button
        self.left_btn = Button(size=(60, 60), pos=(260, 20),
                               background_normal='left.png',
                               background_down='left.png',
                               border=[0, 0, 0, 0])
        self.left_btn.bind(on_press=self._start_left)
        self.left_btn.bind(on_release=self._stop_left)
        self.layout.add_widget(self.left_btn)

        # Right button
        self.right_btn = Button(size=(60, 60), pos=(330, 20),
                                background_normal='right.png',
                                background_down='right.png',
                                border=[0, 0, 0, 0])
        self.right_btn.bind(on_press=self._start_right)
        self.right_btn.bind(on_release=self._stop_right)
        self.layout.add_widget(self.right_btn)

        # Jump button
        self.jump_btn = Button(size=(70, 70), pos=(10, 15),
                               background_normal='jump.png',
                               background_down='jump.png',
                               border=[0, 0, 0, 0])
        self.jump_btn.bind(on_press=self._jump_pressed)
        self.layout.add_widget(self.jump_btn)

        # Game Over Overlay
        self.go_overlay = FloatLayout(size=self.size, pos=self.pos)
        self.go_overlay.opacity = 0
        self.go_overlay.disabled = True

        self.go_title = Label(text='GAME OVER',
                              pos=(100, 420), size=(200, 40),
                              color=(1, 0, 0, 1), font_size=28,
                              bold=True)
        self.go_overlay.add_widget(self.go_title)

        self.go_hs_label = Label(text='High Score: 0',
                                 pos=(110, 380), size=(180, 30),
                                 color=(1, 0, 0, 1), font_size=18)
        self.go_overlay.add_widget(self.go_hs_label)

        self.restart_btn = Button(size=(130, 50), pos=(135, 280),
                                  background_normal='Restart_Button.png',
                                  background_down='Restart_Button.png',
                                  border=[0, 0, 0, 0])
        self.restart_btn.bind(on_press=self._restart_game)
        self.go_overlay.add_widget(self.restart_btn)

        self.go_menu_btn = Button(size=(200, 50), pos=(100, 200),
                                  background_normal='Back to main menu.png',
                                  background_down='Back to main menu.png',
                                  border=[0, 0, 0, 0])
        self.go_menu_btn.bind(on_press=self._back_to_menu)
        self.go_overlay.add_widget(self.go_menu_btn)

        self.layout.add_widget(self.go_overlay)

        # Pause Overlay
        self.pause_overlay = FloatLayout(size=self.size, pos=self.pos)
        self.pause_overlay.opacity = 0
        self.pause_overlay.disabled = True

        self.pause_title = Label(text='Game Paused',
                                 pos=(100, 450), size=(200, 40),
                                 color=(1, 0, 0, 1), font_size=28,
                                 bold=True)
        self.pause_overlay.add_widget(self.pause_title)

        self.pause_hs_label = Label(text='High Score: 0',
                                    pos=(110, 410), size=(180, 30),
                                    color=(1, 0, 0, 1), font_size=18)
        self.pause_overlay.add_widget(self.pause_hs_label)

        self.resume_btn = Button(size=(100, 50), pos=(150, 320),
                                 background_normal='resume.png',
                                 background_down='resume.png',
                                 border=[0, 0, 0, 0])
        self.resume_btn.bind(on_press=self._resume_game)
        self.pause_overlay.add_widget(self.resume_btn)

        self.pause_menu_btn = Button(size=(200, 50), pos=(100, 240),
                                     background_normal='Back to main menu.png',
                                     background_down='Back to main menu.png',
                                     border=[0, 0, 0, 0])
        self.pause_menu_btn.bind(on_press=self._back_to_menu)
        self.pause_overlay.add_widget(self.pause_menu_btn)

        self.layout.add_widget(self.pause_overlay)

        self.add_widget(self.layout)

        # Game loop
        self.game_event = Clock.schedule_interval(self.update, 1.0 / 60.0)

    def _update_layout(self, instance, value):
        self.layout.size = instance.size
        self.layout.pos = instance.pos
        self.bg.size = instance.size
        self.bg.pos = instance.pos
        self.game_canvas.size = instance.size
        self.game_canvas.pos = instance.pos

    def _init_platforms(self):
        self.platforms = []
        # First platform at bottom
        self.platforms.append([150, HEIGHT - 40, PLATFORM_WIDTH, PLATFORM_HEIGHT])
        for i in range(1, 6):
            x = random.randint(0, WIDTH - PLATFORM_WIDTH)
            y = HEIGHT - 40 - (i * JUMP_GAP)
            self.platforms.append([x, y, PLATFORM_WIDTH, PLATFORM_HEIGHT])

    def _play_sound(self, sound):
        if sound:
            sound.play()

    def _start_left(self, instance):
        self.move_left_active = True

    def _stop_left(self, instance):
        self.move_left_active = False

    def _start_right(self, instance):
        self.move_right_active = True

    def _stop_right(self, instance):
        self.move_right_active = False

    def _jump_pressed(self, instance):
        self._do_jump()

    def _do_jump(self):
        if self.on_ground and not self.game_over and not self.game_paused:
            self.velocity_y = JUMP_POWER
            self.on_ground = False
            self._play_sound(self.jump_sound)

    def _pause_game(self, instance=None):
        if not self.game_paused and not self.game_over:
            self._play_sound(self.button_sound)
            self.game_paused = True
            self.pause_overlay.opacity = 1
            self.pause_overlay.disabled = False
            hs = load_high_score()
            self.pause_hs_label.text = f'High Score: {hs}'

    def _resume_game(self, instance):
        self._play_sound(self.button_sound)
        self.game_paused = False
        self.pause_overlay.opacity = 0
        self.pause_overlay.disabled = True

    def _restart_game(self, instance):
        self._play_sound(self.button_sound)
        self._reset_game()

    def _reset_game(self):
        self.game_over = False
        self.game_paused = False
        self.score = 0
        self.player_x = 200
        self.player_y = 500
        self.velocity_y = 0
        self.on_ground = False
        self.facing_right = True
        self.cheat_mode = False
        self.platforms.clear()
        self._init_platforms()
        self.go_overlay.opacity = 0
        self.go_overlay.disabled = True
        self.pause_overlay.opacity = 0
        self.pause_overlay.disabled = True

    def _back_to_menu(self, instance):
        self._play_sound(self.button_sound)
        save_high_score(int(self.score))
        self._reset_game()
        self.manager.current = 'menu'

    def start_new_game(self):
        """Called when entering game screen from menu"""
        self._reset_game()
        if not self.game_started_once:
            if self.game_start_sound:
                self.game_start_sound.play()
            self.game_started_once = True
        if self.bg_music and not self.bg_music.state == 'play':
            self.bg_music.volume = 0.2
            self.bg_music.loop = True
            self.bg_music.play()

    def _check_collision(self):
        """Check collision between player and platforms"""
        px, py = self.player_x, self.player_y
        pw, ph = self.player_w, self.player_h

        for plat in self.platforms:
            platx, platy, platw, plath = plat
            # Check if player is falling onto platform
            if (px + pw > platx and px < platx + platw and
                py + ph > platy and py + ph < platy + plath + self.velocity_y + 2 and
                self.velocity_y >= 0):
                return True, plat
        return False, None

    def update(self, dt):
        if self.game_paused or self.game_over:
            self._draw()
            return

        # Handle movement
        if self.move_left_active:
            self.player_x -= MOVE_SPEED
            self.facing_right = False
        if self.move_right_active:
            self.player_x += MOVE_SPEED
            self.facing_right = True

        # Screen wrap
        if self.player_x + self.player_w < 0:
            self.player_x = WIDTH
        elif self.player_x > WIDTH:
            self.player_x = -self.player_w

        # Apply gravity
        self.velocity_y += GRAVITY
        self.player_y += self.velocity_y

        # Platform collision
        self.on_ground = False
        collided, plat = self._check_collision()
        if collided and plat:
            self.player_y = plat[1] - self.player_h
            self.velocity_y = 0
            self.on_ground = True

        # Camera scroll when player goes up
        if self.player_y < HEIGHT // 3:
            scroll = HEIGHT // 3 - self.player_y
            self.player_y = HEIGHT // 3
            self.score += scroll

            for plat in self.platforms:
                plat[1] += scroll

        # Regenerate platforms that go off screen
        for i, plat in enumerate(self.platforms):
            if plat[1] > HEIGHT:
                highest = min(self.platforms, key=lambda p: p[1])
                new_x = random.randint(0, WIDTH - PLATFORM_WIDTH)
                new_y = highest[1] - JUMP_GAP
                self.platforms[i] = [new_x, new_y, PLATFORM_WIDTH, PLATFORM_HEIGHT]

        # Game over check
        if self.player_y > HEIGHT:
            self.game_over = True
            self._play_sound(self.game_over_sound)
            save_high_score(int(self.score))
            hs = load_high_score()
            self.go_hs_label.text = f'High Score: {hs}'
            self.go_overlay.opacity = 1
            self.go_overlay.disabled = False

        # Draw
        self._draw()

    def _draw(self):
        self.game_canvas.canvas.clear()

        # Cheat mode background
        if self.cheat_mode:
            with self.game_canvas.canvas:
                Color(random.random(), random.random(), random.random(), 1)
                Rectangle(pos=self.game_canvas.pos, size=self.game_canvas.size)

        # Draw platforms
        with self.game_canvas.canvas:
            Color(1, 1, 1, 1)
            for plat in self.platforms:
                Rectangle(source='plateform1.png',
                          pos=(plat[0], plat[1]),
                          size=(plat[2], plat[3]))

        # Draw player
        with self.game_canvas.canvas:
            Color(1, 1, 1, 1)
            player_source = 'charecter.png'
            if not self.facing_right:
                player_source = 'charecter_flipped.png'
            Rectangle(source=player_source,
                      pos=(self.player_x, self.player_y),
                      size=(self.player_w, self.player_h))

        # Update score label
        self.score_label.text = f'Score: {int(self.score)}'

    def on_leave(self, *args):
        """Called when leaving this screen"""
        pass

    def on_enter(self, *args):
        """Called when entering this screen"""
        pass


class UpApp(App):
    def build(self):
        self.sm = ScreenManager()
        self.sm.add_widget(MenuScreen(name='menu'))
        self.sm.add_widget(GameScreen(name='game'))
        return self.sm

    def on_pause(self):
        return True

    def on_resume(self):
        pass


if __name__ == '__main__':
    UpApp().run()