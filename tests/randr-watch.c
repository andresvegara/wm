/* Real event helper against synthetic Xlib/RandR calls, never an X server. */
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
int record_change(const char *text);
#define main watcher_main
#define puts record_change
#include "../scripts/wm-randr-watch.c"
#undef main
#undef puts

static Display *fake;
static int available, extension, closes, changes, position;

Display *
XOpenDisplay(const char *name)
{
	assert(name == NULL);
	return available ? fake : NULL;
}

Bool
XRRQueryExtension(Display *display, int *event, int *error)
{
	assert(display == fake);
	*event = 70;
	*error = 80;
	return extension;
}

void
XRRSelectInput(Display *display, Window root, int mask)
{
	assert(display == fake && root == 0);
	assert(mask == (RRScreenChangeNotifyMask | RROutputChangeNotifyMask
		| RRCrtcChangeNotifyMask | RRResourceChangeNotifyMask));
}

int
XFlush(Display *display)
{
	assert(display == fake);
	return 1;
}

int
XNextEvent(Display *display, XEvent *event)
{
	int types[] = {KeyPress, 70 + RRNotify, 70 + RRScreenChangeNotify};

	assert(display == fake);
	if (position == 3)
		return 1;
	event->type = types[position++];
	return 0;
}

int
XCloseDisplay(Display *display)
{
	assert(display == fake);
	closes++;
	return 1;
}

int
record_change(const char *text)
{
	assert(!strcmp(text, "change"));
	changes++;
	return 0;
}

int
main(void)
{
	_XPrivDisplay storage = calloc(1, sizeof *storage);
	Screen screen = {0};

	assert(storage);
	storage->screens = &screen;
	fake = (Display *)storage;
	assert(!changed(KeyPress, 70) && changed(70 + RRNotify, 70));
	assert(watcher_main() == 1 && !closes);
	available = 1;
	assert(watcher_main() == 1 && closes == 1 && !changes);
	extension = 1;
	assert(watcher_main() == 1 && closes == 2 && changes == 3);
	free(storage);
	puts("PASS: real RandR helper subscription, filtering, initial event and failure cleanup (mock Xlib)");
	return 0;
}
