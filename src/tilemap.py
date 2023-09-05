import pygame as pg
import pytmx
from settings import *
from helpers import debounce
from base import Entity, Block, Zoom


def collide_hit_rect(one, two):
    return one.hit_rect.colliderect(two.rect)


class Map:
    def __init__(self, filename):
        self.data = []
        with open(filename, "rt") as f:
            for line in f:
                self.data.append(line.strip())

        self.tilewidth = len(self.data[0])
        self.tileheight = len(self.data)
        self.width = self.tilewidth * TILESIZE
        self.height = self.tileheight * TILESIZE


class TiledMap:
    def __init__(self, filename):
        self.rect = pg.Rect(0, 0, 0, 0)
        tm = pytmx.load_pygame(filename, pixelalpha=True)
        self.width = tm.width * tm.tilewidth
        self.height = tm.height * tm.tileheight
        self.tmxdata = tm

    def render(self, surface):
        ti = self.tmxdata.get_tile_image_by_gid
        for layer in self.tmxdata.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer):
                for (
                    x,
                    y,
                    gid,
                ) in layer:
                    tile = ti(gid)
                    if tile:
                        surface.blit(
                            tile,
                            (x * self.tmxdata.tilewidth, y * self.tmxdata.tileheight),
                        )

    def make_map(self):
        temp_surface = pg.Surface((self.width, self.height))
        self.render(temp_surface)
        return temp_surface


# TODO: look into the concept of having the entire map loaded, but only adjust what the camera shows
# this might involve having to rethink how things are rendered (sprites + map)
# since they're pixel based instead of relatively sized


class Camera:
    def __init__(
        self, width, height, max_width, max_height, zoom: Zoom, map_img: pg.Surface
    ):
        self.camera = pg.Rect(0, 0, width, height)

        self.sf = 1.0
        self.base_width = width
        self.base_height = height
        self.width = width
        self.height = height
        self.x = 0
        self.y = 0
        self.zoom: Zoom = zoom
        self.map_img = map_img
        self.max_width = max_width
        self.max_height = max_height
        self.scaled_rect: pg.Rect | None = None
        self.rect2: pg.Rect | None = None
        self.prev_sf = 0

    def apply(self, entity: Entity | TiledMap):
        # print(entity.rect.topleft, entity.rect.bottomright)
        return entity.rect.move(self.camera.topleft)

    def apply_rect(self, rect: pg.Rect):
        return rect.move(self.camera.topleft)

    def set_scaled_rect(self, rect1):
        self.scaled_rect = rect1

    # def get_keys(self):
    #     self.rot_speed = 0
    #     self.vel = vec(0, 0)
    #     keys = pg.key.get_pressed()
    #     if keys[pg.K_LEFT] or keys[pg.K_a]:
    #         self.rot_speed = PLAYER_ROT_SPEED
    #     if keys[pg.K_RIGHT] or keys[pg.K_d]:
    #         self.rot_speed = -PLAYER_ROT_SPEED
    #     if keys[pg.K_UP] or keys[pg.K_w]:
    #         self.vel = vec(PLAYER_SPEED, 0)
    #     if keys[pg.K_DOWN] or keys[pg.K_s]:
    #         self.vel = vec(-PLAYER_SPEED / 2, 0)

    def clamp_scroll(self):
        self.x = min(0, self.x)  # left
        self.y = min(0, self.y)  # top


        if self.scaled_rect is not None:
            # print(f"scaled_rect: {self.scaled_rect} {self.zoom.sf}")
            max_x = (self.map_img.get_width() - self.scaled_rect.width) * self.zoom.sf
            max_y = (self.map_img.get_height() - self.scaled_rect.height) * self.zoom.sf

            self.x = max(-max_x, self.x)
            self.y = max(-max_y, self.y)

        # print(
        #     f"mx: {max_x }, my: {max_y } | x: {self.x}, y: {self.y}"
        # )

    def cap_zoom(self):
        if self.zoom.sf == self.prev_sf:
            return True
        else:
            self.prev_sf = self.zoom.sf
            return False

    def get_true_vector(self, display_vector: pg.math.Vector2):
        # display_vector is a vector with respect to the display window
        # ex: a vector A: <3, 6> 's true vector are 3+self.x, 6+self.y
        return vec(self.x, self.y) + display_vector

    def zoom_by_factor(
        self, mouse_vec: pg.math.Vector2, display_rect: pg.Rect, factor: int | float
    ):
        # display_rect: the rectangle of the display (resolution of the window)
        # mouse_vec: the vector of the mouse position at the time of zoom, with respect to the display window
        # if you want to zoom in directly in the center, then you need to provide:
        #   vec(display_rect.centerx, display_rect.centery)
        #   as the mouse_vec

        if self.cap_zoom():
            return False

        # version 0.1:
        # center = mouse_vec
        # true_center = self.get_true_vector(-center)
        # new_true_center = true_center * factor
        # new_topleft = new_true_center + center


        # version 0.2:
        # A*s + B(s-1)
        topleft = vec(self.x, self.y) 
        new_topleft = topleft * factor + (-mouse_vec) * (factor - 1)

        ### debug:
        # print(
        #     f"True center: {true_center} | new true center: {new_true_center} | new topleft: {new_topleft}"
        # )

        self.x, self.y = new_topleft
        self.clamp_scroll()

    def zoom_in(self, mouse_vec: pg.math.Vector2, display_rect: pg.Rect):
        self.zoom_by_factor(mouse_vec, display_rect, 2)
        return True

    def zoom_out(self, mouse_vec: pg.math.Vector2, display_rect: pg.Rect):
        self.zoom_by_factor(mouse_vec, display_rect, 0.5)
        return True

    def move_camera(self):
        cam_move_speed = 2
        keys = pg.key.get_pressed()
        # if keys[pg.K_UP] or keys[pg.K_w]:
        #     self.y += cam_move_speed
        # if keys[pg.K_DOWN] or keys[pg.K_s]:
        #     self.y -= cam_move_speed
        # if keys[pg.K_LEFT] or keys[pg.K_a]:
        #     self.x += cam_move_speed
        # if keys[pg.K_RIGHT] or keys[pg.K_d]:
        #     self.x -= cam_move_speed
        if keys[pg.K_w]:
            self.y += cam_move_speed
        if keys[pg.K_s]:
            self.y -= cam_move_speed
        if keys[pg.K_a]:
            self.x += cam_move_speed
        if keys[pg.K_d]:
            self.x -= cam_move_speed
        if keys[pg.K_0]:
            print("pressed plus")

            print(self.camera)
        if keys[pg.K_9]:
            print("pressed minus")

            print(self.camera)

        self.clamp_scroll()
        # print("final topleft:", self.x, self.y)

    def update(self):
        self.move_camera()
        self.camera = pg.Rect(self.x, self.y, self.width, self.height)

