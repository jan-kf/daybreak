import pygame
 
class Zoom:
    def __init__(self, area, speed, image):
        # Multiply by 2 for smooth rect inflate.
        self.speed = speed * 2
        self.image = image
        self.area = area
        self.inflate = 0
 
    def drift(self, screen_rect, mpos, inward):
        if inward:
            d = (pygame.Vector2(mpos) - screen_rect.center).normalize()
        else:
            d = (pygame.Vector2(screen_rect.center) - mpos).normalize()
 
        d *= self.speed
        self.area.move_ip(int(d.x), int(d.y))
 
    def reset(self, screen_rect):
        self.inflate = 0
        self.area = screen_rect.copy()
        return self.image.subsurface(self.area)
 
    def zoom_in(self, screen_rect, event):
        self.drift(screen_rect, event.pos, True)
        self.inflate -= self.speed
        rect = self.area.inflate(self.inflate, self.inflate)
        rect.clamp_ip(self.image.get_rect())
 
        return pygame.transform.scale(self.image.subsurface(rect), screen_rect.size)
 
    def zoom_out(self, screen_rect, event):
        self.drift(screen_rect, event.pos, False)
        self.inflate += self.speed
        rect = self.area.inflate(self.inflate, self.inflate)
        rect.clamp_ip(self.image.get_rect())
 
        if not self.image.get_rect().contains(rect):
            return self.zoom_in(screen_rect, event)
 
        return pygame.transform.scale(self.image.subsurface(rect), screen_rect.size)
 
def create_map(size, width, colors):
    surface = pygame.Surface((size, size))
    area = pygame.Rect(0, 0, width, width)
    for x in range(0, size, width):
        for y in range(0, size, width):
            area.topleft = x, y
            color = colors[(x//width + y//width) % 2]
            surface.fill(color, area)
 
    return surface
 
def main(caption, width, height, fps=60, flags=0):
    pygame.display.set_caption(caption)
    surface = pygame.display.set_mode((width, height), flags)
    rect = surface.get_rect()
    clock = pygame.time.Clock()
    running = True
    delta = 0
    fps = fps
 
    worldmap = create_map(1000, 50, ('navy', 'dodgerblue'))
    zoom = Zoom(rect.copy(), 5, worldmap)
    area = worldmap.subsurface(zoom.area)
 
    # Main Loop
    while running:
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:
                    area = zoom.zoom_in(rect, event)
                elif event.button == 5:
                    area = zoom.zoom_out(rect, event)
                elif event.button == 1:
                    area = zoom.reset(rect)
 
            elif event.type == pygame.QUIT:
                running = False
 
        surface.fill('black')
        surface.blit(area, (0, 0))
        pygame.display.flip()
        delta = clock.tick(fps)
 
pygame.init()
main("Zoom Example", 800, 600)
pygame.quit()