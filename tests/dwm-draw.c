/* Exercise real drw_text without X: all drawing/font operations are substitutes. */
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <X11/Xlib.h>
#include <X11/Xutil.h>
#include <X11/Xft/Xft.h>
#include "drw.h"

static int fills, strings;
static const XftColor *textcolor;
static int images, destroyed, uploads, imagefail;
static unsigned long rendered[256];

static int
freeimage(XImage *image)
{
	free(image->data);
	free(image);
	destroyed++;
	return 1;
}

XImage *
XCreateImage(Display *display, Visual *visual, unsigned int depth, int format,
	int offset, char *data, unsigned int width, unsigned int height,
	int pad, int stride)
{
	XImage *image;

	if (imagefail)
		return NULL;
	image = calloc(1, sizeof *image);
	assert(image);
	image->width = width;
	image->height = height;
	image->format = ZPixmap;
	image->byte_order = LSBFirst;
	image->bitmap_unit = image->bitmap_pad = 32;
	image->bitmap_bit_order = LSBFirst;
	image->depth = depth;
	image->bits_per_pixel = 32;
	image->bytes_per_line = width * 4;
	assert(XInitImage(image)); /* Local Xlib pixel helpers, no server or display. */
	image->f.destroy_image = freeimage;
	images++;
	return image;
}

int
XPutImage(Display *display, Drawable drawable, GC gc, XImage *image,
	int sx, int sy, int x, int y, unsigned int width, unsigned int height)
{
	unsigned int xx, yy;

	assert(width * height <= 256 && x == 3 && y == 4);
	for (yy = 0; yy < height; yy++)
		for (xx = 0; xx < width; xx++)
			rendered[yy * width + xx] = XGetPixel(image, xx, yy);
	uploads++;
	return 1;
}

static void
parser(void)
{
	unsigned long data[2 + 32 * 16 + 2 + 8 * 4 + 2 + 16 * 8] = {0};
	unsigned long *large = calloc(262147, sizeof(long));
	unsigned long bad[] = {1, 1, 0xffffffff, 0};
	DrwIcon *icon;
	unsigned int i;

	assert(large);
	assert(!drw_icon_create(NULL, 3, 16));
	assert(!drw_icon_create(bad, 0, 16));
	assert(!drw_icon_create(bad, 3, 0));
	assert(!drw_icon_create(bad, 3, 17));
	assert(!drw_icon_create(bad, 1, 16));
	assert(!drw_icon_create(bad, 2, 16));
	assert(!drw_icon_create(bad, 4, 16));
	bad[0] = 0;
	assert(!drw_icon_create(bad, 3, 16));
	bad[0] = ~0UL;
	assert(!drw_icon_create(bad, 3, 16));
	bad[0] = 513;
	assert(!drw_icon_create(bad, 3, 16));
	bad[0] = 1;
	bad[1] = 0;
	assert(!drw_icon_create(bad, 3, 16));
	bad[1] = ~0UL;
	assert(!drw_icon_create(bad, 3, 16));
	large[0] = large[1] = 512;
	large[2] = 0xff123456;
	large[262145] = 0xffabcdef;
	assert(!drw_icon_create(large, 262147, 16));
	assert(!drw_icon_create(large, 262145, 16));
	icon = drw_icon_create(large, 262146, 16);
	assert(icon && icon->w == 16 && icon->h == 16);
	assert(icon->pixels[0] == 0xff123456);
	drw_icon_free(icon);
	free(large);

	data[0] = 32;
	data[1] = 16;
	for (i = 2; i < 514; i++)
		data[i] = 0xff111111;
	data[514] = 8;
	data[515] = 4;
	for (i = 516; i < 548; i++)
		data[i] = 0xff222222;
	data[548] = 16;
	data[549] = 8;
	for (i = 550; i < sizeof data / sizeof *data; i++)
		data[i] = 0xff333333;
	icon = drw_icon_create(data, sizeof data / sizeof *data, 16);
	assert(icon && icon->w == 16 && icon->h == 8 && icon->pixels[0] == 0xff333333);
	drw_icon_free(icon);
	icon = drw_icon_create(data, 548, 16);
	assert(icon && icon->w == 16 && icon->h == 8 && icon->pixels[0] == 0xff111111);
	drw_icon_free(icon);
	icon = drw_icon_create(data + 514, 34, 16);
	assert(icon && icon->w == 16 && icon->h == 8 && icon->pixels[0] == 0xff222222);
	drw_icon_free(icon);
	/* Largest below target wins; nearest-neighbor preserves source samples. */
	data[0] = 2;
	data[1] = 1;
	data[2] = 0xff000001;
	data[3] = 0xff000002;
	data[4] = data[5] = 1;
	data[6] = 0xff000003;
	icon = drw_icon_create(data, 7, 16);
	assert(icon && icon->w == 16 && icon->h == 8);
	assert(icon->pixels[7] == 0xff000001 && icon->pixels[8] == 0xff000002);
	drw_icon_free(icon);
	data[0] = 1;
	data[1] = 32;
	icon = drw_icon_create(data, 34, 16);
	assert(icon && icon->w == 1 && icon->h == 16);
	drw_icon_free(icon);
	drw_icon_free(NULL);
	/* Deterministic hostile headers/tails, under sanitizers. */
	for (i = 0; i < 512; i++) {
		data[0] = i;
		data[1] = 513 - i;
		icon = drw_icon_create(data, 34, 16);
		drw_icon_free(icon);
	}
}

static void
icons(Drw *drawing, Screen *screen)
{
	Visual visual = {.class = TrueColor, .red_mask = 0xff0000,
		.green_mask = 0xff00, .blue_mask = 0xff};
	unsigned int pixels[] = {0x00ff0000, 0xffff0000, 0x80ff0000};
	DrwIcon icon = {.w = 3, .h = 1, .pixels = pixels};
	int previous;

	screen->root_visual = &visual;
	screen->root_depth = 24;
	drawing->scheme[ColBg].pixel = 0x204060;
	drawing->scheme[ColFg].pixel = 0xabcdef;
	assert(drw_icon(drawing, 3, 4, &icon, 0));
	assert(rendered[0] == 0x204060 && rendered[1] == 0xff0000 && rendered[2] == 0x902030);
	assert(drw_icon(drawing, 3, 4, &icon, 1));
	assert(rendered[0] == 0xabcdef && rendered[2] == 0xd56677);
	assert(images == destroyed && uploads == images);
	previous = images;
	visual.class = PseudoColor;
	assert(!drw_icon(drawing, 3, 4, &icon, 0));
	visual.class = TrueColor;
	visual.red_mask = 0x550000;
	assert(!drw_icon(drawing, 3, 4, &icon, 0));
	visual.red_mask = 0xff00;
	assert(!drw_icon(drawing, 3, 4, &icon, 0));
	visual.red_mask = 0;
	assert(!drw_icon(drawing, 3, 4, &icon, 0));
	assert(images == previous);
	visual.red_mask = 0xff0000;
	imagefail = 1;
	assert(!drw_icon(drawing, 3, 4, &icon, 0));
	imagefail = 0;
	visual.red_mask = 0xf800;
	visual.green_mask = 0x7e0;
	visual.blue_mask = 0x1f;
	drawing->scheme[ColBg].pixel = 0x7e0;
	assert(drw_icon(drawing, 3, 4, &icon, 0));
	assert(rendered[0] == 0x7e0 && rendered[1] == 0xf800);
	assert(images == destroyed && uploads == images);
	assert(!drw_icon(NULL, 3, 4, &icon, 0));
	assert(!drw_icon(drawing, 3, 4, NULL, 0));
}

int
XSetForeground(Display *display, GC gc, unsigned long pixel)
{
	return 1;
}

int
XFillRectangle(Display *display, Drawable drawable, GC gc, int x, int y,
	unsigned int w, unsigned int h)
{
	fills++;
	return 1;
}

XftDraw *
XftDrawCreate(Display *display, Drawable drawable, Visual *visual, Colormap colormap)
{
	return (XftDraw *)1;
}

void
XftDrawDestroy(XftDraw *draw)
{
}

FcBool
XftCharExists(Display *display, XftFont *font, FcChar32 character)
{
	return FcTrue;
}

void
XftTextExtentsUtf8(Display *display, XftFont *font, const FcChar8 *text,
	int length, XGlyphInfo *extents)
{
	memset(extents, 0, sizeof *extents);
	extents->xOff = length * 8;
}

void
XftDrawStringUtf8(XftDraw *draw, const XftColor *color, XftFont *font,
	int x, int y, const FcChar8 *text, int length)
{
	strings++;
	textcolor = color;
}

int
main(void)
{
	_XPrivDisplay display = calloc(1, sizeof *display);
	Screen screen = {0};
	XftFont xfont = {.ascent = 12};
	Fnt font = {.h = 16, .xfont = &xfont};
	Clr colors[3] = {{0}};
	Drw drawing = {.dpy = (Display *)display, .fonts = &font, .scheme = colors};
	int flags;

	assert(display);
	display->screens = &screen;
	for (flags = 0; flags < 4; flags++) {
		fills = strings = 0;
		drw_text(&drawing, 0, 0, 200, 24, 4, "Window", flags);
		assert(fills == !(flags & 2));
		assert(strings && textcolor == &colors[flags & 1 ? ColBg : ColFg]);
	}
	fills = strings = 0;
	drw_text(&drawing, 0, 0, 48, 24, 0, "Very long window title", 2);
	assert(!fills && strings);
	assert(textcolor == &colors[ColFg]);
	parser();
	icons(&drawing, &screen);
	puts("PASS: original icon parser limits/selection/aspect/nearest-neighbor and TrueColor alpha/render/fallback/free (mock Xlib, ASan/UBSan)");
	free(display);
	puts("PASS: real dwm text rendering flags, transparent gradient text and ellipsis (mock Xft/Xlib)");
	return 0;
}
