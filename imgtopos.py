from PIL import Image

img = Image.open(r"C:\users\winnie33\desktop\heart.png")
w = img.size[0]
pixelvalues = list(img.getdata())
blackpixels = []
c = 0
for index, pixel in enumerate(pixelvalues):
	if pixel != (255, 255, 255, 255):
		if c % 10 == 0:
			blackpixels.append([index % w, int(index / w)])
		c += 1
print(blackpixels)