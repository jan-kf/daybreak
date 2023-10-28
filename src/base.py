import pygame as pg
from typing import Tuple, TypeVar, List, Iterable

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
        self.max_zoom_in = 2  # cap to 2x zoom in
        self.max_zoom_out = -4  # cap to 4x zoom out
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
        if self.zoom_factor > self.max_zoom_in:
            self.zoom_factor = self.max_zoom_in
        elif self.zoom_factor < self.max_zoom_out:
            self.zoom_factor = self.max_zoom_out

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

    def get_top_left_coords(self):
        return self.rect.x, self.rect.y

    def get_center_coords(self):
        return self.rect.centerx, self.rect.centery

    def vec_to_center(self, vec):
        x, y = vec
        self.rect.center = (int(x), int(y))

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

    def get_pos(self, offset=False):
        current_tile_size = self.zoom.get_tile_size()
        return (
            vec(*self.get_scaled_2tuple("start_grid"))
            * (current_tile_size * (1 / self.zoom.sf))
        ) + (
            vec(current_tile_size // 2, current_tile_size // 2) if offset else vec(0, 0)
        )

    # TODO: add a method that makes sure that the shape is centered in its respective grid tile when not moving

    def update(self):
        ...


class Entity(Shape):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.base_image = kwargs["image"]
        # self.base_pos = vec(kwargs.get("x", 0), kwargs.get("y", 0))
        self.start_grid = kwargs.get(
            "grid", vec(0, 0)
        )  # This is the grid-ref starting location

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

    def entity_update(self, relative: bool = False) -> None:
        self.image = pg.transform.rotate(self.get_image(), self.rot)

        x, y = self.get_pos(offset=True)

        self.rect = self.image.get_rect()
        self.rect.center = (int(x), int(y))
        self.hit_rect = self.rect
        # self.hit_rect.center = self.rect.center

    def update(self) -> None:
        self.entity_update()


class MotionEntity(Entity):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    # motion options:
    # move to specific point
    # move to point that moves (seeking)
    # move relatively to current position (direct control)

    # motion config:
    # direct vs pathfinder
    #   ignore obstacles and collide, or navigate?

    # v0.1 motion idea:
    # given a grid of locations, path-find from location to target
    # final path calculation will be a series of movements from one grid to another
    # ex: 0,0 to 3,4 ->| 0,0 > 1,1 > 2,2 > 3,3 > 3,4
    # perform the movements in that order. Recalculate every few moves to see if the terrain has changed

    def move_to(self, target):
        ...

    def displace(self, displacement_vector: vec):
        # move along vector (direct control)
        self.vel = displacement_vector


class Block(Shape):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        # self.base_pos: Coordinate = (kwargs.get("x", 0), kwargs.get("y", 0))
        self.start_grid = kwargs.get("grid", vec(0, 0))
        self.base_size: Size = (kwargs.get("w", 0), kwargs.get("h", 0))

        self.block_update()

    def get_size(self):
        return self.get_scaled_2tuple("base_size")

    def block_update(self) -> None:
        _x, _y = self.get_pos()
        self.rect: pg.rect.Rect = pg.Rect(_x, _y, *self.get_size())
        self.hit_rect: pg.rect.Rect = self.rect

    def update(self) -> None:
        self.block_update()
