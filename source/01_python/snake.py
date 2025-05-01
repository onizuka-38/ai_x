import curses
import random

def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(1)
    stdscr.timeout(100)

    sh, sw = stdscr.getmaxyx()
    box = [[3,3], [sh-3, sw-3]]

    for y in range(box[0][0], box[1][0]):
        stdscr.addstr(y, box[0][1], '|')
        stdscr.addstr(y, box[1][1], '|')
    for x in range(box[0][1], box[1][1]):
        stdscr.addstr(box[0][0], x, '-')
        stdscr.addstr(box[1][0], x, '-')

    snake = [[sh//2, sw//2 + i] for i in range(5)]
    direction = curses.KEY_LEFT

    for y, x in snake:
        stdscr.addstr(y, x, '#')

    food = [random.randint(box[0][0]+1, box[1][0]-1),
            random.randint(box[0][1]+1, box[1][1]-1)]
    stdscr.addstr(food[0], food[1], '*')

    score = 0
    while True:
        key = stdscr.getch()
        if key in [curses.KEY_UP, curses.KEY_DOWN, curses.KEY_LEFT, curses.KEY_RIGHT]:
            direction = key

        head = snake[0][:]
        if direction == curses.KEY_UP:
            head[0] -= 1
        elif direction == curses.KEY_DOWN:
            head[0] += 1
        elif direction == curses.KEY_LEFT:
            head[1] -= 1
        elif direction == curses.KEY_RIGHT:
            head[1] += 1

        snake.insert(0, head)
        if head == food:
            score += 1
            food = [random.randint(box[0][0]+1, box[1][0]-1),
                    random.randint(box[0][1]+1, box[1][1]-1)]
            stdscr.addstr(food[0], food[1], '*')
        else:
            tail = snake.pop()
            stdscr.addstr(tail[0], tail[1], ' ')

        if (
            head in snake[1:] or
            head[0] in [box[0][0], box[1][0]] or
            head[1] in [box[0][1], box[1][1]]
        ):
            msg = f"💀 GAME OVER! Score: {score} 💀"
            stdscr.addstr(sh//2, sw//2 - len(msg)//2, msg)
            stdscr.nodelay(0)
            stdscr.getch()
            break

        stdscr.addstr(head[0], head[1], '#')

if __name__ == "__main__":
    curses.wrapper(main)
