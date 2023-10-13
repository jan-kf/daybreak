import pygame as pg
from typing import Tuple, TypeVar, List, Iterable, cast

vec = pg.math.Vector2
Coordinate = Tuple[int, int]
Size = Tuple[int, int]

T = TypeVar("T")


def sprite_collision(sprite, group: Iterable[T], dokill, collided=None) -> List[T]:
    result = pg.sprite.spritecollide(sprite, group, dokill, collided=collided)  # type: ignore
    return result


class Zoom:
    def __init__(self):
        self.base_scale = 64
        self.zoom_factor = 0
        self.max_delta_zf = 4
        self.calculate_sf()

    def calculate_sf(self):
        # zoom_factor | sf (scale_factor)
        # ...
        #  2 -> 4
        #  1 -> 2
        #  0 -> 1
        # -1 -> 0.5
        # -2 -> 0.25
        # ...
        #
        # y = 2 ** x

        # clamp zoom_factor:
        if abs(self.zoom_factor) > self.max_delta_zf:
            # handle positive/negative
            sign = 1 if self.zoom_factor >= 0 else -1

            self.zoom_factor = self.max_delta_zf * sign

        self.sf: int = 2**self.zoom_factor

    def reset(self):
        self.zoom_factor = 0

    def zoom_in(self, x, y):
        self.zoom_factor += 1
        self.calculate_sf()

    def zoom_out(self, x, y):
        self.zoom_factor -= 1
        self.calculate_sf()

    def scale_image(self, img: pg.Surface):
        w, h = img.get_size()
        w *= self.sf
        h *= self.sf
        return pg.transform.scale(img, (w, h))

    def update(self, *args, **kwargs) -> None:
        pass

    def get_tile_size(self):
        return int(self.base_scale * self.sf)

    def get_linear_update(self, base_value, inverse=False):
        # return base_value
        # value at 64 is the base value
        # but we need to handle what the value should be at 16 and 256

        # 16  - 100
        # 32  - 200
        # 64  - 400 (base_value)
        # 128 - 800
        # 256 - 1600

        if inverse:
            factor = self.sf
        else:
            factor = 1 / self.sf
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
