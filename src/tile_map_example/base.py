import pygame as pg
from typing import List

vec = pg.math.Vector2


class Zoom:
    def __init__(self):
        self.base_scale = 64
        self.base_scale_index = 2
        self.tile_sizes = [16, 32, 64, 128, 256]
        self.scales = [0.25, 0.5, 1, 1.5, 2]
        self.tile_size_index = 2
        self.scale = self.get_tile_size()
        self.prev_scale = self.get_tile_size()
        self.scale_factor = self.scale / self.prev_scale
        self.net_scale_factor = self.scale / self.base_scale
        self.mouse = (0, 0)

    def update_scale_factor(self):
        self.scale_factor = self.scale / self.prev_scale
        self.net_scale_factor = self.scale / self.base_scale

        print(
            f"Scale: {self.scale} Prev_Scale: {self.prev_scale} ScaleFactor: {self.scale_factor} NetScaleFactor: {self.net_scale_factor}"
        )

    def reset(self):
        self.scale = self.base_scale
        self.update_scale_factor()

    def zoom_in(self, x, y):
        self.prev_scale = self.scale
        self.tile_size_index += 1
        self.tile_size_index = min(4, self.tile_size_index)
        self.scale = self.get_tile_size()
        self.update_scale_factor()
        self.mouse = (x, y)

    def zoom_out(self, x, y):
        self.prev_scale = self.scale
        self.tile_size_index -= 1
        self.tile_size_index = max(0, self.tile_size_index)
        self.scale = self.get_tile_size()
        self.update_scale_factor()
        self.mouse = (x, y)

    # TODO
    # def scale_sprite_image(self, sprite: Entity):
    #     if sprite.base_image is not None:
    #         w, h = sprite.base_image.get_size()
    #         w *= self.net_scale_factor
    #         h *= self.net_scale_factor
    #         sprite.image = pg.transform.scale(sprite.base_image, (w, h))

    def scale_image(self, img: pg.Surface):
        w, h = img.get_size()
        w *= self.net_scale_factor
        h *= self.net_scale_factor
        return pg.transform.scale(img, (w, h))

    # TODO
    # def scale_rect(self, sprite: Entity | Block, screen: pg.surface.Surface):
    #     # sprite.rect.scale_by_ip(self.scales[self.tile_size_index])
    #     # sprite.hit_rect.scale_by_ip(self.scales[self.tile_size_index])
    #     center = screen.get_rect().center

    #     w = sprite.rect.width * self.scale_factor
    #     h = sprite.rect.height * self.scale_factor
    #     x = sprite.rect.x * self.scale_factor
    #     y = sprite.rect.y * self.scale_factor
    #     sprite.rect.x = x
    #     sprite.rect.y = y
    #     sprite.rect.width = w
    #     sprite.rect.height = h
    #     sprite.hit_rect = sprite.rect

    def scale_rectangle(self, rect: pg.Rect, scale_factor=1.0):
        rect.scale_by_ip(x=float(scale_factor), y=float(scale_factor))

    # TODO
    # def update(self, sprite: Entity | Block, screen: pg.surface.Surface):
    #     # return
    #     if sprite.scale != self.scale:
    #         if isinstance(sprite, Entity) and sprite.pos is not None:
    #             sprite.pos *= self.scale_factor
    #             self.scale_rect(sprite, screen)
    #             self.scale_sprite_image(sprite)
    #             pass
    #         elif (
    #             isinstance(sprite, Block)
    #             and sprite.y is not None
    #             and sprite.x is not None
    #         ):
    #             sprite.x *= self.scale_factor
    #             sprite.y *= self.scale_factor
    #             self.scale_rect(sprite, screen)

    #         sprite.scale = self.scale
    #     pass
    def update(self, *args, **kwargs) -> None:
        pass

    def get_tile_size(self):
        return self.tile_sizes[self.tile_size_index]

    def get_linear_update(self, base_value, inverse=False):
        # return base_value
        # value at 64 is the base value
        # but we need to handle what the value should be at 16 and 256

        # 16  - 100
        # 32  - 200
        # 64  - 400 (base_value)
        # 128 - 800
        # 256 - 1600

        if self.scale == self.base_scale:
            return base_value
        if inverse:
            factor = self.net_scale_factor
        else:
            factor = self.base_scale / self.scale
        return base_value / factor

    def get_new_size_from_scale(
        self, image: pg.surface.Surface, current_scale: int, new_scale: int
    ):
        (w, h) = image.get_size()
        return (
            self.get_new_val_from_scale(w, current_scale, new_scale),
            self.get_new_val_from_scale(h, current_scale, new_scale),
        )

    def get_new_val_from_scale(self, val, start_scale, end_scale):
        return (val * end_scale) / start_scale


class Shape(pg.sprite.Sprite):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.game = kwargs["game"]
        self.zoom: Zoom = kwargs["zoom"]
        self.rect: pg.rect.Rect = pg.Rect(0, 0, 0, 0)
        self.hit_rect: pg.rect.Rect = pg.Rect(0, 0, 0, 0)

    # def scale_rect(self, scale_factor):
    #     w = self.rect.width * scale_factor
    #     h = self.rect.height * scale_factor
    #     x = self.rect.x * scale_factor
    #     y = self.rect.y * scale_factor
    #     self.rect.x = x
    #     self.rect.y = y
    #     self.rect.width = w
    #     self.rect.height = h
    #     self.hit_rect = self.rect

    def update(self):
        ...


class Entity(Shape):
    def get_image(self):
        return self.images[self.zoom.tile_size_index]

    def init_images(self, image: pg.Surface):
        self.images: List[pg.surface.Surface] = [
            pg.Surface((0, 0)),
        ] * len(self.zoom.tile_sizes)
        self.images[self.zoom.base_scale_index] = image

        for i in range(len(self.images)):
            if i == self.zoom.base_scale_index:
                continue
            else:
                (w, h) = self.zoom.get_new_size_from_scale(
                    image,
                    self.zoom.tile_sizes[self.zoom.base_scale_index],
                    self.zoom.tile_sizes[i],
                )
                self.images[i] = pg.transform.scale(image, (w, h))

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.init_images(kwargs["image"])

        self.pos = vec(kwargs.get("x", 0), kwargs.get("y", 0))
        self.vel = vec(0, 0)
        self.acc = vec(0, 0)

        self.image = self.get_image()
        self.rect = self.image.get_rect()
        self.hit_rect = self.rect
        self.rot = 0

    def update(self) -> None:
        # self.pos = self.zoom.get_new_val_from_scale(
        #     self.pos, self.zoom.get_tile_size(), 48
        # )
        # TODO: self.pos needs to work like self.images :/
        self.image = self.get_image()
        self.rect = self.image.get_rect()
        self.hit_rect = self.rect


class Block(Shape):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.x = kwargs.get("x", 0)
        self.y = kwargs.get("y", 0)
        self.rect: pg.rect.Rect = pg.Rect(
            self.x, self.y, kwargs.get("w", 0), kwargs.get("h", 0)
        )
        self.hit_rect: pg.rect.Rect = self.rect
        self.rect.x = self.x
        self.rect.y = self.y
