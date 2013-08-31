import math

#CONSTANTS
NUMBER_OF_RAYS = 300
VIEW_DISTANCE = 20


#ORIENTATIONS
#orthogonal
RIGHT = 0
UP = 1
LEFT = 2
DOWN = 3
#diagonal
DRU = 4
DUL = 5
DLD = 6
DDR = 7

#STEPS - go from a direction number to a direction tuple
STEP = [
(1,0),
(0,1),
(-1,0),
(0,-1),

(1,1),
(-1,1),
(-1,-1),
(1,-1)
]

# this dictionary helps changing a direction tuple in a direction number

DIRLOOKUP = {
    ( 1, 0):0,
    ( 0, 1):1,
    (-1, 0):2,
    ( 0,-1):3,

    ( 1, 1):4,
    (-1, 1):5,
    (-1,-1):6,
    ( 1,-1):7

}


def bresenham(x1, y1, x2, y2):
    points = []
    issteep = abs(y2-y1) > abs(x2-x1)
    if issteep:
        x1, y1 = y1, x1
        x2, y2 = y2, x2
    rev = False
    if x1 > x2:
        x1, x2 = x2, x1
        y1, y2 = y2, y1
        rev = True
    deltax = x2 - x1
    deltay = abs(y2-y1)
    error = int(deltax / 2)
    y = y1
    ystep = None
    if y1 < y2:
        ystep = 1
    else:
        ystep = -1
    for x in range(x1, x2 + 1):
        if issteep:
            points.append((y, x))
        else:
            points.append((x, y))
        error -= deltay
        if error < 0:
            y += ystep
            error += deltax
    # Reverse the list if the coordinates were reversed
    if rev:
        points.reverse()
    return points

# Generate a flower of rays, as a list of lists of tuples (all starting with (0,0))

step =  math.pi * 2  / float ( NUMBER_OF_RAYS)

RAYS_LINES = [bresenham(0,0,int(VIEW_DISTANCE * math.cos(i*step)), int(-VIEW_DISTANCE * math.sin(i*step))) for i in range(NUMBER_OF_RAYS)]

# Generate correcting lines

for i in range(4):
    od = STEP[i]
    for j in [0,-1]:
        dd = STEP[ (i+j)%4 + 4]
        for s in range(1,VIEW_DISTANCE):
            out = [ (od[0]*k,od[1]*k) for k in range(s+1) ] + [(od[0]*s + dd[0] ,od[1]*s + dd[1])]
            RAYS_LINES.append(out)

# Generate the step representation of the rays (that is, as a list of directions)


RAYS_STEP = []

for l in RAYS_LINES:
    sl = []
    for i in range(1,len(l)):
        sl.append(DIRLOOKUP[ (l[i][0]-l[i-1][0], l[i][1]-l[i-1][1]  )   ] )
    RAYS_STEP.append(sl)



def add(t1,t2):
    # add 2-tuples

    return (t1[0]+t2[0],t1[1]+t2[1])

