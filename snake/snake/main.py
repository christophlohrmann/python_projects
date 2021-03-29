import pygame
import numpy as np

DIR_UP = np.array([0, -1])
DIR_DOWN = np.array([0, 1])
DIR_LEFT = np.array([-1, 0])
DIR_RIGHT = np.array([1, 0])


class Snake(object):
    def __init__(self, start_pos, head_color=(0, 255, 0), body_color=(0, 150, 0)):
        self.head_color = head_color
        self.body_color = body_color

        self.head_direction = DIR_RIGHT
        self.nodes = [Node(np.asarray(start_pos), color=head_color)]

        # snakes grow to the back, so to add new elements at the rear, we need the last position the snake was
        self.previous_freed_pos = None

    def __len__(self):
        return len(self.nodes)

    def get_head(self):
        return self.nodes[0]

    def get_nodes(self):
        return self.nodes

    def move_one_step(self):
        # update the last freed pos in case we need to grow in this step
        self.previous_freed_pos = self.nodes[-1].pos

        # do the actual moving. start moving at the tail to not override the previous positions
        for i in range(len(self.nodes) - 1, 0, -1):
            self.nodes[i].pos = self.nodes[i - 1].pos
        self.nodes[0].pos += self.head_direction

    def grow(self):
        self.nodes.append(Node(self.previous_freed_pos, color=self.body_color))

    def check_overlap(self):
        pos_filter = lambda node: np.all(node.pos == self.nodes[0].pos)
        return len(list(filter(pos_filter, self.nodes[1:]))) > 0

    def set_direction_if_not_reverse(self, new_dir):
        if not np.all(new_dir == -self.head_direction):
            self.head_direction = new_dir

    def key_response(self, key):
        if key == pygame.K_LEFT:
            self.set_direction_if_not_reverse(DIR_LEFT)
        elif key == pygame.K_RIGHT:
            self.set_direction_if_not_reverse(DIR_RIGHT)
        elif key == pygame.K_UP:
            self.set_direction_if_not_reverse(DIR_UP)
        elif key == pygame.K_DOWN:
            self.set_direction_if_not_reverse(DIR_DOWN)

    def draw(self, win, size):
        for node in self.nodes:
            node.draw(win, size)


class Node(object):
    def __init__(self, pos, color=3 * [100]):
        self.pos = pos
        self.color = color

    @property
    def pos(self):
        return np.copy(self._pos)

    @pos.setter
    def pos(self, p):
        self._pos = np.copy(np.asarray(p))

    def draw(self, win, size):
        window_pos = (size * self.pos[0], size * self.pos[1])
        rect = pygame.Rect(window_pos[0], window_pos[1], size, size)
        pygame.draw.rect(win, self.color, rect)


class GameHandler(object):
    def __init__(self, width, n_rows, line_width=1, snake_kwargs={},
                 background_color=3 * [0], line_color=3 * [255],
                 snack_color=[255, 0, 0], border_color=3 * [150]):
        self.width = width
        self.height = width
        self.n_rows = n_rows

        self.line_width = line_width
        self.node_size = width / n_rows

        self.background_color = background_color
        self.line_color = line_color
        self.snack_color = snack_color
        self.border_color = border_color

        self.win = pygame.display.set_mode((self.width, self.height))
        self.clock = pygame.time.Clock()

        self.snake = Snake(2 * [self.n_rows / 2], **snake_kwargs)
        self.snack = self.add_random_snack()

        pygame.font.init()
        self.pygame_font = pygame.font.Font(None, 30)

    def reset(self, snake_kwargs):
        self.snake = Snake(2 * [self.n_rows / 2], **snake_kwargs)
        self.snack = self.add_random_snack()

    def draw_border(self):
        top_rect = pygame.Rect(0, 0, self.width, self.node_size)
        left_rect = pygame.Rect(0, 0, self.node_size, self.height)
        bottom_rect = pygame.Rect(0, self.height - self.node_size, self.width, self.node_size)
        right_rect = pygame.Rect(self.width - self.node_size, 0, self.node_size, self.height)
        for rect in [top_rect, left_rect, bottom_rect, right_rect]:
            pygame.draw.rect(self.win, self.border_color, rect)

    def draw_score(self):
        score_txt = self.pygame_font.render(f'Current score: {len(self.snake)}', True, 3*[0])
        self.win.blit(score_txt,(0,0))

    def redraw_window(self):
        self.win.fill(self.background_color)
        self.draw_grid()
        self.draw_border()
        self.snake.draw(self.win, self.node_size)
        self.snack.draw(self.win, self.node_size)
        self.draw_score()
        pygame.display.update()

    def draw_grid(self):
        line_coords = np.linspace(0, self.width, num=self.n_rows + 1, endpoint=True)
        for coord in line_coords:
            pygame.draw.line(self.win, self.line_color, (coord, 0), (coord, self.width))
            pygame.draw.line(self.win, self.line_color, (0, coord), (self.width, coord))

    def add_random_snack(self, max_n_tries=int(1e6)):
        snake_nodes = self.snake.get_nodes()
        n_tries = 0
        while n_tries < max_n_tries:
            rand_pos = np.random.randint(1, self.n_rows - 1, 2)
            pos_filter = lambda node: np.all(node.pos == rand_pos)
            if len(list(filter(pos_filter, snake_nodes))) == 0:
                return Node(rand_pos, color=self.snack_color)
        raise RuntimeError('could not find snack position')

    def update_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
            if event.type == pygame.KEYDOWN:
                self.snake.key_response(event.key)

    def is_head_outside(self):
        x, y = self.snake.get_head().pos
        return not (1 <= x < self.n_rows - 1 and 1 <= y < self.n_rows - 1)

    def main_loop(self):
        while True:
            pygame.time.delay(50)
            self.clock.tick(10)
            self.update_events()
            self.snake.move_one_step()

            if np.all(self.snake.get_head().pos == self.snack.pos):
                self.snake.grow()
                self.snack = self.add_random_snack()

            self.redraw_window()

            if self.is_head_outside() or self.snake.check_overlap():
                print('You lost. Score: ', len(self.snake))
                break

            if len(self.snake) >= (self.n_rows-2)**2:
                print('You won. Congratulations')
                break

        return True


if __name__ == "__main__":
    game = GameHandler(500, 20)
    game.main_loop()
    pygame.quit()
