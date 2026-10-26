/* Test the real dwm functions with synthetic clients and Xlib substitutes. */
#include <assert.h>

#define main dwm_main
#define drw_resize test_drw_resize
#define drw_setscheme test_drw_setscheme
#define drw_fontset_getwidth test_drw_fontset_getwidth
#define drw_rect test_drw_rect
#define drw_text test_drw_text
#define drw_map test_drw_map
#include "dwm.c"
#undef main
#undef drw_resize
#undef drw_setscheme
#undef drw_fontset_getwidth
#undef drw_rect
#undef drw_text
#undef drw_map

static Monitor monitor, other;
static Client first, second;
static Fnt testfont = { .h = 16 };
static Cur testcursor;
static Drw testdrw = { .fonts = &testfont };
static Clr testcolors[3];
static Clr *testscheme[] = { testcolors, testcolors };
static Clr testgradient[24];
static int deleteprotocol, closeevents, replayevents, configureevents;
static Window focused, raised, transient, mapped;
static Atom windowtype, initialstate;
static Atom savedstates[128][16];
static unsigned int statecounts[128];
static int clientdecoration, stateformat = 32;
static unsigned long stateextra;
static XWindowChanges clientpositions[128];
static unsigned int lastborder;
static const char *setuppropertyvalue;
static int setuppropertyformat;
static Atom setuppropertytype;

#include "dwm-tray.c"

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
	} else if (property == xembedinfo && embedpresent) {
		*data = calloc(2, sizeof(long));
		((long *)*data)[1] = embedflags;
		*actual = embedtype ? embedtype : xembedinfo;
		*format = embedformat;
		*count = embedcount;
	} else if (property == motifatom && clientdecoration == 1) {
		*data = calloc(5, sizeof(long));
		((long *)*data)[0] = 2;
		*actual = motifatom;
		*format = 32;
		*count = 5;
	} else if (property == csdatom && clientdecoration == 2) {
		*data = calloc(4, sizeof(long));
		*actual = XA_CARDINAL;
		*format = 32;
		*count = 4;
	} else if (property == netatom[NetWMState] && w < LENGTH(statecounts) && statecounts[w]) {
		*count = statecounts[w];
		*data = malloc(*count * sizeof(Atom));
		memcpy(*data, savedstates[w], *count * sizeof(Atom));
		*actual = XA_ATOM;
		*format = stateformat;
		*remaining = stateextra;
	} else if ((property == netatom[NetWMWindowType] && windowtype)
	|| (property == netatom[NetWMState] && initialstate)) {
		*data = malloc(sizeof(long));
		*(long *)*data = property == netatom[NetWMWindowType] ? windowtype : initialstate;
		*actual = XA_ATOM;
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
int
XSetClassHint(Display *display, Window window, XClassHint *hint)
{
	return 1;
}

static unsigned int ungrabs[64];
static unsigned int plainclickgrabs;
static int keyboardgrabfail, keyboardungrabs;
static KeySym testkey;
static char heldkeys[32];
static int pointergrabs, pointerungrabs, pointergrabfail, pointerok;
static int pointerx, pointery, pointerwarps;
static unsigned int pointermask;

int
XGrabPointer(Display *display, Window window, Bool owner, unsigned int mask,
	int pointermode, int keyboardmode, Window confine, Cursor cursor, Time time)
{
	pointergrabs++;
	return pointergrabfail ? AlreadyGrabbed : GrabSuccess;
}

int
XMaskEvent(Display *display, long mask, XEvent *event)
{
	assert(moveeventindex < moveeventcount);
	*event = moveevents[moveeventindex++];
	return 0;
}

int
XWarpPointer(Display *display, Window source, Window destination,
	int x, int y, unsigned int width, unsigned int height, int destx, int desty)
{
	pointerwarps++;
	return 1;
}

int
XUngrabPointer(Display *display, Time time)
{
	pointerungrabs++;
	return 1;
}

int
XGrabKeyboard(Display *display, Window win, Bool owner, int pointermode,
	int keyboardmode, Time time)
{
	return keyboardgrabfail ? AlreadyGrabbed : GrabSuccess;
}

int
XUngrabKeyboard(Display *display, Time time)
{
	keyboardungrabs++;
	return 1;
}

KeySym
XKeycodeToKeysym(Display *display, KeyCode code, int index)
{
	return testkey;
}

KeyCode
XKeysymToKeycode(Display *display, KeySym key)
{
	return key == XK_Alt_L ? 8 : 9;
}

int
XQueryKeymap(Display *display, char keys[32])
{
	memcpy(keys, heldkeys, 32);
	return 1;
}

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
	assert(window < LENGTH(traypositions));
	traypositions[window] = (XWindowChanges){.x = x, .y = y, .width = width, .height = height};
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
	assert(window < LENGTH(clientpositions));
	if (mask & CWX) clientpositions[window].x = changes->x;
	if (mask & CWY) clientpositions[window].y = changes->y;
	if (mask & CWWidth) clientpositions[window].width = changes->width;
	if (mask & CWHeight) clientpositions[window].height = changes->height;
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
	if (event->type == ClientMessage && event->xclient.message_type == xembed)
		embedmessages++;
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
	if (button == Button1 && !(modifiers & MODKEY)) {
		assert(pointermode == GrabModeSync);
		plainclickgrabs++;
	}
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
	if (property == netatom[NetWMState]) {
		assert(window < LENGTH(savedstates) && count <= 16 && type == XA_ATOM && format == 32);
		memcpy(savedstates[window], data, count * sizeof(Atom));
		statecounts[window] = count;
	}
	if (trayready && property == trayready) {
		assert(window == root && type == XA_CARDINAL && format == 32 && count == 2);
		memcpy(readyvalues, data, sizeof readyvalues);
	}
	return 1;
}

int
XDeleteProperty(Display *display, Window window, Atom property)
{
	if (trayready && property == trayready)
		memset(readyvalues, 0, sizeof readyvalues);
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
	assert(window < LENGTH(traymapped));
	traymapped[window] = 1;
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
	*rootx = pointerx;
	*rooty = pointery;
	*x = *y = 0;
	*mask = pointermask;
	return pointerok;
}

static void
reset(void)
{
	int i;

	assert(!trayicons && !traywin);
	statusmon = traymon = NULL;
	randractive = 0;
	embedpresent = embedflags = embedmessages = 0;
	embedformat = 32;
	embedcount = 2;
	embedtype = None;
	trayselection = None;
	memset(readyvalues, 0, sizeof readyvalues);
	failselection = 0;
	trayparents[50] = root;
	memset(traymapped, 0, sizeof traymapped);
	traymapped[10] = traymapped[20] = 1;
	memset(traysaved, 0, sizeof traysaved);
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
	th = 0;
	titlecolors[0] = titlecolors[1] = testcolors;
	titlegradient[0] = titlegradient[1] = testgradient;
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
	plainclickgrabs = 0;
	assert(!switchwin && !switchitems);
	keyboardgrabfail = keyboardungrabs = 0;
	memset(heldkeys, 0, sizeof heldkeys);
	focusserial = 0;
	focusedclient = None;
	clientdecoration = 0;
	stateformat = 32;
	stateextra = 0;
	assert(!movingwin);
	moveeventcount = moveeventindex = 0;
	putbackevents = pointergrabs = pointerungrabs = pointergrabfail = pointerwarps = 0;
	pointerok = True;
	pointerx = monitor.wx + 1;
	pointery = monitor.wy + 1;
	pointermask = Button1Mask;
	for (i = 0; i < CurLast; i++)
		cursor[i] = &testcursor;
	motifatom = 401;
	csdatom = 402;
	frameatom = 403;
	memset(savedstates, 0, sizeof savedstates);
	memset(statecounts, 0, sizeof statecounts);
	memset(clientpositions, 0, sizeof clientpositions);
	for (i = 0; i < NetLast; i++)
		netatom[i] = 100 + i;
	for (i = 0; i < WMLast; i++)
		wmatom[i] = 200 + i;
}

static void
expectgeom(int x, int y, int w, int h)
{
	if (first.x != x || first.y != y || first.w != w || first.h != h)
		fprintf(stderr, "geometry: got %d,%d %dx%d, expected %d,%d %dx%d\n",
			first.x, first.y, first.w, first.h, x, y, w, h);
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
	assert(showbar && !topbar && !layouts[0].arrange);
	assert(strstr(fonts[1], "Noto Color Emoji"));
	assert(!strcmp(dmenucmd[0], "wm-launcher"));
	assert(!strcmp(dmenucmd[1], "-m") && dmenucmd[2] == dmenumon);
	applyrules(&first);
	assert(first.isfloating && first.tags == 1);
	m = createmon();
	assert(m->tagset[0] == 1 && m->tagset[1] == 1);
	assert(!m->lt[0]->arrange && m->showbar);
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

static XEvent
dragrequest(void)
{
	XEvent event = {0};

	event.xclient.type = ClientMessage;
	event.xclient.window = first.win;
	event.xclient.message_type = netatom[NetWMMoveResize];
	event.xclient.format = 32;
	event.xclient.data.l[0] = pointerx = -800;
	event.xclient.data.l[1] = pointery = 120;
	event.xclient.data.l[2] = 8;
	event.xclient.data.l[3] = Button1;
	event.xclient.data.l[4] = 1;
	return event;
}

static void
dragmotion(int x, int y)
{
	moveeventcount = 2;
	moveevents[0] = (XEvent){0};
	moveevents[0].xmotion.type = MotionNotify;
	moveevents[0].xmotion.time = 100;
	moveevents[0].xmotion.x_root = x;
	moveevents[0].xmotion.y_root = y;
	moveevents[1] = (XEvent){0};
	moveevents[1].xbutton.type = ButtonRelease;
	moveevents[1].xbutton.button = Button1;
}

static void
testclientdrag(void)
{
	XEvent request;
	Client *allocated;
	int i, before;

	reset();
	request = dragrequest();
	pointerx += 50; /* The client can send its original press after some motion. */
	dragmotion(-700, 200);
	clientmessage(&request);
	expectgeom(-800, 180, 601, 401);
	assert(pointergrabs == 1 && pointerungrabs == 1 && !movingwin);
	assert(moveeventindex == 2 && focused == first.win);
	/* Super+drag shares movement and keeps root coordinates, including negatives. */
	reset();
	dragrequest();
	dragmotion(-700, 200);
	movemouse(NULL);
	expectgeom(-800, 180, 601, 401);
	assert(pointergrabs == 1 && pointerungrabs == 1);

	for (i = 0; i < 2; i++) {
		reset();
		togglemaximize(NULL);
		request = dragrequest();
		request.xclient.data.l[0] = pointerx = -500;
		request.xclient.data.l[1] = pointery = 60;
		dragmotion(-400, 140);
		if (i) movemouse(NULL); else clientmessage(&request);
		expectgeom(-701, 120, 601, 401);
		assert(!first.placement && !movingwin && pointerungrabs == 1);
	}
	reset();
	snapto(PlaceLeft);
	request = dragrequest();
	dragmotion(-700, 200);
	clientmessage(&request);
	assert(!first.placement && first.w == 601 && first.h == 401);
	reset();
	togglemaximize(NULL);
	request = dragrequest();
	dragmotion(pointerx, pointery);
	clientmessage(&request);
	assert(first.placement == PlaceMax); /* Click/no motion does not restore. */
	expectgeom(-1000, 40, 999, 797);

	for (i = 0; i < 17; i++) {
		reset();
		request = dragrequest();
		switch (i) {
		case 0: request.xclient.format = 8; break;
		case 1: request.xclient.data.l[2] = -1; break;
		case 2: request.xclient.data.l[2] = 9; break;
		case 3: request.xclient.data.l[2] = 10; break;
		case 4: request.xclient.data.l[2] = 11; break;
		case 5: request.xclient.data.l[3] = Button3; break;
		case 6: request.xclient.data.l[4] = 3; break;
		case 7: request.xclient.data.l[0] = SHRT_MAX + 1L; break;
		case 8: request.xclient.data.l[1] = SHRT_MIN - 1L; break;
		case 9: request.xclient.window = 999; break;
		case 10: first.isdock = 1; break;
		case 11: first.isfullscreen = 1; break;
		case 12: first.ishidden = 1; break;
		case 13: first.tags = 2; break;
		case 14: request.xclient.data.l[3] = -1; break;
		case 15: request.xclient.data.l[4] = -1; break;
		case 16: request.xclient.data.l[2] = LONG_MAX; break;
		}
		clientmessage(&request);
		assert(!pointergrabs && !pointerungrabs && !configureevents);
	}
	for (i = 0; i < 3; i++) {
		reset();
		request = dragrequest();
		request.xclient.data.l[4] = i;
		request.xclient.data.l[3] = 0; /* Legacy unknown button; actual button is checked. */
		dragmotion(-700, 200);
		clientmessage(&request);
		expectgeom(-800, 180, 601, 401);
	}
	for (i = 0; i < 3; i++) {
		reset();
		request = dragrequest();
		if (i == 0) pointermask = 0; /* Released before the message arrived. */
		if (i == 1) pointerok = False;
		if (i == 2) pointergrabfail = 1;
		clientmessage(&request);
		assert(pointergrabs == 1 && pointerungrabs == (i != 2));
		assert(!configureevents && !movingwin);
	}

	reset();
	request = dragrequest();
	dragmotion(-700, 200);
	moveeventcount = 4;
	moveevents[3] = moveevents[0];
	moveevents[1] = moveevents[2] = request;
	moveevents[1].xclient.format = 8;
	moveevents[1].xclient.data.l[2] = moveevents[2].xclient.data.l[2] = 11;
	clientmessage(&request);
	expectgeom(-800, 180, 601, 401);
	assert(moveeventindex == 3 && pointerungrabs == 1 && !movingwin);
	/* Another move request must not recursively grab the pointer. */
	reset();
	request = dragrequest();
	dragmotion(-700, 200);
	moveevents[2] = moveevents[1];
	moveevents[1] = moveevents[0];
	moveevents[0] = request;
	moveeventcount = 3;
	clientmessage(&request);
	expectgeom(-800, 180, 601, 401);
	assert(pointergrabs == 1 && pointerungrabs == 1);

	reset();
	other = monitor;
	other.mx = other.wx = 1;
	other.num = 1;
	other.sel = other.clients = other.stack = NULL;
	monitor.next = &other;
	request = dragrequest();
	dragmotion(450, 220);
	clientmessage(&request);
	expectgeom(350, 200, 601, 401);
	assert(first.mon == &other && selmon == &other && other.sel == &first);

	for (i = 0; i < 2; i++) {
		reset();
		request = dragrequest();
		allocated = ecalloc(1, sizeof *allocated);
		*allocated = first;
		monitor.clients = monitor.stack = monitor.sel = allocated;
		moveeventcount = 1;
		moveevents[0] = (XEvent){0};
		moveevents[0].xany.type = i ? UnmapNotify : DestroyNotify;
		if (i) moveevents[0].xunmap.window = first.win;
		else moveevents[0].xdestroywindow.window = first.win;
		clientmessage(&request);
		assert(!monitor.clients && !movingwin && pointerungrabs == 1);
	}
	reset();
	request = dragrequest();
	moveeventcount = 1;
	moveevents[0] = (XEvent){0};
	moveevents[0].xconfigure.type = ConfigureNotify;
	moveevents[0].xconfigure.window = root;
	before = configureevents;
	clientmessage(&request);
	assert(putbackevents == 1 && pointerungrabs == 1 && !movingwin);
	assert(configureevents == before && queuedevent.type == ConfigureNotify);
	for (i = 0; i < 2; i++) {
		reset();
		request = dragrequest();
		randractive = 1;
		randrevent = 90;
		moveeventcount = 1;
		moveevents[0] = (XEvent){.type = randrevent + (i ? RRNotify : RRScreenChangeNotify)};
		clientmessage(&request);
		assert(putbackevents == 1 && pointerungrabs == 1 && !movingwin);
		assert(queuedevent.type == moveevents[0].type);
	}
	reset();
	request = dragrequest();
	moveeventcount = 1;
	moveevents[0] = (XEvent){0};
	moveevents[0].xclient = (XClientMessageEvent){ .type = ClientMessage, .window = first.win,
		.message_type = netatom[NetWMState], .format = 32 };
	moveevents[0].xclient.data.l[0] = 1;
	moveevents[0].xclient.data.l[1] = netatom[NetWMFullscreen];
	clientmessage(&request);
	assert(first.isfullscreen && pointerungrabs == 1 && !movingwin);
	reset();
	monitor.my = monitor.wy = -500;
	first.y = -400;
	request = dragrequest();
	request.xclient.data.l[1] = pointery = -380;
	dragmotion(-700, -300);
	clientmessage(&request);
	expectgeom(-800, -320, 601, 401);
	puts("PASS: general application header drag, anchored restore, cancel, lifecycle and pointer safety (mock Xlib)");
}

static void
testclientresize(void)
{
	static const int geometry[2][8][4] = {
		{
			{ -800, 180, 501, 321 }, { -900, 180, 601, 321 },
			{ -900, 180, 701, 321 }, { -900, 100, 701, 401 },
			{ -900, 100, 701, 481 }, { -900, 100, 601, 481 },
			{ -800, 100, 501, 481 }, { -800, 100, 501, 401 }
		}, {
			{ -1000, 20, 701, 481 }, { -900, 20, 601, 481 },
			{ -900, 20, 501, 481 }, { -900, 100, 501, 401 },
			{ -900, 100, 501, 321 }, { -900, 100, 601, 321 },
			{ -1000, 100, 701, 321 }, { -1000, 100, 701, 401 }
		}
	};
	XEvent request;
	Client *allocated;
	const int *expected;
	int direction, reverse, lifecycle;

	for (direction = 0; direction < 8; direction++) {
		for (reverse = 0; reverse < 2; reverse++) {
			reset();
			request = dragrequest();
			request.xclient.data.l[2] = direction;
			dragmotion(pointerx + (reverse ? -100 : 100), pointery + (reverse ? -80 : 80));
			clientmessage(&request);
			expected = geometry[reverse][direction];
			expectgeom(expected[0], expected[1], expected[2], expected[3]);
			assert(pointergrabs == 1 && pointerungrabs == 1 && !movingwin);
			assert(first.isfloating && !first.placement && moveeventindex == 2);
		}
		reset();
		request = dragrequest();
		request.xclient.data.l[2] = direction;
		first.isfixed = 1;
		clientmessage(&request);
		assert(!pointergrabs && !configureevents);
		/* Every edge uses the same released-button and lifecycle protection. */
		for (lifecycle = 0; lifecycle < 5; lifecycle++) {
			reset();
			request = dragrequest();
			request.xclient.data.l[2] = direction;
			if (lifecycle == 0) {
				pointermask = 0;
			} else if (lifecycle <= 2) {
				allocated = ecalloc(1, sizeof *allocated);
				*allocated = first;
				monitor.clients = monitor.stack = monitor.sel = allocated;
				moveeventcount = 1;
				moveevents[0] = (XEvent){0};
				if (lifecycle == 1) {
					moveevents[0].xdestroywindow.type = DestroyNotify;
					moveevents[0].xdestroywindow.window = first.win;
				} else {
					moveevents[0].xunmap.type = UnmapNotify;
					moveevents[0].xunmap.window = first.win;
				}
			} else if (lifecycle == 3) {
				moveeventcount = 1;
				moveevents[0] = request;
				moveevents[0].xclient.data.l[2] = 11;
			} else {
				moveeventcount = 1;
				moveevents[0] = (XEvent){0};
				moveevents[0].xconfigure.type = ConfigureNotify;
				moveevents[0].xconfigure.window = root;
			}
			clientmessage(&request);
			assert(pointergrabs == 1 && pointerungrabs == 1 && !movingwin);
			if (lifecycle == 1 || lifecycle == 2) assert(!monitor.clients);
			if (lifecycle == 4) assert(putbackevents == 1);
		}
	}
	reset();
	first.isfixed = 1;
	request = dragrequest();
	dragmotion(-700, 200);
	clientmessage(&request);
	expectgeom(-800, 180, 601, 401); /* Fixed size still allows movement. */

	reset();
	request = dragrequest();
	request.xclient.data.l[2] = 0;
	dragmotion(pointerx + 1000, pointery + 1000);
	clientmessage(&request);
	expectgeom(-317, 483, 18, 18); /* Opposite edges stay put after crossing. */
	reset();
	first.minw = 200;
	request = dragrequest();
	request.xclient.data.l[2] = 7;
	dragmotion(pointerx + 1000, pointery);
	clientmessage(&request);
	expectgeom(-499, 100, 200, 401);
	reset();
	first.maxw = 650;
	request = dragrequest();
	request.xclient.data.l[2] = 7;
	dragmotion(pointerx - 400, pointery);
	clientmessage(&request);
	expectgeom(-949, 100, 650, 401);
	reset();
	first.minh = 150;
	request = dragrequest();
	request.xclient.data.l[2] = 1;
	dragmotion(pointerx, pointery + 1000);
	clientmessage(&request);
	expectgeom(-900, 351, 601, 150);
	reset();
	first.maxh = 450;
	request = dragrequest();
	request.xclient.data.l[2] = 1;
	dragmotion(pointerx, pointery - 200);
	clientmessage(&request);
	expectgeom(-900, 51, 601, 450);
	reset();
	first.minw = first.maxw = 601;
	request = dragrequest();
	request.xclient.data.l[2] = 0;
	dragmotion(pointerx + 100, pointery + 80);
	clientmessage(&request);
	expectgeom(-900, 180, 601, 321); /* Only height is resizable. */

	reset();
	first.basew = first.baseh = 1;
	first.incw = 20; first.inch = 10;
	first.minw = 101; first.minh = 81;
	first.maxw = 801; first.maxh = 601;
	request = dragrequest();
	request.xclient.data.l[2] = 0;
	dragmotion(pointerx + 109, pointery + 87);
	clientmessage(&request);
	expectgeom(-780, 190, 481, 311);
	assert(first.x + first.w == -299 && first.y + first.h == 501);
	reset();
	first.mina = first.maxa = 1;
	request = dragrequest();
	request.xclient.data.l[2] = 0;
	dragmotion(pointerx + 100, pointery + 80);
	clientmessage(&request);
	expectgeom(-620, 180, 321, 321);

	reset();
	th = 24;
	createtitle(&first);
	first.h += titleh(&first);
	request = dragrequest();
	request.xclient.data.l[2] = 0;
	dragmotion(pointerx + 100, pointery + 80);
	clientmessage(&request);
	expectgeom(-800, 180, 501, 347);
	assert(titleh(&first) == 26 && clientpositions[first.win].y == 206);
	assert(clientpositions[first.win].height == 321);

	reset();
	snapto(PlaceLeft);
	request = dragrequest();
	request.xclient.data.l[2] = 4;
	dragmotion(pointerx + 100, pointery - 80);
	clientmessage(&request);
	expectgeom(-1000, 40, 598, 717);
	assert(!first.placement);
	reset();
	togglemaximize(NULL);
	request = dragrequest();
	request.xclient.data.l[2] = 4;
	dragmotion(pointerx, pointery);
	clientmessage(&request);
	assert(first.placement == PlaceMax);
	expectgeom(-1000, 40, 999, 797);
	/* Resize the maximized rectangle, rather than restoring its floating size. */
	moveeventindex = 0;
	dragmotion(pointerx - 100, pointery - 80);
	clientmessage(&request);
	expectgeom(-1000, 40, 899, 717);
	assert(!first.placement);
	reset();
	request = dragrequest();
	request.xclient.data.l[2] = 4;
	dragmotion(pointerx + 100, pointery + 80);
	moveeventcount = 3;
	moveevents[2] = moveevents[0];
	moveevents[1] = request;
	moveevents[1].xclient.data.l[2] = 11;
	clientmessage(&request);
	expectgeom(-900, 100, 701, 481);
	assert(moveeventindex == 2 && pointerungrabs == 1 && !movingwin);
	reset();
	monitor.my = monitor.wy = -500;
	first.y = -400;
	request = dragrequest();
	request.xclient.data.l[1] = pointery = -380;
	request.xclient.data.l[2] = 0;
	dragmotion(pointerx + 100, pointery + 80);
	clientmessage(&request);
	expectgeom(-800, -320, 501, 321);
	reset();
	first.isfloating = 0;
	monitor.lt[0] = &layouts[1];
	request = dragrequest();
	request.xclient.data.l[2] = 4;
	dragmotion(pointerx + 100, pointery + 80);
	clientmessage(&request);
	expectgeom(-900, 100, 701, 481);
	assert(first.isfloating);
	puts("PASS: all application resize edges, hints/anchoring, fixed clients and lifecycle (mock Xlib)");
}

static void
maxrequest(long action, Atom a, Atom b)
{
	XEvent event = {0};

	event.xclient.window = first.win;
	event.xclient.message_type = netatom[NetWMState];
	event.xclient.format = 32;
	event.xclient.data.l[0] = action;
	event.xclient.data.l[1] = a;
	event.xclient.data.l[2] = b;
	clientmessage(&event);
}

static int
hasstate(Atom atom)
{
	unsigned int i, count = 0;

	for (i = 0; i < statecounts[first.win]; i++)
		if (savedstates[first.win][i] == atom)
			count++;
	assert(count <= 1);
	return count;
}

static void
testewmhmaximize(void)
{
	Atom h, v;
	XEvent event;
	XWindowAttributes attributes = { .x = -910, .y = 70, .width = 200, .height = 100 };
	Client *client;
	int i;

	reset();
	h = netatom[NetWMMaxH]; v = netatom[NetWMMaxV];
	savedstates[first.win][0] = 999;
	statecounts[first.win] = 1;
	maxrequest(1, h, h);
	assert(first.placement == PlaceMaxH && hasstate(h) && !hasstate(v));
	expectgeom(-1000, 100, 999, 401);
	maxrequest(1, v, None);
	assert(first.placement == PlaceMax && hasstate(h) && hasstate(v));
	expectgeom(-1000, 40, 999, 797);
	maxrequest(0, h, None);
	assert(first.placement == PlaceMaxV && !hasstate(h) && hasstate(v));
	expectgeom(-900, 40, 601, 797);
	maxrequest(2, v, v);
	expectgeom(-900, 100, 601, 401);
	assert(!first.placement && !hasstate(h) && !hasstate(v));
	assert(statecounts[first.win] == 1 && savedstates[first.win][0] == 999);
	maxrequest(0, h, v);
	expectgeom(-900, 100, 601, 401);
	maxrequest(2, v, h);
	assert(first.placement == PlaceMax);
	maxrequest(2, h, v);
	assert(!first.placement);

	for (i = 0; i < 2; i++) {
		reset();
		snapto(PlaceLeft);
		snapto(PlaceTop);
		maxrequest(1, i ? v : h, None);
		assert(first.restoreplacement == (PlaceLeft | PlaceTop));
		expectgeom(-1000, 40, i ? 498 : 999, i ? 797 : 397);
		togglemaximize(NULL);
		assert(first.placement == PlaceMax);
		togglemaximize(NULL);
		assert(first.placement == (PlaceLeft | PlaceTop));
		placeclient(&first, 0);
		expectgeom(-900, 100, 601, 401);
		assert(!hasstate(h) && !hasstate(v));
	}
	for (i = 0; i < 8; i++) {
		reset();
		if (i == 0) first.isfixed = 1;
		if (i == 1) first.isfullscreen = 1;
		if (i == 2) first.isdock = 1;
		if (i == 3) monitor.ww = 2;
		if (i == 4) monitor.wh = 2;
		if (i == 5) maxrequest(-1, h, v);
		if (i == 6) maxrequest(3, h, v);
		if (i == 7) {
			event = (XEvent){0};
			event.xclient.window = first.win;
			event.xclient.message_type = netatom[NetWMState];
			event.xclient.format = 8;
			event.xclient.data.l[0] = 1;
			event.xclient.data.l[1] = h;
			clientmessage(&event);
		}
		if (i < 5) maxrequest(1, h, v);
		assert(!first.placement && !configureevents);
	}
	reset();
	first.maxw = 800; first.maxh = 600;
	first.incw = first.inch = 10;
	maxrequest(1, h, v);
	assert(first.w == 800 && first.h == 600 && hasstate(h) && hasstate(v));
	for (i = 0; i < 2; i++) {
		reset();
		maxrequest(1, h, v);
		event = dragrequest();
		if (i) event.xclient.data.l[2] = 4;
		dragmotion(pointerx - 100, pointery - 80);
		clientmessage(&event);
		assert(!first.placement && !hasstate(h) && !hasstate(v));
	}
	for (i = 0; i < 3; i++) {
		reset();
		savedstates[30][0] = 999;
		savedstates[30][1] = i == 1 ? v : h;
		savedstates[30][2] = i == 2 ? v : savedstates[30][1];
		statecounts[30] = 3;
		manage(30, &attributes);
		client = monitor.clients;
		assert(client->placement == (i == 0 ? PlaceMaxH : i == 1 ? PlaceMaxV : PlaceMax));
		assert(savedstates[30][0] == 999);
		placeclient(client, 0);
		assert(client->w == 200 && client->h == 100);
		assert(statecounts[30] == 1 && savedstates[30][0] == 999);
		free(client);
	}
	for (i = 0; i < 2; i++) {
		reset();
		savedstates[30][0] = h;
		statecounts[30] = 1;
		if (i) stateextra = 1; else stateformat = 8;
		manage(30, &attributes);
		client = monitor.clients;
		assert(!client->placement);
		free(client);
	}
	reset();
	maxrequest(1, 999, None);
	assert(!first.placement && !configureevents);
	togglemaximize(NULL);
	assert(hasstate(h) && hasstate(v));
	moveeventcount = 1;
	moveevents[0] = (XEvent){ .type = ButtonRelease };
	resizemouse(NULL);
	assert(!first.placement && !hasstate(h) && !hasstate(v));
	for (i = 0; i < 3; i++) {
		reset();
		if (i == 0) first.isfixed = 1;
		if (i == 1) first.isfullscreen = 1;
		if (i == 2) first.isdock = 1;
		resizemouse(NULL);
		assert(!pointergrabs && !configureevents);
	}
	puts("PASS: EWMH maximize axes, atomic/duplicate states, snap restore, initial states and invalid requests (mock Xlib)");
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
	assert(!handler[EnterNotify]);
	assert(monitor.sel == &first && selmon == &monitor);
	assert(raised == None);
	event.xmotion.window = root;
	event.xmotion.x_root = 100;
	event.xmotion.y_root = 100;
	motionnotify(&event);
	assert(selmon == &monitor && monitor.sel == &first);
	event.xmotion.window = first.win;
	event.xmotion.x_root = -500;
	motionnotify(&event);
	assert(selmon == &monitor && monitor.sel == &first);
	expectgeom(-900, 100, 601, 401);
	event.xbutton.window = second.win;
	event.xbutton.button = Button1;
	buttonpress(&event);
	assert(monitor.sel == &second && focused == second.win);
	assert(replayevents == 1 && raised == second.win);
	focus(&first);
	assert(monitor.sel == &first);
	event.xclient.format = 32;
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
testtitlebar(void)
{
	XEvent event = {0};
	int outerheight;

	reset();
	assert(!showtitlebar);
	th = showtitlebar ? MAX(24, bh) : 0;
	createtitle(&first);
	assert(!first.titlebar && !titleh(&first));
	th = 24;
	clientdecoration = 1;
	createtitle(&first);
	assert(!first.titlebar);
	clientdecoration = 2;
	createtitle(&first);
	assert(!first.titlebar);
	clientdecoration = 0;
	createtitle(&first);
	assert(first.titlebar && titleh(&first) == 26);
	first.h += titleh(&first);
	outerheight = first.h;
	resizeclient(&first, first.x, first.y, first.w, first.h);
	assert(first.h == outerheight && titleclient(first.titlebar) == &first);
	assert(clientpositions[first.win].y == first.y + 26);
	assert(clientpositions[first.win].height == first.h - 26);
	assert(titlebutton(&first, first.w - 1) == 2);
	assert(titlebutton(&first, first.w - th - 1) == 1);
	assert(titlebutton(&first, first.w - 2 * th - 1) == 0);
	assert(titlebutton(&first, 1) == -1);
	setfullscreen(&first, 1);
	assert(!titleh(&first) && !traymapped[first.titlebar]);
	setfullscreen(&first, 0);
	assert(titleh(&first) == 26 && first.h == outerheight);
	snapto(PlaceLeft);
	assert(first.h == monitor.wh - 2 * first.bw);
	assert(first.x == monitor.wx);
	/* Release outside a pressed button must not close the client. */
	first.pressedbutton = 2;
	event.xbutton.window = first.titlebar;
	event.xbutton.button = Button1;
	event.xbutton.x = first.w - 1;
	event.xbutton.y = -1;
	buttonrelease(&event);
	assert(!closeevents && first.pressedbutton == -1);
	deleteprotocol = 1;
	first.pressedbutton = 2;
	event.xbutton.y = 1;
	buttonrelease(&event);
	assert(closeevents == 1);
	first.pressedbutton = 0;
	event.xbutton.x = first.w - 3 * th + 1;
	buttonrelease(&event);
	assert(first.ishidden && !traymapped[first.titlebar]);
	resizeclient(&first, first.x, first.y, first.w, first.h);
	assert(clientpositions[first.win].x == -2 * WIDTH(&first));
	restoreclient(&first);
	assert(!first.ishidden && traymapped[first.titlebar]);
	windowmenu(&first);
	assert(switchmenu && switchcount == 4);
	endswitcher(1);
	assert(first.isabove && !switchwin);
	windowmenu(&first);
	switchindex = 1;
	endswitcher(1);
	assert(first.ishidden);
	restoreclient(&first);
	first.titlebar = None;
	first.isdock = 1;
	createtitle(&first);
	assert(!first.titlebar);
}

static void
testtaskbar(void)
{
	XEvent event = {0};
	Client dock, elsewhere;
	int start, end;
	unsigned int i;

	reset();
	monitor.showbar = 1;
	monitor.barwin = 2;
	statusmon = &monitor;
	strcpy(stext, "Status");
	strcpy(first.name, "First");
	second = first;
	second.win = 20;
	second.ishidden = second.isurgent = 1;
	strcpy(second.name, "Second");
	first.next = first.snext = &second;
	dock = first;
	dock.win = 30;
	dock.isdock = 1;
	elsewhere = first;
	elsewhere.win = 40;
	elsewhere.tags = 2;
	second.next = &dock;
	dock.next = &elsewhere;
	elsewhere.next = NULL;
	start = barstartwidth(&monitor);
	end = monitor.ww - barstatuswidth(&monitor);
	assert(start > 0 && end > start);
	recordbar = 1;
	bartexts = 0;
	drawbar(&monitor);
	recordbar = 0;
	assert(bartexts == 4);
	assert(!strcmp(barlabels[0].text, "Inicio"));
	assert(!strcmp(barlabels[1].text, "Status"));
	assert(!strcmp(barlabels[2].text, "First"));
	assert(!strcmp(barlabels[3].text, "[min] Second") && barlabels[3].invert);
	assert(barlabels[2].x == start && barlabels[3].x + barlabels[3].w == end);
	assert(!taskbar(&monitor, start - 1) && !taskbar(&monitor, end));
	for (i = 2; i < 4; i++) {
		assert(taskbar(&monitor, barlabels[i].x) == (i == 2 ? &first : &second));
		assert(taskbar(&monitor, barlabels[i].x + barlabels[i].w - 1)
			== (i == 2 ? &first : &second));
	}
	event.xproperty.window = second.win;
	event.xproperty.atom = netatom[NetWMName];
	bartexts = 0;
	recordbar = 1;
	propertynotify(&event);
	recordbar = 0;
	assert(bartexts == 4); /* Title changes also redraw unfocused/minimized clients. */
	memset(&event, 0, sizeof event);
	event.xbutton.window = monitor.barwin;
	event.xbutton.button = Button1;
	event.xbutton.x = barlabels[3].x;
	buttonpress(&event);
	assert(!second.ishidden && monitor.sel == &second && focused == second.win);
	assert(!second.isurgent);
	buttonpress(&event);
	assert(second.ishidden && monitor.sel == &first);
	event.xbutton.x = start;
	event.xbutton.state = Mod4Mask;
	buttonpress(&event);
	assert(!first.ishidden);
	event.xbutton.state = 0;
	event.xbutton.x = -1;
	buttonpress(&event);
	assert(!first.ishidden);
	assert(!strcmp(startcmd[0], "wm-launcher") && !strcmp(startcmd[1], "--start"));
	for (i = 0; i < LENGTH(buttons); i++)
		if (buttons[i].click == ClkStart && buttons[i].button == Button1)
			break;
	assert(i < LENGTH(buttons) && buttons[i].func == spawn && buttons[i].arg.v == startcmd);
	/* The other monitor contains only its own clients. First click activates. */
	monitor.next = &other;
	other = monitor;
	other.next = NULL;
	other.barwin = 3;
	other.clients = other.stack = other.sel = &elsewhere;
	elsewhere.mon = &other;
	elsewhere.tags = 1;
	elsewhere.snext = NULL;
	dock.next = NULL;
	assert(taskbar(&other, barstartwidth(&other)) == &elsewhere);
	assert(taskbar(&monitor, start) == &first);
	event.xbutton.window = other.barwin;
	event.xbutton.x = barstartwidth(&other);
	buttonpress(&event);
	assert(selmon == &other && other.sel == &elsewhere && !elsewhere.ishidden);
	/* Empty and tiny task areas must neither divide by zero nor overlap status. */
	other.clients = NULL;
	assert(!taskbar(&other, barstartwidth(&other)));
	drawbar(&other);
	monitor.ww = start;
	assert(!barstatuswidth(&monitor) && !taskbar(&monitor, start));
	drawbar(&monitor);
	monitor.ww = 1;
	assert(barstartwidth(&monitor) == 1 && !barstatuswidth(&monitor));
	drawbar(&monitor);
	monitor.ww = 0;
	assert(!barstartwidth(&monitor) && !taskbar(&monitor, 0));
	drawbar(&monitor);
}

static void
testalttab(void)
{
	Arg forward = {.i = 1}, backward = {.i = -1};
	XEvent event = {0};

	reset();
	second = first;
	second.win = 20;
	first.next = first.snext = &second;
	second.ishidden = 1;
	first.focused = 2;
	second.focused = 1;
	keyboardgrabfail = 1;
	alttab(&forward);
	assert(!switchwin && !switchitems && monitor.sel == &first);
	keyboardgrabfail = 0;
	alttab(&forward);
	assert(switchwin && switchcount == 2 && switchitems[switchindex] == second.win);
	assert(monitor.sel == &first && second.ishidden);
	endswitcher(0);
	assert(monitor.sel == &first && second.ishidden && keyboardungrabs == 1);
	alttab(&backward);
	testkey = XK_Alt_L;
	heldkeys[1] = 2; /* Right Alt remains held. */
	keyrelease(&event);
	assert(switchwin);
	heldkeys[1] = 0;
	keyrelease(&event);
	assert(!switchwin && !second.ishidden && monitor.sel == &second);
	assert(second.x == -900 && second.y == 100);
	alttab(&forward);
	testkey = XK_Tab;
	event.xkey.state = ShiftMask;
	keypress(&event);
	assert(switchitems[switchindex] == second.win);
	testkey = XK_Escape;
	keypress(&event);
	assert(!switchwin && monitor.sel == &second);

	reset();
	other = monitor;
	other.mx = other.wx = 1;
	other.num = 1;
	second = first;
	second.win = 20;
	second.mon = &other;
	second.x = 40;
	other.sel = other.stack = other.clients = &second;
	monitor.next = &other;
	focus(&first);
	focus(&second);
	assert(second.focused > first.focused);
	focus(&first);
	assert(first.focused > second.focused);
	second.ishidden = 1;
	alttab(&forward);
	assert(switchcount == 2 && switchitems[switchindex] == second.win);
	assert(!handler[EnterNotify] && selmon == &monitor);
	endswitcher(1);
	assert(selmon == &other && other.sel == &second && !second.ishidden);
	assert(second.x == 40);
}

static void
testabove(void)
{
	reset();
	second = first;
	second.win = 20;
	first.next = first.snext = &second;
	savedstates[second.win][0] = 999;
	statecounts[second.win] = 1;
	setabove(&second, 1);
	assert(statecounts[second.win] == 2 && savedstates[second.win][0] == 999);
	assert(savedstates[second.win][1] == netatom[NetWMAbove]);
	assert(second.isabove && monitor.sel == &first && raised == second.win);
	restack(&monitor);
	assert(raised == second.win);
	monitor.sel = NULL;
	restack(&monitor);
	assert(raised == second.win);
	monitor.sel = &first;
	setabove(&second, 0);
	assert(!second.isabove && raised == first.win);
	first.isfullscreen = 1;
	setabove(&second, 1);
	assert(raised == first.win);
	second.isdock = 1;
	setabove(&second, 0);
	assert(second.isabove);
}

static void
testminimize(void)
{
	XEvent event = {0};

	reset();
	wmchangeatom = 400;
	second = first;
	second.win = 20;
	first.next = first.snext = &second;
	hideclient(&first);
	assert(first.ishidden && !ISVISIBLE(&first));
	assert(!traymapped[first.win] && first.ignoreunmaps == 2);
	assert(monitor.sel == &second && focused == second.win);
	focus(&first);
	assert(monitor.sel == &second);
	event.xclient.format = 32;
	event.xclient.window = first.win;
	event.xclient.message_type = netatom[NetActiveWindow];
	clientmessage(&event);
	assert(!first.ishidden && monitor.sel == &first && traymapped[first.win]);
	assert(first.ignoreunmaps == 2);
	/* Even if restored before its UnmapNotify events arrive, it stays managed. */
	event = (XEvent){0};
	event.xunmap.window = first.win;
	unmapnotify(&event);
	unmapnotify(&event);
	assert(!first.ignoreunmaps && monitor.sel == &first);
	expectgeom(-900, 100, 601, 401);
	event.xclient.window = second.win;
	event.xclient.message_type = wmchangeatom;
	event.xclient.format = 32;
	event.xclient.data.l[0] = IconicState;
	clientmessage(&event);
	assert(second.ishidden && monitor.sel == &first);
	event = (XEvent){0};
	event.xmaprequest.window = second.win;
	maprequest(&event);
	assert(!second.ishidden && traymapped[second.win]);
	first.isdock = 1;
	hideclient(&first);
	assert(!first.ishidden);
}

static void
testnotificationactivation(void)
{
	Client above;
	XEvent event;
	unsigned long serial;
	int layer, format;

	for (layer = 0; layer < 3; layer++) {
		reset();
		other = monitor;
		other.mx = other.wx = 1;
		other.next = NULL;
		monitor.next = &other;
		second = first;
		second.win = 20;
		second.x = 100;
		second.mon = &other;
		second.isabove = layer == 1;
		second.isfullscreen = layer == 2;
		above = second;
		above.win = 30;
		above.isabove = 1;
		above.isfullscreen = 0;
		second.next = second.snext = &above;
		other.clients = other.stack = &second;
		other.sel = &above;
		focus(&above);
		focus(&first);
		hideclient(&second);
		serial = focusserial;
		event = (XEvent){0};
		event.xclient.window = second.win;
		event.xclient.message_type = netatom[NetActiveWindow];
		for (format = 0; format <= 16; format += 8) {
			event.xclient.format = format;
			clientmessage(&event);
			assert(second.ishidden && !traymapped[second.win]);
			assert(selmon == &monitor && focused == first.win);
			assert(focusserial == serial && other.stack == &above);
		}
		event.xclient.format = 32;
		clientmessage(&event);
		assert(!second.ishidden && traymapped[second.win]);
		assert(selmon == &other && other.sel == &second && focused == second.win);
		assert(second.mon == &other && first.mon == &monitor);
		assert(other.clients == &second && second.next == &above);
		assert(monitor.clients == &first && !first.next);
		assert(second.x == 100 && second.y == 100 && second.w == 601 && second.h == 401);
		assert(other.stack == &second && second.snext == &above && !above.snext);
		assert(second.focused == serial + 1 && first.focused < second.focused);
		assert(above.focused < first.focused);
		assert(raised == (layer ? second.win : above.win));
		assert(!pointerwarps && pointerx == monitor.wx + 1 && pointery == monitor.wy + 1);
		/* Repeated activation must not manufacture another MRU transition. */
		clientmessage(&event);
		assert(focusserial == serial + 1 && !pointerwarps);
	}
	puts("PASS: format32 activation restores on original monitor, MRU, above/fullscreen and no pointer warp (mock Xlib)");
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
	event.xclient.format = 32;
	event.xclient.window = third.win;
	event.xclient.message_type = netatom[NetActiveWindow];
	clientmessage(&event);
	assert(selmon == &other && other.sel == &third);
	assert(ungrabs[first.win] && ungrabs[second.win]);
	assert(ungrabs[third.win] && focused == third.win);
	event.xbutton.window = first.win;
	event.xbutton.button = Button1;
	buttonpress(&event);
	assert(selmon == &monitor && monitor.sel == &first && focused == first.win);
	second.isdock = 1;
	event.xbutton.window = second.win;
	buttonpress(&event);
	assert(selmon == &monitor && monitor.sel == &first && focused == first.win);
	assert(other.sel == &third);
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
	event.xclient.format = 32;
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

static void
testtheme(void)
{
	char names[2][3][8], previous[2][3][8];
	char valid[] = "#f7f7f7 #212936 #909090 #f5f5f5 #7e9ebd #7e9ebd";

	assert(themevalues(valid, names));
	assert(!strcmp(names[0][0], "#f7f7f7"));
	assert(!strcmp(names[1][2], "#7e9ebd"));
	memcpy(previous, names, sizeof names);
	assert(!themevalues("", names));
	assert(!themevalues("#fff #000", names));
	valid[9] = 'z';
	assert(!themevalues(valid, names));
	assert(!memcmp(names, previous, sizeof names));
	valid[9] = '2';
	valid[7] = ';';
	assert(!themevalues(valid, names));
}

int
main(void)
{
	reset();
	grabbuttons(&first, 1);
	assert(plainclickgrabs == 4);
	first.isdock = 1;
	grabbuttons(&first, 1);
	assert(plainclickgrabs == 4);
	testtheme();
	testconfig();
	testplacement();
	testmaximize();
	testclientdrag();
	testclientresize();
	testewmhmaximize();
	testlimits();
	testfullscreen();
	testclose();
	testfocus();
	testtitlebar();
	testtaskbar();
	testalttab();
	testabove();
	testminimize();
	testnotificationactivation();
	testcrossfocus();
	testmonitors();
	testdock();
	testinitialcenter();
	testspawn();
	testwindowsetups();
	testtray();
	testtrayselection();
	testtraymonitors();
	puts("PASS: dwm taskbar, optional titlebars, geometry, click focus, close, spawn and setup history (mock Xlib, ASan/UBSan)");
	return 0;
}
