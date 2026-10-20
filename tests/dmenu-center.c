/* Exercise real dmenu geometry without opening a display or discovering fonts. */
#include <assert.h>
#define main dmenu_main
#include "dmenu.c"
#undef main

unsigned int
drw_fontset_getwidth(Drw *unused, const char *text)
{
	(void)unused;
	return strlen(text) * 10;
}

int
main(void)
{
	int x, y;
	struct item empty[] = {{0}};
	struct item labels[] = {{.text = "short"}, {.text = "a longer label"}, {0}};

	centered = 1;
	mh = 200;
	items = NULL;
	menugeometry(1920, -200, 1001, 801, &x, &y);
	assert(mw == 500 && mh == 200 && x == 2170 && y == 100);
	items = empty;
	menugeometry(-1000, 0, 320, 100, &x, &y);
	assert(mw == 320 && mh == 100 && x == -1000 && y == 0);
	items = labels;
	lrpad = 10;
	assert(max_textw() == 150);
	promptw = 400;
	mh = 200;
	menugeometry(0, 0, 1000, 800, &x, &y);
	assert(mw == 550 && x == 225 && y == 300);
	promptw = 2000;
	menugeometry(0, 0, 1000, 800, &x, &y);
	assert(mw == 1000 && x == 0 && y == 300);
	centered = 0;
	topbar = 1;
	menugeometry(1920, -200, 1001, 801, &x, &y);
	assert(mw == 1001 && x == 1920 && y == -200);
	topbar = 0;
	menugeometry(1920, -200, 1001, 801, &x, &y);
	assert(mw == 1001 && x == 1920 && y == 401);
	puts("PASS: dmenu center, bounds, text width, empty input and normal mode (UBSan; no X)");
	return 0;
}
