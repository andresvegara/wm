/* Terminal core only: synthetic runes and frontend substitutes, no PTY/X11. */
#include <assert.h>
#include <locale.h>
#include "st.c"

char *utmp, *scroll, *stty_args, *vtiden = "test", *termname = "st-256color";
wchar_t *worddelimiters = L" ";
int allowaltscreen = 1, allowwindowops;
unsigned int tabspaces = 8, defaultfg = 7, defaultbg = 0, defaultcs = 7;

void xbell(void) {}
void xclipcopy(void) {}
void xdrawcursor(int a, int b, Glyph c, int d, int e, Glyph f) {}
void xdrawline(Line a, int b, int c, int d) {}
void xfinishdraw(void) {}
void xloadcols(void) {}
int xsetcolorname(int a, const char *b) { return 0; }
int xgetcolor(int a, unsigned char *b, unsigned char *c, unsigned char *d) { return 1; }
void xseticontitle(char *s) {}
void xsettitle(char *s) {}
int xsetcursor(int n) { return 0; }
void xsetmode(int a, unsigned int b) {}
void xsetpointermotion(int n) {}
void xsetsel(char *s) { free(s); }
int xstartdraw(void) { return 0; }
void xximspot(int a, int b) {}

static void
history(void)
{
	Arg all = {.i = HISTSIZE + 100};
	char *text;
	int i, count, alt = 1049;
	Rune first, screen;

	treset();
	kscrollup(&all);
	assert(term.scr == 0);
	for (i = 0; i < HISTSIZE + 10; i++) {
		tputc('A' + i % 26);
		tputc('\r');
		tputc('\n');
	}
	assert(term.histf == HISTSIZE);
	kscrollup(&all);
	assert(term.scr == HISTSIZE);
	first = TLINE(0)[0].u;
	selstart(0, 0, 0);
	selextend(0, 0, SEL_REGULAR, 0);
	selextend(0, 0, SEL_REGULAR, 1);
	text = getsel();
	assert(text && text[0] == first && text[1] == '\0');
	free(text);
	selclear();
	kscrolldown(&all);
	assert(!term.scr);
	count = term.histf;
	screen = term.line[0][0].u;
	tsetmode(1, 1, &alt, 1);
	for (i = 0; i < 10; i++) {
		tputc('x');
		tputc('\n');
	}
	kscrollup(&all);
	assert(!term.scr && term.histf == count);
	tsetmode(1, 0, &alt, 1);
	assert(term.line[0][0].u == screen);
	treset();
	assert(!term.histf && !term.scr);
}

int
main(void)
{
	assert(setlocale(LC_CTYPE, "C.UTF-8"));
	selinit();
	tnew(16, 4);
	history();
	puts("PASS: st history capacity, selection, reset and alternate screen (no PTY/X)");
	return 0;
}
