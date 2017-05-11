# hooray, let's try something new!
# we will try to make it so that [[a,b,c],[d,e,f],[g,h,i]]
# becomes 	[a, d, g]
# 			[b, e, h]
# 			[c, f, i]
# this is so you can effectively use map[x][y]

from PIL import Image
from random import randint
from math import sqrt, log


class Colors:
	list = []

	def __init__(self, size, seedlist):
		print('generating colors...')
		for seed in seedlist:
			dis = get_distance(seed, [size[0] / 2, size[1] / 2])
			if dis > 200:
				newcolor = (randint(30, 35), 200 - int(dis / 2), 500 - dis)		# blue sea
			elif 200 >= dis > 140:
				newcolor = (dis + 50, dis + 50, randint(15, 30))				# beach color
			elif 140 >= dis > 70:
				newcolor = (int(dis / 4), dis, int(dis / 4))							# grass
			elif 70 >= dis > 30:
				newcolor = (230 - dis, 230 - dis, 220 - dis)					# mountain
			else:
				newcolor = (255 - dis, 255 - dis, 255 - dis)					# snow
			Colors.list.append(newcolor)
		Colors.list.append((0, 0, 0))
		print('colors generated (' + str(len(Colors.list)) + ')')


def get_distance(point1, point2):
	return int(round(sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2), 0))


def generate_map(size, seedamount):
	print('generating empty map with seedlist... (' + str(size[0]) + 'x' + str(size[1]) + ')')
	fullmap = []
	center = [size[0] / 2, size[1] / 2]

	# we first generate the map list itself, and fill each pixel with a 0.
	for column in range(size[0]):
		fullmap.append([])
	for row in range(size[1]):
		for column in range(size[0]):
			fullmap[column].append(0)

	# now we select some random pixels that will become our seeds
	seedposlist = []
	for _ in range(seedamount):
		reroll = 1
		while reroll == 1:
			reroll = 0
			seed = [randint(0, size[0]), randint(0, size[1])]
			for otherseed in seedposlist:
				if get_distance(seed, otherseed) < size[0] / seedamount:
					reroll = 1
		if seed not in seedposlist:
			seedposlist.append(seed)

	print('empty map with seedlist generated')
	return fullmap, seedposlist


def color_in(map, seedlist, showseeds=False):
	print('coloring in the map...')
	for x in range(len(map)):
		for y in range(len(map[0])):
			closest = 1000000000
			closestone = 0
			for index, seed in enumerate(seedlist):
				if get_distance([x, y], seed) < closest:
					closestone = index
					closest = get_distance([x, y], seed)
				if get_distance([x, y], seed) < 3 and showseeds:
					closestone = -1
			try:
				color = Colors.list[closestone]
			except IndexError:
				print('Color error! - ignoring...')
				color = Colors.list[closestone - 1]
			map[x][y] = color
		if x % (len(map) / 10) == 0:
			print('coloring progress: ', str(int(round(100 * x / len(map), 2))) + '%')
	print('done with coloring')
	return map


def convert_to_image(pixellist, number=0):
	print('converting to image...')
	width = len(pixellist)
	height = len(pixellist[0])
	# first we will need to convert our list to something that can be read row by row.
	fullList = []
	for y in range(height):
		for x in range(width):
			fullList.append(pixellist[x][y])
	img = Image.new('RGB', [width, height])
	img.putdata(fullList)
	img.save('image' + str(number) + '.png')
	print('done with converting')

size = [500, 500]
mapvalues, seedlist = generate_map(size, 500)
Colors(size, seedlist)
mapcolor = color_in(mapvalues, seedlist)
convert_to_image(mapcolor)
