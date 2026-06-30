# Mightex SLC LED Controller Library: Knowledge Transfer

Status: living source of truth. Everything below the "Locked decisions" line is
settled and should not be relitigated without a deliberate change. Open items
are listed separately at the end.

Purpose: capture every decision, its rationale, and the agreed plan, so a new
contributor or agent can pick up the work without rediscovering the reasoning.
The "why" matters as much as the "what" here, because most of these choices were
made by ruling out heavier alternatives.

Note on revision: an earlier version of this document treated hand-authored
YAML/JSON Schema as the source of truth and preferred generated stdlib
dataclasses plus a generated recursive codec for the client/server contract.
That decision has been deliberately reversed. The contract is now defined by
Pydantic models, and the YAML/JSON Schema files are generated artifacts. The
sections below reflect the new decision throughout.

---

## 1. What we are building

A Python library that controls Mightex Sirius SLC-XXXX LED controllers. The
device is a multi-channel constant-current LED driver. Each channel runs in one
of four modes (disable, normal, strobe, trigger), holds its own parameters per
mode, and can store settings to non-volatile memory.

The work is being done in stages on purpose:

1. Establish the public-facing Python API as a skeleton first (done).
2. Express the contract as Pydantic models derived from that surface, generate
   the schema artifacts from those models, lock the contract, then build the
   client and server implementations against the shared models.

The reason for doing the API skeleton first is that the contract is essentially
the public surface re-expressed as Pydantic models. With the surface fixed, the
models follow almost mechanically, and the implementation can be written against
a contract that no longer moves.

---

## 2. Architecture vision

A three-layer design with a Pydantic-defined contract as the seam between the
public API and the device implementation.

```
client/      HIGH   public API users import; stateless proxies holding a device_id
   │
contract/    SEAM   Pydantic models (source of truth) + generated schema artifacts
   │
server/      LOW    owns live Controllers, drives the transport
   └─ transport/    swappable backends: fake (no hardware) and rs232 (pyserial)
```

The client is high level and user-facing. The contract is the client/server
seam. The server owns all device state keyed by `device_id`. The transport seam
(`transport/base.py`) is what lets the whole stack be built and tested against
the fake backend with no hardware, then flipped to the RS232 backend by changing
one line. The public API stays transport-neutral, and no raw protocol passthrough
appears in it.

The `contract/` directory holds two things:

- `contract/mightex_contract/`: the Pydantic source-of-truth models.
- `contract/schemas/`: generated YAML/JSON Schema artifacts, committed and
  treated as outputs rather than hand-edited source.

### Data flow

A client call builds a Pydantic request model and serializes it with
`model_dump(mode="json")`. It hands that payload to the server entry point, which
validates by constructing the matching Pydantic request model, routes by
operation to the device model, which drives the transport. The handler returns a
Pydantic reply model. The client parses the reply and either returns the success
value or raises the mapped exception from an error reply.

### Seam mechanics

- `client/link.py` builds Pydantic request models and serializes them with
  `model_dump(mode="json")`.
- `server/dispatch.py` validates each incoming payload with the matching Pydantic
  request model, then routes by operation.
- Server handlers return Pydantic reply models.
- `client/link.py` parses the reply: on an ok reply it returns the success value,
  and on an error reply it raises the mapped exception.

### What was cut, and why

No C++ binding. The transport is already solved in Python over pyserial, so a
native binding boundary added complexity and bought nothing.

No message broker (RabbitMQ or similar). This is a single producer and single
consumer with no second consumer in sight. A broker would add connection
management, correlation IDs, and reply queues to solve a decoupling problem that
does not exist here, and it never enforced the contract anyway. The contract,
which is the part that earns its keep, stands on its own without a wire forcing
it.

### What stayed

The contract, enforced at the seam. Request and reply are Pydantic models shared
by both sides, and validation at the seam is Pydantic validation. There is no
separate hand-authored runtime validation layer, so there is one validator, not
two.

Tests, focused on the seam and a full round-trip. See the test list in the build
plan below.

### Open architectural item (not blocking)

The serial port is single-owner. If two processes open the same port they
collide. The deferred fix is a thin local socket so one process owns the port,
a daemon need rather than a broker need. The contract and transport layers do
not move when this is added, which is why it is safe to defer.

---

## 3. The public API surface (established)

The public API skeleton is the canonical artifact for the surface. It is a
single Python module of classes, enums, constants, type hints, and docstrings,
with no method bodies. The contract models are derived from it. Treat the
skeleton and the contract as two views of one thing that must agree exactly.

### How the surface was produced

The skeleton went through deliberate review. Two independent versions were
written from the same device documents. One stayed strictly faithful to the
documents; the other added good structural ideas but also fabricated device
facts (a non-existent current resolution for one module family, an invented
trigger sub-mode, and capability fields the device never reports). The faithful
version was chosen as the base, then revised to fold in the good structural
ideas from the second version while excluding every fabrication.

That review produced a standing rule that now governs the contract work too.

### The standing traceability rule

Every device fact asserted anywhere in the surface or the contract (in a
docstring, a Pydantic model, a field description, an enum value, a constraint, or
a generated schema description) must trace back to the device documents. If a
statement cannot be supported from the documents, either remove it or label it
plainly as a library convention rather than a device fact. This single rule is
what catches fabrication, and it is the primary acceptance test for every model
and generated schema we write.

### Operations on the surface

Module-level functions: `enumerate_devices`, `open_device`.

Controller (device-wide) operations: `channel`, `device_info`, `initialize`,
`store_settings`, `restore_factory_defaults`, `soft_reset`, `set_fan_pwm_level`,
`close`, plus context-manager entry and exit. Controller read-only properties:
`serial_number`, `channel_count`, `module_type`, `current_resolution_ma`,
`max_profile_steps`, `supports_trigger_mode`, `supports_load_voltage`,
`supports_fan_control`, `requires_initialization`, `is_closed`, `channels`.

Channel (per-channel) operations: `configure_normal`, `set_normal_current`,
`configure_strobe`, `configure_trigger`, `set_active_mode`, `get_active_mode`,
`read_parameters`, `read_load_voltage`, plus the `number` property.

### Types on the surface

Enums: `OperatingMode` (DISABLE, NORMAL, STROBE, TRIGGER), `TriggerPolarity`
(RISING, FALLING), `ModuleType` (AA through QA).

Data shapes: `NormalParameters`, `StrobeParameters`, `TriggerParameters`,
`ChannelState`, `DeviceInfo`, `DeviceDescriptor`.

Aliases and constants: `ProfileStep` is `(current_ma, time_us)`, `Profile` is a
sequence of those, `REPEAT_FOREVER` is the reserved strobe repeat value.

### Error model on the surface

An exception hierarchy rooted at `MightexLEDError`:

- `DeviceConnectionError` (transport and handle failures)
  - `DeviceNotFoundError` (a device index cannot be opened)
- `DeviceCommandError` (device reports an error executing an accepted command;
  carries a device error `code` when available)
- `UnsupportedOperationError` (operation not provided by the module)
- `ControllerClosedError` (use of a closed controller)

Argument validation uses the built-in `ValueError`. The device reports a
device-side error as a single condition and does not separate an out-of-range
argument from other execution errors, so both surface as `DeviceCommandError`
rather than inventing a category the device cannot produce.

### Device facts the surface locks in (now contract facts)

These are the non-obvious behaviors the contract must preserve. Each traces to
the documents.

Channels are one-based, matching the hardware labels.

Currents cross the boundary as milliamps (float) and are rounded to the nearest
device step. Resolution is 1 mA for AA, AV, SA, SV, HA, HV, MA, and CA, and
0.1 mA for FA, FV, XA, and XV. The documents do not state a resolution for QA,
so any value used there is a library convention, not a documented fact.

A profile is a sequence of `(current_ma, time_us)` pairs. The terminating zero
pair is handled internally and must never be supplied by the caller. Maximum
usable steps is 127 on full-profile modules and as few as 2 on modules the
documents call limited, without enumerating which modules are limited.

Strobe repeat count follows the device convention: the profile is output
`repeat_count + 1` times. `REPEAT_FOREVER` repeats indefinitely, which means a
profile cannot be asked to output exactly 10000 times. Valid range is 0 to
99999999.

A mode's parameters can be configured while that mode is not active. Physical
output does not change until the mode is made active. Re-entering strobe mode
restarts the profile.

Capability differences are queries, not guesses: trigger mode is absent on MA
and CA; load-voltage read-back is a voltage-monitoring (V) variant feature, with
AV04 and SV04 given as examples; fan control and the required initialization
step exist only on the SLC-MA04-MU and SLC-CA04-MU variants. Requesting an
unsupported operation raises `UnsupportedOperationError`.

Load voltage is reported in millivolts and is meaningful only in normal mode or
a slow strobe mode, because the controller polls the load at a 20 ms interval.

Factory defaults: every channel in disable mode, normal maximum 20 mA and
working current 10 mA, strobe and trigger each at maximum 20 mA with no profile
points.

Settings are volatile until `store_settings` writes them to non-volatile memory.
`restore_factory_defaults` loads defaults into current settings, which must then
be stored to persist.

The public surface is transport-neutral. No USB, HID, or serial detail appears
in any signature. For this project the server's backend is RS232 over pyserial,
with a fake backend for hardware-free testing. There is no raw command
passthrough; capabilities the vendor SDK reaches only through raw commands
(device information, the initialization step, fan control) are exposed as named
methods.

---

## Locked decisions

Everything below is settled.

### 4. Pydantic contract models are the source of truth

The Pydantic models in `contract/mightex_contract/` are authoritative for the
client/server contract. Both the client public types and the server device model
derive from them, so the two cannot drift by construction.

The generated YAML/JSON Schema files in `contract/schemas/` are the documented
contract artifacts. They are generated from the Pydantic models, committed to the
repository, and treated as outputs, not hand-edited source. They exist for human
readability, documentation, and contract review.

The schemas are checked for staleness in CI. The generator runs and the committed
schema files are diffed; a stale or hand-edited schema fails the build.

This supersedes the earlier note in the architecture file tree that described
`client/types.py` as "mirrored from contract." The client types are not mirrored
by hand. They re-export or import the shared contract models. See the next
decision.

### 5. Write the Pydantic models once; generate schemas from them

The link between Python and schema is one-directional generation: write the
Pydantic models once, generate the schemas from them. Do not hand-maintain
parallel Python types and YAML schemas. Maintaining both by hand is the drift
problem this decision exists to remove.

Client public types re-export or import from the shared `mightex_contract`
package rather than mirror them manually. Hand-mirroring of the contract types in
the client is not allowed; a thin alias or import is the only permitted form.

The generated schema files are the read-only artifact in this arrangement. They
carry a "generated; do not edit" header where feasible, and CI regenerates them
and fails if the committed output is stale.

Note that the recursive dataclass codec from the earlier design is gone. The
contract no longer needs a hand-rolled `to_dict`/`from_dict`, because Pydantic
serializes and validates itself. The only codec that survives is the private
hardware codec inside the RS232 transport, described in decision 7.

### 6. Shape models, operation models, and where rules live

The contract is authored as Pydantic models, and they fall into clear groups.

Shape models become Pydantic models and enums: the enums, `NormalParameters`,
`ChannelState`, `DeviceInfo`, `DeviceDescriptor`, the profile step, and the rest.

Operation request and reply models are Pydantic models, one request and one reply
per operation.

Cross-field and conditional rules are expressed with Pydantic validators
(`field_validator` and `model_validator`) where appropriate, rather than as a
separate validation layer.

The generated JSON Schema documents the shape and as much of the validation as
JSON Schema can faithfully express (types, ranges, required fields, enums). Any
validation rule that cannot be exported faithfully to JSON Schema (most
cross-field validators, for example) must be clearly documented as
Pydantic/runtime validation, both in the model and in the generated schema
description, so a reader of the schema alone is not misled into thinking the rule
is absent.

### 7. Pydantic for the contract models

The contract, config, and request/reply models use Pydantic. This is the
deliberate reversal of the earlier dataclasses-first decision.

Rationale: this project is primarily a Python client/server library, and the
contract is a human-facing client/server interface, not the hardware packet
format. For that interface, Pydantic reduces boilerplate compared with
schema-first dataclasses plus a generated recursive codec, and it makes the
models themselves the single validator at the seam. The earlier concern about
two validators disagreeing is resolved here by not having a second one: there is
no hand-authored runtime jsonschema layer, only Pydantic.

Conventions:

- Use strict models where practical, with `extra="forbid"` so unknown fields are
  rejected, and frozen or immutable models where appropriate so request and reply
  values do not mutate after construction.
- Pydantic validation occurs at the client/server boundary, on the request when
  the server receives it and on the reply when the client receives it.
- The RS232 hardware codec stays private to `transport/rs232`. It encodes and
  decodes the device's wire format and is not the client/server contract
  mechanism. The contract never sees protocol bytes.

### 8. Authoring and generation flow for schemas

The YAML/JSON Schema files are no longer hand-authored as the primary source.
They are generated from the Pydantic models.

The generated files preserve the per-operation organization, because that
structure is valuable for human readability, documentation, and contract review.
Each operation gets its own generated schema file, and shared components get
their own files under `schemas/components/`. Generated files are marked with a
"generated; do not edit" header where feasible.

The source of truth is the Pydantic model. Example of an operation request model
with a cross-field rule:

```python
# contract/mightex_contract/operations/configure_normal.py
from pydantic import BaseModel, ConfigDict, Field, model_validator


class ConfigureNormalRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    device_id: str = Field(description="Handle from open_device")
    channel: int = Field(ge=1, description="One-based channel")
    current_max_ma: float = Field(ge=0)
    current_set_ma: float = Field(ge=0)

    @model_validator(mode="after")
    def _set_not_above_max(self) -> "ConfigureNormalRequest":
        # Cross-field rule; does not export to JSON Schema, so it is documented
        # as runtime validation in the generated schema description.
        if self.current_set_ma > self.current_max_ma:
            raise ValueError("current_set_ma must not exceed current_max_ma")
        return self
```

The reply envelope, shared by every operation, is also Pydantic:

```python
# contract/mightex_contract/errors.py
from enum import Enum
from typing import Annotated, Literal, Union
from pydantic import BaseModel, ConfigDict, Field


class ErrorType(str, Enum):
    VALUE_ERROR = "ValueError"
    CONTROLLER_CLOSED = "ControllerClosedError"
    DEVICE_CONNECTION = "DeviceConnectionError"
    DEVICE_NOT_FOUND = "DeviceNotFoundError"
    DEVICE_COMMAND = "DeviceCommandError"
    UNSUPPORTED_OPERATION = "UnsupportedOperationError"


class Ok(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["ok"] = "ok"


class Error(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["error"] = "error"
    error_type: ErrorType
    message: str
    code: int | None = None  # populated for DeviceCommandError


Reply = Annotated[Union[Ok, Error], Field(discriminator="status")]
```

The generator (`contract/generate_schemas.py`) calls the models' JSON Schema
export, writes one file per operation and component under `contract/schemas/`,
and is the only thing that writes those files. The `error_type` enum surfaces in
`client/link.py` as a map from `ErrorType` to the exception class to raise.

### 9. Cross-field constraints, case by case

Some relationships do not map onto a single field. Two known examples:
`current_set_ma` must not exceed `current_max_ma`, and `code` is populated only
for `DeviceCommandError`. Each is expressed as a Pydantic validator. For each
one we record whether it exports to JSON Schema or is runtime-only, and the
runtime-only ones are documented in the generated schema description so the
schema does not appear to omit a rule the models enforce. This is the same
decision regardless of how the schema is generated.

---

## 10. Contract layer structure

```
contract/
├── mightex_contract/              # SOURCE OF TRUTH: Pydantic contract models
│   ├── __init__.py
│   ├── enums.py
│   ├── shared_models.py           # NormalParameters, ChannelState, DeviceInfo...
│   ├── profile.py
│   ├── errors.py                  # Ok/Error reply models and error type enum
│   └── operations/
│       ├── __init__.py
│       ├── enumerate_devices.py
│       ├── open_device.py
│       ├── configure_normal.py
│       ├── set_normal_current.py
│       ├── configure_strobe.py
│       ├── configure_trigger.py
│       ├── set_active_mode.py
│       ├── read_parameters.py
│       └── ...
│
├── schemas/                       # GENERATED artifacts; committed, not hand-edited
│   ├── operations.yaml
│   ├── components/
│   │   ├── enums.yaml
│   │   ├── shared_models.yaml
│   │   ├── profile.yaml
│   │   └── error.yaml
│   └── operations/
│       ├── enumerate_devices.yaml
│       ├── open_device.yaml
│       ├── configure_normal.yaml
│       ├── set_normal_current.yaml
│       └── ...
│
└── generate_schemas.py
```

### Operation inventory (public API mapped to operations)

Every public function becomes one operation module (request and reply Pydantic
models) and one generated schema file. The client proxy holds a `device_id`;
per-channel operations also carry a one-based `channel`.

Device-level: `enumerate_devices` (no args), `open_device` (index in, device_id
and identity out), `get_capabilities` (device_id), `device_info`, `initialize`,
`store_settings`, `restore_factory_defaults`, `soft_reset`, `set_fan_pwm_level`
(device_id and level), and a close operation for the device handle.

Channel-level (all carry device_id and channel): `configure_normal`,
`set_normal_current`, `configure_strobe`, `configure_trigger`, `set_active_mode`,
`get_active_mode`, `read_parameters`, `read_load_voltage`.

The shape models (enums, the parameter models, `ChannelState`, `DeviceInfo`,
`DeviceDescriptor`, profile) are authored once in the shared model module and
referenced by the operations that return or accept them.

---

## 11. Build plan and sequencing

The order is deliberate and each step is gated on the previous being locked.

1. Write the Pydantic contract models. Author `errors.py` first, since every
   operation reply references the envelope and the `ErrorType` enum. Then the
   other components (enums, profile, the parameter and state models). Then the
   per-operation request and reply models, with the operation set matching the
   public surface exactly. This is the current task.
2. Generate and commit the YAML/JSON Schema artifacts with
   `generate_schemas.py`, preserving the per-operation organization and the
   generated-do-not-edit header.
3. Add a schema-generation staleness test in CI that regenerates the schemas and
   fails if the committed artifacts differ.
4. Build client and server against the shared Pydantic contract models. Client
   proxies and `link.py` on one side; `dispatch.py`, `session.py`, and the device
   model on the other, validating with the models at the seam.
5. Build the fake transport first, so the whole stack runs with no hardware.
6. Implement the private RS232 codec and the RS232 transport, then flip the
   backend.

### Tests

- `test_contract_models.py`: valid and invalid Pydantic requests and replies.
- `test_contract_schemas.py`: the generated schemas are current (staleness) and
  structurally valid.
- `test_integration.py`: client to server to fake, one full round-trip.
- Optional `test_rs232_codec.py`: the private hardware protocol encode and decode.

### Definition of "locked"

The contract is locked when the Pydantic models accept the intended payloads and
reject malformed ones, every operation model maps to exactly one public function
and vice versa, every referenced component model exists, the generated schemas
are current and pass the staleness check, every cross-field rule is implemented
as a validator with its exportability documented, and every device fact traces to
the documents under the standing rule. Changing a locked contract is a deliberate
act, not a casual edit, because the generated schemas and both implementations
follow from it.

---

## 12. Open decisions to resolve during contract authoring

These are not blocking the start of authoring, but they need answers as we go.

Error envelope granularity. The `ErrorType` enum can carry leaf exception types
or parent categories. `DeviceNotFoundError` is a subtype of
`DeviceConnectionError` and must be accounted for either way. Decide whether the
envelope reports the leaf type (more precise, the client maps directly to the
leaf class) or the parent category (smaller enum, client decides specificity).
The example above lists the leaf set including `DeviceNotFoundError`.

Cross-field constraints, per decision 9: for each one, confirm the validator and
record whether it exports to JSON Schema or is runtime-only, and document the
runtime-only ones in the generated schema description.

Discovery payload. `enumerate_devices` returns descriptors whose serial number,
module type, and channel count may be unavailable before opening. Confirm the
reply model marks those as optional and that nothing is invented to fill them.

Close and lifecycle operations. Confirm how the device close and the
context-manager exit map onto operations, since the client proxy is stateless
and the server owns the handle.

QA resolution convention. The documents are silent on QA current resolution.
Record the chosen fallback explicitly as a library convention wherever it
appears, never as a device fact.

---

## 13. Quick reference

```
Source of truth: Pydantic contract models in contract/mightex_contract/.
Schema artifacts: generated YAML/JSON Schema in contract/schemas/, committed and checked for staleness.
Validation: Pydantic at the client/server seam.
Python types: shared Pydantic models and enums, imported/re-exported rather than mirrored.
Hardware codec: private to transport/rs232.
Transport for this project: RS232 over pyserial, with a fake backend for tests.
Governing rule: every asserted device fact traces to the device documents.
Current task: write the Pydantic contract models, generate schemas, then build client/server against them.
```
