import math
import ratcave as rc
from geometry import *
from engine import *
from operator import itemgetter

import pyglet
from pyglet.window import key

window = pyglet.window.Window(width=640, height=360)
keys = key.KeyStateHandler()
window.push_handlers(keys)

playerpos = None

map = None

sec = None
cells = None
entities = None

dead = True

label = pyglet.text.Label('Press [SPACE]',
                          font_name='Helvetica',
                          font_size=36,
                          multiline=True,
                          width=window.width,
                          align="center",
                          x=window.width // 2, y=window.height // 2,
                          anchor_x='center', anchor_y='center')


def getIntersectingCell(cells, pp):
    for c in range(len(cells)):
        if cells[c] is not None and cells[c].playerInCell(pp):
            return c
    return -1


# print("INTER:"+str())


# print(clipX(5,5,0,0,5))

def toScreenSpace(x, y):
    return x + window.width // 2, y + window.height // 2


def project(z, x):
    return (
        -300 * x / z,
        5000 / z
    )


def extrapolate(x1, y1, x2, y2, x):
    m = (y2 - y1) / (x2 - x1)
    return y1 + m * (x - x1)


@window.event
def on_draw():
    window.clear()

    # print(cell.playerInCell(playerpos))

    # draw sky
    if not dead:
        if map is None:
            spawn()

        pyglet.graphics.draw(4, pyglet.gl.GL_QUADS,
                             ('v2f',
                              (0, window.height // 2, window.width, window.height // 2, window.width, window.height, 0,
                               window.height)
                              ),
                             ('c3B', (50, 50, 55) * 4))

        # draw ground
        pyglet.graphics.draw(4, pyglet.gl.GL_QUADS,
                             ('v2f',
                              (0, 0, window.width, 0, window.width, window.height // 2, 0,
                               window.height // 2)
                              ),
                             ('c3B', (80, 80, 85) * 4))

        # print("current",getIntersectingCell(cells, playerpos))
        cells[getIntersectingCell(cells, playerpos)].render(playerpos, window, cells, entities, visited=[])

        # cell.render(playerpos, window, [cell])

        pyglet.graphics.draw(4, pyglet.gl.GL_LINES,
                             ('v2f',
                              toScreenSpace(-10, 0) + toScreenSpace(10, 0) + toScreenSpace(0, -10) + toScreenSpace(0,
                                                                                                                   10)
                              ))
    else:
        label.draw()


def update(dt):
    global playerpos, dead
    if keys[key.SPACE] and dead:
        spawn()

    if not dead:

        pnpp = playerpos.add(playerpos.getForwardVector().scale((int(keys[key.W]) - int(keys[key.S])) * 2)).add(
            playerpos.getForwardVector().rotate(math.pi / 2).scale((int(keys[key.A]) - int(keys[key.D])) * 2))

        # print(cnpp.x, cnpp.y)
        inter = getIntersectingCell(cells, pnpp)

        # print(inter)
        if inter >= 0:
            playerpos = pnpp

        # tick entities
        for ent in entities:
            if ent.tag == "enemy":
                ent.moveTowardsPlayer(getIntersectingCell(cells, playerpos), cells, playerpos)
                if ent.distanceToPlayer(playerpos) < 2:
                    dead = True
            if ent.tag == "goal":
                if ent.distanceToPlayer(playerpos) < 10:
                    dead = True
                    label.text = "You Win!\nPress [SPACE]"


@window.event
def on_mouse_motion(x, y, dx, dy):
    global playerpos, dead
    # print(dx)
    if not dead:
        playerpos = playerpos.rotate(-dx * 0.005)


def spawn():
    global map, sec, cells, entities, playerpos, dead
    label.text = 'You Died!\nPress [SPACE]'
    playerpos = Transform2(275, 275, 0)
    map = Map()
    map.generate()
    sec = map.toSectors()
    cells = sec[0]
    entities = sec[1]

    dead = False


pyglet.clock.schedule(update)

window.set_caption("escape the q")
window.set_exclusive_mouse(True)
pyglet.app.run()
