/* Test the real dwm functions with synthetic clients and Xlib substitutes. */
#include <assert.h>

#define main dwm_main
#define drw_resize test_drw_resize
#include "dwm.c"
#undef main
#undef drw_resize

static Monitor monitor, other;
static Client first, second;
static Fnt testfont = { .h = 16 };
static Drw testdrw = { .fonts = &testfont };
static Clr testcolors[3];
static Clr *testscheme[] = { testcolors, testcolors };
static int deleteprotocol, closeevents, replayevents, configureevents;
static Window focused, raised, transient, mapped;
static Atom windowtype, initialstate;
static unsigned int lastborder;
static const char *setuppropertyvalue;
static int setuppropertyformat;
static Atom setuppropertytype;

int
XGetWindowProperty(Display *display, Window w, Atom property, long offset,
	long length, Bool del, Atom requested, Atom *actual, int *format,
	unsigned long *count, unsigned long *remaining, unsigned char **data)
{
	*data = NULL;
	*count = 0;
	*remaining = 0;
	if (w == root && property == windowsetupatom && setuppropertyvalue) {
		*count = strlen(setuppropertyvalue);
		*data = malloc(*count + 1);
		memcpy(*data, setuppropertyvalue, *count + 1);
		*actual = setuppropertytype;
		*format = setuppropertyformat;
	} else if ((property == netatom[NetWMWindowType] && windowtype)
	|| (property == netatom[NetWMState] && initialstate)) {
		*data = malloc(sizeof(long));
		*(long *)*data = property == netatom[NetWMWindowType] ? windowtype : initialstate;
		*format = 32;
		*count = 1;
	}
	return Success;
}

int
XSetWindowBorderWidth(Display *display, Window w, unsigned int width)
{
	lastborder = width;
	return 1;
}
static unsigned int ungrabs[64];

/* Never let a test open a real display, even if its environment is wrong. */
Display *
XOpenDisplay(const char *name)
{
	assert(!"tests must not open an X display");
	return NULL;
}

int
XMoveResizeWindow(Display *display, Window window, int x, int y,
	unsigned int width, unsigned int height)
{
	assert(width > 0 && height > 0);
	return 1;
}

int
XConfigureWindow(Display *display, Window window, unsigned int mask,
	XWindowChanges *changes)
{
	if (mask & CWWidth)
		assert(changes->width > 0);
	if (mask & CWHeight)
		assert(changes->height > 0);
	configureevents++;
	return 1;
}

Status
XSendEvent(Display *display, Window window, Bool propagate, long mask,
	XEvent *event)
{
	if (event->type == ClientMessage
	&& event->xclient.data.l[0] == wmatom[WMDelete]) {
		assert(event->xclient.message_type == wmatom[WMProtocols]);
		assert(event->xclient.format == 32);
		closeevents++;
	}
	return 1;
}

Status
XGetWMProtocols(Display *display, Window window, Atom **protocols, int *count)
{
	if (!deleteprotocol) {
		*count = 0;
		return 0;
	}
	*protocols = malloc(sizeof(Atom));
	assert(*protocols);
	(*protocols)[0] = wmatom[WMDelete];
	*count = 1;
	return 1;
}

int
XFree(void *data)
{
	free(data);
	return 1;
}

XWMHints *
XGetWMHints(Display *display, Window window)
{
	return NULL;
}

Status
XGetClassHint(Display *display, Window window, XClassHint *hint)
{
	return 0;
}

XModifierKeymap *
XGetModifierMapping(Display *display)
{
	return NULL;
}

int
XUngrabButton(Display *display, unsigned int button, unsigned int modifiers,
	Window window)
{
	assert(window < LENGTH(ungrabs));
	ungrabs[window]++;
	return 1;
}

int
XGrabButton(Display *display, unsigned int button, unsigned int modifiers,
	Window window, Bool owner, unsigned int mask, int pointermode,
	int keyboardmode, Window confine, Cursor pointer)
{
	return 1;
}

int
XSetWindowBorder(Display *display, Window window, unsigned long pixel)
{
	return 1;
}

int
XSetInputFocus(Display *display, Window window, int revert, Time time)
{
	focused = window;
	return 1;
}

int
XChangeProperty(Display *display, Window window, Atom property, Atom type,
	int format, int mode, const unsigned char *data, int count)
{
	return 1;
}

int
XDeleteProperty(Display *display, Window window, Atom property)
{
	return 1;
}

int
XRaiseWindow(Display *display, Window window)
{
	raised = window;
	return 1;
}

int
XMoveWindow(Display *display, Window window, int x, int y)
{
	return 1;
}

int
XSync(Display *display, Bool discard)
{
	return 1;
}

Bool
XCheckMaskEvent(Display *display, long mask, XEvent *event)
{
	return False;
}

int
XAllowEvents(Display *display, int mode, Time time)
{
	assert(mode == ReplayPointer);
	replayevents++;
	return 1;
}

int
XKillClient(Display *display, XID resource)
{
	assert(!"ordinary close must not kill an X client");
	return 0;
}

Status
XGetTransientForHint(Display *display, Window window, Window *parent)
{
	*parent = transient;
	return transient != None;
}

Status
XGetWMNormalHints(Display *display, Window window, XSizeHints *hints, long *supplied)
{
	return 0;
}

Status
XGetTextProperty(Display *display, Window window, XTextProperty *property, Atom atom)
{
	return 0;
}

int
XSelectInput(Display *display, Window window, long mask)
{
	return 1;
}

int
XMapWindow(Display *display, Window window)
{
	mapped = window;
	return 1;
}

void
test_drw_resize(Drw *drawing, unsigned int width, unsigned int height)
{
	assert(width && height);
}

Bool
XineramaIsActive(Display *display)
{
	return False;
}

Bool
XQueryPointer(Display *display, Window window, Window *rootwin, Window *child,
	int *rootx, int *rooty, int *x, int *y, unsigned int *mask)
{
	*rootwin = root;
	*child = None;
	*rootx = monitor.wx + 1;
	*rooty = monitor.wy + 1;
	*x = *y = 0;
	*mask = 0;
	return True;
}

static void
reset(void)
{
	int i;

	monitor = (Monitor){0};
	other = (Monitor){0};
	first = (Client){0};
	second = (Client){0};
	monitor.mx = monitor.wx = -1000;
	monitor.my = monitor.wy = 40;
	monitor.mw = monitor.ww = 1001;
	monitor.mh = monitor.wh = 799;
	monitor.tagset[0] = monitor.tagset[1] = 1;
	monitor.lt[0] = monitor.lt[1] = &layouts[0];
	first.x = -900;
	first.y = 100;
	first.w = 601;
	first.h = 401;
	first.bw = 1;
	first.hintsvalid = first.isfloating = 1;
	first.tags = 1;
	first.win = 10;
	first.mon = &monitor;
	monitor.sel = monitor.clients = monitor.stack = &first;
	mons = selmon = &monitor;
	drw = &testdrw;
	scheme = testscheme;
	dpy = NULL;
	root = 1;
	bh = 18;
	sw = 4000;
	sh = 2400;
	deleteprotocol = closeevents = replayevents = configureevents = 0;
	focused = raised = windowtype = transient = mapped = initialstate = None;
	lastborder = 99;
	windowsetupatom = 300;
	windowsetup[0] = '\0';
	setuppending = 0;
	setuppropertyvalue = NULL;
	setuppropertyformat = 8;
	setuppropertytype = XA_STRING;
	memset(ungrabs, 0, sizeof ungrabs);
	for (i = 0; i < NetLast; i++)
		netatom[i] = 100 + i;
	for (i = 0; i < WMLast; i++)
		wmatom[i] = 200 + i;
}

static void
expectgeom(int x, int y, int w, int h)
{
	assert(first.x == x && first.y == y);
	assert(first.w == w && first.h == h);
}

static void
snapto(unsigned int direction)
{
	Arg arg = { .ui = direction };

	snapclient(&arg);
}

static void
testconfig(void)
{
	size_t i, j;
	Monitor *m;

	reset();
	assert(LENGTH(tags) == 1 && MODKEY == Mod4Mask);
	assert(!showbar && !topbar && !layouts[0].arrange);
	assert(strstr(fonts[1], "Noto Color Emoji"));
	assert(!strcmp(dmenucmd[0], "wm-launcher"));
	assert(!strcmp(dmenucmd[1], "-m") && dmenucmd[2] == dmenumon);
	applyrules(&first);
	assert(first.isfloating && first.tags == 1);
	m = createmon();
	assert(m->tagset[0] == 1 && m->tagset[1] == 1);
	assert(!m->lt[0]->arrange && !m->showbar);
	free(m);
	for (i = 0; i < LENGTH(keys); i++)
		for (j = i + 1; j < LENGTH(keys); j++)
			assert(keys[i].mod != keys[j].mod
				|| keys[i].keysym != keys[j].keysym);
}

static void
testplacement(void)
{
	unsigned int horizontal[] = { PlaceLeft, PlaceRight };
	unsigned int vertical[] = { PlaceTop, PlaceBottom };
	size_t i, j;

	for (i = 0; i < LENGTH(horizontal); i++)
		for (j = 0; j < LENGTH(vertical); j++) {
			reset();
			snapto(horizontal[i]);
			expectgeom(i ? -500 : -1000, 40, i ? 499 : 498, 797);
			snapto(vertical[j]);
			expectgeom(i ? -500 : -1000, j ? 439 : 40,
				i ? 499 : 498, j ? 398 : 397);
			snapto(horizontal[i]);
			expectgeom(-1000, j ? 439 : 40, 999, j ? 398 : 397);
			snapto(vertical[j]);
			expectgeom(-900, 100, 601, 401);
			assert(!first.placement);
		}
	reset();
	snapto(PlaceTop);
	snapto(PlaceLeft);
	expectgeom(-1000, 40, 498, 397);
	snapto(PlaceRight);
	expectgeom(-500, 40, 499, 397);
	snapto(PlaceBottom);
	expectgeom(-500, 439, 499, 398);
	snapto(PlaceRight);
	snapto(PlaceBottom);
	expectgeom(-900, 100, 601, 401);
	snapto(0);
	expectgeom(-900, 100, 601, 401);
}

static void
testmaximize(void)
{
	reset();
	togglemaximize(NULL);
	assert(first.placement == PlaceMax && !first.isfullscreen);
	expectgeom(-1000, 40, 999, 797);
	togglemaximize(NULL);
	expectgeom(-900, 100, 601, 401);
	snapto(PlaceLeft);
	togglemaximize(NULL);
	togglemaximize(NULL);
	assert(first.placement == PlaceLeft);
	expectgeom(-1000, 40, 498, 797);
	snapto(PlaceLeft);
	expectgeom(-900, 100, 601, 401);
	togglemaximize(NULL);
	snapto(PlaceBottom);
	expectgeom(-1000, 439, 999, 398);
	snapto(PlaceBottom);
	expectgeom(-900, 100, 601, 401);
}

static void
testlimits(void)
{
	reset();
	first.isfixed = 1;
	snapto(PlaceLeft);
	togglemaximize(NULL);
	expectgeom(-900, 100, 601, 401);
	assert(!first.placement);
	reset();
	monitor.ww = 2;
	snapto(PlaceLeft);
	assert(!first.placement && !configureevents);
	reset();
	first.minw = 550;
	snapto(PlaceLeft);
	assert(first.w == 550);
	reset();
	snapto(PlaceRight);
	monitor.ww = 400;
	monitor.wh = 300;
	snapto(PlaceRight);
	expectgeom(-1000, 40, 398, 298);
	monitor.sel = NULL;
	snapto(PlaceLeft);
	togglemaximize(NULL);
	togglefullscreen(NULL);
	centerclient(NULL);
	killclient(NULL);
}

static void
testfullscreen(void)
{
	reset();
	snapto(PlaceLeft);
	togglefullscreen(NULL);
	assert(first.isfullscreen && first.bw == 0);
	expectgeom(-1000, 40, 1001, 799);
	/* Screen changes must not overwrite the pre-fullscreen geometry. */
	resizeclient(&first, -1000, 40, 1200, 850);
	snapto(PlaceRight);
	togglemaximize(NULL);
	centerclient(NULL);
	expectgeom(-1000, 40, 1200, 850);
	togglefullscreen(NULL);
	assert(!first.isfullscreen && first.bw == 1);
	expectgeom(-1000, 40, 498, 797);
	snapto(PlaceLeft);
	expectgeom(-900, 100, 601, 401);
	centerclient(NULL);
	expectgeom(-801, 238, 601, 401);
	snapto(PlaceBottom);
	centerclient(NULL);
	expectgeom(-801, 238, 601, 401);
	assert(!first.placement);
}

static void
testclose(void)
{
	reset();
	killclient(NULL);
	assert(!closeevents);
	deleteprotocol = 1;
	killclient(NULL);
	assert(closeevents == 1);
	monitor.sel = NULL;
	killclient(NULL);
	assert(closeevents == 1);
}

static void
testfocus(void)
{
	XEvent event = {0};

	reset();
	second = first;
	second.win = 20;
	first.next = first.snext = &second;
	monitor.next = &other;
	other.mx = other.wx = 1;
	other.mw = other.ww = 1000;
	other.mh = other.wh = 800;
	event.xcrossing.window = second.win;
	event.xcrossing.mode = NotifyGrab;
	enternotify(&event);
	assert(monitor.sel == &first && selmon == &monitor);
	event.xcrossing.mode = NotifyNormal;
	event.xcrossing.detail = NotifyInferior;
	enternotify(&event);
	assert(monitor.sel == &first && selmon == &monitor);
	event.xcrossing.detail = NotifyNonlinear;
	enternotify(&event);
	assert(monitor.sel == &second && focused == second.win);
	assert(raised == None);
	focus(&first);
	second.isdock = 1;
	enternotify(&event);
	assert(monitor.sel == &first && focused == first.win);
	second.isdock = 0;
	event.xmotion.window = root;
	event.xmotion.x_root = 100;
	event.xmotion.y_root = 100;
	motionnotify(&event);
	assert(selmon == &other && focused == root);
	event.xmotion.window = first.win;
	event.xmotion.x_root = -500;
	motionnotify(&event);
	assert(selmon == &other);
	event.xcrossing.window = root;
	event.xcrossing.mode = NotifyNormal;
	event.xcrossing.x_root = -500;
	event.xcrossing.y_root = 100;
	enternotify(&event);
	assert(selmon == &monitor && monitor.sel == &first);
	expectgeom(-900, 100, 601, 401);
	event.xbutton.window = second.win;
	event.xbutton.button = Button1;
	buttonpress(&event);
	assert(monitor.sel == &second && focused == second.win);
	assert(replayevents == 1 && raised == second.win);
	focus(&first);
	assert(monitor.sel == &first);
	event.xclient.window = second.win;
	event.xclient.message_type = netatom[NetActiveWindow];
	clientmessage(&event);
	assert(monitor.sel == &second && focused == second.win);
	assert(raised == second.win);
	event.xclient.window = 999;
	clientmessage(&event);
	assert(monitor.sel == &second);
}

static void
testcrossfocus(void)
{
	Client third;
	XEvent event = {0};

	reset();
	other = monitor;
	other.sel = other.clients = other.stack = &second;
	monitor.next = &other;
	second = first;
	second.win = 20;
	second.mon = &other;
	third = second;
	third.win = 30;
	second.next = second.snext = &third;
	event.xclient.window = third.win;
	event.xclient.message_type = netatom[NetActiveWindow];
	clientmessage(&event);
	assert(selmon == &other && other.sel == &third);
	assert(ungrabs[first.win] && ungrabs[second.win]);
	assert(ungrabs[third.win] && focused == third.win);
	event.xcrossing.window = first.win;
	event.xcrossing.mode = NotifyNormal;
	event.xcrossing.detail = NotifyNonlinear;
	enternotify(&event);
	assert(selmon == &monitor && monitor.sel == &first && focused == first.win);
	second.isdock = 1;
	event.xcrossing.window = second.win;
	enternotify(&event);
	assert(selmon == &other && other.sel == &third && focused == third.win);
	expectgeom(-900, 100, 601, 401);
}

static void
testmonitors(void)
{
	Arg arg = { .i = 1 };
	XEvent event = {0};

	reset();
	other = monitor;
	other.mx = other.wx = 1;
	other.my = other.wy = 0;
	other.sel = other.clients = other.stack = NULL;
	monitor.next = &other;
	snapto(PlaceLeft);
	togglemaximize(NULL);
	tagmon(&arg);
	assert(selmon == &other && first.mon == &other);
	assert(other.sel == &first && focused == first.win);
	assert(!monitor.clients && !monitor.stack);
	assert(first.restoreplacement == PlaceLeft);
	togglemaximize(NULL);
	expectgeom(1, 0, 498, 797);
	snapto(PlaceLeft);
	expectgeom(101, 60, 601, 401);
	tagmon(&arg);
	assert(selmon == &monitor && first.mon == &monitor);
	expectgeom(-900, 100, 601, 401);
	second = first;
	second.win = 20;
	second.mon = &other;
	other.sel = other.clients = other.stack = &second;
	event.xclient.window = second.win;
	event.xclient.message_type = netatom[NetActiveWindow];
	clientmessage(&event);
	assert(selmon == &other && other.sel == &second);
	assert(focused == second.win && raised == second.win);

	reset();
	other = monitor;
	other.mx = other.wx = 1;
	other.my = other.wy = 0;
	other.mw = other.ww = 801;
	other.mh = other.wh = 601;
	other.sel = other.clients = other.stack = NULL;
	monitor.next = &other;
	snapto(PlaceLeft);
	togglefullscreen(NULL);
	tagmon(&arg);
	assert(first.isfullscreen && first.mon == &other);
	expectgeom(1, 0, 801, 601);
	togglefullscreen(NULL);
	expectgeom(1, 0, 398, 599);
	snapto(PlaceLeft);
	expectgeom(101, 60, 601, 401);
}

static void
testdock(void)
{
	XEvent event = {0};
	Arg next = {.i = 1};

	reset();
	second = first;
	second.win = 20;
	second.next = second.snext = &first;
	monitor.clients = monitor.stack = &second;
	windowtype = netatom[NetWMWindowTypeDock];
	updatewindowtype(&second);
	assert(second.isdock && second.isfloating && !second.bw && !lastborder);
	focus(&second);
	assert(monitor.sel == &first);
	focus(NULL);
	assert(monitor.sel == &first);
	focusstack(&next);
	assert(monitor.sel == &first && raised == second.win);
	first.isfullscreen = 1;
	restack(&monitor);
	assert(raised == first.win);
	event.xconfigurerequest.window = second.win;
	event.xconfigurerequest.value_mask = CWX|CWY|CWWidth|CWHeight|CWBorderWidth;
	event.xconfigurerequest.x = -900;
	event.xconfigurerequest.y = 800;
	event.xconfigurerequest.width = 50;
	event.xconfigurerequest.height = 24;
	event.xconfigurerequest.border_width = 10;
	configurerequest(&event);
	assert(second.x == -900 && second.y == 800);
	assert(second.w == 50 && second.h == 24 && !second.bw);
}

static void
testinitialcenter(void)
{
	XWindowAttributes attributes = { .x = -910, .y = 70, .width = 200, .height = 100 };
	Client *client;
	int x, y, mode;

	reset();
	manage(30, &attributes);
	client = monitor.clients;
	assert(client != &first && client->win == mapped && mapped == 30);
	assert(client->x == -601 && client->y == 388);
	assert(client->oldx == client->x && client->oldy == client->y);
	assert(client->w == 200 && client->h == 100);
	free(client);

	reset();
	other = monitor;
	other.wx = other.mx = 2000;
	other.wy = other.my = -100;
	other.clients = other.stack = other.sel = NULL;
	monitor.next = &other;
	selmon = &other;
	transient = first.win;
	manage(30, &attributes);
	client = monitor.clients;
	assert(client->mon == &monitor && client->x == -601 && client->y == 388);
	free(client);
	monitor.clients = monitor.stack = monitor.sel = &first;
	transient = None;
	manage(31, &attributes);
	client = other.clients;
	assert(client->mon == &other && client->x == 2399 && client->y == 248);
	free(client);

	reset();
	first.w = monitor.ww + 100;
	first.h = monitor.wh + 100;
	centerfloating(&first);
	assert(first.x == monitor.wx && first.y == monitor.wy);
	for (mode = 0; mode < 3; mode++) {
		reset();
		x = first.x;
		y = first.y;
		first.isfloating = mode != 0;
		first.isdock = mode == 1;
		first.isfullscreen = mode == 2;
		centerfloating(&first);
		assert(first.x == x && first.y == y);
	}

	reset();
	windowtype = netatom[NetWMWindowTypeDock];
	manage(30, &attributes);
	client = monitor.clients;
	assert(client->isdock && client->x == attributes.x && client->y == attributes.y);
	free(client);

	reset();
	initialstate = netatom[NetWMFullscreen];
	manage(30, &attributes);
	client = monitor.clients;
	assert(client->isfullscreen && client->x == monitor.mx && client->y == monitor.my);
	assert(client->oldx == attributes.x && client->oldy == attributes.y);
	free(client);
}

static void
setupproperty(const char *value)
{
	XEvent event = {0};

	setuppropertyvalue = value;
	event.xproperty.window = root;
	event.xproperty.atom = windowsetupatom;
	event.xproperty.state = PropertyNewValue;
	propertynotify(&event);
	setuppropertyvalue = NULL;
}

static void
readysetup(unsigned int setup)
{
	char key[SetupLength + 1];

	snprintf(key, sizeof key, "%064x", setup);
	setupproperty(key);
}

static void
testwindowsetups(void)
{
	XEvent event = {0};
	SavedGeometry geometry;
	Client *fresh;
	char original[SetupLength + 1];
	unsigned int i;
	int configured;

	reset();
	beginwindowsetup();
	assert(!first.geometrycount);
	readysetup(1);
	assert(!setuppending && !first.geometrycount);
	monitor.clients = monitor.stack = monitor.sel = NULL;
	readysetup(2);
	assert(!setuppending);
	reset();
	readysetup(1);
	resizeclient(&first, -880, 110, 500, 300);
	setupproperty("pending");
	assert(setuppending && first.geometrycount == 1);
	resizeclient(&first, -970, 80, 250, 180);
	setupproperty("pending");
	assert(first.geometrycount == 1 && first.geometry[0].w == 500);
	readysetup(2);
	expectgeom(-970, 80, 250, 180);
	resizeclient(&first, -800, 200, 400, 250);
	setupproperty("pending");
	resizeclient(&first, -950, 60, 200, 100);
	readysetup(1);
	expectgeom(-880, 110, 500, 300);
	assert(!setuppending && focused == first.win && raised == None);
	resizeclient(&first, -850, 120, 420, 260);
	configured = configureevents;
	readysetup(1);
	expectgeom(-850, 120, 420, 260);
	assert(configureevents == configured);

	/* Root resize captures BEFORE any automatic geometry changes. */
	monitor.barwin = 2;
	event.xconfigure.window = root;
	event.xconfigure.width = 800;
	event.xconfigure.height = 600;
	configurenotify(&event);
	assert(setuppending && first.geometry[0].w == 420);
	resizeclient(&first, -980, 45, 100, 100);
	configurenotify(&event);
	assert(first.geometry[0].w == 420);
	readysetup(1);
	expectgeom(-850, 120, 420, 260);
	configurenotify(&event);
	assert(!setuppending);

	/* Same-class windows remain independent; new/recycled XIDs inherit nothing. */
	reset();
	readysetup(1);
	setupproperty("pending");
	fresh = ecalloc(1, sizeof *fresh);
	fresh->win = 20;
	fresh->x = -940; fresh->y = 80; fresh->w = 200; fresh->h = 100;
	fresh->isfloating = fresh->hintsvalid = 1;
	fresh->tags = 1; fresh->bw = 1; fresh->mon = &monitor;
	attach(fresh); attachstack(fresh);
	readysetup(2);
	readysetup(1);
	assert(fresh->x == -940 && fresh->w == 200 && fresh->geometrycount == 1);
	unmanage(fresh, 1);
	fresh = ecalloc(1, sizeof *fresh);
	assert(!fresh->geometrycount);
	free(fresh);

	reset();
	other = monitor;
	other.num = 1;
	other.mx = other.wx = 1;
	other.my = other.wy = 0;
	other.clients = other.stack = other.sel = &second;
	monitor.next = &other;
	second = first;
	second.win = 20; second.mon = &other; second.x = 100; second.y = 60;
	readysetup(1);
	setupproperty("pending");
	detach(&second); detachstack(&second);
	other.sel = NULL;
	second.mon = &monitor;
	attach(&second); attachstack(&second);
	monitor.next = NULL;
	readysetup(2);
	setupproperty("pending");
	monitor.next = &other;
	readysetup(1);
	assert(second.mon == &other && second.x == 100 && second.y == 60);
	assert(selmon == &monitor && monitor.sel == &first && focused == first.win);

	reset();
	readysetup(1);
	snapto(PlaceLeft);
	setfullscreen(&first, 1);
	setupproperty("pending");
	readysetup(2);
	setupproperty("pending");
	readysetup(1);
	assert(first.isfullscreen && first.placement == PlaceLeft);
	setfullscreen(&first, 0);
	snapto(PlaceLeft);
	expectgeom(-900, 100, 601, 401);
	reset();
	readysetup(1);
	togglemaximize(NULL);
	setupproperty("pending"); readysetup(2);
	setupproperty("pending"); readysetup(1);
	assert(first.placement == PlaceMax);
	togglemaximize(NULL);
	expectgeom(-900, 100, 601, 401);

	reset();
	readysetup(1);
	setfullscreen(&first, 1);
	setupproperty("pending"); readysetup(2);
	setupproperty("pending"); readysetup(1);
	assert(first.isfullscreen && first.fullw == 601 && first.fullh == 401);
	setfullscreen(&first, 0);
	expectgeom(-900, 100, 601, 401);

	reset();
	geometry = (SavedGeometry){ .monitor = 99, .x = 99999, .y = -99, .w = 99999, .h = 99999 };
	restoregeometry(&first, &geometry);
	assert(first.mon == &monitor && first.x == monitor.wx && first.y == monitor.wy);
	assert(first.w <= monitor.ww && first.h <= monitor.wh);
	reset();
	readysetup(1); setupproperty("pending");
	first.isdock = 1;
	readysetup(2);
	resizeclient(&first, -940, 70, 220, 120);
	setupproperty("pending"); readysetup(1);
	expectgeom(-940, 70, 220, 120);
	assert(first.geometrycount == 1);
	reset();
	first.isdock = 1;
	readysetup(1); setupproperty("pending");
	assert(!first.geometrycount);
	reset();
	first.isfloating = 0;
	readysetup(1); setupproperty("pending");
	assert(!first.geometrycount);

	reset();
	readysetup(1);
	memcpy(original, windowsetup, sizeof original);
	setupproperty("invalid");
	assert(!strcmp(windowsetup, original) && !setuppending);
	setuppropertyformat = 32;
	readysetup(2);
	assert(!strcmp(windowsetup, original));
	setuppropertyformat = 8;
	setuppropertytype = XA_ATOM;
	readysetup(2);
	assert(!strcmp(windowsetup, original));
	setuppropertytype = XA_STRING;
	setupproperty("pending");
	setupproperty("fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffZ");
	assert(setuppending && !strcmp(windowsetup, original));
	readysetup(1);
	for (i = 2; i < SavedSetups + 5; i++)
		readysetup(i);
	assert(first.geometrycount == SavedSetups);
	for (i = 0; i < first.geometrycount; i++)
		assert(strcmp(first.geometry[i].setup, original));
}

static void
testspawn(void)
{
	const char *command[] = { "synthetic", "with spaces", "$(never-run);secret=value", NULL };
	Arg arg = { .v = command };
	const char *bin = getenv("WM_SPAWN_BIN"), *log = getenv("WM_SPAWN_LOG");
	char active[1024], disabled[1024], buffer[1024];
	char *path;
	FILE *file;
	int status;
	size_t length;

	assert(bin && log);
	path = strdup(getenv("PATH"));
	assert(path && setenv("PATH", bin, 1) == 0);
	reset();
	spawn(&arg);
	assert(waitpid(-1, &status, 0) > 0 && WIFEXITED(status) && !WEXITSTATUS(status));
	file = fopen(log, "r");
	assert(file);
	length = fread(buffer, 1, sizeof buffer - 1, file);
	buffer[length] = '\0';
	fclose(file);
	assert(!strcmp(buffer, "--\nsynthetic\nwith spaces\n$(never-run);secret=value\n"));
	snprintf(active, sizeof active, "%s/wm-run", bin);
	snprintf(disabled, sizeof disabled, "%s/disabled", bin);
	assert(rename(active, disabled) == 0);
	spawn(&arg);
	assert(waitpid(-1, &status, 0) > 0 && WIFEXITED(status) && !WEXITSTATUS(status));
	file = fopen(log, "r");
	assert(file);
	length = fread(buffer, 1, sizeof buffer - 1, file);
	buffer[length] = '\0';
	fclose(file);
	assert(strstr(buffer, "-center\n-timeout\n15\nwm:"));
	assert(rename(disabled, active) == 0);
	assert(setenv("PATH", path, 1) == 0);
	free(path);
}

int
main(void)
{
	testconfig();
	testplacement();
	testmaximize();
	testlimits();
	testfullscreen();
	testclose();
	testfocus();
	testcrossfocus();
	testmonitors();
	testdock();
	testinitialcenter();
	testspawn();
	testwindowsetups();
	puts("PASS: dwm geometry, initial centering, pointer focus, close, spawn and setup history (mock Xlib, ASan/UBSan)");
	return 0;
}
