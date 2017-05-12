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


class Centers:
	list = []
	# list holds lists, with each sublist holding the values [x, y, size]

	def __init__(self, mapsize, amount, size=200):
		for i in range(amount):
			x = randint(0, mapsize[0])
			y = randint(0, mapsize[1])
			Centers.list.append([x, y, size])


class Colors:
	list = []

	def __init__(self, size, seedlist):
		print('generating colors...')
		for seed in seedlist:
			closest = 1000000000
			closestone = 0
			for index, center in enumerate(Centers.list):
				if get_distance(seed, center) < closest:
					closestone = index
					closest = get_distance(seed, center)
			closestcenter = Centers.list[closestone]
			dis = get_distance(seed, closestcenter[0:2])
			dis = int(dis / 200 * closestcenter[2])
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
		print('colors generated')


def get_distance(point1, point2):
	return int(round(sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2), 0))


def generate_map(size, seedamount):
	print('generating empty map... (' + str(size[0]) + 'x' + str(size[1]) + ')')
	fullmap = []
	center = [size[0] / 2, size[1] / 2]

	# we first generate the map list itself, and fill each pixel with a 0.
	for column in range(size[0]):
		fullmap.append([])
	for row in range(size[1]):
		for column in range(size[0]):
			fullmap[column].append(column)
	print('empty map generated')

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
	seedposlist = []
	rerolls = 0
	for _ in range(seedamount):
		reroll = 1
		while reroll == 1:
			reroll = 0
			seed = [randint(0, size[0]), randint(0, size[1])]
			for otherseed in seedposlist:
				if get_distance(seed, otherseed) < size[0] / seedamount:
					rerolls += 1
					reroll = 1
		if seed not in seedposlist:
			seedposlist.append(seed)

	print('seedlist generated (' + str(rerolls) + ' rerolls)')
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
	mapqueue = Queue()
	progressqueue = Queue()
	splitmap = chunkit(map, cores)
	for i in range(cores):
		startpos = splitmap[i][0][0]
		t = Process(target=color_in, args=(i, startpos, splitmap[i], seedlist, mapqueue, progressqueue, Colors.list,))
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


def color_in(number, startpos, map, seedlist, queue, progressqueue, colorlist, showseeds=False):
	print('Process ' + str(number) + ': going to color ' + str(len(map)) + ' columns!')
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
		progressqueue.put([100 * (x + 1) / len(map), number])
	print('Process ' + str(number) + ': done coloring')
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
	size = [300, 300]
	mapvalues, seedlist = generate_map(size, 600)
	Centers(size, 2, 600)
	Colors(size, seedlist)
	mapcolor = divide_work(mapvalues, seedlist, 7)
	convert_to_image(mapcolor)
