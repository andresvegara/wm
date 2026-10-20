# Patches

One functionality per patch. Personal configuration and documentation are
separate from reusable code changes. Do not export a whole working tree as a
single cumulative customization patch.

`sources.tsv` records five TSV fields: project, official source URL, official
source revision, local import root commit and original tree hash. Each source
repository has its own fresh history; the local import has identical source
files and licenses but no parent or inherited official commit objects.

Each project's `series` records application order. Apply it to the local import
(or identical official source snapshot), using patch -p1 or git apply, never
git am. Official revision identifiers describe provenance, not Git ancestry.

## dwm series

Filenames use `dwm-<feature>-YYYYMMDD-bca7cf2.diff`. The order is:

| Feature | Scope |
| --- | --- |
| clickfocus | No focus changes on pointer crossing/motion. |
| gracefulclose | Request WM_DELETE_WINDOW without XKillClient fallback. |
| focusonnetactive | External activation, including correct cross-monitor focus. |
| pointerungrab | Release the pointer when its position cannot be queried. |
| snap | Half/quarter placement, floating restore and manual drag release. |
| maximize | Maximize/restore using the snap geometry state. |
| fullscreenrestore | Separate fullscreen restore geometry and toggle action. |
| center | Restore floating geometry and center the window. |
| monitorplacement | Translate/reapply geometry when moving between monitors. |
| profile | Personal config.def.h: bindings, single tag, floating and fonts. |
| documentation | Manual and development notice for the complete configuration. |
| launcherbinding | Personal binding to the combined external launcher. |
| docks | Borderless, unfocusable EWMH docks with absolute configure coordinates. |
| sessionkeys | Personal media, volume, brightness, screenshot and lock bindings. |
| sessiondocs | Manual/README for the complete session shortcut configuration. |
| alacritty | Personal terminal binding, retaining st as an alternative. |
| terminaldocs | Manual update for the preferred terminal. |
| launcherdocs | Manual update for the apps/actions-only launcher. |
| thunar | Personal Super+E binding to jumpapp -f thunar. |
| thunardocs | Manual update for Thunar and background-process handling. |
| superclose | Personal Super+Q alias for the existing graceful close action. |
| superclosedocs | Document Super+Q alongside Ctrl+Q and Alt+F4. |
| centerfloating | Center newly managed floating clients, excluding docks/fullscreen. |
| centerfloatingdocs | Document initial placement and assigned-monitor behavior. |
| pointerfocus | Restore pointer focus across clients/monitors without focusing docks. |
| pointerfocusdocs | Document pointer focus and existing-window behavior. |
| launcherrors | Route spawned commands through wm-run, with missing-helper fallback. |
| launchprofile | Personal jumpapp -n bindings for observable startup. |
| launchdocs | Document visible startup failures and limits. |
| osdprofile | Personal volume/brightness bindings to wm-control. |
| osddocs | Document real-state OSD feedback and unchanged control limits. |
| windowsetups | Per-client geometry history and private display-transition protocol. |
| windowsetupnoop | Do not leave a no-op root configure event pending. |
| windowsetupdocs | Document in-memory history, exclusions and limits. |
| systray | Native XEmbed tray, primary RandR status placement and bar stacking. |
| barprofile | Personal config: show the existing bottom bar on every monitor. |
| systraydocs | Document the native bar, bridge, clock and ownership handshake. |

These are ordered patches, not interchangeable standalone patches.
Snap builds on pointerungrab; maximize builds on snap. Fullscreen restoration
integrates with placement state, center uses floating restoration, and monitor
placement integrates with snap/fullscreen restoration and cross-monitor focus.
Profile binds the functions introduced earlier. Documentation describes that
profile. Use the recorded prefix for each patch: minimal alternative patch
combinations are not validated.

The hash in the filename identifies the official source snapshot. The local
import root and feature commits have their own hashes, recorded separately;
they do not inherit the official history. `make test` checks patch -p1 and
git apply, rebuilds after every patch, compares
the final sources with dwm/, and runs the behavior tests with simulated Xlib.

The activation behavior matches the community
[focusonnetactive](https://dwm.suckless.org/patches/focusonnetactive/) feature,
whose page credits Danny O'Brien. Its original 6.2 diff was not applied; this
version integrates the behavior with the recorded base and tests across
monitors. The later systray adaptation replaces the external tint2 panel;
snixembed is still needed for SNI/AppIndicator icons. launcherbinding depends on
the profile and the wm-launcher runtime installed by the coordinator. docks
allows the external tray to keep its requested corner geometry, stay above
ordinary windows but below fullscreen, and stay out of focus/cycling. It depends
on the earlier focus/fullscreen changes; it is not an XEmbed implementation.
Sessionkeys follows the profile/launcherbinding and depends at runtime on
playerctl, wpctl, brightnessctl, Flameshot and wm-launcher (see docs/session.md).
Sessiondocs follows sessionkeys and changes only documentation.
Windowsetups builds on monitor placement, fullscreen/snap, docks and initial
centering. It stores up to sixteen normal rectangles/monitor indices per live
client, in memory, and coordinates `_WM_DISPLAY_SETUP` with wm-displays. Pending
captures happen before updategeom; ready restores after stable display setup.
Current fullscreen/snap state and keyboard focus are retained; docks/tiled clients
are excluded. Windowsetupnoop avoids treating unchanged root geometry as an
unfinished transition. Windowsetupdocs follows both. Tests call real configure,
property and geometry functions with synthetic layouts and Xlib substitutes.
Osdprofile follows launchprofile and depends at runtime on the coordinator's
wm-control, wpctl, brightnessctl and notify-send/Dunst; it does not add another
key-grabbing daemon or audio backend. Osddocs follows it. Tests verify every
compiled binding and mock all control queries/changes and notifications.
Launcherrors depends at runtime on the coordinator's wm-run helper. It preserves
spawn argv/setsid and falls back to xmessage if that helper cannot execute.
Launchprofile follows it and uses jumpapp -n, retaining focus/cycle for existing
windows. Launchdocs follows both; these are separate code/config/documentation
patches. Tests call real spawn with only synthetic executables on a closed PATH.
Pointerfocus supersedes the historical clickfocus behavior without rewriting
that patch. It restores upstream-style EnterNotify focus, uses crossing coordinates
on the root, and switches monitors on root MotionNotify immediately (no static
previous-monitor state). It depends on the existing dock/focus code; dock crossings
may select their monitor but focus a normal client, never the dock. Pointerfocusdocs
follows it. Tests use synthetic crossing/motion events with real focus handlers.
Centerfloating follows the existing docks/fullscreen/monitor changes. It centers
once during manage, using assigned-monitor usable coordinates and outer size;
transients retain their parent's monitor. Oversized clients stay at the top-left,
and docks/fullscreen retain placement. Centerfloatingdocs follows it. Tests call
real manage with mock Xlib as well as the placement helper.
Thunar follows the existing profile/session bindings; `jumpapp -f` still raises
and cycles existing windows, but can open one when only a background process is
running. It depends on the coordinator's `thunar` dependency. Thunardocs follows
thunar and only updates the manual. No file associations or Plasma defaults change.

### Native tray adaptation

Systray follows windowsetupdocs and reconciles the existing docks, focus,
placement, fullscreen and geometry-history code. It adds `systray.c`, included
by dwm.c, and the libXrandr build dependency; Makefile tracks the include and
ships it in source distributions. Barprofile and systraydocs follow separately.
It does not require barpadding, status2d, statuscmd or another panel.

The inspected source is [dwm-systray-20260516-44dbc68.diff](https://dwm.suckless.org/patches/systray/dwm-systray-20260516-44dbc68.diff),
by Bakkeby; the [community page](https://dwm.suckless.org/patches/systray/) credits
Jan Christoph Ebersbach, Eon S. Jeon, David Phillips, Eric Pruitt, Igor Gevka,
Michel Boaventura, Hritik Vijay, Markus Hanetzok and Aleksei Kozadaev across
versions. The unchanged artifact and SHA256SUMS are retained in `upstream/dwm/`.
Original dwm licensing/attributions remain unchanged. This is an adaptation,
not an unchanged upstream patch or an independent upstream implementation.

The original acquires the X11 tray selection, advertises MANAGER, reparents
XEmbed windows, handles their properties/resize/destruction and reserves bar
space. Its default follows the selected monitor. This version instead:

- embeds the tray as a child of the primary monitor's bar (first-monitor
  fallback), without shrinking/restarting a separate root panel;
- uses native RandR events, including primary-only changes, and preserves
  the coordinator's display-transition/window-history protocol;
- separates icons from normal Client objects and retains existing close/focus
  semantics and personal bindings (the original also changes those interfaces);
- honors zero/hidden XEmbed flags, bounds invalid/extreme sizes, clips overflow,
  rejects duplicate/invalid docking and handles failed/lost selection safely;
- never steals an existing selection; the private `_WM_SYSTRAY` root CARDINAL
  pair (dwm PID, tray window) lets the supervisor verify its own tray is ready;
- keeps ordinary windows under the bar, fullscreen above it, and restores icons
  to the root/save-set on cleanup. No native SNI implementation is added.

Tests exercise real tray/event functions with synthetic Xlib/RandR state under
ASan/UBSan, plus mocked supervisor readiness/clock and installer packaging in
`make test`. They do not establish graphical compatibility of real applets.

## dmenu series

Base: `8627d0c659f5bb79ba29edd0e7264fb7549e6fac`. Apply `dmenu/series` in order:

| Feature | Scope |
| --- | --- |
| center | Optional `-c` horizontal/vertical centering on the selected monitor. |
| centerdocs | Manual for centering, adaptive width and monitor bounds. |

Center adapts the community [dmenu-center-5.2.diff](https://tools.suckless.org/dmenu/patches/center/),
credited there to Ed van Bruggen, Nihal Jere, El Bachir Kassimi and Leliel
(across the published versions). The original
is preserved unchanged in `upstream/dmenu/` with SHA256SUMS. The adaptation keeps
normal mode and `-m`, factors geometry for isolated tests, bounds menu height on
small displays and includes `-c` in usage. The launcher opts into `-c`; there is
no change to standalone dmenu defaults. Centerdocs depends on center.
`make test` builds each prefix and checks real geometry with synthetic dimensions
and text widths under UBSan, without opening X11 or discovering fonts.

## st series

Base: `fdaadd5b1e1bc900769b3c38031c0a658e5cd4da` (0.9.3).
Order is recorded in `st/series`:

| Feature | Scope |
| --- | --- |
| anysize | Per-pixel resize increments, without centering fixed padding. |
| alpha | 32-bit transparency, checked -A parsing and opaque visual fallback. |
| blinkingcursor | Real cursor blink scheduling and DECSCUSR styles. |
| profile | Alacritty font/palette, padding, opacity and clipboard/zoom bindings. |
| documentation | Current options, bindings and explicit development limits. |
| scrollback | Bounded history, selection and alternate-screen isolation. |
| reflow | Reflow default screen/history on resize; preserve alternate screen. |
| mousehistory | Mouse dispatch to history, with alternate-screen fallback. |
| historybindings | Personal keyboard/wheel bindings, after mousehistory/reflow. |
| historydocs | User documentation and provenance for terminal history. |
| fontprimary | Personal profile: only Hack as primary, keeping per-glyph fallback. |
| fontprimarydocs | Document primary-font selection and existing fallback. |

Source artifacts are preserved unchanged in `upstream/st/`, with SHA256SUMS
checked by make test. Sources and attribution:

- [expected-anysize](https://st.suckless.org/patches/anysize/st-expected-anysize-0.9.diff),
  linked from the community anysize page; integrated on 0.9.3 without changes
  to its two-line behavior.
- [alpha](https://st.suckless.org/patches/alpha/st-alpha-20240814-a0274bc.diff),
  from the community alpha page (authors credited there include Eon S. Jeon
  and pr). The new tabspaces comment required config context adaptation.
  The local version also rejects nonfinite/invalid opacity, avoids a signed
  alpha-bit shift, handles failed visual queries and keeps non-32-bit visuals
  opaque. These are adaptations of the same transparency functionality.
- [blinking_cursor](https://st.suckless.org/patches/blinking_cursor/st-blinking_cursor-20230819-3a6d6d7.diff),
  Steven Ward; applied without semantic changes. Its original attribution is
  retained in the source artifact.

The profile depends on alpha and blinkingcursor. Each recorded prefix is
rebuilt, and the full frontend tests use Xlib/Xft substitutes plus UBSan.
No real display, font discovery, compositor or terminal process is started.
Fontconfig parsing tests a supplied family pattern, not installed-font coverage.
Fontprimary follows the profile/history series and removes the explicit emoji
family from primary matching: it could win Fontconfig matching and impose a
large bitmap strike on all terminal cells. Existing per-glyph fallback remains
unchanged. Fontprimarydocs follows fontprimary and only updates user documentation.

The scrollback patch adapts [the community 0.9.2 patch](https://st.suckless.org/patches/scrollback/st-scrollback-0.9.2.diff)
to this series, separately from bindings. It tracks valid history lines instead
of exposing uninitialized rows, bounds scrolling and does not save alternate
screen output. The original is retained with its checksum. tests/st-core.c uses
synthetic terminal input, frontend substitutes and ASan/UBSan, without a PTY/X.
Reflow depends on scrollback. It adapts the community
[0.9.2 reflow patch](https://st.suckless.org/patches/scrollback/st-scrollback-reflow-0.9.2.diff)
to 0.9.3, retaining the upstream dummy-cell guard and clear-region bounds.
The bounded resize ring, wide-cell boundary handling and allocation cleanup
follow [st-flexipatch/reflow.c](https://github.com/bakkeby/st-flexipatch/blob/master/patch/reflow.c),
based on work by BeyondMagic et al. Both source artifacts and the flexipatch MIT
license are preserved. Local adaptations handle one-column widths, hide the
cursor while scrolled, correct selection coordinates and avoid overflow in
large erase/insert/delete requests. Tests preserve 300 mixed ASCII/CJK runes
through width/height changes and alternate screens, then stress 5,000 synthetic
runes/resizes under ASan/UBSan. Width changes clear an active selection instead
of retaining invalid cell coordinates. Transparency, blur and emoji appearance are not visually
validated; blur is a compositor responsibility, not another st patch.

## Exporting the next functionality

Implement only one functionality at a time, then run:

```
make patch PROJECT=dwm FEATURE=feature-name
make test
```

The exporter starts from the local import root, retaining the official source
hash in filenames. It reconstructs the existing series in a temporary Git index and
exports only the remaining working-tree changes as the next patch. It does not
rewrite the previous patches, change the checkout's index or create commits.
The working-tree change must already be scoped to one feature: an exporter
cannot infer semantic boundaries automatically.

Empty exports, invalid names, collisions and untracked files are rejected. New
source files must be deliberately tracked before export. The old `make patches`
target is an alias requiring the same explicit PROJECT and FEATURE; it cannot
silently regenerate an aggregate patch.

To change an earlier feature, reconstruct the state immediately before it in
a temporary tree, update that feature's diff and rebase the dependent patches.
Run the complete validation afterward; do not hide such a change inside an
unrelated later patch.

Naming and patch application follow https://suckless.org/hacking/.
