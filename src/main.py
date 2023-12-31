# Tilemap Demo
# KidsCanCode 2017
import pygame as pg
import sys
from random import choice, random
from os import path
from settings import *
from sprites import *
from tilemap import *
from base import Zoom, sprite_collision
from typing import List

vec = pg.math.Vector2


# HUD functions
def draw_player_health(surf, x, y, pct):
    if pct < 0:
        pct = 0
    BAR_LENGTH = 100
    BAR_HEIGHT = 20
    fill = pct * BAR_LENGTH
    outline_rect = pg.Rect(x, y, BAR_LENGTH, BAR_HEIGHT)
    fill_rect = pg.Rect(x, y, fill, BAR_HEIGHT)
    if pct > 0.6:
        col = GREEN
    elif pct > 0.3:
        col = YELLOW
    else:
        col = RED
    pg.draw.rect(surf, col, fill_rect)
    pg.draw.rect(surf, WHITE, outline_rect, 2)


class Game:
    def __init__(self):
        pg.mixer.pre_init(44100, -16, 4, 2048)
        pg.init()
        # flags = pg.OPENGL | pg.RESIZABLE
        flags = pg.RESIZABLE
        self.screen = pg.display.set_mode((WIDTH, HEIGHT), flags)
        self.rect = self.screen.get_rect()
        self.zoom = Zoom()
        pg.display.set_caption(TITLE)
        self.clock = pg.time.Clock()
        self.load_data()

    def draw_text(self, text, font_name, size, color, x, y, align="topleft"):
        font = pg.font.Font(font_name, size)
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect(**{align: (x, y)})
        self.screen.blit(text_surface, text_rect)

    def load_data(self):
        game_folder = path.dirname(__file__)
        img_folder = path.join(game_folder, "img")
        snd_folder = path.join(game_folder, "snd")
        music_folder = path.join(game_folder, "music")
        self.map_folder = path.join(game_folder, "maps")
        self.title_font = path.join(img_folder, "ZOMBIE.TTF")
        self.hud_font = path.join(img_folder, "Impacted2.0.ttf")
        self.dim_screen = pg.Surface(self.screen.get_size()).convert_alpha()
        self.dim_screen.fill((0, 0, 0, 180))
        self.player_img = pg.image.load(
            path.join(img_folder, PLAYER_IMG)
        ).convert_alpha()
        self.bullet_images = {}
        self.bullet_images["lg"] = pg.image.load(
            path.join(img_folder, BULLET_IMG)
        ).convert_alpha()
        self.bullet_images["sm"] = pg.transform.scale(
            self.bullet_images["lg"], (10, 10)
        )
        self.mob_img = pg.image.load(path.join(img_folder, MOB_IMG)).convert_alpha()
        self.splat = pg.image.load(path.join(img_folder, SPLAT)).convert_alpha()
        self.splat = pg.transform.scale(self.splat, (64, 64))
        self.gun_flashes = []
        for img in MUZZLE_FLASHES:
            self.gun_flashes.append(
                pg.image.load(path.join(img_folder, img)).convert_alpha()
            )
        self.item_images = {}
        for item in ITEM_IMAGES:
            self.item_images[item] = pg.image.load(
                path.join(img_folder, ITEM_IMAGES[item])
            ).convert_alpha()
        # lighting effect
        self.fog = pg.Surface((WIDTH, HEIGHT))
        self.fog.fill(NIGHT_COLOR)
        self.light_mask = pg.image.load(
            path.join(img_folder, LIGHT_MASK)
        ).convert_alpha()
        self.light_mask = pg.transform.scale(self.light_mask, LIGHT_RADIUS)
        self.light_rect = self.light_mask.get_rect()
        # Sound loading
        pg.mixer.music.load(path.join(music_folder, BG_MUSIC))
        self.effects_sounds = {}
        for type in EFFECTS_SOUNDS:
            self.effects_sounds[type] = pg.mixer.Sound(
                path.join(snd_folder, EFFECTS_SOUNDS[type])
            )
        self.weapon_sounds = {}
        for weapon in WEAPON_SOUNDS:
            self.weapon_sounds[weapon] = []
            for snd in WEAPON_SOUNDS[weapon]:
                s = pg.mixer.Sound(path.join(snd_folder, snd))
                s.set_volume(0.3)
                self.weapon_sounds[weapon].append(s)
        self.zombie_moan_sounds = []
        for snd in ZOMBIE_MOAN_SOUNDS:
            s = pg.mixer.Sound(path.join(snd_folder, snd))
            s.set_volume(0.2)
            self.zombie_moan_sounds.append(s)
        self.player_hit_sounds = []
        for snd in PLAYER_HIT_SOUNDS:
            self.player_hit_sounds.append(pg.mixer.Sound(path.join(snd_folder, snd)))
        self.zombie_hit_sounds = []
        for snd in ZOMBIE_HIT_SOUNDS:
            self.zombie_hit_sounds.append(pg.mixer.Sound(path.join(snd_folder, snd)))

    def new(self):
        # initialize all variables and do all the setup for a new game
        self.all_sprites = pg.sprite.LayeredUpdates()
        self.walls = pg.sprite.Group()
        self.mobs: pg.sprite.Group[Mob] = pg.sprite.Group()  # type: ignore (can't fix without using private types)
        self.bullets: pg.sprite.Group[Bullet] = pg.sprite.Group()  # type: ignore (can't fix without using private types)
        self.items: pg.sprite.Group[Item] = pg.sprite.Group()  # type: ignore (can't fix without using private types)
        self.map = TiledMap(path.join(self.map_folder, "level1.tmx"))
        self.map_img = self.map.make_map()
        self.base_map_img = self.map_img.copy()
        self.map.rect = self.map_img.get_rect()
        self.map_wh = (
            self.base_map_img.get_width(),
            self.base_map_img.get_height(),
        )
        for tile_object in self.map.tmxdata.objects:
            obj_center = vec(tile_object.x, tile_object.y)
            if tile_object.name == "player":
                self.player = Player(self, obj_center, self.zoom)
            if tile_object.name == "zombie":
                Mob(self, obj_center, self.zoom)
            if tile_object.name == "wall":
                Obstacle(
                    self,
                    obj_center,
                    tile_object.width,
                    tile_object.height,
                    self.zoom,
                )
            if tile_object.name in ["health", "shotgun"]:
                Item(self, obj_center, tile_object.name, self.zoom)
        self.camera = Camera(
            self.map.width,
            self.map.height,
            *self.map_wh,
            self.zoom,
            self.base_map_img,
        )
        self.draw_debug = True
        self.skip_drawing_map = False
        self.paused = False
        self.night = False
        self.effects_sounds["level_start"].play()

    def run(self):
        # game loop - set self.playing = False to end the game
        self.playing = True
        pg.mixer.music.play(loops=-1)
        while self.playing:
            self.dt = self.clock.tick() / 1000.0  # fix for Python 2.x
            self.events()
            # self.screen.fill('black')
            # self.screen.unlock()
            # self.area.unlock()

            # self.screen.lock()
            if not self.paused:
                self.update()
            self.draw()

    def quit(self):
        pg.quit()
        sys.exit()

    def update(self):
        # update portion of the game loop

        self.all_sprites.update()

        # self.camera.update(self.player) # camera follows the player

        self.camera.update()

        # game over?
        if len(self.mobs) == 0:
            self.playing = False
        # player hits items
        hits = sprite_collision(self.player, self.items, False)
        for hit in hits:
            if hit.type == "health" and self.player.health < PLAYER_HEALTH:
                hit.kill()
                self.effects_sounds["health_up"].play()
                self.player.add_health(HEALTH_PACK_AMOUNT)
            if hit.type == "shotgun":
                hit.kill()
                self.effects_sounds["gun_pickup"].play()
                self.player.weapon = "shotgun"
        # mobs hit player
        hits = sprite_collision(self.player, self.mobs, False, collide_hit_rect)
        for hit in hits:
            if random() < 0.7:
                choice(self.player_hit_sounds).play()
            self.player.health -= MOB_DAMAGE
            hit.vel = vec(0, 0)
            if self.player.health <= 0:
                self.playing = False
        if hits:
            self.player.hit()
            # TODO: rethink hit logic
            # self.player.pos += vec(MOB_KNOCKBACK, 0).rotate(-hits[0].rot)

        # bullets hit mobs
        hits = pg.sprite.groupcollide(self.mobs, self.bullets, False, True)  # type: ignore (I'm not sure how to improve)
        for mob in hits:
            # hit.health -= WEAPONS[self.player.weapon]['damage'] * len(hits[hit])
            for bullet in hits[mob]:
                mob.health -= bullet.damage
            mob.vel = vec(0, 0)

    def draw_grid(self):
        camera_top_left_x, camera_top_left_y = self.camera.camera.topleft
        max_possible_x, max_possible_y = self.camera.get_map_boundary()
        for x in range(0, max_possible_x, self.zoom.get_tile_size()):
            pg.draw.line(
                self.screen,
                LIGHTGREY,
                (x + camera_top_left_x, 0),
                (x + camera_top_left_x, max_possible_y),
            )
        for y in range(0, max_possible_y, self.zoom.get_tile_size()):
            pg.draw.line(
                self.screen,
                LIGHTGREY,
                (0, y + camera_top_left_y),
                (max_possible_x, y + camera_top_left_y),
            )

    # def render_fog(self):
    #     # draw the light mask (gradient) onto fog image
    #     self.fog.fill(NIGHT_COLOR)
    #     self.light_rect.center = self.camera.apply(self.player).center
    #     self.fog.blit(self.light_mask, self.light_rect)
    #     self.screen.blit(self.fog, (0, 0), special_flags=pg.BLEND_MULT)

    def get_map_img(self, display_rect=None):
        if not display_rect:
            display_rect = pg.display.get_surface().get_rect()

        if display_rect.width < self.map_wh[0] and display_rect.height < self.map_wh[1]:
            # zoomed in to the point where the view box is smaller than entire map

            max_x = self.map_wh[0] - display_rect.width
            max_y = self.map_wh[1] - display_rect.height
            x, y = self.camera.camera.topleft
            inv_sf = 1 / self.zoom.sf
            x = abs(x) * inv_sf
            y = abs(y) * inv_sf
            sub = pg.Rect(
                min(x, max_x), min(y, max_y), display_rect.width, display_rect.height
            )
            sub_surface = self.base_map_img.subsurface(sub)
            return self.zoom.scale_image(sub_surface)
        else:
            # zoomed out and can see entire map
            return self.zoom.scale_image(self.base_map_img)

    def draw_map(self, just_black=False):
        self.screen.fill(BLACK)
        # print(self.camera.camera)
        if not just_black:
            # self.screen.blit(self.map_img, self.camera.apply(self.map)) # original
            # self.screen.blit(self.map_img, self.camera.camera)

            display_rect = pg.display.get_surface().get_rect()
            scale_factor = 1 / self.zoom.sf
            w = display_rect.width
            h = display_rect.height
            w *= scale_factor
            h *= scale_factor
            scaled_rect = pg.Rect(display_rect.x, display_rect.y, w, h)
            # self.camera.set_scaled_rect(scaled_rect)

            self.map_img = self.get_map_img(display_rect=scaled_rect)
            self.camera.set_scaled_rect(scaled_rect)
            # print(f"display rectangle: {display_rect} | scaled_rect: {scaled_rect}")
            self.screen.blit(
                self.map_img,
                scaled_rect,
            )

    def draw(self):
        pg.display.set_caption("{:.2f}".format(self.clock.get_fps()))

        # self.screen.fill(BGCOLOR)

        # render the map:
        # TODO: only update/scale map when something changes (the scale, or the camera movement)
        self.draw_map(self.skip_drawing_map)
        # render a black background (featureless map, practically no performance hit)
        # self.screen.fill(BLACK)

        # pg.display.flip()

        for sprite in self.all_sprites:
            # self.zoom.update(sprite, self.screen)
            if isinstance(sprite, Mob):
                sprite.draw_health()
            self.screen.blit(sprite.image, self.camera.apply(sprite))
            if self.draw_debug:
                pg.draw.rect(
                    self.screen, CYAN, self.camera.apply_rect(sprite.hit_rect), 1
                )
        if self.draw_debug:
            self.draw_grid()
            for wall in self.walls:
                # self.zoom.update(wall, self.screen)
                wall.update()
                pg.draw.rect(self.screen, CYAN, self.camera.apply_rect(wall.rect), 1)

        # pg.draw.rect(self.screen, WHITE, self.player.hit_rect, 2)
        # if self.night:
        #     self.render_fog()

        # HUD functions
        draw_player_health(self.screen, 10, 10, self.player.health / PLAYER_HEALTH)
        self.draw_text(
            "Zombies: {}".format(len(self.mobs)),
            self.hud_font,
            30,
            WHITE,
            WIDTH - 10,
            10,
            align="topright",
        )

        if self.paused:
            self.screen.blit(self.dim_screen, (0, 0))
            self.draw_text(
                "Paused",
                self.title_font,
                105,
                RED,
                WIDTH / 2,
                HEIGHT / 2,
                align="center",
            )

        # temp_surface = pg.Surface(self.screen.get_size())
        # temp_surface.blit(self.area, (0,0))
        # self.screen.blit(temp_surface, (0,0))

        pg.display.flip()

    def events(self):
        # catch all events here
        for event in pg.event.get():
            if event.type == pg.MOUSEBUTTONDOWN:
                print(event.__dict__)
                x, y = pg.mouse.get_pos()
                mouse_vec = vec(x, y)
                display_rect = pg.display.get_surface().get_rect()
                print(f"Clicked at ({x}, {y})")
                if event.button == 4:
                    self.area = self.zoom.zoom_in(x, y)
                    self.draw_map(self.skip_drawing_map)
                    self.camera.zoom_in(mouse_vec, display_rect)
                elif event.button == 5:
                    self.area = self.zoom.zoom_out(x, y)
                    self.draw_map(self.skip_drawing_map)
                    self.camera.zoom_out(mouse_vec, display_rect)
                elif event.button == 1:
                    self.area = self.zoom.reset()
            if event.type == pg.QUIT:
                self.quit()
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    self.quit()
                if event.key == pg.K_h:
                    self.draw_debug = not self.draw_debug
                if event.key == pg.K_g:
                    self.skip_drawing_map = not self.skip_drawing_map
                if event.key == pg.K_p:
                    self.paused = not self.paused
                if event.key == pg.K_n:
                    self.night = not self.night
            # if event.type == pg.MOUSEWHEEL:
            #     print(event.x, event.y)
            #     self.camera.handle_mousewheel(event.x, event.y, self.screen)

    def show_start_screen(self):
        pass

    def show_go_screen(self):
        self.screen.fill(BLACK)
        self.draw_text(
            "GAME OVER",
            self.title_font,
            100,
            RED,
            WIDTH / 2,
            HEIGHT / 2,
            align="center",
        )
        self.draw_text(
            "Press a key to start",
            self.title_font,
            75,
            WHITE,
            WIDTH / 2,
            HEIGHT * 3 / 4,
            align="center",
        )
        self.zoom.sf = 1
        pg.display.flip()
        self.wait_for_key()

    def wait_for_key(self):
        pg.event.wait()
        waiting = True
        while waiting:
            # self.clock.tick(FPS)
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    waiting = False
                    self.quit()
                if event.type == pg.KEYUP:
                    waiting = False


# create the game object
g = Game()
g.show_start_screen()
while True:
    g.new()
    g.run()
    g.show_go_screen()
