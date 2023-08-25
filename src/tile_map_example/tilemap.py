import pygame as pg
import pytmx
from settings import *


def collide_hit_rect(one, two):
    return one.hit_rect.colliderect(two.rect)

class Map:
    def __init__(self, filename):
        self.data = []
        with open(filename, 'rt') as f:
            for line in f:
                self.data.append(line.strip())

        self.tilewidth = len(self.data[0])
        self.tileheight = len(self.data)
        self.width = self.tilewidth * TILESIZE
        self.height = self.tileheight * TILESIZE

class TiledMap:
    def __init__(self, filename):
        tm = pytmx.load_pygame(filename, pixelalpha=True)
        self.width = tm.width * tm.tilewidth
        self.height = tm.height * tm.tileheight
        self.tmxdata = tm

    def render(self, surface):
        ti = self.tmxdata.get_tile_image_by_gid
        for layer in self.tmxdata.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer):
                for x, y, gid, in layer:
                    tile = ti(gid)
                    if tile:
                        surface.blit(tile, (x * self.tmxdata.tilewidth,
                                            y * self.tmxdata.tileheight))

    def make_map(self):
        temp_surface = pg.Surface((self.width, self.height))
        self.render(temp_surface)
        return temp_surface

class Camera:
    def __init__(self, width, height, zoom):
        self.camera = pg.Rect(0, 0, width, height)
        
        self.base_width = width
        self.base_height = height
        self.width = width
        self.height = height
        self.x = 0
        self.y = 0
        self.zoom = zoom

    def apply(self, entity):
        return entity.rect.move(self.camera.topleft)

    def apply_rect(self, rect):
        return rect.move(self.camera.topleft)
    
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
        # self.x = max(-(self.width - self.zoom.get_linear_update(WIDTH, inverse=True)), self.x)  # right
        # self.y = max(-(self.height - self.zoom.get_linear_update(HEIGHT, inverse=True)), self.y)  # bottom
        self.x = max(-(self.width - WIDTH), self.x)  # right
        self.y = max(-(self.height - HEIGHT), self.y)  # bottom
        
    def move_camera(self):
        cam_move_speed = 1
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
        
        self.clamp_scroll()

    def update(self):
        self.move_camera()
        # print(self.x, self.y)
        
        # x = -target.rect.centerx + int(WIDTH / 2)
        # y = -target.rect.centery + int(HEIGHT / 2)
        
        # limit scrolling to map size
        x = min(0, self.x)  # left
        y = min(0, self.y)  # top
        # x = max(-(self.width - self.zoom.get_linear_update(WIDTH, inverse=True)), x)  # right
        # y = max(-(self.height - self.zoom.get_linear_update(HEIGHT, inverse=True)), y)  # bottom
        x = max(-(self.width - WIDTH), x)  # right
        y = max(-(self.height - HEIGHT), y)  # bottom
        self.camera = pg.Rect(x, y, self.width, self.height)