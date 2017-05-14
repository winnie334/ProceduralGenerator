# hooray, let's try something new!
# we will try to make it so that [[a,b,c],[d,e,f],[g,h,i]]
# becomes 	[a, d, g]
# 			[b, e, h]
# 			[c, f, i]
# this is so you can effectively use map[x][y]

from PIL import Image
from random import randint
from math import sqrt, log
from multiprocessing import Process, Queue
from noise import pnoise2, snoise2
from time import clock


class Centers:
	list = []
	# list holds lists, with each sublist holding the values [x, y, size]

	def __init__(self, mapsize, amount, size=200):
		for i in range(amount):
			x = randint(0, mapsize[0])
			y = randint(0, mapsize[1])
			Centers.list.append([x, y, size])


class Seeds:
	list = []

	def __init__(self, pos, height):
		self.pos = pos
		self.height = height
		self.color = self.get_colorheight()
		Seeds.list.append(self)

	def get_colorblack(self):
		color = (self.height, self.height, self.height)
		return color

	def get_colorheight(self):
		if self.height > 200:
			newcolor = (self.height, self.height + randint(1, 5), self.height + randint(2, 7))			# snow
		elif 200 >= self.height > 165:
			r = randint(20, 25)
			newcolor = (int(self.height / 2) + r, int(self.height / 2) + r, int(self.height / 2) + r)  # mountain
		elif 165 >= self.height > 100:
			newcolor = (randint(25, 30), 255 - self.height, 35 - int(self.height / 10))  # grass
		elif 100 >= self.height > 60:
			newcolor = (250 - self.height, 250 - self.height, randint(15, 25))  # beach color
		else:
			newcolor = (randint(15, 20), self.height + 25, self.height + 100)  # blue sea
		return newcolor

	def get_color(self):
		closest = 1000000000
		closestone = 0
		for index, center in enumerate(Centers.list):
			if get_distance(self.pos, center) < closest:
				closestone = index
				closest = get_distance(self.pos, center)
		closestcenter = Centers.list[closestone]
		dis = get_distance(self.pos, closestcenter[0:2])
		dis = int(dis / 200 * closestcenter[2])
		if dis > 200:
			newcolor = (randint(15, 20), 225 - int(dis / 2), 500 - dis)  # blue sea
		elif 200 >= dis > 150:
			newcolor = (dis + 50, dis + 50, randint(15, 30))  # beach color
		elif 150 >= dis > 70:
			newcolor = (int(dis / 4), dis, int(dis / 4))  # grass
		elif 70 >= dis > 30:
			newcolor = (230 - dis, 230 - dis, 220 - dis)  # mountain
		else:
			newcolor = (255 - dis, 255 - dis, 255 - dis)  # snow
		return newcolor


def get_distance(point1, point2):
	return int(round(sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2), 0))


def generate_maps(size, seedamount, freq, o, height, r):
	estimated_time = size[0] * size[1] * seedamount / 936654
	m, s = divmod(estimated_time, 60)
	h, m = divmod(m, 60)
	print('estimated duration: ' + str(h) + ' hours, ' + str(int(m)) + ' minutes and ' + str(int(s)) + ' seconds')
	print('generating empty map... (' + str(size[0]) + 'x' + str(size[1]) + ')')
	center = [size[0] / 2, size[1] / 2]

	# we first generate the map list itself, and fill each pixel with a 0.
	emptymap = []
	for column in range(size[0]):
		emptymap.append([])

	for row in range(size[1]):
		for column in range(size[0]):
			emptymap[column].append(column)
	print('empty map generated')

	# generate a copy of this map, but add height values to each position.
	heightmap = []
	for x in range(size[0] + 10):
		heightmap.append([])
	for y in range(size[1] + 10):
		for x in range(size[0] + 10):
			heightmap[x].append(0)
	for x in range(size[0] + 5):
		for y in range(size[1] + 5):
			heightmap[x][y] = int(snoise2(y / freq, x / freq, o, persistence=0.25, base=r) * 127 + height)

	# now we select some random pixels that will become our seeds
	print('generating seedlist... (' + str(seedamount) + ' seeds)')
	if seedamount <= 100:
		print('heh, this is gonna be quick')
	elif 1000 >= seedamount > 500:
		print('this is going to be pretty')
	elif 3000 >= seedamount > 1000:
		print("oh, you like it intense? This is gonna take a while, but let's do it!")
	elif seedamount > 3000:
		print('wait... WHAT THE HELL ARE YOU THINKING??')
		print(str(seedamount) + ' SEEDS? THIS IS GOING TO TAKE AGES!')
		print("anyway... I guess we'll continue...")
	rerolls = 0
	for _ in range(seedamount):
		reroll = 1
		while reroll == 1:
			reroll = 0
			seed = [randint(0, size[0]), randint(0, size[1])]
			for otherseed in Seeds.list:
				if get_distance(seed, otherseed.pos) <= size[0] / seedamount:
					rerolls += 1
					reroll = 1
		Seeds(seed, heightmap[seed[0]][seed[1]])

	print('seedlist generated (' + str(rerolls) + ' rerolls)')
	return emptymap, heightmap


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


def divide_work(map, cores=1):
	"""divides the map into columns, then assigns each column to a core"""
	print('dividing the work over ' + str(cores) + ' cores...')
	threadlist = []
	mapqueue = Queue()
	progressqueue = Queue()
	splitmap = chunkit(map, cores)
	for i in range(cores):
		startpos = splitmap[i][0][0]
		t = Process(target=color_in, args=(i, startpos, splitmap[i], mapqueue, progressqueue, Seeds.list,))
		threadlist.append(t)
	for thread in threadlist:
		thread.start()
	scrambledmap = []
	percentages = [0 for _ in range(cores)]
	lastaverage = 0
	average = 0
	while int(average) != 100:
		progress = progressqueue.get()
		percentages[progress[-1]] = progress[0]
		average = sum(percentages) / len(percentages)
		if average > lastaverage + 1:
			print('coloring progress: ' + str(round(average, 2)) + '%')
			lastaverage = average
	while len(scrambledmap) < cores:
		scrambledmap.append(mapqueue.get())
	coloredmap = []
	for i in range(cores):
		for block in scrambledmap:
			if block[-1] == i:
				coloredmap.append(block[:len(block) - 1])
	new = [x for y in coloredmap for x in y]  	# for some reason we have nested lists, this fixes that
	return new


def color_in(number, startpos, map, queue, progressqueue, seedlist, showseeds=False):
	"""this does not really color in, but rather check for each pixel to what seed it belongs"""
	print('Process ' + str(number) + ': going to color ' + str(len(map)) + ' columns!')
	for x in range(len(map)):
		for y in range(len(map[0])):
			closest = 1000000000
			closestone = 0
			for index, seed in enumerate(seedlist):
				if get_distance([x + startpos, y], seed.pos) < closest:
					closestone = index
					closest = get_distance([x + startpos, y], seed.pos)
				if get_distance([x + startpos, y], seed.pos) < 3 and showseeds:
					closestone = -1
			color = seedlist[closestone].color
			map[x][y] = color
		progressqueue.put([100 * (x + 1) / len(map), number])
	print('Process ' + str(number) + ': done coloring')
	map.append(number)
	queue.put(map)


def convert_to_image(pixellist, p, number=0):
	"""takes a list of pixels, converts it to an image viewable by a human"""
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
	dumpname = "s" + str(p[0]) + " o" + str(p[1]) + " f" + str(p[2]) + " h" + str(p[3]) + " r" + str(p[4])
	img.save('imagedump\\' + dumpname + '.png')
	print('done with converting')


def time_stuff(starttime):
	endtime = clock()
	time_elapsed = endtime - starttime
	minutes, seconds = divmod(time_elapsed, 60)
	hours, minutes = divmod(minutes, 60)
	print('done with generating image!')
	print('time elapsed: ' + str(hours) + ' hours, ' + str(minutes) + ' minutes and ' + str(seconds) + ' seconds')


if __name__ == '__main__':
	starttime = clock()
	size = [1000, 1000]
	seeds = 600
	octaves = 1
	frequency = 600
	height = 90
	rseed = randint(1, 100000)
	parameters = [seeds, octaves, frequency, height, rseed]
	emptymap, heightmap = generate_maps(size, seeds, frequency, octaves, height, rseed)
	mapcolor = divide_work(emptymap, 7)
	convert_to_image(mapcolor, parameters)
	time_stuff(starttime)
