# Backend Seam: Redesign Options

> **Superseded (2026-07-07).** The refactor this option study fed has landed.
> The executor-pinning core of Option 1 was adopted and extended: the
> transport (not the executor) became the public injection point
> (`open_device(transport=...)`), `open_fake_device()` became the explicit
> fake spelling, and `create_transport`, `default_port`, and both environment
> variables were deleted outright. See `architecture.md` for the current
> design. Kept as history.

Three grounded alternatives to the module-global `_backend` singleton in
`client/link.py`, produced 2026-07-07 by three independent design passes
plus an adversarial cross-review that stress-tested each sketch against the
actual code. Companion to `backend_seam.md` (the analysis of the current
design).

**Shared constraints all three honor:**
- The wire-shaped contract seam (JSON dicts, errors-as-data, opaque ids)
  is untouched — it's the load-bearing asset.
- `open_device()` with zero args must keep working for the lab user.
- The future-daemon story must stay credible.
- No contract, dispatch, session, or transport changes required.

**One free-standing fix that should land regardless of the option chosen:**
the `Backend` Protocol docstring should state its real error semantics —
*"returns a contract reply dict (Ok or Error envelope) for well-formed
payloads of known operations; may raise for malformed payloads or
implementation bugs; never raises to signal device/domain errors — those
travel as Error replies."* All three designs claimed this as theirs; it is
a one-paragraph orthogonal fix.

---

## Option 1 — Backend travels with the handle (recommended)

### Core idea

Delete the module global. `open_device(port=None, backend=None)` resolves
a backend exactly once — explicit argument wins, else a default factory —
and hands it to the `Controller` it constructs. `Channel` receives it from
its Controller. `link.py` becomes a stateless module of pure functions
that take `backend` as their first parameter. The binding is decided at
the call site, visible in scope, and can never be swapped underneath a
live object.

### What changes, concretely

- **`client/link.py`** — delete `_backend`, `use_backend()`, `call()`.
  The four operation functions and `_roundtrip` gain a leading
  `backend: Backend` parameter. Keep the Protocol, error map, and
  `TypeAdapter`s as-is.
- **`client/backend.py` (new, small)** — `_default_backend()` moves here,
  promoted to public `default_backend()`, still lazily importing
  `Server`/`create_transport` so the client stays import-light.
- **`client/controller.py`** —

  ```python
  def open_device(port: str | None = None, backend: Backend | None = None) -> Controller:
      resolved = backend if backend is not None else default_backend()
      reply = link.open_device(resolved, port=port)
      return Controller(resolved, device_id=reply.device_id, capabilities=reply.capabilities)
  ```

  `Controller` stores `self._backend`; `channel(n)` returns
  `Channel(self._backend, self._device_id, n)`.
- **`client/channel.py`** — holds `(backend, device_id, number)`;
  deliberately not a reference to its Controller, keeping it decoupled
  from `_closed` bookkeeping.
- **Exports** — `Backend` and `default_backend` become public API in both
  `__init__.py`s. The injection point stops being a semi-private poke.
- **Tests** — the autouse `_reset_link_backend` fixture
  (`conftest.py:151-156`) is deleted. `test_seam.py` changes
  `link.use_backend(Server(FakeTransport()))` →
  `open_device(backend=Server(FakeTransport()))`. Same fakes, same layer.
- **`server/`, `contract/`, `transport/`, schemas** — zero changes.

### Usage

```python
# Happy path — unchanged
import mightex_slc
with mightex_slc.open_device() as ctrl:
    ctrl.channel(1).set_normal_parameters(NormalParameters(current_max_ma=500, current_set_ma=200))

# Test injection — no fixture, no globals
ctrl = open_device(backend=Server(FakeTransport()))

# Contract-level stub (UI demo, future daemon client)
class RecordingBackend:
    def handle(self, operation, payload): ...
ctrl = open_device(backend=RecordingBackend())
```

### The one design decision you must make (found by the adversarial review)

The naive version makes `default_backend()` **un-cached** (fresh
`Server(create_transport())` per open), which fixes the frozen-env problem
— but breaks something real: single-open enforcement is **per transport
instance**, not per port (`fake_transport.py:83-84`,
`rs232_transport.py:79-80`). Two bare `open_device()` calls would create
two transports on the same `MIGHTEX_SLC_PORT`; today the second fails with
`DeviceConnectionError`, un-cached it would succeed and put two pyserial
handles on one device (pyserial isn't opened with `exclusive=True`). It
also resets fake-channel state across reopen, which today persists via the
cached Server. Two resolutions:

- **(a) Memoize `default_backend()`** with an explicit, *closing*
  `reset_default_backend()`. Preserves today's single-open and fake-state
  semantics; env stays frozen until an explicit, named reset (an honest
  version of today's `use_backend(None)`). Reintroduces one tiny global —
  but one that is never consulted after open, so live Controllers still
  can't be rerouted. **Recommended.**
- **(b) Stay un-cached** and accept/mitigate: pass `exclusive=True` to
  pyserial, document that fake state resets per open. Fresh env every
  call; truly zero module state.

### Scorecard

| Problem | Outcome |
|---|---|
| Global mutable state | Eliminated (variant a: one never-rerouting cache remains) |
| Test-reset fixture | Deleted; isolation is structural |
| Silent rerouting of live Controllers | Impossible by construction |
| Orphaned serial port on reset | Reset path removed (a: reset now *closes* first) |
| Env frozen at first call | (a) explicit named reset; (b) solved outright |
| Semi-private injection point | First-class API: `backend=` kwarg + exports |

**Migration:** ~60 lines across `link.py`, `controller.py`, `channel.py`,
two `__init__.py`s; delete one fixture; rewrite ~7 `use_backend` call
sites. Roughly half a day. Breaking surface: any direct caller of `link.*`
functions (in-repo: only the proxies and tests) and `use_backend`
importers (tests only).

**Honest downsides:** no one-line process-wide swap for embedders
(they thread `backend=` or monkeypatch `default_backend`); `Backend` in
the public signature couples the API to the seam abstraction (low risk —
the shape is the frozen wire contract); default-path tests still need env
hygiene (`MIGHTEX_SLC_BACKEND`), since a bare `open_device()` builds a
real transport.

---

## Option 2 — Explicit client Session façade

### Core idea

A first-class `mightex_slc.Session` owns exactly what the global owns
implicitly today: the backend binding (resolved once at construction) and
the lifetime of everything opened through it. Controllers/Channels are
opened *from* a session and hold a reference to it. Module-level
`open_device()` survives as sugar over a lazily created default session.

The client Session **mirrors** the server `Session` rather than absorbing
it — it tracks only the device_ids it opened (so `close()`/`__exit__` can
close them via ordinary `close_device` operations through the seam, which
also works for a future daemon). When the backend is a remote daemon
someday: client Session = connection handle, server Session =
per-connection registry. The shapes already line up with
`server/api.py:28-37`.

### What changes, concretely

- **`client/session.py` (new, ~100 lines)** — `Session(backend=None)`
  (None → builds `Server(create_transport())` at construction, env read at
  a visible point), `open_device()`, `close()` (best-effort `close_device`
  for every id it opened, then `SessionClosedError` on further use),
  context-manager protocol, plus `connect()` alias. Module-level
  `default_session()` / `reset_default_session()` — the latter *closes*
  the old default before dropping it, fixing the orphaned-port problem.
- **`client/link.py`** — same statelessness change as Option 1 (functions
  gain a `backend` parameter; global/`use_backend`/`call` deleted).
- **`controller.py` / `channel.py`** — proxies gain a `session` reference;
  module `open_device()` becomes `default_session().open_device(port)`.
- **Exports** — `Session`, `connect`, `reset_default_session`, `Backend`.

### Usage

```python
# Happy path — unchanged
with mightex_slc.open_device() as ctrl: ...

# Test injection — scoped, self-cleaning
with Session(Server(FakeTransport())) as s:
    ctrl = s.open_device()
    ctrl.channel(2).set_normal_parameters(NormalParameters(current_max_ma=500, current_set_ma=100))
# session exit → close_device for anything left open → transport released
```

### Scorecard and honest accounting

Rerouting of live Controllers becomes structurally impossible (they hold
their Session), and lifecycle cleanup is the best of the three options:
session close deterministically releases the serial port. But — as the
adversarial review stressed — problems 1/2/5 are **relocated, not
solved**: `_default_session` is still a module global with env frozen at
its lazy creation, and default-path tests still need
`reset_default_session()` (the fixture survives, renamed). Other real
costs: eager construction in `Session.__init__` erodes the import-light
property; two "Session" classes invite confusion (consider renaming the
server's to `DeviceRegistry`); `SessionClosedError` adds a second
closed-state machine next to the server's `CONTROLLER_CLOSED`; and the API
doubles (module sugar vs. explicit session) for a multi-device lifecycle
benefit the project has explicitly scoped out.

**Migration:** ~a day. **When it's right:** the day the daemon
materializes, this is the correct shape — and Option 1 migrates into it
trivially (a Session is just an object that owns a Backend plus ids), so
choosing Option 1 now forecloses nothing.

---

## Option 3 — Minimal surgery: pin-at-open + ContextVar default

### Core idea

Keep the module-level convenience; make the state safe. Two combined
moves:

1. **Pin the backend to the Controller at open time** — `open_device()`
   resolves "the current backend" once; proxies never consult ambient
   state again (this half is identical to Option 1's core and is what
   kills the rerouting hazard).
2. **Replace the bare global with a `contextvars.ContextVar`** whose
   override is a context manager: `with link.backend(Server(FakeTransport())):`
   — scoped, self-restoring on exit, thread/async-safe. The lazy
   env-driven default remains, cached under a lock, torn down by an
   explicit `reset_default()`.

Resolution precedence: `backend=` kwarg > active `with link.backend(...)`
scope > locked lazy default.

### What changes, concretely

Almost everything stays in `link.py`: the ContextVar + lock + cached
default, a `backend()` contextmanager replacing `use_backend()`,
`current_backend()`, `reset_default()`; operation functions gain the
`backend` parameter; `controller.py`/`channel.py` pin as in Option 1;
`server/api.py` gains a small `Server.close()` so `reset_default()` can
release the outgoing default's transport.

```python
# Test injection — scoped; exiting the with cannot reroute ctrl (pinned)
with link.backend(Server(FakeTransport())):
    ctrl = mightex_slc.open_device()
ctrl.close()   # still reaches the pinned backend, not the restored default
```

### Scorecard and honest accounting

The pinning half genuinely solves the rerouting hazard and, as a bonus,
the lazy-init race and the one-backend-per-process limit. The `with`-based
override is the only design that preserves "swap for a whole scope without
touching call sites" (what tests do today) while remaining
order-independent and self-cleaning.

But the adversarial review found this option carries the most machinery
and two unresolved edges: **(1) close-under-pin contradiction** —
`reset_default()` closing the outgoing default `Server` will close the
transport underneath any live Controller pinned to it (today's silent
*leak* becomes a silent *kill*); the design must pick one: reset never
closes (leak, like today) or closes only when no pins remain (refcounting
— more machinery). **(2)** A `use_backend` compatibility shim via
`ContextVar.set` is *not* process-wide like today's global (per-thread
contexts), so it can't be sold as behavior-compatible. And the three-level
precedence stack is real documentation/maintenance weight for a
one-maintainer library whose only scope-swap consumer is one test file.

**Migration:** ~half a day; touches only `link.py` (+~40 lines),
proxies (+~10), `server/api.py` (+~8), exports.

---

## Comparative verdict

**Ranking for this project (single-device lab library, one maintainer,
daemon aspiration): Option 1 > Option 3 > Option 2.**

- **Option 1** is the only design that *eliminates* rather than contains
  the ambient state, adds zero new concepts for the lab user, matches the
  codebase's existing structure (proxies already hold only ids — the
  retrofit is exactly the "mechanical, local change" `backend_seam.md` §8
  predicted), and leaves the daemon story unchanged-to-stronger. Its one
  real defect (un-cached default vs. single-open/fake-persistence
  semantics) has a clean fix: memoized `default_backend()` with a closing
  `reset_default_backend()`.
- **Option 3** shares Option 1's sound core but wraps it in a
  ContextVar/precedence apparatus that reintroduces hidden state, keeps a
  reset function, and contains a genuine close-under-pin contradiction —
  machinery serving an ergonomic (scope-wide swap) that only the test
  suite uses and that `backend=` covers more simply.
- **Option 2** is the right *eventual* shape if the daemon becomes real,
  and the best at deterministic port cleanup — but today it relocates the
  global, doubles the API, and pays ceremony now for benefits the project
  has scoped out. Nothing is foreclosed by doing Option 1 first: it
  upgrades into Option 2 mechanically.
