import pygame
from pygame.locals import *
 
pygame.init()
clock = pygame.time.Clock()
 
screen_size = 1920, 1080
aspect_ratio = 16,9
screen = pygame.display.set_mode((screen_size[0], screen_size[1]))
pygame.display.set_caption('Zooooom')
 
image_path = 'C:/Users/jasfo/Documents/projects/daybreak/src/world map HD.jpg'
original_image = pygame.image.load(image_path).convert()
 
zoom = 0 
zoom_limit = screen_size[0] / aspect_ratio[0] - 1
pos = [0,0]
 
running = True
 
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
 
            if event.button == 4:
                if zoom < zoom_limit:
 
                    this_crop_distance = zoom * aspect_ratio[0], zoom * aspect_ratio[1]
                    next_crop_distance = (zoom + 1) * aspect_ratio[0], (zoom + 1) * aspect_ratio[1]
 
                    this_zoom_resolution = screen_size[0] - this_crop_distance[0], screen_size[1] - this_crop_distance[1]
                    next_zoom_resolution = screen_size[0] - next_crop_distance[0], screen_size[1] - next_crop_distance[1]
 
                    factor = this_zoom_resolution[0] / next_zoom_resolution[0]
 
                    updated_x = (event.pos[0] - pos[0]) * (factor - 1)
                    updated_y = (event.pos[1] - pos[1]) * (factor - 1)
 
                    pos[0] += updated_x
                    pos[1] += updated_y
 
                    zoom += 1
 
            elif event.button == 5:
                if zoom > 0:
                     
                    this_crop_distance = zoom * aspect_ratio[0], zoom * aspect_ratio[1]
                    next_crop_distance = (zoom-1) * aspect_ratio[0], (zoom-1) * aspect_ratio[1]
 
                    this_zoom_resolution = screen_size[0] - this_crop_distance[0], screen_size[1] - this_crop_distance[1]
                    next_zoom_resolution = screen_size[0] - next_crop_distance[0], screen_size[1] - next_crop_distance[1]
 
                    factor = this_zoom_resolution[0] / next_zoom_resolution[0]
 
                    updated_x = (event.pos[0] - pos[0]) * (factor - 1)
                    updated_y = (event.pos[1] - pos[1]) * (factor - 1)
 
                    pos[0] += updated_x
                    pos[1] += updated_y
 
                    zoom -= 1
 
 
    crop_distance = zoom * aspect_ratio[0], zoom * aspect_ratio[1]
    cropped_region = pos[0], pos[1] , screen_size[0] - crop_distance[0], screen_size[1] - crop_distance[1]
 
    blit_output = pygame.transform.scale(original_image.subsurface(cropped_region), screen_size)
    screen.blit(blit_output, (0,0))
 
    pygame.display.update()
    clock.tick(60)
 
pygame.quit()
quit()