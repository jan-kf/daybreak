from sprites import Entity, Block
import pygame as pg

class Zoom:
    def __init__(self):
        self.base_scale = 64
        self.base_scale_index = 2
        self.tile_sizes = [16, 32, 64, 128, 256]
        self.tile_size_index = 2
        self.scale = self.get_tile_size()
        self.prev_scale = self.get_tile_size()
        self.scale_factor = self.scale / self.prev_scale
        self.net_scale_factor = self.scale / self.base_scale
        
    def update_scale_factor(self):
        self.scale_factor = self.scale / self.prev_scale
        self.net_scale_factor = self.scale / self.base_scale
 
    def reset(self):
        self.scale = self.base_scale
        self.update_scale_factor()
        
    def zoom_in(self):
        self.prev_scale = self.scale
        self.tile_size_index += 1
        self.tile_size_index = min(4, self.tile_size_index)
        self.scale = self.get_tile_size()
        self.update_scale_factor()
        
    def zoom_out(self):
        self.prev_scale = self.scale
        self.tile_size_index -= 1
        self.tile_size_index = max(0, self.tile_size_index)
        self.scale = self.get_tile_size()
        self.update_scale_factor()
        
    def scale_sprite_image(self, sprite: Entity):
        if sprite.base_image is not None:
            w,h = sprite.base_image.get_size()
            w *= self.net_scale_factor
            h *= self.net_scale_factor
            sprite.image = pg.transform.scale(sprite.base_image, (w, h))
    
    def scale_image(self, img: pg.Surface):
        w,h = img.get_size()
        w *= self.net_scale_factor
        h *= self.net_scale_factor
        return pg.transform.scale(img, (w,h))
        
    def scale_rect(self, sprite: Entity | Block):
        w = sprite.rect.width * self.scale_factor
        h = sprite.rect.height * self.scale_factor
        x = sprite.rect.x * self.scale_factor
        y = sprite.rect.y * self.scale_factor
        sprite.rect.x = x
        sprite.rect.y = y
        sprite.rect.width = w
        sprite.rect.height = h
        sprite.hit_rect = sprite.rect
        
    def update(self, sprite:Entity | Block):
        if sprite.scale != self.scale:
            if isinstance(sprite, Entity) and sprite.pos is not None:
                sprite.pos *= self.scale_factor
                self.scale_rect(sprite)
                self.scale_sprite_image(sprite)
                pass
            elif isinstance(sprite, Block) and sprite.y is not None and sprite.x is not None:
                sprite.x *= self.scale_factor
                sprite.y *= self.scale_factor
                self.scale_rect(sprite)
                    
            sprite.scale = self.scale
        pass
    
    def get_tile_size(self):
        return self.tile_sizes[self.tile_size_index]
    
    def get_linear_update(self, base_value, inverse=False):
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
            factor = (self.base_scale/self.scale) 
        return base_value/factor
        
        