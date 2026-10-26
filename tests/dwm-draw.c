/* Exercise real drw_text without X: all drawing/font operations are substitutes. */
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <X11/Xlib.h>
#include <X11/Xft/Xft.h>
#include "drw.h"

static int fills, strings;
static const XftColor *textcolor;

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
	free(display);
	puts("PASS: real dwm text rendering flags, transparent gradient text and ellipsis (mock Xft/Xlib)");
	return 0;
}
