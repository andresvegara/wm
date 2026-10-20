/* Test st's real X frontend functions without opening a display. */
#include <assert.h>
#include <string.h>
#include <sys/wait.h>

#define main st_main
#define kscrollup testscrollup
#define kscrolldown testscrolldown
#define tisaltscreen testaltscreen
#define ttywrite testttywrite
#include "x.c"
#undef main

static int alt, up, down;
static char sent;

void testscrollup(const Arg *a) { up = a->i; }
void testscrolldown(const Arg *a) { down = a->i; }
int testaltscreen(void) { return alt; }
void testttywrite(const char *s, size_t n, int echo) { assert(n == 1); sent = *s; }

static XSizeHints hints;
static Atom owned, converted;
static Window owner;

Display *
XOpenDisplay(const char *name)
{
	assert(!"tests must not open an X display");
	return NULL;
}

XSizeHints *
XAllocSizeHints(void)
{
	return calloc(1, sizeof(XSizeHints));
}

void
XSetWMProperties(Display *display, Window window, XTextProperty *title,
	XTextProperty *icon, char **argv, int argc, XSizeHints *size,
	XWMHints *wm, XClassHint *class)
{
	hints = *size;
}

int
XFree(void *data)
{
	free(data);
	return 1;
}

Atom
XInternAtom(Display *display, const char *name, Bool onlyexisting)
{
	assert(!strcmp(name, "CLIPBOARD"));
	return 42;
}

int
XSetSelectionOwner(Display *display, Atom selection, Window window, Time time)
{
	owned = selection;
	owner = window;
	return 1;
}

int
XConvertSelection(Display *display, Atom selection, Atom target,
	Atom property, Window window, Time time)
{
	converted = selection;
	assert(window == xw.win && target == xsel.xtarget);
	return 1;
}

Bool
XftColorAllocName(Display *display, const Visual *visual, Colormap colormap,
	const char *name, XftColor *color)
{
	assert(!strcmp(name, "#112233"));
	color->pixel = 0x112233;
	color->color = (XRenderColor){ 0x1111, 0x2222, 0x3333, 0xffff };
	return True;
}

void
XftColorFree(Display *display, Visual *visual, Colormap colormap,
	XftColor *color)
{
}

static void
testalpha(void)
{
	const char *invalid[] = {
		"", "nan", "inf", "-0.1", "1.1", "oops", "0.5x", "1e99"
	};
	Color color = {0};
	Color palette[300] = {0};
	float original = alpha;
	size_t i;
	pid_t child;
	int status;

	assert(parsealpha("0") == 0 && parsealpha("1") == 1);
	assert(fabsf(parsealpha("0.9") - 0.9f) < 0.000001f);
	for (i = 0; i < LEN(invalid); i++) {
		child = fork();
		assert(child >= 0);
		if (child == 0) {
			close(STDERR_FILENO);
			parsealpha(invalid[i]);
			_exit(0);
		}
		assert(waitpid(child, &status, 0) == child);
		assert(WIFEXITED(status) && WEXITSTATUS(status) == 1);
	}
	xw.depth = 32;
	alpha = 0.5;
	color.pixel = 0x112233;
	xsetalpha(&color);
	assert(color.color.alpha == 32767);
	assert(color.pixel == 0x7f112233UL);
	alpha = 1;
	xsetalpha(&color);
	assert(color.color.alpha == 65535 && color.pixel == 0xff112233UL);
	alpha = 0;
	xsetalpha(&color);
	assert(!color.color.alpha && color.pixel == 0x112233UL);
	xw.depth = 24;
	alpha = 0.5;
	xsetalpha(&color);
	assert(color.color.alpha == 65535 && color.pixel == 0x112233UL);
	xw.depth = 32;
	dc.col = palette;
	dc.collen = LEN(palette);
	assert(xsetcolorname(defaultbg, "#112233") == 0);
	assert(palette[defaultbg].color.alpha == 32767);
	assert(xsetcolorname(defaultfg, "#112233") == 0);
	assert(palette[defaultfg].color.alpha == 65535);
	assert(xsetcolorname(-1, "#112233") == 1);
	assert(xsetcolorname(300, "#112233") == 1);
	dc.col = NULL;
	dc.collen = 0;
	alpha = original;
}

static Shortcut *
shortcut(KeySym key, uint mask)
{
	size_t i;

	for (i = 0; i < LEN(shortcuts); i++)
		if (shortcuts[i].keysym == key && shortcuts[i].mod == mask)
			return &shortcuts[i];
	return NULL;
}

static void
testprofile(void)
{
	const char *palette[] = {
		"#2d2d2d", "#f2777a", "#99cc99", "#ffcc66",
		"#6699cc", "#cc99cc", "#66cccc", "#cccccc",
		"#999999", "#f2777a", "#99cc99", "#ffcc66",
		"#6699cc", "#cc99cc", "#66cccc", "#ffffff"
	};
	FcPattern *pattern;
	FcChar8 *family;
	double size;
	size_t i;

	assert(!borderpx && cursorstyle == 1 && blinktimeout);
	assert(fabsf(alpha - 0.9f) < 0.000001f);
	assert(!strcmp(termname, "st-256color") && !allowwindowops);
	for (i = 0; i < LEN(palette); i++)
		assert(!strcmp(colorname[i], palette[i]));
	assert(!strcmp(colorname[defaultbg], "#2d2d2d"));
	assert(!strcmp(colorname[defaultfg], "#cccccc"));
	assert(!strcmp(colorname[defaultcs], "#cccccc"));
	assert(shortcut(XK_Insert, ControlMask)->func == clipcopy);
	assert(shortcut(XK_C, TERMMOD)->func == clipcopy);
	assert(shortcut(XK_V, TERMMOD)->func == clippaste);
	assert(shortcut(XK_Insert, ShiftMask)->func == selpaste);
	assert(shortcut(XK_equal, ControlMask)->func == zoom);
	assert(shortcut(XK_minus, ControlMask)->arg.f == -1);
	assert(shortcut(XK_0, ControlMask)->func == zoomreset);
	assert(shortcut(XK_Prior, ShiftMask)->func == kscrollup);
	assert(shortcut(XK_Next, ShiftMask)->func == kscrolldown);
	assert(mshortcuts[1].func == mousescroll && mshortcuts[1].arg.i == 3);
	assert(mshortcuts[2].func == mousescroll && mshortcuts[2].arg.i == -3);

	/* Parse a supplied pattern; do not discover or load real fonts. */
	pattern = FcNameParse((const FcChar8 *)font);
	assert(pattern);
	assert(FcPatternGetString(pattern, FC_FAMILY, 0, &family)
		== FcResultMatch);
	assert(!strcmp((const char *)family, "Hack Nerd Font Mono"));
	assert(FcPatternGetString(pattern, FC_FAMILY, 1, &family)
		== FcResultMatch);
	assert(!strcmp((const char *)family, "Noto Color Emoji"));
	assert(FcPatternGetDouble(pattern, FC_SIZE, 0, &size) == FcResultMatch);
	assert(size == 11);
	FcPatternDestroy(pattern);
}

static void
testcursor(void)
{
	int blinking[] = { 1, 1, 0, 1, 0, 1, 0, 1, 0 };
	int i;

	for (i = 0; i < LEN(blinking); i++) {
		assert(xsetcursor(i) == 0);
		assert(win.cursor == i && cursorblinks == blinking[i]);
	}
	assert(xsetcursor(-1) == 1 && win.cursor == 8);
	assert(xsetcursor(9) == 1 && win.cursor == 8);
}

static void
testhints(void)
{
	win.w = 803;
	win.h = 407;
	win.cw = 8;
	win.ch = 16;
	xw.isfixed = 0;
	xhints();
	assert(hints.width_inc == 1 && hints.height_inc == 1);
	assert(hints.min_width == win.cw + 2 * borderpx);
	assert(hints.min_height == win.ch + 2 * borderpx);
	assert(hints.base_width == 2 * borderpx);
	assert(hints.base_height == 2 * borderpx);
	xw.isfixed = 1;
	xhints();
	assert(hints.flags & PMaxSize);
	assert(hints.min_width == 803 && hints.max_width == 803);
	assert(hints.min_height == 407 && hints.max_height == 407);
}

static void
testclipboard(void)
{
	xw.win = 10;
	xsel.xtarget = 43;
	xsel.primary = "synthetic clipboard: espa\303\261ol \360\237\230\200";
	clipcopy(NULL);
	assert(xsel.clipboard != xsel.primary);
	assert(!strcmp(xsel.clipboard, xsel.primary));
	assert(owned == 42 && owner == xw.win);
	clippaste(NULL);
	assert(converted == 42);
	selpaste(NULL);
	assert(converted == XA_PRIMARY);
	xsel.primary = NULL;
	clipcopy(NULL);
	assert(!xsel.clipboard);
}

int
main(void)
{
	mousescroll(&(Arg){.i = 3});
	assert(up == 3 && !down && !sent);
	mousescroll(&(Arg){.i = -3});
	assert(down == 3);
	alt = 1;
	mousescroll(&(Arg){.i = 3});
	assert(sent == '\031');
	mousescroll(&(Arg){.i = -3});
	assert(sent == '\005');
	testprofile();
	testhints();
	testclipboard();
	testalpha();
	testcursor();
	puts("PASS: st profile, hints, clipboard, alpha and cursor (mock Xlib, UBSan)");
	return 0;
}
