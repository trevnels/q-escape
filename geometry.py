import math
import pyglet


def toScreenSpace(x, y, window):
    return x + window.width // 2, y + window.height // 2


def project(z, x):
    return [
        -300 * x / z,
        5000 / z
    ]


def extrapolate(x1, y1, x2, y2, x):
    m = (y2 - y1) / (x2 - x1)
    return y1 + m * (x - x1)


class Vector2:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def rotate(self, theta):
        return Vector2(
            self.x * math.cos(theta) - self.y * math.sin(theta),
            self.x * math.sin(theta) + self.y * math.cos(theta)
        )

    def translate(self, dx, dy):
        return Vector2(self.x + dx, self.y + dy)

    def scale(self, scl):
        return Vector2(self.x * scl, self.y * scl)

    def add(self, vec):
        return Vector2(self.x + vec.x, self.y + vec.y)

    def addAssign(self, vec):
        self.x += vec.x
        self.y += vec.y


class Transform2(Vector2):
    def __init__(self, x, y, theta):
        Vector2.__init__(self, x, y)
        self.theta = theta

    def toVector(self):
        return Vector2(self.x, self.y)

    def getForwardVector(self):
        return Vector2(math.cos(self.theta), math.sin(self.theta))

    def add(self, vec):
        return Transform2(self.x + vec.x, self.y + vec.y, self.theta)

    def rotate(self, dth):
        return Transform2(self.x, self.y, self.theta + dth)


class Wall:
    def __init__(self, v1, v2, color):
        self.v1 = v1
        self.v2 = v2
        self.color = color

    def render(self, pp, window, minx=None, maxx=None):
        trns1 = self.v1.add(pp.scale(-1)).rotate(-pp.theta)
        trns2 = self.v2.add(pp.scale(-1)).rotate(-pp.theta)

        if minx is None and maxx is None:
            minx = -window.width // 2
            maxx = window.width // 2

        if trns1.x < 0.01 and trns2.x < 0.01:
            return

        # print(trns1.x, trns1.y, trns2.x, trns2.y)
        clipped = clipX(trns1.x, trns1.y, trns2.x, trns2.y, 0.01)

        if trns1.x < 0.01:
            trns1.x = clipped[0]
            trns1.y = clipped[1]

        if trns2.x < 0.01:
            trns2.x = clipped[0]
            trns2.y = clipped[1]

        prj1 = project(trns1.x, trns1.y)
        prj2 = project(trns2.x, trns2.y)

        # backface culling
        if prj1[0] >= prj2[0]:
            return

        # cull unseen faces
        if prj1[0] < minx and prj2[0] < minx:
            return
        if prj1[0] > maxx and prj2[0] > maxx:
            return

        if prj1[0] < minx:
            # clip left
            prj1[1] = extrapolate(prj1[0], prj1[1], prj2[0], prj2[1], minx)
            prj1[0] = minx

        if prj2[0] > maxx:
            # clip right
            prj2[1] = extrapolate(prj1[0], prj1[1], prj2[0], prj2[1], maxx)
            prj2[0] = maxx

        # dist1 = max(round((prj1[1]) * 2.5), 0)
        # dist2 = max(round((prj2[1]) * 2.5), 0)

        pyglet.graphics.draw(6, pyglet.gl.GL_TRIANGLE_STRIP,
                             ('v2f',
                              (toScreenSpace(prj1[0], prj1[1], window) + toScreenSpace(prj1[0], -prj1[1],
                                                                                       window) + toScreenSpace(
                                  prj2[0], -prj2[1], window) +
                               toScreenSpace(prj2[0], -prj2[1], window) + toScreenSpace(prj2[0], prj2[1],
                                                                                        window) + toScreenSpace(
                                          prj1[0], prj1[1], window)
                               )
                              ),
                             ('c3B',
                              (self.color * 6))
                             )


class Portal:
    def __init__(self, v1, v2, dest):
        self.v1 = v1
        self.v2 = v2
        self.dest = dest

    def render(self, pp, window, cells, entities, minx=None, maxx=None, visited=[]):

        if minx is None and maxx is None:
            minx = -window.width // 2
            maxx = window.width // 2

        trns1 = self.v1.add(pp.scale(-1)).rotate(-pp.theta)
        trns2 = self.v2.add(pp.scale(-1)).rotate(-pp.theta)

        if trns1.x < 0.01 and trns2.x < 0.01:
            return

        # print(trns1.x, trns1.y, trns2.x, trns2.y)
        clipped = clipX(trns1.x, trns1.y, trns2.x, trns2.y, 0.01)

        if trns1.x < 0.01:
            trns1.x = clipped[0]
            trns1.y = clipped[1]

        if trns2.x < 0.01:
            trns2.x = clipped[0]
            trns2.y = clipped[1]

        prj1 = project(trns1.x, trns1.y)
        prj2 = project(trns2.x, trns2.y)

        if prj1[0] >= prj2[0]:
            return

        # cull unseen faces
        if prj1[0] < minx and prj2[0] < minx:
            return
        if prj1[0] > maxx and prj2[0] > maxx:
            return

        if prj1[0] < minx:
            # clip left
            prj1[1] = extrapolate(prj1[0], prj1[1], prj2[0], prj2[1], minx)
            prj1[0] = minx

        if prj2[0] > maxx:
            # clip right
            prj2[1] = extrapolate(prj1[0], prj1[1], prj2[0], prj2[1], maxx)
            prj2[0] = maxx

        # print("portal to "+str(self.dest))
        # print(self.dest)
        cells[self.dest].render(pp, window, cells, entities, prj1[0], prj2[0], visited)


class Sprite:
    def __init__(self, pos, img):
        self.pos = pos
        self.img = img

        self.img.anchor_x = self.img.width // 2
        self.img.anchor_y = int(self.img.height * 0.66)

    def getObserverDistance(self, pp):
        trns = self.pos.add(pp.scale(-1)).rotate(-pp.theta)

        if trns.x < 0.01:
            return 0.0

        return trns.x

    def render(self, pp, window, minx, maxx):
        trns = self.pos.add(pp.scale(-1)).rotate(-pp.theta)

        if trns.x < 0.01:
            return

        prj = project(trns.x, trns.y)

        spr = pyglet.sprite.Sprite(self.img, toScreenSpace(prj[0], prj[1], window)[0], window.height // 2)
        spr.scale = 1.5 * prj[1] / self.img.height

        if prj[0] < minx or prj[0] > maxx:
            return

        spr.draw()


class Sector:
    def __init__(self, id, walls, portals):
        self.id = id
        self.walls = walls
        self.portals = portals

    def render(self, pp, window, cells, entities, minx=None, maxx=None, visited=[]):
        if minx is None and maxx is None:
            minx = -window.width // 2
            maxx = window.width // 2

        if self.id in visited:
            return

        visited.append(self.id)

        for wall in self.walls:
            wall.render(pp, window, minx, maxx)
        for portal in self.portals:
            # pass
            portal.render(pp, window, cells, entities, minx, maxx, visited)

        for entity in sorted(entities, key=lambda s: s.sprite.getObserverDistance(pp), reverse=True):
            if entity.currentCell(cells) == self.id:
                entity.sprite.render(pp, window, minx, maxx)

    def playerInCell(self, pp):
        prev = None
        point = (pp.x, pp.y)

        for wall in self.walls:
            sgn = crs(pp.x, pp.y, wall.v1.x, wall.v1.y, wall.v2.x, wall.v2.y)
            # print(sgn)
            if sgn < 0:
                if prev is None:
                    prev = "L"
                if prev != "L":
                    # prev = "L"
                    return False
            elif sgn > 0:
                if prev is None:
                    prev = "R"
                if prev != "R":
                    # prev = "R"
                    return False

        for portal in self.portals:
            # affs = portal.v2.add(portal.v1.scale(-1))
            # affp = (pp.x - portal.v1.x, pp.y, portal.v1.y)

            sgn = crs(pp.x, pp.y, portal.v1.x, portal.v1.y, portal.v2.x, portal.v2.y)
            if sgn < 0:
                if prev is None:
                    prev = "L"
                if prev != "L":
                    return False
            elif sgn > 0:
                if prev is None:
                    prev = "R"
                if prev != "R":
                    return False
            else:
                return True
        return True


def clipX(x1, y1, x2, y2, clipx):
    if x1 < x2:
        if clipx < x1:
            return None
        if clipx > x2:
            return None

    if x1 > x2:
        if clipx > x1:
            return None
        if clipx < x2:
            return None

    if x2 == x1:
        return None

    m = (y2 - y1) / (x2 - x1)
    return clipx, y1 + m * (clipx - x1)


# compute the cross product between two vectors
def crs(x, y, x1, y1, x2, y2):
    return (x - x1) * (y2 - y1) - (y - y1) * (x2 - x1)
