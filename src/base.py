import pygame as pg
from typing import List, Tuple

vec = pg.math.Vector2
Coordinate = Tuple[int, int]
Size = Tuple[int, int]


class Zoom:
    def __init__(self):
        self.base_scale = 64
        self.base_scale_index = 2
        self.tile_sizes = [16, 32, 64, 128, 256]
        self.scales = [0.25, 0.5, 1, 2, 4]
        self.tile_size_index = 2
        self.sf: float | int = self.scales[self.tile_size_index]
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
        self.sf = self.scales[self.tile_size_index]
        self.scale = self.get_tile_size()
        self.update_scale_factor()
        self.mouse = (x, y)

    def zoom_out(self, x, y):
        self.prev_scale = self.scale
        self.tile_size_index -= 1
        self.tile_size_index = max(0, self.tile_size_index)
        self.sf = self.scales[self.tile_size_index]
        self.scale = self.get_tile_size()
        self.update_scale_factor()
        self.mouse = (x, y)

    def scale_image(self, img: pg.Surface):
        w, h = img.get_size()
        w *= self.net_scale_factor
        h *= self.net_scale_factor
        return pg.transform.scale(img, (w, h))

    def scale_rectangle(self, rect: pg.Rect, scale_factor=1.0):
        rect.scale_by_ip(x=float(scale_factor), y=float(scale_factor))

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

    def get_rounded_val_from_scale(self, val, start_scale, end_scale) -> int:
        return int(self.get_new_val_from_scale(val, start_scale, end_scale) + 0.5)

    def get_new_val_from_scale(self, val, start_scale, end_scale) -> float:
        return (val * end_scale) / start_scale


class Shape(pg.sprite.Sprite):
    def __init__(self, *args, **kwargs) -> None:
        # super().__init__(*args, **kwargs)

        self.game = kwargs["game"]
        self.zoom: Zoom = kwargs["zoom"]
        self.rect: pg.rect.Rect = pg.Rect(0, 0, 0, 0)
        self.hit_rect: pg.rect.Rect = pg.Rect(0, 0, 0, 0)

    def get_scaled_2tuple(self, attr):
        return (
            self.zoom.get_new_val_from_scale(
                getattr(self, attr)[0],
                self.zoom.base_scale,
                int(self.zoom.base_scale * self.zoom.sf),
            ),
            self.zoom.get_new_val_from_scale(
                getattr(self, attr)[1],
                self.zoom.base_scale,
                int(self.zoom.base_scale * self.zoom.sf),
            ),
        )

    def update(self):
        ...


class Entity(Shape):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.base_image = kwargs["image"]
        self.base_pos = vec(kwargs.get("x", 0), kwargs.get("y", 0))

        self.vel = vec(0, 0)
        self.acc = vec(0, 0)
        self.rot = 0

        self.entity_update(kwargs.get("relative", False))

    def get_image(self):
        (w, h) = self.zoom.get_new_size_from_scale(
            self.base_image,
            self.zoom.base_scale,
            int(self.zoom.base_scale * self.zoom.sf),
        )
        return pg.transform.scale(self.base_image.copy(), (w, h))

    def get_pos(self):
        return vec(*self.get_scaled_2tuple("base_pos"))

    def entity_update(self, relative: bool = False) -> None:
        self.image = self.get_image()
        if relative:
            self.pos = self.base_pos
        else:
            self.pos = self.get_pos()
        self.rect = self.image.get_rect()
        self.hit_rect = self.rect
        self.rect.center = (int(self.pos.x), int(self.pos.y))
        self.hit_rect.center = self.rect.center

    def update(self) -> None:
        self.entity_update()


class Block(Shape):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.base_pos: Coordinate = (kwargs.get("x", 0), kwargs.get("y", 0))
        self.base_size: Size = (kwargs.get("w", 0), kwargs.get("h", 0))

        self.block_update()

    def get_pos(self):
        return self.get_scaled_2tuple("base_pos")

    def get_size(self):
        return self.get_scaled_2tuple("base_size")

    def block_update(self) -> None:
        self.x, self.y = self.get_pos()
        self.w, self.h = self.get_size()
        self.rect: pg.rect.Rect = pg.Rect(self.x, self.y, self.w, self.h)
        self.hit_rect: pg.rect.Rect = self.rect
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)

    def update(self) -> None:
        self.block_update()
