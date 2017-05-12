# hooray, let's try something new!
# we will try to make it so that [[a,b,c],[d,e,f],[g,h,i]]
# becomes 	[a, d, g]
# 			[b, e, h]
# 			[c, f, i]
# this is so you can effectively use map[x][y]

from PIL import Image
from random import randint
from math import sqrt, log
from multiprocessing import Process, Manager, Queue


class Colors:
	list = []

	def __init__(self, size, seedlist):
		print('generating colors...')
		for seed in seedlist:
			dis = get_distance(seed, [size[0] / 2, size[1] / 2])
			if dis > 200:
				newcolor = (randint(30, 35), 200 - int(dis / 2), 500 - dis)		# blue sea
			elif 200 >= dis > 150:
				newcolor = (dis + 50, dis + 50, randint(15, 30))				# beach color
			elif 150 >= dis > 70:
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
			fullmap[column].append(column)
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


def chunkit(seq, num):
	# divides a list into lists of roughly equal sizes.
	# completely stolen from the internet, no questions.
	avg = len(seq) / float(num)
	out = []
	last = 0.0
	while last < len(seq):
		out.append(seq[int(last):int(last + avg)])
		last += avg
	return out


def divide_work(map, seedlist, cores=1):
	print('dividing the work over ' + str(cores) + ' cores...')
	threadlist = []
	queue = Queue()
	splitmap = chunkit(map, cores)
	for i in range(cores):
		startpos = splitmap[i][0][0]
		t = Process(target=color_in, args=(i, startpos, splitmap[i], seedlist, queue, Colors.list,))
		threadlist.append(t)
	for thread in threadlist:
		thread.start()
	scrambledmap = []
	while len(scrambledmap) < cores:
		scrambledmap.append(queue.get())
	coloredmap = []
	for i in range(cores):
		for block in scrambledmap:
			if block[-1] == i:
				coloredmap.append(block[:len(block) - 1])
	new = [x for y in coloredmap for x in y]  	# for some reason we have nested lists, this fixes that
	return new


def color_in(number, startpos, map, seedlist, queue, colorlist, showseeds=False):
	print('Proces ' + str(number) + ': going to color ' + str(len(map)) + ' columns!')
	for x in range(len(map)):
		for y in range(len(map[0])):
			closest = 1000000000
			closestone = 0
			for index, seed in enumerate(seedlist):
				if get_distance([x + startpos, y], seed) < closest:
					closestone = index
					closest = get_distance([x + startpos, y], seed)
				if get_distance([x + startpos, y], seed) < 3 and showseeds:
					closestone = -1
			color = colorlist[closestone]
			map[x][y] = color
		if x % (len(map) / 20) == 0:
			print('coloring progress: ', str(int(round(100 * x / len(map), 2))) + '%')
	print('done with coloring')
	map.append(number)
	queue.put(map)


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

if __name__ == '__main__':
	size = [500, 500]
	mapvalues, seedlist = generate_map(size, 500)
	Colors(size, seedlist)
	mapcolor = divide_work(mapvalues, seedlist, 8)
	convert_to_image(mapcolor)
