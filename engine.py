import random
from geometry import *
import pyglet


class Entity:
    def __init__(self, pos, img, tag=""):
        self.pos = pos
        self.tag = tag
        self.speed = random.random() * 0.4 + 1.01
        # print(pos.x)
        self.sprite = Sprite(pos, img)

    def moveTowardsPlayer(self, pc, cells, pp):
        path = self.pathTo(pc, cells)

        if path is not None and len(path) < 10:
            tgpt = 1 if len(path) > 1 else 0

            x = 0.75 if (path[tgpt] % 3 != 2) else 0.25
            y = 0.75 if (path[tgpt] % 3 != 1) else 0.25

            p = indexToCoords(path[tgpt])
            # print("current"+str(indexToCoords(self.currentCell(cells)))+","+str(self.currentCell(cells)))
            # print("target"+str(p)+","+str(path[1]))

            wc = cellCoordinatesToWorld(x, y, p[0], p[1], 100)

            if len(path) == 1:
                wc = pp
            # print(self.pos.x,self.pos.y)
            # print(wc.x,wc.y)

            dx = 0
            dy = 0
            if wc.x < self.pos.x - 2:
                dx -= self.speed
            if wc.x > self.pos.x + 2:
                dx += self.speed
            if wc.y < self.pos.y - 2:
                dy -= self.speed
            if wc.y > self.pos.y + 2:
                dy += self.speed

            self.pos = self.pos.add(Vector2(dx, dy))
            self.sprite.pos = self.pos

    def distanceToPlayer(self, pp):
        return math.sqrt(pow(pp.x - self.pos.x, 2) + pow(pp.y - self.pos.y, 2))

    def pathTo(self, tgt, cells):
        return self.pathToRecurse(self.currentCell(cells), [], tgt, cells)

    def pathToRecurse(self, cell, visited, target, cells):
        # print(visited)
        if cell in visited:
            return None

        if cell == target:
            return visited + [cell]

        for portal in cells[cell].portals:
            # print(str(cell) + "portal" + str(portal.dest))
            # print(target)
            # print(portal.dest)
            v = self.pathToRecurse(portal.dest, visited + [cell], target, cells)
            if v is not None:
                return v

    def currentCell(self, cells):
        for c in range(len(cells)):
            if cells[c] is not None and cells[c].playerInCell(self.pos):
                return c
        return -1


class Map:
    def __init__(self):
        self.tiles = []
        self.walls = []

    def generate(self):
        for r in range(5):
            self.tiles.append([])
            for c in range(5):
                self.tiles[r].append(None)

        self.tiles[1][1] = PrimCell(1, 1, self.walls, self.tiles)

        while len(self.walls) > 0:
            # print(len(self.walls))
            wall = random.choice(self.walls)
            if wall.dir == "u" and self.tiles[wall.r - 1][wall.c] is None:
                self.tiles[wall.r - 1][wall.c] = PrimCell(wall.r - 1, wall.c, self.walls, self.tiles)
                wall.remove(True)
            elif wall.dir == "d" and self.tiles[wall.r + 1][wall.c] is None:
                self.tiles[wall.r + 1][wall.c] = PrimCell(wall.r + 1, wall.c, self.walls, self.tiles)
                wall.remove(True)
            elif wall.dir == "l" and self.tiles[wall.r][wall.c - 1] is None:
                self.tiles[wall.r][wall.c - 1] = PrimCell(wall.r, wall.c - 1, self.walls, self.tiles)
                wall.remove(True)
            elif wall.dir == "r" and self.tiles[wall.r][wall.c + 1] is None:
                self.tiles[wall.r][wall.c + 1] = PrimCell(wall.r, wall.c + 1, self.walls, self.tiles)
                wall.remove(True)
            else:
                self.walls.remove(wall)

    def toSectors(self):
        sectors = []
        entities = []
        endpoints = []
        for r in self.tiles:
            for c in r:
                calc = c.toAreaPortals()
                sectors.extend(calc[0])
                # print(calc[1])
                if calc[1] and (c.r <= 1 or c.r >= 3 or c.c <= 1 or c.c >= 3):
                    endpoints.append((c.r, c.c))

        goal = random.choice(endpoints)

        for pt in endpoints:
            if pt == goal:
                entities.append(
                    Entity(cellCoordinatesToWorld(0.75, 0.75, pt[0], pt[1], 100), pyglet.image.load("img/L copy.png"),
                           "goal"))
            elif random.random() < 0.9:
                entities.append(Entity(cellCoordinatesToWorld(0.75, 0.75, pt[0], pt[1], 100),
                                       pyglet.image.load("img/enemy copy.png"), "enemy"))

        return sectors, entities


class PrimWall:
    def __init__(self, r, c, dir, walls, tiles):
        self.r = r
        self.c = c
        self.dir = dir
        self.tiles = tiles
        self.walls = walls

        if self.dir == "u" and self.r == 0:
            return
        if self.dir == "d" and self.r == len(tiles) - 1:
            return
        if self.dir == "l" and self.c == 0:
            return
        if self.dir == "r" and self.c == len(tiles[0]) - 1:
            return

        self.walls.append(self)

    def remove(self, checkNeighbors=False):
        if checkNeighbors:
            if self.dir == "u":
                if 0 <= self.r - 1 < len(self.tiles):
                    self.tiles[self.r - 1][self.c].down.remove()
            if self.dir == "d":
                if 0 <= self.r + 1 < len(self.tiles):
                    self.tiles[self.r + 1][self.c].up.remove()
            if self.dir == "l":
                if 0 <= self.c - 1 < len(self.tiles[0]):
                    self.tiles[self.r][self.c - 1].right.remove()
            if self.dir == "r":
                if 0 <= self.c + 1 < len(self.tiles[0]):
                    self.tiles[self.r][self.c + 1].left.remove()

        self.walls.remove(self)

        if self.dir == "u":
            self.tiles[self.r][self.c].up = None
        if self.dir == "d":
            self.tiles[self.r][self.c].down = None
        if self.dir == "l":
            self.tiles[self.r][self.c].left = None
        if self.dir == "r":
            self.tiles[self.r][self.c].right = None
        del self


def toIndex(r, c):
    return r * 5 + c


def indexToCoords(ind):
    newi = ind // 3
    r = newi // 5
    c = newi % 5
    return (r, c)


def cellCoordinatesToWorld(x, y, r, c, scl):
    return Vector2(c * scl + x * scl, r * scl + y * scl)


class PrimCell:
    def __init__(self, r, c, walls, tiles):
        self.r = r
        self.c = c
        self.tiles = tiles

        self.up = PrimWall(r, c, "u", walls, tiles)
        self.down = PrimWall(r, c, "d", walls, tiles)
        self.left = PrimWall(r, c, "l", walls, tiles)
        self.right = PrimWall(r, c, "r", walls, tiles)

    def numWalls(self):
        n = 0
        if self.up is not None:
            n += 1
        if self.down is not None:
            n += 1
        if self.left is not None:
            n += 1
        if self.right is not None:
            n += 1
        return n

    def toAreaPortals(self):
        ind = toIndex(self.r, self.c) * 3
        scale = 50

        corewalls = []
        coreportals = []

        topwalls = []
        topportals = []

        leftwalls = []
        leftportals = []

        #
        #    _
        #  _|1|
        # |2_0|
        #

        color1 = (60, 60, 65)
        color2 = (70, 70, 75)

        if self.up is None:
            coreportals.append(
                Portal(cellCoordinatesToWorld(1.0, 0.5, self.r, self.c, 100),
                       cellCoordinatesToWorld(0.5, 0.5, self.r, self.c, 100),
                       ind + 1)
            )

            topwalls.extend([
                Wall(cellCoordinatesToWorld(0.5, 0.0, self.r, self.c, 100),
                     cellCoordinatesToWorld(0.5, 0.5, self.r, self.c, 100), color1),
                Wall(cellCoordinatesToWorld(1.0, 0.5, self.r, self.c, 100),
                     cellCoordinatesToWorld(1.0, 0.0, self.r, self.c, 100), color1),
            ])

            topportals.extend([
                Portal(cellCoordinatesToWorld(0.5, 0.5, self.r, self.c, 100),
                       cellCoordinatesToWorld(1.0, 0.5, self.r, self.c, 100), ind),
                Portal(cellCoordinatesToWorld(1.0, 0.0, self.r, self.c, 100),
                       cellCoordinatesToWorld(0.5, 0.0, self.r, self.c, 100), toIndex(self.r - 1, self.c) * 3)
            ])
        else:
            corewalls.append(
                Wall(cellCoordinatesToWorld(1.0, 0.5, self.r, self.c, 100),
                     cellCoordinatesToWorld(0.5, 0.5, self.r, self.c, 100), color2)
            )

        if self.left is None:
            coreportals.append(
                Portal(cellCoordinatesToWorld(0.5, 0.5, self.r, self.c, 100),
                       cellCoordinatesToWorld(0.5, 1.0, self.r, self.c, 100),
                       ind + 2)
            )

            leftportals.extend([
                Portal(cellCoordinatesToWorld(0.5, 1.0, self.r, self.c, 100),
                       cellCoordinatesToWorld(0.5, 0.5, self.r, self.c, 100),
                       ind),
                Portal(cellCoordinatesToWorld(0.0, 0.5, self.r, self.c, 100),
                       cellCoordinatesToWorld(0.0, 1.0, self.r, self.c, 100),
                       toIndex(self.r, self.c - 1) * 3)
            ])

            leftwalls.extend([
                Wall(cellCoordinatesToWorld(0.5, 0.5, self.r, self.c, 100),
                     cellCoordinatesToWorld(0.0, 0.5, self.r, self.c, 100),
                     color2),
                Wall(cellCoordinatesToWorld(0.0, 1.0, self.r, self.c, 100),
                     cellCoordinatesToWorld(0.5, 1.0, self.r, self.c, 100),
                     color2)
            ])
        else:
            corewalls.append(
                Wall(cellCoordinatesToWorld(0.5, 0.5, self.r, self.c, 100),
                     cellCoordinatesToWorld(0.5, 1.0, self.r, self.c, 100),
                     color1)
            )

        if self.right is None:
            coreportals.append(
                Portal(cellCoordinatesToWorld(1.0, 1.0, self.r, self.c, 100),
                       cellCoordinatesToWorld(1.0, 0.5, self.r, self.c, 100),
                       toIndex(self.r, self.c + 1) * 3 + 2)
            )
        else:
            corewalls.append(
                Wall(cellCoordinatesToWorld(1.0, 1.0, self.r, self.c, 100),
                     cellCoordinatesToWorld(1.0, 0.5, self.r, self.c, 100),
                     color1)
            )

        if self.down is None:
            coreportals.append(
                Portal(cellCoordinatesToWorld(0.5, 1.0, self.r, self.c, 100),
                       cellCoordinatesToWorld(1.0, 1.0, self.r, self.c, 100),
                       toIndex(self.r + 1, self.c) * 3 + 1)
            )
        else:
            corewalls.append(
                Wall(cellCoordinatesToWorld(0.5, 1.0, self.r, self.c, 100),
                     cellCoordinatesToWorld(1.0, 1.0, self.r, self.c, 100),
                     color2)
            )

        endpoint = self.numWalls() == 3

        sectors = []
        core = Sector(ind, corewalls, coreportals)
        sectors.append(core)

        if len(topwalls) > 0:
            top = Sector(ind + 1, topwalls, topportals)
            sectors.append(top)
        else:
            sectors.append(None)

        if len(leftwalls) > 0:
            left = Sector(ind + 2, leftwalls, leftportals)
            sectors.append(left)
        else:
            sectors.append(None)

        return sectors, endpoint
