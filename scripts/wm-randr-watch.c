/* Subscribe to RandR changes; the external display manager owns all policy. */
#include <stdio.h>
#include <X11/Xlib.h>
#include <X11/extensions/Xrandr.h>

static int
changed(int type, int base)
{
	return type == base + RRScreenChangeNotify || type == base + RRNotify;
}

int
main(void)
{
	Display *display;
	XEvent event;
	int base, error;

	if (!(display = XOpenDisplay(NULL))) {
		fputs("wm-randr-watch: cannot open display\n", stderr);
		return 1;
	}
	if (!XRRQueryExtension(display, &base, &error)) {
		fputs("wm-randr-watch: RandR unavailable\n", stderr);
		XCloseDisplay(display);
		return 1;
	}
	XRRSelectInput(display, DefaultRootWindow(display), RRScreenChangeNotifyMask
		| RROutputChangeNotifyMask | RRCrtcChangeNotifyMask | RRResourceChangeNotifyMask);
	XFlush(display);
	puts("change");
	fflush(stdout);
	while (!XNextEvent(display, &event))
		if (changed(event.type, base)) {
			puts("change");
			if (fflush(stdout) == EOF)
				break;
		}
	XCloseDisplay(display);
	return 1;
}
