/* Terminal core only: synthetic runes and frontend substitutes, no PTY/X11. */
#include <assert.h>
#include <locale.h>
#include "st.c"

char *utmp, *scroll, *stty_args, *vtiden = "test", *termname = "st-256color";
wchar_t *worddelimiters = L" ";
int allowaltscreen = 1, allowwindowops;
unsigned int tabspaces = 8, defaultfg = 7, defaultbg = 0, defaultcs = 7;

static char *clipboard;
static int clipboardcopies;

void xbell(void) {}
void xclipcopy(void) { clipboardcopies++; }
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
void xsetsel(char *s) { free(clipboard); clipboard = s; }
int xstartdraw(void) { return 0; }
void xximspot(int a, int b) {}

static void
osc52(void)
{
	const char bel[] = "\033]52;c;aGVsbG8=\007";
	const char st[] = "\033]52;c;d29ybGQ=\033\\";

	treset();
	allowwindowops = 0;
	twrite(bel, sizeof(bel) - 1, 0);
	assert(!clipboard && !clipboardcopies);
	allowwindowops = 1;
	twrite(bel, sizeof(bel) - 1, 0);
	assert(clipboard && !strcmp(clipboard, "hello") && clipboardcopies == 1);
	twrite(st, sizeof(st) - 1, 0);
	assert(!strcmp(clipboard, "world") && clipboardcopies == 2);
	allowwindowops = 0;
	twrite(bel, sizeof(bel) - 1, 0);
	assert(!strcmp(clipboard, "world") && clipboardcopies == 2);
	free(clipboard);
	clipboard = NULL;
}

static void
selection(void)
{
	const char wrapped[] = "https://example.com/path";
	const char newline[] = "https://example.\r\ncom/path";
	char *text;

	treset();
	twrite(wrapped, sizeof(wrapped) - 1, 0);
	selstart(0, 0, 0);
	selextend(7, 1, SEL_REGULAR, 0);
	selextend(7, 1, SEL_REGULAR, 1);
	text = getsel();
	assert(text && !strcmp(text, wrapped));
	free(text);
	selclear();
	treset();
	twrite(newline, sizeof(newline) - 1, 0);
	selstart(0, 0, 0);
	selextend(7, 1, SEL_REGULAR, 0);
	selextend(7, 1, SEL_REGULAR, 1);
	text = getsel();
	assert(text && !strcmp(text, "https://example.\ncom/path"));
	free(text);
	selclear();
}

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

static size_t
contents(Rune *out)
{
	size_t n = 0;
	int y, x;
	Line line;

	for (y = -term.histf; y < term.row; y++) {
		line = TLINEABS(y);
		for (x = 0; x < tlinelen(line); x++)
			if (!(line[x].mode & ATTR_WDUMMY) && line[x].u != ' ')
				out[n++] = line[x].u;
	}
	return n;
}

static void
reflow(void)
{
	Rune before[10000], after[10000];
	int widths[] = {7, 3, 2, 1, 8, 24, 5, 16};
	int i, j, alt = 1049;
	size_t n;

	treset();
	for (i = 0; i < 300; i++)
		tputc(i % 5 ? 'a' + i % 26 : 0x4e2d);
	n = contents(before);
	assert(n == 300);
	for (j = 0; j < 3; j++) {
		for (i = 0; i < LEN(widths); i++) {
			tresize(widths[i], 4 + j);
			assert(contents(after) == n);
			assert(!memcmp(before, after, n * sizeof(Rune)));
			assert(BETWEEN(term.c.x, 0, term.col - 1));
			assert(BETWEEN(term.c.y, 0, term.row - 1));
		}
	}
	tsetmode(1, 1, &alt, 1);
	tputc('Q');
	tresize(9, 3);
	tresize(12, 8);
	tsetmode(1, 0, &alt, 1);
	assert(contents(after) == n);
	assert(!memcmp(before, after, n * sizeof(Rune)));
	tresize(0, 0);
	assert(term.col == 12 && term.row == 8);
	tdeletechar(INT_MAX);
	tinsertblank(INT_MAX);
	csiescseq.mode[0] = 'X';
	csiescseq.arg[0] = INT_MAX;
	csihandle();
	for (i = 0; i < 5000; i++) {
		tputc(i % 11 ? 'z' : 0x4e2d);
		if (!(i % 7))
			tresize(1 + (i * 13) % 79, 1 + i % 11);
		assert(BETWEEN(term.histf, 0, HISTSIZE));
		assert(BETWEEN(term.c.x, 0, term.col - 1));
		assert(BETWEEN(term.c.y, 0, term.row - 1));
	}
}

int
main(void)
{
	assert(setlocale(LC_CTYPE, "C.UTF-8"));
	selinit();
	tnew(16, 4);
	osc52();
	selection();
	history();
	reflow();
	puts("PASS: st OSC 52 permissions/copy, wrapped/explicit newlines, bounded history, Unicode reflow, resize and alternate screen (ASan/UBSan; no PTY/X)");
	return 0;
}
