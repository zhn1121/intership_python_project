import pygame
import sys
import random
import math
from game_objects import Paddle, Ball, Brick, PowerUp, Laser, Particle, Firework

# -- General Setup --
pygame.init()
pygame.mixer.init()
clock = pygame.time.Clock()

# -- Screen Setup --
screen_width = 800
screen_height = 600
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("PyGame Arkanoid")

# -- Colors --
BG_COLOR = pygame.Color('grey12')
BRICK_COLORS = [(178, 34, 34), (255, 165, 0), (255, 215, 0), (50, 205, 50)]

# -- Font Setup --
# !!! PHASE: TITLE SCREEN !!!
title_font = pygame.font.Font(None, 70)
# !!! END PHASE: TITLE SCREEN !!!
game_font = pygame.font.Font(None, 40)
message_font = pygame.font.Font(None, 30)

# -- Sound Setup --
try:
    bounce_sound = pygame.mixer.Sound('bounce.wav')
    brick_break_sound = pygame.mixer.Sound('brick_break.wav')
    game_over_sound = pygame.mixer.Sound('game_over.wav')
    laser_sound = pygame.mixer.Sound('laser.wav')
except pygame.error as e:
    print(f"Warning: Sound file not found. {e}")


    class DummySound:
        def play(self): pass


    bounce_sound, brick_break_sound, game_over_sound, laser_sound = DummySound(), DummySound(), DummySound(), DummySound()

# -- Game Objects --
paddle = Paddle(screen_width, screen_height)
ball = Ball(screen_width, screen_height)


# --- Brick Wall Setup Function ---
def create_brick_wall(level=1):
    bricks = []
    patterns = [
        [(r + c) % 2 == 0 for c in range(10)] for r in range(4)  # level 1 pattern
    ]
    if level == 2:
        patterns = [
            [1 if c % 3 != 0 else 0 for c in range(10)] for r in range(4)
        ]
    elif level == 3:
        patterns = [
            [1 for _ in range(10)] if r != 2 else [0] * 10 for r in range(4)
        ]
    brick_width = 75
    brick_height = 20
    brick_padding = 5
    wall_start_y = 50
    for row in range(len(patterns)):
        for col in range(len(patterns[row])):
            if patterns[row][col]:
                x = col * (brick_width + brick_padding) + brick_padding
                y = row * (brick_height + brick_padding) + wall_start_y
                color = BRICK_COLORS[row % len(BRICK_COLORS)]
                bricks.append(Brick(x, y, brick_width, brick_height, color))
    return bricks


level = 1
bricks = create_brick_wall(level)
power_ups = []
lasers = []
particles = []
fireworks = []

# --- Game Variables ---
# !!! PHASE: TITLE SCREEN !!!
# The game now starts on the title screen
game_state = 'title_screen'
sound_muted = False

# !!! END PHASE: TITLE SCREEN !!!
score = 0
level = 1
lives = 3
display_message = ""
message_timer = 0
firework_timer = 0

# -- Main Game Loop --
while True:
    # --- Event Handling ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            # !!! PHASE: TITLE SCREEN !!!
            if event.key == pygame.K_SPACE:
                # If on title screen, start the game
                if game_state == 'title_screen':
                    game_state = 'playing'
                # If game is over, go back to title screen
                elif game_state in ['game_over', 'you_win']:
                    paddle.reset()
                    ball.reset()
                    bricks = create_brick_wall(level)
                    score = 0
                    level = 1
                    lives = 3
                    power_ups.clear()
                    lasers.clear()
                    particles.clear()
                    fireworks.clear()
                    game_state = 'title_screen'
                    sound_muted = False

                # Launch glued ball
                elif ball.is_glued:
                    ball.is_glued = False
            # !!! END PHASE: TITLE SCREEN !!!

            if event.key == pygame.K_m:
                sound_muted = not sound_muted
            if event.key == pygame.K_f and paddle.has_laser:
                lasers.append(Laser(paddle.rect.centerx - 30, paddle.rect.top))
                lasers.append(Laser(paddle.rect.centerx + 30, paddle.rect.top))
                if not sound_muted: laser_sound.play()

    # --- Drawing and Updating based on Game State ---
    screen.fill(BG_COLOR)

    # !!! PHASE: TITLE SCREEN !!!
    if game_state == 'title_screen':
        # Draw the title
        title_surface = title_font.render("ARKANOID", True, (255, 255, 255))
        title_rect = title_surface.get_rect(center=(screen_width / 2, screen_height / 2 - 50))
        screen.blit(title_surface, title_rect)

        # Draw the start message
        start_surface = game_font.render("Press SPACE to Start", True, (255, 255, 255))
        start_rect = start_surface.get_rect(center=(screen_width / 2, screen_height / 2 + 20))
        screen.blit(start_surface, start_rect)

    elif game_state == 'playing':
        # --- Update all game objects ---
        paddle.update()
        keys = pygame.key.get_pressed()
        ball_status, collision_object = ball.update(paddle, keys[pygame.K_SPACE])

        if ball_status == 'lost':
            lives -= 1
            if lives <= 0:
                game_state = 'game_over'
                if not sound_muted: game_over_sound.play()
            else:
                ball.reset()
                paddle.reset()
        elif collision_object in ['wall', 'paddle']:
            if not sound_muted: bounce_sound.play()
            for _ in range(5):
                particles.append(Particle(ball.rect.centerx, ball.rect.centery, (255, 255, 0), 1, 3, 1, 3, 0))

        for brick in bricks[:]:
            if ball.rect.colliderect(brick.rect):
                ball.speed_y *= -1
                for _ in range(15):
                    particles.append(Particle(brick.rect.centerx, brick.rect.centery, brick.color, 1, 4, 1, 4, 0.05))
                bricks.remove(brick)
                score += 10
                if not sound_muted: brick_break_sound.play()
                if random.random() < 0.3:
                    power_up_type = random.choice(['grow', 'laser', 'glue', 'slow', 'extra_life', 'shrink'])
                    power_up = PowerUp(brick.rect.centerx, brick.rect.centery, power_up_type)
                    power_ups.append(power_up)
                break

        for power_up in power_ups[:]:
            power_up.update()
            if power_up.rect.top > screen_height:
                power_ups.remove(power_up)
            elif paddle.rect.colliderect(power_up.rect):
                display_message = power_up.PROPERTIES[power_up.type]['message']
                message_timer = 120
                if power_up.type in ['grow', 'laser', 'glue']:
                    paddle.activate_power_up(power_up.type)
                elif power_up.type == 'extra_life':
                    lives += 1
            elif power_up.type == 'shrink':
                paddle.activate_power_up('shrink')
                ball.activate_power_up(power_up.type)
                power_ups.remove(power_up)

        for laser in lasers[:]:
            laser.update()
            if laser.rect.bottom < 0:
                lasers.remove(laser)
            else:
                for brick in bricks[:]:
                    if laser.rect.colliderect(brick.rect):
                        for _ in range(10):
                            particles.append(
                                Particle(brick.rect.centerx, brick.rect.centery, brick.color, 1, 3, 1, 3, 0.05))
                        bricks.remove(brick)
                        lasers.remove(laser)
                        score += 10
                        if not sound_muted: brick_break_sound.play()
                        break

        if not bricks:
            if level < 3:
                level += 1
                bricks = create_brick_wall(level)
                ball.reset()
                paddle.reset()
            else:
                game_state = 'you_win'

        # --- Draw all game objects ---
        paddle.draw(screen)
        ball.draw(screen)
        for brick in bricks:
            brick.draw(screen)
        for power_up in power_ups:
            power_up.draw(screen)
        for laser in lasers:
            laser.draw(screen)

        # --- Draw UI ---
        score_text = game_font.render(f"Score: {score}", True, (255, 255, 255))
        screen.blit(score_text, (10, 10))
        lives_text = game_font.render(f"Lives: {lives}", True, (255, 255, 255))
        screen.blit(lives_text, (screen_width - lives_text.get_width() - 10, 10))

    elif game_state in ['game_over', 'you_win']:
        if game_state == 'you_win':
            firework_timer -= 1
            if firework_timer <= 0:
                fireworks.append(Firework(screen_width, screen_height))
                firework_timer = random.randint(20, 50)

            for firework in fireworks[:]:
                firework.update()
                if firework.is_dead():
                    fireworks.remove(firework)

            for firework in fireworks:
                firework.draw(screen)

        message = "GAME OVER" if game_state == 'game_over' else "YOU WIN!"
        text_surface = game_font.render(message, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(screen_width / 2, screen_height / 2 - 20))
        screen.blit(text_surface, text_rect)

        # !!! PHASE: TITLE SCREEN !!!
        # The restart message is now consistent
        restart_surface = game_font.render("Press SPACE to return to Title", True, (255, 255, 255))
        # !!! END PHASE: TITLE SCREEN !!!
        restart_rect = restart_surface.get_rect(center=(screen_width / 2, screen_height / 2 + 30))
        screen.blit(restart_surface, restart_rect)

    # --- Update effects and messages (these run in all states) ---
    if message_timer > 0:
        message_timer -= 1
        message_surface = message_font.render(display_message, True, (255, 255, 255))
        message_rect = message_surface.get_rect(center=(screen_width / 2, screen_height - 60))
        screen.blit(message_surface, message_rect)

    for particle in particles[:]:
        particle.update()
        if particle.size <= 0:
            particles.remove(particle)
    for particle in particles:
        particle.draw(screen)
    # !!! END PHASE: TITLE SCREEN !!!

    # --- Final Display Update ---
    pygame.display.flip()
    clock.tick(60)
