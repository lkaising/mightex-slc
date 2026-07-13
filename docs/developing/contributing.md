# Contributing

## Development setup

Requires Python ≥ 3.12. From the repository root:

```
pip install -e ".[dev]"
```

The `dev` extra brings in `ruff` (lint/format; configured in
`pyproject.toml` — line length 100, py312 target) and `pyyaml` (for the
schema generator). Lint with:

```
ruff check src scripts
```

## Repository layout

- `src/mightex_slc/` — the library: `contract/` (Pydantic seam models),
  `client/` (public proxies), `server/` (dispatch, session, device models),
  `transport/` (the fake and rs232 backends behind one interface). The
  layering is described in [architecture.md](architecture.md).
- `docs/` — this documentation, plus the converted vendor manuals in
  `docs/vendor/`.
- `schemas/` — generated documentation artifacts
  (`python scripts/generate_schemas.py`); never hand-edited.

## Working method

The library is built in **vertical slices**: the smallest complete path
through every layer — contract, transport, server, client — proven end to
end, then repeated for the next capability. The current slice is TRIGGER-mode
configuration with read-backs (parameters and profiles; arming stays with
`set_active_mode`).

## Verifying changes

The repository itself ships no test suite; the hardware-free pytest suite
lives in the sibling `examples/tests` directory (see its README) and runs the
whole stack over the fake transport and scripted serial bytes. Exercise
changes there, or end to end against the simulated device directly:

- `open_fake_device()` runs the full client → server → transport stack over
  the in-memory fake — the quickest whole-stack check.
- `open_device(transport=FakeTransport())` (from `mightex_slc.transport`) is
  the same thing with the transport injection spelled out, and the pattern to
  extend when a scripted transport is needed.
- Any claim about real-device behavior needs a real controller. New device
  facts learned that way belong in [protocol.md](protocol.md), tagged
  **[HW]**.

## Adding an operation

The seam is deliberately mechanical to extend. A new device operation
touches, in dependency order:

1. **Contract** — a `Request`/`Ok`/`Reply` model triple in
   `src/mightex_slc/contract/operations/`, plus any new component models.
2. **Transport interface** — a method on the `Transport` ABC in
   `src/mightex_slc/transport/base.py`.
3. **Both transports** — the fake (`transport/fake/fake_transport.py`,
   modeling the documented device semantics) and the real backend
   (`transport/rs232/`: wire strings in `codec.py`, orchestration in
   `rs232_transport.py`).
4. **Server** — a handler and route in `src/mightex_slc/server/dispatch.py`,
   with the device policy in `server/impl/`.
5. **Client** — a link function in `src/mightex_slc/client/link.py` and a
   proxy method on `Controller` or `Channel`; export any new public names
   from `src/mightex_slc/__init__.py`.
6. **Schemas** — regenerate with `python scripts/generate_schemas.py`.

## Documentation rules

- The devices are "LED controllers" (the vendor's term).
- Every asserted device fact traces to the vendor documents (**[V]**),
  hardware evidence (**[HW]**), or is explicitly labeled a library
  convention (**[C]**) — see [protocol.md](protocol.md). Never invent a
  device fact.
- Docs state what the code does today. If a change makes a doc wrong, fix
  the doc in the same change.
