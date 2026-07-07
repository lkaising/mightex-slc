# The Backend Seam

> **Superseded (2026-07-07).** This document analyzes the module-global
> backend design that the backend-seam refactor removed: `_backend`,
> `use_backend()`, the cached lazy default, `create_transport()`, and the
> `MIGHTEX_SLC_BACKEND` / `MIGHTEX_SLC_PORT` environment variables no longer
> exist. The current design — a `RequestExecutor` pinned to each `Controller`
> at open, `transport=` as the public injection point, `open_fake_device()`
> as the explicit fake spelling — is described in `architecture.md` (§2, §3,
> §6). Kept as historical analysis; symbols below no longer exist in the code.

How the `Backend` protocol in `client/link.py` works — locally, across the
package, and as the load-bearing boundary of the whole architecture.

Compiled 2026-07-07 from a full read-only exploration of the repository
(client, server, contract, transport, tests, examples, docs). No code was
changed. All paths are relative to `mightex-slc/src/mightex_slc/` unless
noted.

---

## 1. The tip of the iceberg: what lives in link.py

`client/link.py` contains three interlocking decisions:

1. **A structural Protocol** (`link.py:52-55`):

   ```python
   class Backend(Protocol):
       def handle(self, operation: str, payload: dict[str, Any]) -> dict[str, Any]: ...
   ```

   One method, string + dict in, dict out. Duck-typed — anything with that
   signature qualifies. Nothing rich crosses it: no object references, no
   exceptions, no handles.

2. **A module-global singleton** (`link.py:58`):

   ```python
   _backend: Backend | None = None
   ```

   Installed via `use_backend(backend | None)` (`link.py:61-68`); `None`
   resets to the lazy default. Consumed by every request through
   `call(operation, payload)` (`link.py:71-76`).

3. **A lazy, environment-driven default** (`link.py:79-85`):

   ```python
   def _default_backend() -> Backend:
       from ..server.api import Server
       from ..transport import create_transport
       return Server(create_transport())
   ```

   Built on the *first* `call()`, cached forever after. This is the one
   place the client package touches the server, and the import is inside
   the function so the client carries no server dependency until first use.

Around the seam, link.py owns the request/reply plumbing
(`_roundtrip`, `link.py:103-113`): build the operation's Pydantic request
model, `model_dump(mode="json")`, send through `call()`, re-validate the
reply dict against a cached `TypeAdapter[Ok | Error]`, raise a mapped
client exception on `Error`, return the Ok model otherwise. Four public
functions — `open_device`, `configure_normal`, `set_active_mode`,
`close_device` — each do exactly this.

Error mapping (`link.py:88-100`): `ErrorType → exception class`
(`DEVICE_CONNECTION→DeviceConnectionError`, `DEVICE_NOT_FOUND→DeviceNotFoundError`,
`UNSUPPORTED_OPERATION→UnsupportedOperationError`,
`CONTROLLER_CLOSED→ControllerClosedError`), with `DEVICE_COMMAND`
special-cased to carry the device code:
`DeviceCommandError(reply.message, code=reply.code)`.

---

## 2. Who calls into the seam (client side)

- `client/controller.py:33-36` — module-level `open_device(port=None)` is
  the library entry point: `link.open_device(...)` →
  `Controller(device_id, capabilities)`.
- `Controller` (`controller.py:39-72`) holds only `_device_id`, cached
  `_capabilities`, and a client-side `_closed` flag. `channel(n)` is pure
  client-side construction (no seam crossing, no range check —
  the server enforces range). `close()` is idempotent locally and sets
  `_closed` only after the link call succeeds.
- `Channel` (`channel.py:26-49`) is stateless beyond `(device_id, number)`
  and just forwards to `link.configure_normal` / `link.set_active_mode`.

**Key structural fact:** neither `Controller` nor `Channel` stores a
backend reference. They hold only string/int identity and route through
the module global at call time. All proxies in a process therefore share
one backend.

**Public API surface:** `mightex_slc/__init__.py` exports `open_device`,
`Controller`, `Channel`, the exception tree, and the re-exported contract
enums. `use_backend` and `Backend` are deliberately **not** exported —
swapping backends requires `from mightex_slc.client import link;
link.use_backend(...)`. It is a test/embedding seam, not public API.

---

## 3. The concrete Backend: Server (server side)

`server/api.py:28-37`:

```python
class Server:
    def __init__(self, transport: Transport) -> None:
        self._transport = transport
        self._session = Session()

    def handle(self, operation: str, payload: dict[str, Any]) -> dict[str, Any]:
        return dispatch(operation, payload, session=self._session, transport=self._transport)
```

`Server` satisfies `Backend` *structurally* — it never imports the client.
It binds one `Transport` (injected) and one fresh `Session` per instance.
The module docstring frames it as the in-process "front door": a
socket/daemon could replace it without moving the contract.

**dispatch.py** (`dispatch.py:41-63`) per call:
1. Route lookup in `_ROUTES` (`dispatch.py:117-122`), operation string →
   `(RequestModel, handler)`. Unknown operation → an
   `UNSUPPORTED_OPERATION` `Error` envelope.
2. Server-side re-validation: `request = request_type(**payload)` rebuilds
   the Pydantic model. Pydantic `ValidationError` is deliberately **not**
   caught ("inert with the in-process client", `dispatch.py:58-61`).
3. Handler call; only `TransportError` and `UnknownDeviceError` are caught
   and converted via `to_error()`. Anything else re-raises as a bug.
4. `reply.model_dump(mode="json")` — every path ends in exactly one
   contract model (`*Ok` or `Error`), so replies cannot drift from the
   contract schema.

**session.py** — `Session` owns live `ControllerModel`s keyed by a
server-generated `device_id = uuid4().hex` (`session.py:47`). The model and
transport handle never leave the server; clients hold only the opaque id.
Missing ids raise `UnknownDeviceError` → mapped to `CONTROLLER_CLOSED`.
Note `_close_device` pops the session **before** `model.close()`
(`dispatch.py:109-114`).

**impl/** — the real device model. `ControllerModel` holds the open
`TransportHandle` + capabilities, deliberately no mode/parameter state
("the device owns its state"); it range-checks channel numbers.
`ChannelModel` enforces capability policy (e.g. TRIGGER rejected on MA/CA
modules → `CommandRejectedError`).

**server/errors.py** — the mirror of the client's error mapping:
`unsupported_operation()` and `to_error(exc)` build `Error` envelopes;
`_classify` maps `UnknownDeviceError`/`InvalidHandleError` →
`CONTROLLER_CLOSED`, `DeviceNotPresentError` → `DEVICE_NOT_FOUND`,
`CommandRejectedError` → `DEVICE_COMMAND`, other `TransportError` →
`DEVICE_CONNECTION`. It never sets `code` (the vendor's post-`#!` error
command is undocumented) — so today `DeviceCommandError.code` is **always
None**; the contract's `code` field and link.py's `code=reply.code`
plumbing are forward-provisioned, currently dead weight.

---

## 4. What crosses the seam: the contract

`contract/base.py:14-22` — `ContractModel(BaseModel)` with
`extra="forbid", frozen=True` (deliberately not strict-mode: JSON round
trips legitimately deliver ints where floats/IntEnums are declared).

Each operation follows the same pattern: `XRequest`, `XOk`, and
`XReply = Annotated[XOk | Error, Field(discriminator="status")]` — a
tagged union on the `"ok"`/`"error"` literal. Requests carry their own
validation (e.g. `configure_normal` rejects `current_set_ma >
current_max_ma` before anything crosses the seam).

`ErrorType` (`components/error_type.py`) is a `StrEnum` whose **values are
literally the client exception class names** — errors travel as data and
are reconstructed as exceptions on the client side only.

Because `_roundtrip` re-validates replies into fresh frozen models and
dispatch rebuilds requests, **no object identity crosses the seam even
in-process** — only JSON-safe dicts. The wire shapes are also exported as
generated YAML JSON-Schemas under `mightex-slc/schemas/`
(written solely by `scripts/generate_schemas.py`; nothing consumes them
yet — they document the seam for a future out-of-process caller).

---

## 5. The layer below: Transport, and how the default backend is chosen

The `Transport` ABC (`transport/base.py:71-114`) is the *hardware* swap
seam one layer beneath the Backend seam: four abstract methods
(`open_device`, `configure_normal`, `set_active_mode`, `close_device`),
its own exception tree rooted at `TransportError`.

`create_transport()` (`transport/__init__.py:35-54`) picks the
implementation: **explicit argument > env `MIGHTEX_SLC_BACKEND` > default
`"rs232"`**. The rs232 backend takes its default serial port from
`MIGHTEX_SLC_PORT`. Imports are lazy so pyserial never loads for
fake-backend use. These two env vars are the *only* live configuration
inputs (examples/config.yaml is read by nothing).

- `rs232/` — codec.py is pure string↔string protocol (whole-mA only,
  `#!`/`#?` → `CommandRejectedError`, capability table for 8 module
  families; unknown families refuse rather than guess);
  `rs232_transport.py` drives pyserial (9600 baud, `\n\r` TX terminator,
  ECHOOFF + DEVICEINFO presence probe, single-open enforcement,
  `serial_factory` test seam).
- `fake/` — simulates a single SLC-MA04-MU with per-channel state that
  persists across close; same single-open enforcement.

So when nothing calls `use_backend()`, the effective stack on first use is:

```
Controller/Channel → link._roundtrip → link.call
                        └─ lazily: Server(create_transport())
                             └─ dispatch → Session/ControllerModel/ChannelModel
                                  └─ Transport (rs232 or fake, per env)
                                       └─ serial port / in-memory fake
```

---

## 6. How the seam is actually used in the repo

- **Production / examples**: nobody calls `use_backend`.
  `examples/normal_mode_timed_on.py` relies entirely on the lazy default
  and documents `MIGHTEX_SLC_BACKEND=fake` as the way to run without
  hardware. The probe scripts bypass the seam and talk to the
  transport/serial layer directly.
- **Tests** (`examples/tests/`): the only callers of `use_backend`.
  - An **autouse fixture** (`conftest.py:151-156`) leak-proofs the
    singleton by calling `link.use_backend(None)` before and after every
    test.
  - `test_seam.py` installs `Server(FakeTransport())` and
    `Server(RS232Transport(serial_factory=...))` and drives the *public*
    API, asserting fake state and exact wire bytes. Notably no test ever
    mocks `Backend` itself — the fake lives at the Transport layer, so
    dispatch/session/policy are always exercised for real.
- **Docs**: `docs/reference/architecture.md` §"backend selection" and §7
  (deliberate cuts: in-process only, no thread safety — "the seam design
  makes the eventual daemon a wiring change");
  `docs/stale/build_plan_normal_mode_timed_on.md:443-445` records the
  decision: "link creates the default backend lazily … replaceable via
  link.use_backend(...). That is the whole mechanism."

---

## 7. Properties, edges, and sharp corners

Facts that follow from the design — verified in code, several of them
non-obvious:

1. **One backend per process.** No per-instance injection point exists;
   two controllers cannot use different backends.
2. **At most one open device per default backend.** Both transports raise
   `TransportError("device is already open")` on a second open
   (`rs232_transport.py:86-87`, `fake_transport.py:83-84`), which surfaces
   client-side as `DeviceConnectionError`. The Session has no capacity
   limit — the cap is purely the transport. Reopen after close works.
3. **Mid-lifetime `use_backend()` silently reroutes live Controllers.** A
   Controller opened against backend A sends its later calls (including
   `close()`) to backend B, whose Session has never seen the device_id →
   a *misleading* `ControllerClosedError`, while A's serial port leaks
   until process exit. Nothing detects or warns about this. Similarly,
   `use_backend(None)` after an open discards the cached Server *and its
   Session*, orphaning the open transport handle.
4. **Environment is frozen at first call.** `MIGHTEX_SLC_BACKEND` set
   after the first operation is silently ignored; the escape hatch is
   `use_backend(None)` (documented in the docstring, easy to miss).
5. **No thread safety, by declared scope.** The lazy init in `call()` is
   check-then-set with no lock, and nothing serializes `Server.handle`
   over the shared pyserial port. architecture.md §7 declares threading a
   deliberate cut.
6. **`handle` is not actually "never raises."** Pydantic
   `ValidationError` from malformed payloads and any non-transport bug
   propagate raw out of `Server.handle`. The Protocol's implicit contract
   is really: "returns a contract reply dict for well-formed payloads of
   known operations; may raise otherwise." That semantics is enforced only
   by convention — the Protocol docstring doesn't state it.
7. **Client `_closed` is local bookkeeping only.** It guards duplicate
   `close()` but does not gate channel operations; a post-close
   `configure_normal` still crosses the seam and relies on the server's
   `CONTROLLER_CLOSED` reply.
8. **No import cycle, by construction.** Server never imports client;
   client imports server only inside `_default_backend()`. The Protocol is
   what breaks the would-be cycle.

---

## 8. Architectural assessment

**What the design buys**

- *A pre-paid IPC boundary that currently costs one function call.* The
  seam is exactly wire-shaped (string + JSON dict), errors travel as data,
  ids are opaque, and no identity crosses it. The claim that "the eventual
  daemon is a wiring change" is credible because of this — it is the
  strongest asset of the design and would survive any refactor of the rest.
- *Clean dependency direction and import weight.* Client is import-light
  until first use; pyserial loads only when rs232 is selected. Splitting
  client and server into separate packages later means deleting one
  function, not untangling imports.
- *Zero-ceremony user API.* For the target user — a lab script driving one
  LED controller on one port — `open_device()` with no wiring is exactly
  right, and this was an explicit, documented decision.
- *Adequate testability in practice*, via two stacked seams: Backend
  (whole server) and Transport/`serial_factory` (below it). Tests inject
  real `Server`s over fakes at the right layer.

**What it costs**

- *Test isolation is a discipline, not a guarantee* — the autouse reset
  fixture in conftest.py is the tell; any embedder who forgets it inherits
  stale global state.
- *The global's failure modes are silent and mislabeled* — the
  rerouting/orphaning edge (§7.3) produces a wrong-category error plus a
  leaked serial port, unguarded and undocumented.
- *Action-at-a-distance configuration* — effective backend = (last
  `use_backend` call) × (environment at first call); behavior depends on
  call order, not values in scope.
- *Semi-private injection point* — the only seam requires reaching into an
  unexported module and mutating global state.

**Compared to alternatives**

- *Constructor injection* (`Controller` carries its backend) would kill
  the global, the reset fixture, and the rerouting hazard, and enable
  multi-backend — but the top-level `open_device()` still needs a default,
  so the env-driven factory only moves; and you lose "one place to swap
  for a whole process." Because proxies hold only ids, retrofitting this
  later is a mechanical, local change (link.py + two proxy constructors).
- *Context/session object* (`with mightex_slc.session(...) as s`) —
  notably the server *already has* this shape (`Server` = transport
  binding + Session registry); the design keeps the context server-side
  and hides it behind the singleton client-side. That split becomes
  correct the day the server is a daemon; it is ceremony if the library
  stays in-process forever. The design bets on the former.

**Bottom line.** The Protocol + contract-dict seam is the load-bearing,
high-quality decision. The module-global singleton is the debatable part,
but its costs all bite only in scenarios the project has explicitly scoped
out (multi-device, threads, mid-run reconfiguration), and its blast radius
is contained because proxies hold only ids. The two genuine weaknesses if
anything is to be improved: (1) the silent-rerouting/orphaning behavior of
mid-lifetime `use_backend()`, and (2) the Backend protocol's error
semantics being unstated — worth writing into the Protocol docstring
before a second implementation ever exists.
