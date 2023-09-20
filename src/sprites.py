import pygame as pg
from random import uniform, choice, randint, random
from settings import *
from base import Entity, Block
from tilemap import collide_hit_rect
import pytweening as tween
from itertools import chain

vec = pg.math.Vector2


def collide_with_walls(sprite, group, dir):
    if dir == "x":
        hits = pg.sprite.spritecollide(sprite, group, False, collide_hit_rect)
        if hits:
            if hits[0].rect.centerx > sprite.hit_rect.centerx:
                sprite.pos.x = hits[0].rect.left - sprite.hit_rect.width / 2
            if hits[0].rect.centerx < sprite.hit_rect.centerx:
                sprite.pos.x = hits[0].rect.right + sprite.hit_rect.width / 2
            sprite.vel.x = 0
            sprite.hit_rect.centerx = sprite.pos.x
    if dir == "y":
        hits = pg.sprite.spritecollide(sprite, group, False, collide_hit_rect)
        if hits:
            if hits[0].rect.centery > sprite.hit_rect.centery:
                sprite.pos.y = hits[0].rect.top - sprite.hit_rect.height / 2
            if hits[0].rect.centery < sprite.hit_rect.centery:
                sprite.pos.y = hits[0].rect.bottom + sprite.hit_rect.height / 2
            sprite.vel.y = 0
            sprite.hit_rect.centery = sprite.pos.y


class Player(Entity):
    def __init__(self, game, x, y, zoom):
        super().__init__(x=x, y=y, image=game.player_img.copy(), zoom=zoom, game=game)
        self._layer = PLAYER_LAYER
        self.groups = game.all_sprites
        pg.sprite.Sprite.__init__(self, self.groups)

        self.last_shot = 0
        self.health = PLAYER_HEALTH
        self.weapon = "pistol"
        self.damaged = False

    def get_keys(self):
        self.rot_speed = 0
        self.vel = vec(0, 0)
        keys = pg.key.get_pressed()
        # if keys[pg.K_LEFT] or keys[pg.K_a]:
        #     self.rot_speed = PLAYER_ROT_SPEED
        # if keys[pg.K_RIGHT] or keys[pg.K_d]:
        #     self.rot_speed = -PLAYER_ROT_SPEED
        # if keys[pg.K_UP] or keys[pg.K_w]:
        #     self.vel = vec(PLAYER_SPEED, 0).rotate(-self.rot)
        # if keys[pg.K_DOWN] or keys[pg.K_s]:
        #     self.vel = vec(-PLAYER_SPEED / 2, 0).rotate(-self.rot)
        if keys[pg.K_LEFT]:
            self.rot_speed = PLAYER_ROT_SPEED
        if keys[pg.K_RIGHT]:
            self.rot_speed = -PLAYER_ROT_SPEED
        if keys[pg.K_UP]:
            self.vel = vec(PLAYER_SPEED, 0).rotate(-self.rot)
        if keys[pg.K_DOWN]:
            self.vel = vec(-PLAYER_SPEED / 2, 0).rotate(-self.rot)
        if keys[pg.K_SPACE]:
            self.shoot()

    def shoot(self):
        now = pg.time.get_ticks()
        if now - self.last_shot > WEAPONS[self.weapon]["rate"]:
            self.last_shot = now
            dir = vec(1, 0).rotate(-self.rot)
            pos = (self.get_pos()) + (BARREL_OFFSET * self.zoom.sf).rotate(-self.rot)

            self.vel = vec(
                -(self.game.zoom.get_linear_update(WEAPONS[self.weapon]["kickback"])), 0
            ).rotate(-self.rot)
            for i in range(WEAPONS[self.weapon]["bullet_count"]):
                _spread = self.game.zoom.get_linear_update(
                    WEAPONS[self.weapon]["spread"]
                )
                spread = uniform(-_spread, _spread)
                Bullet(
                    self.game,
                    pos,
                    dir.rotate(spread),
                    WEAPONS[self.weapon]["damage"],
                    self.zoom,
                )
                snd = choice(self.game.weapon_sounds[self.weapon])
                if snd.get_num_channels() > 2:
                    snd.stop()
                snd.play()
            MuzzleFlash(self.game, pos, self.zoom)

    def hit(self):
        self.damaged = True
        self.damage_alpha = chain(DAMAGE_ALPHA * 4)

    def update(self):
        super().update()

        self.get_keys()

        # self.rot = (self.rot + self.rot_speed * self.game.dt) % 360
        # self.image = pg.transform.rotate(self.image, self.rot)
        if self.damaged:
            try:
                self.image.fill(
                    (255, 255, 255, next(self.damage_alpha)),
                    special_flags=pg.BLEND_RGBA_MULT,
                )
            except:
                self.damaged = False
        # self.rect = self.image.get_rect()
        # self.rect.center = self.pos

        # self.pos += self.vel * self.game.dt

        # collisions:
        # self.hit_rect.centerx = self.pos.x
        # collide_with_walls(self, self.game.walls, "x")
        # self.hit_rect.centery = self.pos.y
        # collide_with_walls(self, self.game.walls, "y")
        # self.rect.center = self.hit_rect.center

    def add_health(self, amount):
        self.health += amount
        if self.health > PLAYER_HEALTH:
            self.health = PLAYER_HEALTH


class Mob(Entity):
    def __init__(self, game, x, y, zoom):
        super().__init__(x=x, y=y, image=game.mob_img.copy(), zoom=zoom, game=game)
        pg.sprite.Sprite.__init__(self, game.all_sprites, game.mobs)

        self._layer = MOB_LAYER
        self.health = MOB_HEALTH
        self.speed = choice(MOB_SPEEDS)
        self.target = game.player

    def avoid_mobs(self):
        for mob in self.game.mobs:
            if mob != self:
                dist = self.pos - mob.pos
                if 0 < dist.length() < self.game.zoom.get_linear_update(AVOID_RADIUS):
                    self.acc += dist.normalize()

    def update(self):
        super().update()
        target_dist = self.target.get_pos() - self.get_pos()
        if (
            target_dist.length_squared()
            < self.game.zoom.get_linear_update(DETECT_RADIUS) ** 2
        ):
            if random() < 0.002:
                choice(self.game.zombie_moan_sounds).play()
            # self.rot = target_dist.angle_to(vec(1, 0))
            # self.image = pg.transform.rotate(self.game.mob_img, self.rot)
            # self.rect.center = self.pos

            # self.acc = vec(1, 0).rotate(-self.rot)
            # self.avoid_mobs()
            # self.acc.scale_to_length(self.speed)
            # self.acc += self.vel * -1
            # self.vel += self.acc * self.game.dt
            # self.pos += self.vel * self.game.dt + 0.5 * self.acc * self.game.dt**2

            # collisions:
            # self.hit_rect.centerx = self.pos.x
            # collide_with_walls(self, self.game.walls, "x")
            # self.hit_rect.centery = self.pos.y
            # collide_with_walls(self, self.game.walls, "y")
            # self.rect.center = self.hit_rect.center

        if self.health <= 0:
            choice(self.game.zombie_hit_sounds).play()
            self.kill()
            self.game.map_img.blit(self.game.splat, self.pos - vec(32, 32))

    def draw_health(self):
        if self.health > 60:
            col = GREEN
        elif self.health > 30:
            col = YELLOW
        else:
            col = RED
        width = int(self.rect.width * self.health / MOB_HEALTH)
        self.health_bar = pg.Rect(0, 0, width, 7)
        if self.health < MOB_HEALTH:
            pg.draw.rect(self.image, col, self.health_bar)


class Bullet(Entity):
    def __init__(self, game, pos, dir, damage, zoom):
        super().__init__(
            x=pos[0],
            y=pos[1],
            image=game.bullet_images[WEAPONS[game.player.weapon]["bullet_size"]],
            zoom=zoom,
            game=game,
        )
        pg.sprite.Sprite.__init__(self, game.all_sprites, game.bullets)
        self._layer = BULLET_LAYER
        self.game = game
        # self.base_image = game.bullet_images[WEAPONS[game.player.weapon]["bullet_size"]]
        # self.image = game.bullet_images[WEAPONS[game.player.weapon]["bullet_size"]]
        # self.rect = self.image.get_rect()
        # self.hit_rect = self.rect
        self.pos = vec(pos)
        self.rect.center = pos
        # spread = uniform(-GUN_SPREAD, GUN_SPREAD)
        self.vel = (
            dir
            * self.game.zoom.get_linear_update(
                WEAPONS[game.player.weapon]["bullet_speed"]
            )
            * uniform(0.9, 1.1)
        )
        self.spawn_time = pg.time.get_ticks()
        self.damage = damage

    def update(self):
        # intentional: no super().update()
        self.pos += self.vel * self.game.dt
        self.rect.center = self.pos
        if pg.sprite.spritecollideany(self, self.game.walls):
            self.kill()
        if (
            pg.time.get_ticks() - self.spawn_time
            > WEAPONS[self.game.player.weapon]["bullet_lifetime"]
        ):
            self.kill()


class Obstacle(Block):
    def __init__(self, game, x, y, w, h, zoom):
        super().__init__(x=x, y=y, w=w, h=h, game=game, zoom=zoom)
        self.groups = game.walls
        pg.sprite.Sprite.__init__(self, self.groups)
        # self.game = game
        # self.rect = pg.Rect(x, y, w, h)
        # self.hit_rect = self.rect
        # self.x = x
        # self.y = y
        # self.rect.x = x
        # self.rect.y = y


class MuzzleFlash(Entity):
    def __init__(self, game, pos, zoom):
        size = randint(20, 50)
        super().__init__(
            x=pos[0],
            y=pos[1],
            image=pg.transform.scale(choice(game.gun_flashes), (size, size)),
            zoom=zoom,
            game=game,
            relative=True,
        )
        self._layer = EFFECTS_LAYER
        self.groups = game.all_sprites
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game

        # self.base_image = pg.transform.scale(choice(game.gun_flashes), (size, size))
        # self.image = pg.transform.scale(choice(game.gun_flashes), (size, size))
        # self.rect = self.image.get_rect()
        # self.hit_rect = self.image.get_rect()
        # self.pos = pos
        # self.rect.center = pos
        # self.hit_rect.center = pos
        self.spawn_time = pg.time.get_ticks()

    def update(self):
        # intentional: no super().update()
        if pg.time.get_ticks() - self.spawn_time > FLASH_DURATION:
            self.kill()


class Item(Entity):
    def __init__(self, game, pos, type, zoom):
        super().__init__(
            x=pos[0],
            y=pos[1],
            image=game.item_images[type].copy(),
            zoom=zoom,
            game=game,
        )
        pg.sprite.Sprite.__init__(self, game.all_sprites, game.items)

        self._layer = ITEMS_LAYER
        self.game = game
        # self.base_image = game.item_images[type].copy()
        # self.image = game.item_images[type].copy()
        # self.rect = self.image.get_rect()
        # self.hit_rect = self.image.get_rect()
        self.type = type
        # self.pos = pos
        # self.rect.center = pos
        # self.hit_rect.center = pos
        self.tween = tween.easeInOutSine
        self.step = 0
        self.dir = 1

    def update(self):
        super().update()
        # bobbing motion
        bob_range = self.zoom.sf * BOB_RANGE
        interval = min(max(self.step / bob_range, 0), 1)
        offset = bob_range * (self.tween(interval) - 0.5)
        self.rect.centery = int(self.pos.y + offset * self.dir)
        self.hit_rect.centery = int(self.pos.y + offset * self.dir)
        self.step += BOB_SPEED * self.zoom.sf
        if self.step > bob_range:
            self.step = 0
            self.dir *= -1
