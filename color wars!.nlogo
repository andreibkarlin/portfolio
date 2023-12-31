globals [leader temp losers selected]
patches-own [save store]
turtles-own [special]

to go
  tick
  ;Find largest color if leader debuff is not 0.
  if (leader-debuff != 0) [set leader [pcolor] of patches
    set leader remove yellow remove white remove black leader
    set leader modes leader]
  ;Find countries about to die if loser-rebound is above 0.
  if (loser-rebound > 0) [
    set losers (list)
    foreach remove-duplicates [pcolor] of turtles [x -> if (length filter [f -> f = x] [pcolor] of patches < 5) [set losers lput x losers]]]
  ask patches [
    ;Black and white tiles don't do anything.
    if (pcolor != white and pcolor != black) [
      ;If there are enemy turtles here, become contested
      if (any? turtles-here with [not (color = pcolor)]) [set store pcolor set pcolor yellow]
      ;Randomly spawn turtles, taking into account border bonus and not spawning if there are already turtles there.
      if (pcolor != yellow and random spawn-rate < (1 + border-bonus * count neighbors with [pcolor != [pcolor] of myself]) and count turtles-here = 0)
        ;Sprout the turtle with basic setup and code to make a power work.
        [sprout 1 [set color pcolor set shape "eyeball" set hidden? not show-troops
        if (power = "magnet" and selected = color and random powerN = 0) [setxy mouse-xcor mouse-ycor] if (power = "disable" and selected = color) [die]
        if (power = "spawnrate" and selected = color) [hatch powerN [set heading random 360]]]]
      ;If the tile is contested and there is only one color of turtles here, become that color.
      if (pcolor = yellow and length remove-duplicates [color] of turtles-here = 1) [set pcolor [color] of one-of turtles-here set store pcolor]
    ]
  ]
  ask turtles [
    if special = true [ask other turtles-here with [color != [color] of myself] [die]]
    ifelse (pcolor = yellow)[
      ;In yellow tiles, ask differently colored turtles to die with a 1 in fight-rate chance.
      ask other turtles-here with [color != [color] of myself] [if (random fight-rate = 0) [die]]
      run cycle
      ;Leader-debuff code. Strongest color has more troops die based on that rate.
      if (leader-debuff != 0 and color = one-of leader and random (fight-rate / leader-debuff) = 0) [die]]
    ;In friendly or white tiles, go foward.
    [ifelse (pcolor = color or pcolor = white) [fd speed]
      ;In black tiles, try to get out. Die if you can't.
      [ifelse (pcolor = black) [bk speed set heading random 360 if (pcolor = black) [die]] []]]
    ;Loser-rebound code. If the color is dying, claim tiles you have troops on and spawn more troops.
    if (loser-rebound > 0 and length losers > 0 and color = one-of losers and count turtles-here with [color = [color] of myself] < 10)
      [hatch loser-rebound [set heading random 360] set pcolor color ask turtles-here with [color != [color] of myself] [die]]
    set hidden? not show-troops
  ]
  ;If borderless is on, yellow tiles become the color of the most turtles there
  ask turtles [if not borders and pcolor = yellow [set pcolor store if pcolor = yellow [set pcolor one-of modes [color] of turtles-here]]]
  powers
end

to xby [x y n]
  ifelse x = "all" [ifelse y = "all"
    [ask other turtles-here with [color != [color] of myself] [sfd n]]
    [if (color != y) [ask other turtles-here with [color = y] [sfd n]]]]
  [ifelse y = "all"
    [if (color = x) [ask other turtles-here with [color != [color] of myself] [sfd n]]]
    [if (color = x) [ask other turtles-here with [color = y] [sfd n]]]]
end
to sfd [n] if (random (strong-fight / n) = 0) [die] end
to stripes-cycle xby 5 15 1 xby 15 25 1 xby 25 35 1 xby 35 65 1 xby 65 55 1 xby 55 75 1 xby 75 85 1 xby 85 95 1 xby 95 105 1 xby 105 115 1 xby 115 125 1 xby 125 135 1 xby 135 5 1 end
to quad-cycle xby green orange 1 xby orange cyan 1 xby cyan magenta 1 xby magenta green 1 end
to full-cycle ask other turtles-here with [color > [color] of myself and color < [color] of myself + 10] [sfd 1] end

to default
  set fight-rate 50 set spawn-rate 20 set speed 0.5 set map-type "rgb" set event-type "die" set show-troops false set strong-fight 50 set border-bonus 0 set leader-debuff 0
  set loser-rebound 0 set borders false set power "clear" set radius 10 set powerN 0 set colors-plot false resize-world -64 64 -64 64 set-patch-size 4.6
  set cycle "xby red green 1 \nxby green blue 1 \nxby blue red 1"
end

to import-map
  ca
  reset-ticks
  let map-size read-from-string user-input "What will the new map size be?"
  resize-world -1 * map-size map-size -1 * map-size map-size
  set-patch-size 64 / map-size * 4.6
  let fn user-file
  if fn != false [import-pcolors fn]
end

to setup [preset]
  ask turtles [die]
  reset-ticks
  clear-all-plots
  ask patches [
    set pcolor black
    set store yellow
    (ifelse
      preset = "rgb" [set pcolor one-of [red green blue]]
      preset = "rgby" [set pcolor one-of [red green blue yellow]]
      preset = "rgba" [set pcolor one-of [red green blue gray]]
      preset = "rgbya" [set pcolor one-of [red green blue gray yellow]]
      preset = "rb" [set pcolor one-of [red blue]]
      preset = "rbb" [set pcolor one-of [red blue blue]]
      preset = "rbbb" [set pcolor one-of [red blue blue blue]]
      preset = "rgbyawl" [set pcolor one-of [red green blue yellow gray black white]]
      preset = "maze" [set pcolor one-of [orange cyan black black]]
      preset = "lakes" [set pcolor random 1400 / 10 if (random 2 = 0) [set pcolor white]]
      (preset = "quad" or preset = "quad2" or preset = "sea") [set pcolor yellow
        if (pxcor > 0 and pycor > 0) [set pcolor orange]
        if (pxcor > 0 and pycor < 0) [set pcolor cyan]
        if (pxcor < 0 and pycor < 0) [set pcolor magenta]
        if (pxcor < 0 and pycor > 0) [set pcolor green]
        if (preset = "quad2" and distancexy 0 0 < 60) [set pcolor yellow]
        if (preset = "sea" and distancexy 0 0 < 60) [set pcolor white if (random 40 = 0) [set pcolor yellow]]]
      preset = "seeds" [set pcolor yellow if (random 500 = 0) [set pcolor one-of [orange cyan magenta green]]]
      preset = "seeds2" [set pcolor yellow if (random 500 = 0) [set pcolor random 1400 / 10]]
      preset = "yellow" [set pcolor yellow]
      preset = "stripes" [set pcolor round (pxcor / 10) * 10 + 5 if pcolor = 65 [set pcolor 75] if pcolor = 45 [set pcolor 65]]
      preset = "diagonal" [set pcolor pxcor + pycor]
      preset = "multiply" [set pcolor pxcor * pycor]
      preset = "division" [ifelse pycor = 0 [set pcolor black] [set pcolor pxcor / pycor]]
      preset = "blob" [set pcolor random 1400 / 10]
      ;You can add more presets here.


      [set pcolor random 1400 / 10 if (pcolor = black or pcolor = white) [set pcolor yellow]]
    )]
  if preset = "blob" [repeat 4 [ask patches [set pcolor one-of modes [pcolor] of neighbors]]]
end

to event [preset]
  ask turtles [
    (ifelse
      preset = "die" [die]
      preset = "jump" [fd 5]
      preset = "tele" [setxy random-xcor random-ycor]
      preset = "shift" [set color (color + 10)]
      preset = "chaos" [set color yellow]
      preset = "collapse" [if (color = one-of leader) [set color random 1400 / 10] if (color = white or color = black) [set color yellow]]
      preset = "nuke" [if (color = one-of leader) [set color one-of [black white]]]
      preset = "thanos" [if random 2 = 0 [die]]
      ;You can add more turtle events here.


      []
    )
  ]
  ask patches [
    (ifelse
      preset = "random" [set pcolor random 1400 / 10]
      preset = "yellow" [set pcolor yellow]
      preset = "move" [set pcolor [pcolor] of patch (pxcor + random 5) pycor]
      preset = "grayscale" [set pcolor pcolor mod 10]
      preset = "acid" [set pcolor pcolor + random 2]
      preset = "save" [set save pcolor]
      preset = "load" [set pcolor save]
      preset = "clean" [if (pcolor = white or pcolor = black) [set pcolor yellow]]
      preset = "purge" [if random 2 = 0 and (pcolor = white or pcolor = black) [set pcolor yellow]]
      preset = "wall" [if (pcolor = yellow) [set pcolor black]]
      preset = "swap" [if (pcolor = white or pcolor = black) [ifelse (pcolor = white) [set pcolor black] [set pcolor white]]]
      preset = "blob" [set pcolor one-of modes [pcolor] of neighbors]
      preset = "scatter" [let x round random-xcor let y round random-ycor ask turtles-here [setxy x y]]
      ;You can add more patch events here. An event can have both a turtle and patch component.


      []
    )
  ]
end

to powers
  ifelse mouse-down? and mouse-inside? and power != "" [
    (ifelse
      power = "pull" [ifelse radius > 0 [ask patch mouse-xcor mouse-ycor [ask patches in-radius radius [ask turtles-here
        [facexy mouse-xcor mouse-ycor]]]] [ask turtles [facexy mouse-xcor mouse-ycor]]]
      power = "push" [ifelse radius > 0 [ask patch mouse-xcor mouse-ycor [ask patches in-radius radius [ask turtles-here
        [facexy mouse-xcor mouse-ycor rt 180]]]] [ask turtles [facexy mouse-xcor mouse-ycor rt 180]]]
      power = "cyclone" [ifelse radius > 0 [ask patch mouse-xcor mouse-ycor [ask patches in-radius radius [ask turtles-here
        [facexy mouse-xcor mouse-ycor rt 90]]]] [ask turtles [facexy mouse-xcor mouse-ycor rt 90]]]
      power = "die" [ifelse radius > 0 [ask patch mouse-xcor mouse-ycor [ask patches in-radius radius [ask turtles-here [die]]]] [ask turtles [die]]]
      power = "draw" [ifelse selected = "none" [set selected [pcolor] of patch mouse-xcor mouse-ycor] [ask patch mouse-xcor mouse-ycor [ask patches in-radius radius [set pcolor selected]]]]
      power = "spawn" [ifelse selected = "none" [set selected [pcolor] of patch mouse-xcor mouse-ycor] [ask patch mouse-xcor mouse-ycor [ask patches in-radius radius [
        let x powerN if x = 0 [set x 2] sprout x [set color selected set shape "eyeball" set hidden? not show-troops]]]]]
      power = "spawnN" [ask patch mouse-xcor mouse-ycor [ask patches in-radius radius [sprout 2 [set color powerN set shape "eyeball" set hidden? not show-troops]]]]
      power = "buff" [ask patch mouse-xcor mouse-ycor [ask patches in-radius radius [ask turtles-here [set special true]]]] ;Part of the main code makes this work.
      power = "chaos" [ask patch mouse-xcor mouse-ycor [ask patches in-radius radius [ask turtles-here
        [set color random 1400 / 10 if color = black or color = white [set color yellow]]set pcolor random 1400 / 10 if pcolor = black or pcolor = white [set pcolor yellow]]]]
      power = "shift" [ask patch mouse-xcor mouse-ycor [ask patches in-radius radius [ask turtles-here [if pcolor != yellow [ifelse pcolor = brown [set color green] [set color pcolor + 10]]]]]]
      power = "drawN" [ask patch mouse-xcor mouse-ycor [ask patches in-radius radius [set pcolor powerN]]]
      power = "clear" [ask patch mouse-xcor mouse-ycor [ask turtles-here [die] ask patches in-radius radius [set pcolor yellow set store yellow ask turtles-here [die]]]]
      power = "control" [ifelse selected = "none" [set selected [pcolor] of patch mouse-xcor mouse-ycor] [ask turtles with [color = selected] [if random PowerN = 0 [facexy mouse-xcor mouse-ycor]]]]
      power = "magnet" or power = "disable" or power = "spawnrate" [if selected = "none" [set selected [pcolor] of patch mouse-xcor mouse-ycor]] ;Part of the main code makes this work.
      power = "paint" [ifelse selected = "none" [set selected [pcolor] of patch mouse-xcor mouse-ycor]
        [ask patch mouse-xcor mouse-ycor [ask patches in-radius radius [ask turtles-here [set color selected] set pcolor selected]]]]
      power = "paintN" [ask patch mouse-xcor mouse-ycor [ask patches in-radius radius [ask turtles-here [set color powerN] set pcolor powerN]]]
      power = "replace" [let x [pcolor] of patch mouse-xcor mouse-ycor ifelse powerN = 45 [ask patches with [pcolor = x] [set pcolor yellow set store yellow] ask turtles with [color = x] [die]]
        [ask patches with [pcolor = x] [set pcolor powerN] ask turtles with [color = x] [set color powerN]]]
      power = "collapse" [let x [pcolor] of patch mouse-xcor mouse-ycor ask patches with [pcolor = x] [set pcolor random 1400 / 10 if pcolor = white or pcolor = black [set pcolor yellow]]
        ask turtles with [color = x] [set color random 1400 / 10 if color = white or color = black [set color yellow]]]
      power = "nuke" [let x [pcolor] of patch mouse-xcor mouse-ycor ask patches with [pcolor = x] [set pcolor one-of [black white]] ask turtles with [color = x] [set color one-of [black white]]]
      power = "kill" [ifelse selected = "none" [set selected [pcolor] of patch mouse-xcor mouse-ycor]
        [ifelse radius > 0 [ask patch mouse-xcor mouse-ycor [ask patches in-radius radius [ask turtles-here with [color = selected] [die]]]] [ask turtles with [color = selected] [die]]]]
      power = "ikill" [ifelse selected = "none" [set selected [pcolor] of patch mouse-xcor mouse-ycor]
        [ifelse radius > 0 [ask patch mouse-xcor mouse-ycor [ask patches in-radius radius [ask turtles-here with [color != selected] [die]]]] [ask turtles with [color != selected] [die]]]]
      ;You can add more powers here.


      []
  )] [set selected "none"]
end
@#$#@#$#@
GRAPHICS-WINDOW
233
10
834
612
-1
-1
4.6
1
10
1
1
1
0
1
1
1
-64
64
-64
64
1
1
1
ticks
30.0

BUTTON
29
84
102
117
setup
setup map-type
NIL
1
T
OBSERVER
NIL
A
NIL
NIL
1

BUTTON
36
36
99
69
go
go
T
1
T
OBSERVER
NIL
S
NIL
NIL
1

SWITCH
47
190
193
223
show-troops
show-troops
1
1
-1000

INPUTBOX
78
236
153
296
spawn-rate
20.0
1
0
Number

INPUTBOX
9
236
72
296
fight-rate
50.0
1
0
Number

INPUTBOX
25
337
111
397
strong-fight
50.0
1
0
Number

INPUTBOX
159
234
209
294
speed
0.5
1
0
Number

INPUTBOX
18
125
115
185
map-type
quad
1
0
String

BUTTON
113
37
203
70
go once
go
NIL
1
T
OBSERVER
NIL
W
NIL
NIL
1

BUTTON
132
85
204
118
event
event event-type
NIL
1
T
OBSERVER
NIL
D
NIL
NIL
1

INPUTBOX
118
340
198
400
border-bonus
0.0
1
0
Number

BUTTON
944
29
1057
62
import map
import-map
NIL
1
T
OBSERVER
NIL
NIL
NIL
NIL
1

INPUTBOX
23
409
107
469
leader-debuff
0.0
1
0
Number

INPUTBOX
118
411
205
471
loser-rebound
0.0
1
0
Number

SWITCH
47
476
181
509
borders
borders
1
1
-1000

INPUTBOX
67
549
117
609
radius
5.0
1
0
Number

INPUTBOX
6
549
64
609
power
paint
1
0
String

TEXTBOX
92
10
143
29
MAIN
16
0.0
1

TEXTBOX
69
312
168
331
ADVANCED
16
0.0
1

TEXTBOX
81
521
153
541
POWERS
16
0.0
1

PLOT
857
231
1057
381
Color Area
NIL
NIL
0.0
140.0
0.0
10.0
true
false
"" "if colors-plot [foreach (remove-duplicates [pcolor] of patches) [\nx -> create-temporary-plot-pen (word x)\nset-plot-pen-color x\nplotxy ticks (count patches with [pcolor = x])]]"
PENS

SWITCH
898
386
1017
419
colors-plot
colors-plot
0
1
-1000

INPUTBOX
122
549
172
609
powerN
85.0
1
0
Number

BUTTON
858
29
929
62
default
default
NIL
1
T
OBSERVER
NIL
NIL
NIL
NIL
1

MONITOR
176
560
226
605
color
selected
17
1
11

INPUTBOX
123
125
217
185
event-type
die
1
0
String

INPUTBOX
872
453
1032
574
cycle
xby red green 1 \nxby green blue 1 \nxby blue red 1
1
1
String (commands)

BUTTON
942
137
1042
170
NIL
run Hotkey1
NIL
1
T
OBSERVER
NIL
1
NIL
NIL
1

BUTTON
883
146
983
179
NIL
run Hotkey2
NIL
1
T
OBSERVER
NIL
2
NIL
NIL
1

BUTTON
858
184
921
217
HK 3
run Hotkey3
NIL
1
T
OBSERVER
NIL
3
NIL
NIL
1

BUTTON
924
146
1024
179
NIL
run Hotkey4
NIL
1
T
OBSERVER
NIL
4
NIL
NIL
1

BUTTON
875
149
975
182
NIL
run Hotkey5
NIL
1
T
OBSERVER
NIL
5
NIL
NIL
1

BUTTON
897
128
952
161
HK 6
run Hotkey6
NIL
1
T
OBSERVER
NIL
6
NIL
NIL
1

BUTTON
926
102
981
135
HK 7
run Hotkey7
NIL
1
T
OBSERVER
NIL
7
NIL
NIL
1

BUTTON
980
160
1035
193
HK 8
run Hotkey8
NIL
1
T
OBSERVER
NIL
8
NIL
NIL
1

BUTTON
943
127
998
160
HK 9
run Hotkey9
NIL
1
T
OBSERVER
NIL
9
NIL
NIL
1

PLOT
855
75
1055
225
Population
NIL
NIL
0.0
10.0
0.0
10.0
true
false
"" ""
PENS
"default" 1.0 0 -16777216 true "" "plot count turtles"

INPUTBOX
1061
29
1216
89
Hotkey1
set power \"spawn\" set radius 5
1
0
String (commands)

INPUTBOX
1062
92
1217
152
Hotkey2
set power \"clear\" set radius 10
1
0
String (commands)

INPUTBOX
1064
154
1219
214
Hotkey3
event \"scatter\"
1
0
String (commands)

INPUTBOX
1062
216
1217
276
Hotkey4
NIL
1
0
String (commands)

INPUTBOX
1062
277
1217
337
Hotkey5
NIL
1
0
String (commands)

INPUTBOX
1061
340
1216
400
Hotkey6
NIL
1
0
String (commands)

INPUTBOX
1061
401
1216
461
Hotkey7
NIL
1
0
String (commands)

INPUTBOX
1060
461
1215
521
Hotkey8
NIL
1
0
String (commands)

INPUTBOX
1059
523
1214
583
Hotkey9
NIL
1
0
String (commands)

@#$#@#$#@
# Basics

## How it works

There are various colors fighting. Colored tiles spawn troops of their color. These troops will go in a straight line until they enter enemy territory, making it contested (shown as yellow if borders are on). In a contested tile, troops will randomly kill eachother until only one color is left. 

## How to use

  * Setup sets up the model based on the map type, which you type in (list of maps is provided).
  * Go runs the model continuously. Go once runs the model for only a single tick.
  * Event runs an event based on the event type (list of events is provided).
It is highly recommended to increase the speed to 75%, fast enough that you see the individual ticks.

## Basic Settings

  * Spawn-rate is the rate (1 in X) that new troops spawn. More troops means more lag. When lower, the borders are less chaotic.
  * Fight-rate is the rate troops kill eachother. When lower, the borders are more chaotic.
  * Speed is the speed they move at. When lower, the borders are less chaotic.
  * Show-troops shows the troops. Not recommended because it makes the thign really laggy, but it can help you to understand what is going on.

## The Game

The point of the game is to mess around with the parameters and see what happens. The game is a sandbox. You can try to create specific effects, or try to use the tools to make a specific color win, or just watch the countries fight. 
If the game is too laggy, you can lower the map size to 48 by clicking import map and then not importing a map.

## Things to try

Default - 50 fight-rate, 20 spawn-rate, 0.5 speed
Rock Paper Scissors - rgb, rgb-cycle, default with 0 strong-fight. Similar thing with quad and quad-cycle.
Forever War - quad, default with 1 leader-debuff.
See the troops - seeds, 200 fight-rate, 500 spawn-rate, 0.5 speed, show troops and bordrs on. Population here is low enough for you to see the behavior without extreme lag.
Try bringing a losing color to victory with the pull power.
Try the maps, events, powers, parameters, etc. There are many things to try.

# Extras

You do not need to understand this to understand the model.

## Special colors

Strong-fight is a bonus 1 in X where troops kill at a bonus if they beat that color. For example, if it is the same as fight-rate, there is an extra 1 in X where the weaker troop dies, or a double chance. 
By default, red beats blue, green beats red, blue beats green, other colors (including slightly impure versions of red green or blue) are neutral to everyone.
This is easily moddable in the "cycle" variable. xby means x-beats-y.The first color beats the second color, and the number is the amount it beats it by, 1 being strong fight, 2 being two times stronger than that. You can put "all" in place of a color and everything will beat a color or a color will beat everything. Hitting the default button gets back the default for that.

Yellow tiles are unclaimed and do not spawn troops, so any turtle can easily claim empty ones, and if every turtle in a battle dies it stays yellow. Black and white tiles cannot be claimed. Black tiles are like walls, troops cannot go through them. White tiles are like sea, troops can go through them.

## Advanced Buttons

  * Border-bonus increases the spawn rate when a tile is on the border. Makes borders less chaotic without as much lag.
  * Leader-debuff makes the largest color have its troops die more, with 1 being double deaths, 2 being triple, 0.5 being 50% more, etc. The largest color is not kept track of if this is 0.
  * Loser-rebound prevents countries from being eliminated by giving them land where they have troops and spawning many more troops for them, larger spawns more troops. Not to be used with the default preset.
  * Borderless removes the yellow borders. Purely cosmetic.

Powers can be set with the "power" option, and the radius can be changed with "radius". Powers are used by clicking on the map. List of powers is provided. PowerN is a customizable option for some powers. Color shows for some powers the color that is selected.
If you want an easy cycle between the quadrant colors or the stripes colors, put in quad-cycle or stripes-cycle, or full-cycle for a cycle with every color.

## Right side features

Default sets everything to its defaults.
Import map allows you to import an image as a map.
The graphs show population and the area of each color over time. These graphs can provide useful insights. THE COLOR GRAPH CAUSES A LOT OF LAG IF THERE ARE MANY COLORS (such as the default preset), so it can be disabled.

## Hotkeys

There are hotkeys based on the numbers 1 to 9 that can be used and customized. You can use a hotkey by clicking its button, like pressing the number 5 to activate #5. There are some examples when the game is loaded.
With the "customize hotkeys" button, you can set a hotkey to 'event "x"' to do an event, or 'setup "x"' for a map, or set 'power "x"' to quickly change powers, and it also works for any other parameter, like 'set fight-rate 0'. The list of what the hotkeys does is shown on the right, the buttons for the hotkeys are hidden. You can also make a hotkey do multiple things, just put spaces between the different commands.

## Modding

The code supports modding of various features such as presets, events, the color cycle, and more if you know what you are doing. These parts of the code are have large spaces and a comment.

## Bugs and Credits

Bugs: Lag under certain conditions, mostly fixed.
Credits: By me (Andrei). I think the sea idea was inspired by something Otto said.

# Lists
All of these should be in lowercase, as it is case sensitive.

## Maps
Default/all - Every tile is a different random color.
rgb - Every tile is randomly red, green, or blue.
rgby/rgba/rgbya - Works like RGB, Y is yellow (unclaimed) and A is gray.
rb/rrb/rrrb - Red and blue, but not equal distribution. Red beats blue.
quad - Creates four quadrants of different colors.
quad2 - Yellow circle in the center.
seeds - Yellow map, a few colored tiles of four colors.
seeds2 - The "seeds" are random colors.
yellow - Pure yellow.
rgbyawl - Random out of any of those colors (W is white, L is black)
maze - Orange and cyan with a lot of black tiles.
lakes - Many colors, with a lot of white tiles.
sea - Quad2 except the circle in the middle is white.
stripes - Stripes of rainbow colors.
diagonal - Diagonal stripes in a gradient.
multiply - The map is divided into cells of rainbows. (xcor multiplied by ycor)
division - xcor is divided by ycor, making a sort of gradient around the center.

## Events
die - Kills every turtle.
jump - Makes every turtle move five units foward in whatever direction it is facing.
tele - Makes every turtle teleport to a random position.
shift - Makes every turtle change hue.
chaos - Makes every turtle yellow (turning tiles contested and starting battles)
collapse - Makes the largest color's turtles become random colors. Only works if leader-debuff isn't 0. (Can be 0.01)
nuke - Makes the largest color's turtles become black or white (permanently turning tiles black or white). Like above, only works if leader-debuff isn't 0.
scatter - Takes each tile, and teleports the turtles of that tile to a specific random tile. (Each tile goes to one other tile)
thanos - Kills half of the turtles.

## Patch Events

Patch events don't effect turtles, so turtles will often revert the changes made unless you also kill the turtles.
clean - Sets black and white tiles to yellow so they can be claimed.
save - Saves the color of every tile. Only saves the color.
load - Loads the color of every tile.
random - Sets every tile to a random color.
yellow - Sets every tile to be yellow.
move - Moves every tile randomly to the left.
grayscale - Sets every tile to be grayscale.
acid - Changes the color of every tile a bit. Hold this down for a cool effect.
purge - clean but for only half of the black and white tiles.
wall - Sets yellow tiles to be black. (Maybe do with borders on?)
swap - Swaps black and white tiles.
blob - Makes tiles change color to be more like their neighbors.

## Powers
A radius of 0 impacts the entire map for some powers.

clear - Deletes troops and turns tiles yellow.
pull - Makes turtles in the radius face the mouse.
push - Makes turtles in the radius face away from the mouse.
cyclone - Makes turtles in the radius face perpendicular to the mouse.
The above three abilities are pretty laggy, so you would want to lower the population.
die - Kills the turtles in the radius.
draw - "Draws" with the color when the mouse is first pressed, you can move around the mouse to draw. The radius is the thickness. The troops that are already there will take the tiles back, usually.
spawn - Draw but it spawns powerN turtles per tile of that color in the radius. (Two if n is 0)
drawN - Draw but it draws with the color put in powerN. (Netlogo has colors as numbers, 0 is black, 9.9 is white, 45 is yellow. You can see it in "tools".)
spawnN - Spawns 2 turtles per tile of color powerN in the radius.
buff - Make troops in the radius super killing machines.
chaos - Make troops in the area switch to random countries.
shift - Make troops in the area become the patch color + 10.
control - Click on a color and hold (select it), and every tick 1 out of powerN troops will face towards the mouse of that color.
magnet - Select a color like in control, and 1 out of powerN troops spawning will teleport to the mouse.
disable - Select a color, and it will not spawn troops.
spawnrate - Select a color, and every troop it spawns will spawn an additional powerN troops.
paint - Click a color, and all of its troops and tiles will be recolored to powerN. If the color is yellow, it will delete the troops.
collapse - Click a color, and its troops and tiles will be randomly recolored.
nuke - Click a color, and all of its troops and tiles will become black or white.
@#$#@#$#@
default
true
0
Polygon -7500403 true true 150 5 40 250 150 205 260 250

airplane
true
0
Polygon -7500403 true true 150 0 135 15 120 60 120 105 15 165 15 195 120 180 135 240 105 270 120 285 150 270 180 285 210 270 165 240 180 180 285 195 285 165 180 105 180 60 165 15

arrow
true
0
Polygon -7500403 true true 150 0 0 150 105 150 105 293 195 293 195 150 300 150

box
false
0
Polygon -7500403 true true 150 285 285 225 285 75 150 135
Polygon -7500403 true true 150 135 15 75 150 15 285 75
Polygon -7500403 true true 15 75 15 225 150 285 150 135
Line -16777216 false 150 285 150 135
Line -16777216 false 150 135 15 75
Line -16777216 false 150 135 285 75

bug
true
0
Circle -7500403 true true 96 182 108
Circle -7500403 true true 110 127 80
Circle -7500403 true true 110 75 80
Line -7500403 true 150 100 80 30
Line -7500403 true 150 100 220 30

butterfly
true
0
Polygon -7500403 true true 150 165 209 199 225 225 225 255 195 270 165 255 150 240
Polygon -7500403 true true 150 165 89 198 75 225 75 255 105 270 135 255 150 240
Polygon -7500403 true true 139 148 100 105 55 90 25 90 10 105 10 135 25 180 40 195 85 194 139 163
Polygon -7500403 true true 162 150 200 105 245 90 275 90 290 105 290 135 275 180 260 195 215 195 162 165
Polygon -16777216 true false 150 255 135 225 120 150 135 120 150 105 165 120 180 150 165 225
Circle -16777216 true false 135 90 30
Line -16777216 false 150 105 195 60
Line -16777216 false 150 105 105 60

car
false
0
Polygon -7500403 true true 300 180 279 164 261 144 240 135 226 132 213 106 203 84 185 63 159 50 135 50 75 60 0 150 0 165 0 225 300 225 300 180
Circle -16777216 true false 180 180 90
Circle -16777216 true false 30 180 90
Polygon -16777216 true false 162 80 132 78 134 135 209 135 194 105 189 96 180 89
Circle -7500403 true true 47 195 58
Circle -7500403 true true 195 195 58

circle
false
0
Circle -7500403 true true 0 0 300

circle 2
false
0
Circle -7500403 true true 0 0 300
Circle -16777216 true false 30 30 240

cow
false
0
Polygon -7500403 true true 200 193 197 249 179 249 177 196 166 187 140 189 93 191 78 179 72 211 49 209 48 181 37 149 25 120 25 89 45 72 103 84 179 75 198 76 252 64 272 81 293 103 285 121 255 121 242 118 224 167
Polygon -7500403 true true 73 210 86 251 62 249 48 208
Polygon -7500403 true true 25 114 16 195 9 204 23 213 25 200 39 123

cylinder
false
0
Circle -7500403 true true 0 0 300

dot
false
0
Circle -7500403 true true 90 90 120

eyeball
false
0
Circle -1 true false 22 20 248
Circle -7500403 true true 47 45 194
Circle -16777216 true false 122 120 44

face happy
false
0
Circle -7500403 true true 8 8 285
Circle -16777216 true false 60 75 60
Circle -16777216 true false 180 75 60
Polygon -16777216 true false 150 255 90 239 62 213 47 191 67 179 90 203 109 218 150 225 192 218 210 203 227 181 251 194 236 217 212 240

face neutral
false
0
Circle -7500403 true true 8 7 285
Circle -16777216 true false 60 75 60
Circle -16777216 true false 180 75 60
Rectangle -16777216 true false 60 195 240 225

face sad
false
0
Circle -7500403 true true 8 8 285
Circle -16777216 true false 60 75 60
Circle -16777216 true false 180 75 60
Polygon -16777216 true false 150 168 90 184 62 210 47 232 67 244 90 220 109 205 150 198 192 205 210 220 227 242 251 229 236 206 212 183

fish
false
0
Polygon -1 true false 44 131 21 87 15 86 0 120 15 150 0 180 13 214 20 212 45 166
Polygon -1 true false 135 195 119 235 95 218 76 210 46 204 60 165
Polygon -1 true false 75 45 83 77 71 103 86 114 166 78 135 60
Polygon -7500403 true true 30 136 151 77 226 81 280 119 292 146 292 160 287 170 270 195 195 210 151 212 30 166
Circle -16777216 true false 215 106 30

flag
false
0
Rectangle -7500403 true true 60 15 75 300
Polygon -7500403 true true 90 150 270 90 90 30
Line -7500403 true 75 135 90 135
Line -7500403 true 75 45 90 45

flower
false
0
Polygon -10899396 true false 135 120 165 165 180 210 180 240 150 300 165 300 195 240 195 195 165 135
Circle -7500403 true true 85 132 38
Circle -7500403 true true 130 147 38
Circle -7500403 true true 192 85 38
Circle -7500403 true true 85 40 38
Circle -7500403 true true 177 40 38
Circle -7500403 true true 177 132 38
Circle -7500403 true true 70 85 38
Circle -7500403 true true 130 25 38
Circle -7500403 true true 96 51 108
Circle -16777216 true false 113 68 74
Polygon -10899396 true false 189 233 219 188 249 173 279 188 234 218
Polygon -10899396 true false 180 255 150 210 105 210 75 240 135 240

house
false
0
Rectangle -7500403 true true 45 120 255 285
Rectangle -16777216 true false 120 210 180 285
Polygon -7500403 true true 15 120 150 15 285 120
Line -16777216 false 30 120 270 120

leaf
false
0
Polygon -7500403 true true 150 210 135 195 120 210 60 210 30 195 60 180 60 165 15 135 30 120 15 105 40 104 45 90 60 90 90 105 105 120 120 120 105 60 120 60 135 30 150 15 165 30 180 60 195 60 180 120 195 120 210 105 240 90 255 90 263 104 285 105 270 120 285 135 240 165 240 180 270 195 240 210 180 210 165 195
Polygon -7500403 true true 135 195 135 240 120 255 105 255 105 285 135 285 165 240 165 195

line
true
0
Line -7500403 true 150 0 150 300

line half
true
0
Line -7500403 true 150 0 150 150

pentagon
false
0
Polygon -7500403 true true 150 15 15 120 60 285 240 285 285 120

person
false
0
Circle -7500403 true true 110 5 80
Polygon -7500403 true true 105 90 120 195 90 285 105 300 135 300 150 225 165 300 195 300 210 285 180 195 195 90
Rectangle -7500403 true true 127 79 172 94
Polygon -7500403 true true 195 90 240 150 225 180 165 105
Polygon -7500403 true true 105 90 60 150 75 180 135 105

plant
false
0
Rectangle -7500403 true true 135 90 165 300
Polygon -7500403 true true 135 255 90 210 45 195 75 255 135 285
Polygon -7500403 true true 165 255 210 210 255 195 225 255 165 285
Polygon -7500403 true true 135 180 90 135 45 120 75 180 135 210
Polygon -7500403 true true 165 180 165 210 225 180 255 120 210 135
Polygon -7500403 true true 135 105 90 60 45 45 75 105 135 135
Polygon -7500403 true true 165 105 165 135 225 105 255 45 210 60
Polygon -7500403 true true 135 90 120 45 150 15 180 45 165 90

sheep
false
15
Circle -1 true true 203 65 88
Circle -1 true true 70 65 162
Circle -1 true true 150 105 120
Polygon -7500403 true false 218 120 240 165 255 165 278 120
Circle -7500403 true false 214 72 67
Rectangle -1 true true 164 223 179 298
Polygon -1 true true 45 285 30 285 30 240 15 195 45 210
Circle -1 true true 3 83 150
Rectangle -1 true true 65 221 80 296
Polygon -1 true true 195 285 210 285 210 240 240 210 195 210
Polygon -7500403 true false 276 85 285 105 302 99 294 83
Polygon -7500403 true false 219 85 210 105 193 99 201 83

square
false
0
Rectangle -7500403 true true 30 30 270 270

square 2
false
0
Rectangle -7500403 true true 30 30 270 270
Rectangle -16777216 true false 60 60 240 240

star
false
0
Polygon -7500403 true true 151 1 185 108 298 108 207 175 242 282 151 216 59 282 94 175 3 108 116 108

target
false
0
Circle -7500403 true true 0 0 300
Circle -16777216 true false 30 30 240
Circle -7500403 true true 60 60 180
Circle -16777216 true false 90 90 120
Circle -7500403 true true 120 120 60

tree
false
0
Circle -7500403 true true 118 3 94
Rectangle -6459832 true false 120 195 180 300
Circle -7500403 true true 65 21 108
Circle -7500403 true true 116 41 127
Circle -7500403 true true 45 90 120
Circle -7500403 true true 104 74 152

triangle
false
0
Polygon -7500403 true true 150 30 15 255 285 255

triangle 2
false
0
Polygon -7500403 true true 150 30 15 255 285 255
Polygon -16777216 true false 151 99 225 223 75 224

truck
false
0
Rectangle -7500403 true true 4 45 195 187
Polygon -7500403 true true 296 193 296 150 259 134 244 104 208 104 207 194
Rectangle -1 true false 195 60 195 105
Polygon -16777216 true false 238 112 252 141 219 141 218 112
Circle -16777216 true false 234 174 42
Rectangle -7500403 true true 181 185 214 194
Circle -16777216 true false 144 174 42
Circle -16777216 true false 24 174 42
Circle -7500403 false true 24 174 42
Circle -7500403 false true 144 174 42
Circle -7500403 false true 234 174 42

turtle
true
0
Polygon -10899396 true false 215 204 240 233 246 254 228 266 215 252 193 210
Polygon -10899396 true false 195 90 225 75 245 75 260 89 269 108 261 124 240 105 225 105 210 105
Polygon -10899396 true false 105 90 75 75 55 75 40 89 31 108 39 124 60 105 75 105 90 105
Polygon -10899396 true false 132 85 134 64 107 51 108 17 150 2 192 18 192 52 169 65 172 87
Polygon -10899396 true false 85 204 60 233 54 254 72 266 85 252 107 210
Polygon -7500403 true true 119 75 179 75 209 101 224 135 220 225 175 261 128 261 81 224 74 135 88 99

wheel
false
0
Circle -7500403 true true 3 3 294
Circle -16777216 true false 30 30 240
Line -7500403 true 150 285 150 15
Line -7500403 true 15 150 285 150
Circle -7500403 true true 120 120 60
Line -7500403 true 216 40 79 269
Line -7500403 true 40 84 269 221
Line -7500403 true 40 216 269 79
Line -7500403 true 84 40 221 269

wolf
false
0
Polygon -16777216 true false 253 133 245 131 245 133
Polygon -7500403 true true 2 194 13 197 30 191 38 193 38 205 20 226 20 257 27 265 38 266 40 260 31 253 31 230 60 206 68 198 75 209 66 228 65 243 82 261 84 268 100 267 103 261 77 239 79 231 100 207 98 196 119 201 143 202 160 195 166 210 172 213 173 238 167 251 160 248 154 265 169 264 178 247 186 240 198 260 200 271 217 271 219 262 207 258 195 230 192 198 210 184 227 164 242 144 259 145 284 151 277 141 293 140 299 134 297 127 273 119 270 105
Polygon -7500403 true true -1 195 14 180 36 166 40 153 53 140 82 131 134 133 159 126 188 115 227 108 236 102 238 98 268 86 269 92 281 87 269 103 269 113

x
false
0
Polygon -7500403 true true 270 75 225 30 30 225 75 270
Polygon -7500403 true true 30 75 75 30 270 225 225 270
@#$#@#$#@
NetLogo 6.2.0
@#$#@#$#@
@#$#@#$#@
@#$#@#$#@
@#$#@#$#@
@#$#@#$#@
default
0.0
-0.2 0 0.0 1.0
0.0 1 1.0 0.0
0.2 0 0.0 1.0
link direction
true
0
Line -7500403 true 150 150 90 180
Line -7500403 true 150 150 210 180
@#$#@#$#@
0
@#$#@#$#@
