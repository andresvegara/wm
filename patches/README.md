# Patches

One functionality per patch. Personal configuration and documentation are
separate from reusable code changes. Do not export a whole working tree as a
single cumulative customization patch.

`sources.tsv` records the official base revisions. Each project's `series`
records application order. Apply the complete series to that base without
commits, using patch -p1 or git apply, never git am.

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

These are ordered patches, not eleven interchangeable standalone patches.
Snap builds on pointerungrab; maximize builds on snap. Fullscreen restoration
integrates with placement state, center uses floating restoration, and monitor
placement integrates with snap/fullscreen restoration and cross-monitor focus.
Profile binds the functions introduced earlier. Documentation describes that
profile. Use the recorded prefix for each patch: minimal alternative patch
combinations are not validated.

The hash in the filename identifies the initial official base, not an invented
commit for each intermediate state. No intermediate commits were created.
`make test` checks patch -p1 and git apply, rebuilds after every patch, compares
the final sources with dwm/, and runs the behavior tests with simulated Xlib.

The activation behavior matches the community
[focusonnetactive](https://dwm.suckless.org/patches/focusonnetactive/) feature,
whose page credits Danny O'Brien. Its original 6.2 diff was not applied; this
version integrates the behavior with the recorded base and tests across
monitors. No systray patch has been applied yet.

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

st is not complete: scrollback/reflow still needs investigation and isolated
behavior tests. Transparency, blur and emoji appearance are not visually
validated; blur is a compositor responsibility, not another st patch.

## Exporting the next functionality

Implement only one functionality at a time, then run:

```
make patch PROJECT=dwm FEATURE=feature-name
make test
```

The exporter reconstructs the existing series in a temporary Git index and
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
