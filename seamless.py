#importing utility functions from src/calc.py
from calc import *
import random

# list of tile IDs

TILE_NONE = 0
FLOOR = 1
WALL = 2
GLASS = 3

TRANSPARENT = [FLOOR,GLASS]

charTileset = "X #~XXXXXXXXXXXXXXXXXXXXXXXXXXX"

# the tile class
class Tile:
    def __init__(self,ID = TILE_NONE,decal = None):
        self.ID = ID
        self.sprite = charTileset[ID]
        if decal != None:
            self.sprite = decal
    def solid(self):
        return self.ID != FLOOR
    def opaque(self):
        return not self.ID in TRANSPARENT

class Portal:
    def __init__(self,angle,p0,p1,oneway=None):
        self.angle = angle 
        #0 horizontal, 1 vertical
        # horizontal:  p0 goes right, p1 goes left
        # vertical:    p0 goes up, p1 goes down
        self.pos1 = p0
        self.pos2 = p1
        self.pos = [p0,p1]
        if oneway in [None,-1]:
            self.waymask = [0,1]
        elif oneway == 0:
            self.waymask = [0]
        elif oneway == 1:
            self.waymask = [1]

    def direction(self,portalindex):
        return portalindex*2 + self.angle

    def __str__(self):
        return "%s %s-%s (%s)"%("HV"[self.angle],self.pos[0],self.pos[1],self.waymask)

# the level structure class containing raw (unmoved) level data
# array is in the form array[x][y] and contains Tiles
class Level:
    def __init__(self,array):
        self.data = array
    def size(self):
        return (len(self.data),len(self.data[0]))
    

# the actual level as it is played. This one returns "rendered" data
class Board:
    def __init__(self,lvl,portallist = []):
            self.tiles = lvl.data
            (self.sizex,self.sizey) = lvl.size()
            self.portals = portallist


    # this function returns the tile at position (x,y) in REAL space
    def _getxy(self,x,y):
        if x in range(self.sizex) and y in range(self.sizey):
            return self.tiles[x][y]
        else:
            return Tile() #outside level data, return default Tile

    
    # this function moves a "cursor" (player, raycaster, whatever) one step in a direction, considering portals.
    # coords are coordinates in real space.
    def stepDir(self,coords,direction):

        portaledcoords = coords #coordinates are unchanged before stepping if there is no portal
        for p in self.portals:
            #if we're standing on a portal
            if coords in p.pos:
                enterIndex = p.pos.index(coords)
                exitIndex = not enterIndex
               
                #compute the subset of directions that the portal will capture
                d = p.direction(enterIndex)
                enteringDirs = [ d, d+4, (d-1)%4 ]                
 
                #if we step in the direction of teleporting...
                if (direction in enteringDirs and 
                #...and the portal allows movement from this side
                    enterIndex in p.waymask
                    ):
                    #teleport to the other portal
                    portaledcoords = p.pos[exitIndex]

                break

        #only THEN step forward.

        return add(portaledcoords, STEP[direction])


# the player class handles obviously player stuff but also raycasting
# when you init this class, you have to bind it to the board object.
class Player:
    def __init__(self,sx,sy,board=None):
        self.pos = (sx,sy)
        self._b = board

        # raycasting setup
        self.resetRaycast()

    def resetRaycast(self):
        # the current view is stored as a dictionary. The visible positions (tiles in viewspace - relative to the player) are the keys, the real tile displayed at that view position is the value.
        self.view = {}

    def doRay(self,rayindex):
        i = 0
        pointerReal = self.pos
        pointerRelative = (0,0)

        raysteps = RAYS_STEP[rayindex]
        raytuples = RAYS_LINES[rayindex]

        while i<len(raysteps):
           
            #move relative and absolute pointers one step forward
            pointerReal = self._b.stepDir(pointerReal,raysteps[i])
            pointerRelative = raytuples[i+1]

            #add to view dictionary
            if not pointerRelative in self.view:
                self.view[pointerRelative] = pointerReal
            
            #if solid, stop raycasting
            if self._b._getxy(pointerReal[0],pointerReal[1]).opaque():
                break

            #increment counter
            i+=1

    def doRaycast(self):
        #current position is certainly visible.
        self.view[(0,0)] = self.pos
        
        #start rays all over the place.
        for j in range(NUMBER_OF_RAYS):
            self.doRay(j)


    def tileAtPos(self,co):
        rco = self.view[co]
        return self._b._getxy(rco[0],rco[1])


    def _asciiDraw(self):
        s=''
        for j in range(0,20):
            for i in range(0,20):
                rx = i-10
                ry = j-10
                if (rx,ry)==(0,0):
                    s+='@'
                    continue

                if (rx,ry) in self.view:
                    s += "X.#~"[self.tileAtPos((rx,ry)).ID]
                else:
                    s += " "
            s+='\n'

        print(s)

    def move(self,direction):
        npos = self._b.stepDir(self.pos,direction)
        if not self._b._getxy(npos[0],npos[1]).solid():
            self.pos = npos


stdscr = None
WY = None
WX = None
s0 = None

def gfxInit():
    global stdscr
    stdscr = curses.initscr()
    curses.noecho()
    curses.cbreak()
    stdscr.keypad(1)
    curses.curs_set(0)

    updateClear()



def updateClear():
    global WX,WY,s0
    (WY,WX) = stdscr.getmaxyx()
    s0 = (WX//2,WY//2)
    #stdscr.clear()
    for j in range(WY):
        stdscr.addstr(j,0,'.'*(WX-1))

def flushScreen():
    stdscr.refresh()

def drawTile(rp,TID):
    pc = add(s0,rp)
    if pc[0] in range(WX) and pc[1] in range(WY):
        #we mirror the y coordinate for a more... MODERN coordinate system
        stdscr.addch(WY-pc[1]-1,pc[0],TID)

#level = Level( [[Tile(random.choice([WALL,FLOOR,FLOOR,GLASS,FLOOR])) for _ in range(40)] for _ in range(40)])




#LOAD LEVEL DATA

print("LOADING LEVEL...")

mapdataf = open('map/mapdata','r')
mapdata = mapdataf.readlines()
sz = max(map(len,mapdata))

aray = [[Tile(WALL) for _ in range(len(mapdata))] for _ in range(sz)]

mapper = {'#':WALL,' ':FLOOR,'@':FLOOR,'~':GLASS}
for i in "0123456789":
    mapper[i] = FLOOR

for j in range(len(mapdata)):
    l = mapdata[j].strip('\n')
    for i in range(0,len(l)):
        if l[i] == '@':
            player = Player(i,j)
        if l[i] in mapper:
            aray[i][j] = Tile(mapper[l[i]])
            if l[i] in "0123456789":
                aray[i][j] = Tile(FLOOR,decal = l[i])
        else:
            print("Unrecognized character in level map: %s"%l[i])
    
level = Level(aray)
board = Board(level)
player._b = board
#                           ^      v                  ->    <-
#board.portals = [Portal(1,(2,12),(9,1),1), Portal(0,(13,7),(0,7))]

porfile = open('map/portals','r')
pordata = map (lambda x: map(int,x.strip('\n').split(' '))  , porfile.readlines())
board.portals = [ Portal(x[0],(x[1],x[2]),(x[3],x[4]),x[5]) for x in pordata]

def Game(gnoredscreen):
    global board,player,stdscr
    
    #MAIN LOOP
    while True:
        #draw
        updateClear()
        player.resetRaycast()
        player.doRaycast()
        for t in player.view:
            drawTile(t,player.tileAtPos(t).sprite)
            '''for p in board.portals:
                if player.view[t] in p.pos:
                    drawTile(t,'P')'''
        drawTile((0,0),'@')
        flushScreen()

        #input
        cmd = stdscr.getch()

        #interpret input
        
        if cmd in [ord('d'),ord('l'),KEY_RIGHT]:
            player.move(RIGHT)
        if cmd in [ord('w'),ord('j'),KEY_UP]:
            player.move(UP)
        if cmd in [ord('a'),ord('h'),KEY_LEFT]:
            player.move(LEFT)
        if cmd in [ord('s'),ord('k'),KEY_DOWN]:
            player.move(DOWN)


print(board.portals[0])

import curses
from curses import KEY_LEFT,KEY_DOWN,KEY_RIGHT,KEY_UP
gfxInit()
curses.wrapper(Game)
