/* Included by dwm-core.c: synthetic XEmbed/RandR state, never an X server. */
static int embedpresent, embedflags, embedformat, embedmessages, failselection;
static unsigned long embedcount;
static Atom embedtype;
static Window trayselection, trayparents[128];
static int traymapped[128], traysaved[128];
static XWindowChanges traypositions[128];
static int primaryx, primaryy, primaryavailable, outputconnected = 1;
static int randrupdates, nextevent, servergrabbed;
static unsigned long readyvalues[2];
static XEvent queuedevent, moveevents[16];
static size_t moveeventcount, moveeventindex;
static int putbackevents;
static void reset(void);
static void snapto(unsigned int direction);
static int recordbar, bartexts;
static struct {
	int x, w, invert;
	char text[256];
} barlabels[16];

void
test_drw_setscheme(Drw *drawing, Clr *colors)
{
}

unsigned int
test_drw_fontset_getwidth(Drw *drawing, const char *text)
{
	return strlen(text) * 8;
}

void
test_drw_rect(Drw *drawing, int x, int y, unsigned int w, unsigned int h,
	int filled, int invert)
{
}

int
test_drw_text(Drw *drawing, int x, int y, unsigned int w, unsigned int h,
	unsigned int padding, const char *text, int invert)
{
	if (recordbar) {
		assert(bartexts < LENGTH(barlabels));
		barlabels[bartexts].x = x;
		barlabels[bartexts].w = w;
		barlabels[bartexts].invert = invert;
		snprintf(barlabels[bartexts++].text, sizeof barlabels[0].text, "%s", text);
	}
	assert(w <= (unsigned int)sw);
	assert(h == (unsigned int)bh || (switchwin && h == (unsigned int)bh + 8)
		|| (th && h == (unsigned int)th));
	return x + w;
}

void
test_drw_map(Drw *drawing, Window win, int x, int y, unsigned int w, unsigned int h)
{
	assert(w > 0 && h > 0);
}

int
XUnmapWindow(Display *display, Window win)
{
	assert(win < LENGTH(traymapped));
	traymapped[win] = 0;
	return 1;
}

int
XMapRaised(Display *display, Window win)
{
	assert(win < LENGTH(traymapped));
	traymapped[win] = 1;
	return 1;
}

int
XReparentWindow(Display *display, Window win, Window parent, int x, int y)
{
	assert(win < LENGTH(trayparents));
	trayparents[win] = parent;
	return 1;
}

int
XAddToSaveSet(Display *display, Window win)
{
	assert(win < LENGTH(traysaved) && !traysaved[win]);
	traysaved[win] = 1;
	return 1;
}

int
XRemoveFromSaveSet(Display *display, Window win)
{
	assert(win < LENGTH(traysaved) && traysaved[win]);
	traysaved[win] = 0;
	return 1;
}

Status
XGetWindowAttributes(Display *display, Window win, XWindowAttributes *wa)
{
	if (win == 99)
		return 0;
	*wa = (XWindowAttributes){.width = 24, .height = 24,
		.class = win == 98 ? InputOnly : InputOutput,
		.map_state = traymapped[win] ? IsViewable : IsUnmapped};
	return 1;
}

Atom
XInternAtom(Display *display, const char *name, Bool only)
{
	static Atom atom = 500;

	if (!strncmp(name, "_NET_SYSTEM_TRAY_S", 18))
		assert(!strcmp(name, "_NET_SYSTEM_TRAY_S0"));
	return ++atom;
}

Window
XGetSelectionOwner(Display *display, Atom selection)
{
	return trayselection;
}

int
XSetSelectionOwner(Display *display, Atom selection, Window owner, Time time)
{
	assert(servergrabbed && !trayselection); /* Never steal a foreign tray. */
	if (!failselection)
		trayselection = owner;
	return 1;
}

Window
XCreateWindow(Display *display, Window parent, int x, int y,
	unsigned int w, unsigned int h, unsigned int border, int depth,
	unsigned int class, Visual *visual, unsigned long mask, XSetWindowAttributes *wa)
{
	assert(w && h);
	trayparents[50] = parent;
	return 50;
}

int
XDestroyWindow(Display *display, Window win)
{
	if (trayselection == win)
		trayselection = None;
	return 1;
}

int
XGrabServer(Display *display)
{
	assert(!servergrabbed);
	servergrabbed = 1;
	return 1;
}

int
XUngrabServer(Display *display)
{
	assert(servergrabbed);
	servergrabbed = 0;
	return 1;
}

RROutput
XRRGetOutputPrimary(Display *display, Window win)
{
	return primaryavailable ? 1 : None;
}

XRRScreenResources *
XRRGetScreenResourcesCurrent(Display *display, Window win)
{
	return calloc(1, sizeof(XRRScreenResources));
}

XRROutputInfo *
XRRGetOutputInfo(Display *display, XRRScreenResources *resources, RROutput output)
{
	XRROutputInfo *info = calloc(1, sizeof *info);

	info->connection = outputconnected ? RR_Connected : RR_Disconnected;
	info->crtc = 1;
	return info;
}

XRRCrtcInfo *
XRRGetCrtcInfo(Display *display, XRRScreenResources *resources, RRCrtc crtc)
{
	XRRCrtcInfo *info = calloc(1, sizeof *info);

	info->x = primaryx;
	info->y = primaryy;
	info->width = 1001;
	info->height = 799;
	return info;
}

void
XRRFreeScreenResources(XRRScreenResources *resources)
{
	free(resources);
}

void
XRRFreeOutputInfo(XRROutputInfo *info)
{
	free(info);
}

void
XRRFreeCrtcInfo(XRRCrtcInfo *info)
{
	free(info);
}

int
XRRUpdateConfiguration(XEvent *event)
{
	randrupdates++;
	return 1;
}

int
XPutBackEvent(Display *display, XEvent *event)
{
	queuedevent = *event;
	nextevent = 0;
	putbackevents++;
	return 1;
}

int
XNextEvent(Display *display, XEvent *event)
{
	if (moveeventcount) {
		if (moveeventindex == moveeventcount)
			return 1;
		*event = moveevents[moveeventindex++];
		return 0;
	}
	if (nextevent++)
		return 1;
	*event = queuedevent;
	return 0;
}

static void
testsetuptray(void)
{
	_XPrivDisplay display = calloc(1, sizeof *display);
	Screen fake = {0};

	display->screens = &fake;
	dpy = (Display *)display;
	setuptray();
	dpy = NULL;
	free(display);
}

static void
testtray(void)
{
	TrayIcon *i;
	XEvent event = {0};
	int x;

	reset();
	monitor.barwin = 2;
	monitor.showbar = 1;
	updatebarpos(&monitor);
	updateprimary();
	testsetuptray();
	assert(traywin == 50 && trayselection == traywin && !servergrabbed);
	assert(readyvalues[0] == (unsigned long)getpid() && readyvalues[1] == traywin);
	assert(trayparents[traywin] == monitor.barwin && !gettraywidth(&monitor));
	for (x = 0; x < 5; x++)
		docktrayicon((Window[]){None, root, monitor.barwin, 98, 99}[x]);
	docktrayicon(first.win);
	assert(!trayicons);
	embedpresent = 1;
	embedflags = 1;
	event.xclient.window = traywin;
	event.xclient.message_type = trayopcode;
	event.xclient.data.l[2] = 40;
	event.xclient.format = 8;
	clientmessage(&event);
	assert(!trayicons);
	event.xclient.format = 32;
	clientmessage(&event);
	i = trayicons;
	assert(i && i->win == 40 && traysaved[40] && trayparents[40] == traywin);
	assert(traymapped[40] && gettraywidth(&monitor) == bh + 4);
	clientmessage(&event);
	assert(trayicons == i && !i->next);
	assert(!wintoclient(40) && wintomon(40) == &monitor);
	assert(monitor.sel == &first && !focused);
	assert(embedmessages > 0);

	/* Flags zero are valid, and UnmapNotify must not resurrect a hidden icon. */
	embedflags = 0;
	event.xproperty.window = 40;
	event.xproperty.atom = xembedinfo;
	propertynotify(&event);
	assert(!i->mapped && !traymapped[40] && !gettraywidth(&monitor));
	event.xunmap.window = 40;
	unmapnotify(&event);
	assert(!traymapped[40]);
	event.xmaprequest.window = 40;
	maprequest(&event);
	assert(!traymapped[40] && !wintoclient(40));
	embedflags = 1;
	event.xproperty.atom = xembedinfo;
	propertynotify(&event);
	assert(i->mapped && traymapped[40]);
	/* Malformed properties retain the last valid state. */
	embedflags = 0;
	embedformat = 8;
	trayiconstate(i);
	assert(i->mapped);
	embedformat = 32;
	embedcount = 1;
	trayiconstate(i);
	assert(i->mapped);
	embedcount = 2;
	embedtype = XA_STRING;
	trayiconstate(i);
	assert(i->mapped);
	embedtype = None;
	embedflags = 1;

	for (x = 0; x < 4; x++) {
		event.xresizerequest.window = 40;
		event.xresizerequest.width = (int[]){0, -1, 2147483647, 1}[x];
		event.xresizerequest.height = (int[]){0, 1, 1, 2147483647}[x];
		resizerequest(&event);
		assert(i->w > 0 && i->w <= 4 * bh && i->h == bh);
	}
	monitor.ww = 3;
	updatesystray();
	assert(gettraywidth(&monitor) <= 2);
	monitor.ww = monitor.mw;
	/* A child tray follows the bar's stacking, including fullscreen. */
	restack(&monitor);
	assert(raised == monitor.barwin);
	setfullscreen(&first, 1);
	restack(&monitor);
	assert(raised == first.win);
	setfullscreen(&first, 0);
	restack(&monitor);
	assert(raised == monitor.barwin);

	/* Snap/max use the reserved strip; fullscreen still covers the full monitor. */
	snapto(PlaceBottom);
	assert(first.y + HEIGHT(&first) == monitor.by);
	togglemaximize(NULL);
	assert(first.y == monitor.wy && HEIGHT(&first) == monitor.wh);
	setfullscreen(&first, 1);
	assert(first.y == monitor.my && first.h == monitor.mh);

	docktrayicon(41);
	event.xdestroywindow.window = 41;
	destroynotify(&event);
	assert(!wintotrayicon(41) && trayicons == i);
	/* Simulate the server's save-set removal when an icon is destroyed. */
	traysaved[41] = 0;
	cleanuptray();
	assert(!traywin && !trayicons && trayparents[40] == root && !traysaved[40]);
	assert(!readyvalues[0] && !readyvalues[1]);
	puts("PASS: native tray docking, mapping, malformed input, bounds, cleanup and fullscreen");
}

static void
testtrayselection(void)
{
	XEvent event = {0};

	reset();
	monitor.barwin = 2;
	updateprimary();
	trayselection = 90;
	testsetuptray();
	assert(!traywin && trayselection == 90 && !gettraywidth(&monitor));
	assert(!readyvalues[0] && !servergrabbed);
	trayselection = None;
	failselection = 1;
	testsetuptray();
	assert(!traywin);
	failselection = 0;
	testsetuptray();
	docktrayicon(40);
	trayselection = 90;
	event.xselectionclear.selection = trayatom;
	selectionclear(&event);
	assert(!traywin && !trayicons && trayselection == 90);
	assert(!readyvalues[0] && !servergrabbed);
	assert(!traysaved[40] && trayparents[40] == root);
	puts("PASS: tray conflict, failed ownership and selection loss without stealing");
}

static void
testtraymonitors(void)
{
	Monitor *removed;
	_XPrivDisplay display;
	Screen fake = {0};

	reset();
	monitor.barwin = 2;
	other = monitor;
	other.barwin = 3;
	other.mx = other.wx = 2000;
	other.my = other.wy = -900;
	other.sel = other.clients = other.stack = NULL;
	monitor.next = &other;
	randractive = primaryavailable = 1;
	primaryx = other.mx;
	primaryy = other.my;
	updateprimary();
	assert(statusmon == &other);
	testsetuptray();
	assert(trayparents[traywin] == other.barwin);
	selmon = &monitor;
	assert(wintomon(traywin) == &other && statusmon == &other);
	primaryx = monitor.mx;
	primaryy = monitor.my;
	updateprimary();
	assert(statusmon == &monitor && trayparents[traywin] == monitor.barwin);
	outputconnected = 0;
	updateprimary();
	assert(statusmon == mons);
	outputconnected = 1;
	primaryavailable = 0;
	updateprimary();
	assert(statusmon == mons);

	/* Detach the child before destroying a removed monitor's bar. */
	removed = createmon();
	removed->barwin = 4;
	other.next = removed;
	traymon = statusmon = removed;
	cleanupmon(removed);
	assert(!traymon && trayparents[traywin] == root);
	updateprimary();
	assert(trayparents[traywin] == monitor.barwin);
	cleanuptray();
	/* Dispatch primary-only RandR changes and reject extension events as indexes. */
	monitor.next = NULL;
	monitor.mx = monitor.wx = monitor.my = monitor.wy = 0;
	monitor.mw = monitor.ww = sw;
	monitor.mh = monitor.wh = sh;
	display = calloc(1, sizeof *display);
	fake.width = sw;
	fake.height = sh;
	display->screens = &fake;
	dpy = (Display *)display;
	randrevent = 80;
	queuedevent = (XEvent){.type = randrevent + RRNotify};
	nextevent = randrupdates = 0;
	run();
	assert(randrupdates == 1 && statusmon == mons && !setuppending);
	queuedevent.type = 1000;
	nextevent = 0;
	run();
	dpy = NULL;
	free(display);
	puts("PASS: primary-only RandR events, negative origins, fallback and monitor removal");
}
