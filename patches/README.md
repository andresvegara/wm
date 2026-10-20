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

Filenames use `dwm-<feature>-20261020-bca7cf2.diff`. The order is:

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

These are ordered patches, not eleven interchangeable standalone patches.
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
monitors. No systray patch has been applied: the session integration will reuse trayer and
snixembed instead of duplicating tray services in dwm. launcherbinding depends on
the profile and the wm-launcher runtime installed by the coordinator. docks
allows the external tray to keep its requested corner geometry, stay above
ordinary windows but below fullscreen, and stay out of focus/cycling. It depends
on the earlier focus/fullscreen changes; it is not an XEmbed implementation.

## st series (partial)

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
