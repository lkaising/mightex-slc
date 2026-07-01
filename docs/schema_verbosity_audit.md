# Contract Schema Verbosity Audit — `contract/schemas/`

## Summary

This audit examines the 31 generated YAML artifacts under `contract/schemas/` (18
`operations/*.yaml`, 12 `components/*.yaml`, and the `operations.yaml` index) for
redundancy and other structural noise. The headline finding: **1537 of the 2727
lines across the 30 schema files (56.4%) are verbatim copies of shapes that
already own a canonical component file** — the single largest contributor being
the `Error`/`ErrorType` reply envelope, which is inlined identically into all 18
operation replies (844 duplicated lines, 55% of the total). The key enabling fact
is that **nothing in the repo consumes `contract/schemas/`** (only
`generate_schemas.py` writes it; `pyyaml` is an optional extra, not a runtime
dependency), and the CI staleness diff that will freeze this output **does not yet
exist** (no `.github/`; `tests/` holds only `.gitkeep` files) — so the shape can
be changed cheaply right now, before any golden-file test locks it in.

## Scope & method

Files read in full for this audit:

- `contract/schemas/operations/*.yaml` (18 files) and `contract/schemas/operations.yaml`.
- `contract/schemas/components/*.yaml` (12 files).
- `contract/generate_schemas.py` (the sole writer), `contract/mightex_contract/base.py`,
  `pyproject.toml`.

All line ranges are 1-based and were extracted programmatically. Every duplicated
`$defs` block was parsed and compared, indent-normalized, against its canonical
component definition: **each shape's copies collapse to exactly one distinct
variant — 0 content mismatches**, confirming the copies are byte-for-byte
identical modulo indentation. The per-file and per-shape counts below were
computed with a read-only parser and independently re-derived by an adversarial
verifier (which corrected two aggregate cells in the operation-file total row —
those corrected values are used here). No repo file was modified during the audit.

Environment for reference: pydantic 2.13.4, pyyaml 6.0.3. Pydantic's target
dialect is JSON Schema draft 2020-12 (`$defs`, `const`, `additionalProperties`).

Canonical owner map (shape → the component file dedicated to it):

| Shape | Owner file | Shape | Owner file |
|---|---|---|---|
| ChannelState | `channel_state.yaml` | OperatingMode | `operating_mode.yaml` |
| ControllerCapabilities | `controller_capabilities.yaml` | Profile / ProfileStep | `profile.yaml` |
| DeviceDescriptor | `device_descriptor.yaml` | StrobeParameters | `strobe_parameters.yaml` |
| DeviceInfo | `device_info.yaml` | TriggerParameters | `trigger_parameters.yaml` |
| Error / ErrorType | `error_envelope.yaml` | TriggerPolarity | `trigger_polarity.yaml` |
| ModuleType | `module_type.yaml` | NormalParameters | `normal_parameters.yaml` |

---

## 1. Quantified duplication — operation files (18)

`dup $defs` counts the `$defs` entries in a file that are verbatim copies of a
shape owning a canonical component file (the per-operation `<Op>Ok` wrapper is the
only non-duplicate `$def` and is excluded). `dup lines` is the physical lines those
duplicate blocks occupy.

| Operation file | Total | req $defs | reply $defs | dup $defs | dup lines | dup % | Duplicated shapes |
|---|--:|--:|--:|--:|--:|--:|---|
| `read_parameters.yaml` | 230 | 0 | 10 | 9 | 183 | 80% | ChannelState, NormalParameters, OperatingMode, ProfileStep, StrobeParameters, TriggerParameters, TriggerPolarity, Error, ErrorType |
| `open_device.yaml` | 180 | 0 | 5 | 4 | 126 | 70% | ControllerCapabilities, ModuleType, Error, ErrorType |
| `get_capabilities.yaml` | 167 | 0 | 5 | 4 | 126 | 75% | ControllerCapabilities, ModuleType, Error, ErrorType |
| `enumerate_devices.yaml` | 144 | 0 | 5 | 4 | 106 | 74% | DeviceDescriptor, ModuleType, Error, ErrorType |
| `configure_trigger.yaml` | 142 | 2 | 3 | 4 | 76 | 54% | ProfileStep(req), TriggerPolarity(req), Error, ErrorType |
| `configure_strobe.yaml` | 139 | 1 | 3 | 3 | 69 | 50% | ProfileStep(req), Error, ErrorType |
| `device_info.yaml` | 114 | 0 | 4 | 3 | 73 | 64% | DeviceInfo, Error, ErrorType |
| `get_active_mode.yaml` | 104 | 0 | 4 | 3 | 57 | 55% | OperatingMode, Error, ErrorType |
| `set_active_mode.yaml` | 104 | 1 | 3 | 3 | 57 | 55% | OperatingMode(req), Error, ErrorType |
| `configure_normal.yaml` | 101 | 0 | 3 | 2 | 46 | 46% | Error, ErrorType |
| `read_load_voltage.yaml` | 97 | 0 | 3 | 2 | 46 | 47% | Error, ErrorType |
| `set_normal_current.yaml` | 94 | 0 | 3 | 2 | 46 | 49% | Error, ErrorType |
| `set_fan_pwm_level.yaml` | 89 | 0 | 3 | 2 | 46 | 52% | Error, ErrorType |
| `restore_factory_defaults.yaml` | 83 | 0 | 3 | 2 | 46 | 55% | Error, ErrorType |
| `close_device.yaml` | 82 | 0 | 3 | 2 | 46 | 56% | Error, ErrorType |
| `initialize.yaml` | 82 | 0 | 3 | 2 | 46 | 56% | Error, ErrorType |
| `soft_reset.yaml` | 82 | 0 | 3 | 2 | 46 | 56% | Error, ErrorType |
| `store_settings.yaml` | 82 | 0 | 3 | 2 | 46 | 56% | Error, ErrorType |
| **TOTAL** | **2116** | **4** | **69** | **55** | **1287** | **61%** |  |

> Aggregate-cell correction: the `reply $defs` and `dup $defs` TOTAL cells are the
> verifier-corrected values (**69** and **55**), not the 63/47 in an earlier draft.
> `reply $defs` = 51 reply-side duplicate `$defs` + 18 `<Op>Ok` wrappers = 69;
> `dup $defs` = 4 request-side + 51 reply-side = 55, which matches the 68 total
> copy-blocks in §3 minus the 13 component-side embeds. The load-bearing figures in
> that row (1287 dup lines, 61%) were already correct.

Of the 1287 duplicated lines in operation files, **828 come from the `Error`
(30 lines) + `ErrorType` (16 lines) envelope alone** — 46 lines × 18 replies, 64%
of all operation-file duplication. 64 further duplicate lines are request-side
(configure_strobe: ProfileStep 23; configure_trigger: ProfileStep 23 +
TriggerPolarity 7; set_active_mode: OperatingMode 11); the remaining 1223 are
reply-side.

### Exemplar — `read_parameters.yaml` (largest, 230 lines)

| `$def` in `reply.$defs` | Lines | Count | Duplicate of |
|---|---|--:|---|
| ChannelState | 24–46 | 23 | `channel_state.yaml` |
| Error | 47–76 | 30 | `error_envelope.yaml` |
| ErrorType | 77–92 | 16 | `error_envelope.yaml` |
| NormalParameters | 93–111 | 19 | `normal_parameters.yaml` |
| OperatingMode | 112–122 | 11 | `operating_mode.yaml` |
| ProfileStep | 123–145 | 23 | `profile.yaml` |
| ReadParametersOk | 146–161 | 16 | *(unique wrapper — no canonical file)* |
| StrobeParameters | 162–190 | 29 | `strobe_parameters.yaml` |
| TriggerParameters | 191–215 | 25 | `trigger_parameters.yaml` |
| TriggerPolarity | 216–222 | 7 | `trigger_polarity.yaml` |
| discriminator + oneOf | 223–231 | 9 | (glue) |

9 of the 10 `reply.$defs` entries (**183 of 230 lines = 80%**) are verbatim copies.
Only the request block, `ReadParametersOk`, and the discriminator/`oneOf` tail are
unique to this file.

---

## 2. Quantified duplication — component files (12)

Several component files embed **other** canonical components inside their own
`$defs` rather than referencing the sibling file — a second layer of the same
duplication.

| Component file | Total | Embedded dup $defs | dup lines | dup % | Embeds |
|---|--:|--:|--:|--:|---|
| `channel_state.yaml` | 140 | 6 | 114 | 81% | NormalParameters(19), OperatingMode(11), ProfileStep(23), StrobeParameters(29), TriggerParameters(25), TriggerPolarity(7) |
| `trigger_parameters.yaml` | 58 | 2 | 30 | 52% | ProfileStep(23), TriggerPolarity(7) |
| `profile.yaml` | 53 | 1 | 23 | 43% | ProfileStep(23) — self-copy (see below) |
| `strobe_parameters.yaml` | 55 | 1 | 23 | 42% | ProfileStep(23) |
| `device_descriptor.yaml` | 63 | 1 | 22 | 35% | ModuleType(22) |
| `controller_capabilities.yaml` | 82 | 1 | 22 | 27% | ModuleType(22) |
| `error_envelope.yaml` | 64 | 1 | 16 | 25% | ErrorType(16) — self-copy (see below) |
| `device_info.yaml` | 29 | 0 | 0 | 0% | — |
| `module_type.yaml` | 24 | 0 | 0 | 0% | — |
| `normal_parameters.yaml` | 21 | 0 | 0 | 0% | — |
| `operating_mode.yaml` | 13 | 0 | 0 | 0% | — |
| `trigger_polarity.yaml` | 9 | 0 | 0 | 0% | — |
| **TOTAL** | **611** | **13** | **250** | **41%** |  |

`channel_state.yaml` is effectively a mini-copy of the entire parameter family:
its `ChannelState.$defs` (lines 5–118, 114 of 140 lines) re-inlines six other
canonical shapes.

### The two-layer duplication, concretely

The operation files copy components, and some components copy other components. A
single shape (e.g. `ProfileStep`, 23 lines) therefore lands in seven separate
files: `read_parameters.yaml`, `configure_strobe.yaml` (request),
`configure_trigger.yaml` (request), `channel_state.yaml`,
`strobe_parameters.yaml`, `trigger_parameters.yaml`, and a self-copy inside
`profile.yaml`.

### `error_envelope.yaml` — `ErrorType` appears TWICE

A 64-line file carries the same 6-value enum body twice:

- **Standalone top-level `ErrorType:`** — lines **3–17** (the canonical enum export).
- **Nested duplicate `ErrorType:` under `Error.$defs`** — lines **20–35**.

```yaml
# error_envelope.yaml, lines 3-17 (standalone) — canonical export
ErrorType:
  description: Library exception names reported in an error reply. ...
  enum:
  - ValueError
  - ControllerClosedError
  ...
  title: ErrorType
  type: string
Error:                       # lines 18-64
  $defs:
    ErrorType:               # lines 20-35 — the SAME enum, re-inlined
      description: Library exception names reported in an error reply. ...
      enum:
      - ValueError
      ...
```

Both encode the identical enum (`ValueError, ControllerClosedError,
DeviceConnectionError, DeviceNotFoundError, DeviceCommandError,
UnsupportedOperationError`); the 1-line delta (16 vs 15 physical lines) is only
description folding at the deeper indentation. `profile.yaml` has the analogous
shape: standalone `ProfileStep:` (lines 3–24) plus a nested copy
`Profile.$defs.ProfileStep:` (lines 27–49).

### One duplicated block, verbatim, in the wild

The `Error` block below is byte-identical (modulo indentation) in
`error_envelope.yaml` and in all 18 operation replies. From `close_device.yaml`
(lines 29–58):

```yaml
Error:
  additionalProperties: false
  description: 'Error reply envelope shared by every operation. Runtime-only rule
    (does not export to JSON Schema): code is populated only for DeviceCommandError.
    It may still be None for a DeviceCommandError when the device reports no code.'
  properties:
    status: {const: error, default: error, title: Status, type: string}
    error_type: {$ref: '#/$defs/ErrorType', description: Library exception name to raise}
    message: {description: Human-readable error description, title: Message, type: string}
    code:
      anyOf: [{type: integer}, {type: 'null'}]
      default: null
      description: Device-reported error code, present only for DeviceCommandError
      title: Code
  required: [error_type, message]
  title: Error
  type: object
```

---

## 3. Grand totals

| Metric | Value |
|---|--:|
| 18 operation files, total lines | 2116 |
| 12 component files, total lines | 611 |
| **30 schema files (ops + components), total lines** | **2727** |
| `operations.yaml` index | 70 |
| 31 files including index | 2797 |
| Duplicated lines in operation files | 1287 |
| Duplicated lines in component files | 250 |
| **Total duplicated lines** | **1537** |
| **Duplicated % of the 30 schema files (2727)** | **56.4%** |
| Duplicated % of all 31 files incl. index (2797) | 55.0% |

The index (`operations.yaml`, 70 lines) contains no `$defs` and no duplication.

### Per-shared-shape "copied into N files" catalog

14 shapes own a canonical file; 13 of them are copied elsewhere (`Profile` is not).
"Copies" counts duplicate `$def` blocks; the canonical top-level definition in the
owner file is **not** counted.

| Shape | Copy blocks | Distinct files copied into | Lines / copy | Duplicated lines |
|---|--:|--:|--:|--:|
| ErrorType | 19 | 19 | 16 | 304 |
| Error | 18 | 18 | 30 | 540 |
| ProfileStep | 7 | 7 | 23 | 161 |
| ModuleType | 5 | 5 | 22 | 110 |
| OperatingMode | 4 | 4 | 11 | 44 |
| TriggerPolarity | 4 | 4 | 7 | 28 |
| ControllerCapabilities | 2 | 2 | 58 | 116 |
| NormalParameters | 2 | 2 | 19 | 38 |
| StrobeParameters | 2 | 2 | 29 | 58 |
| TriggerParameters | 2 | 2 | 25 | 50 |
| ChannelState | 1 | 1 | 23 | 23 |
| DeviceDescriptor | 1 | 1 | 38 | 38 |
| DeviceInfo | 1 | 1 | 27 | 27 |
| Profile | 0 | 0 | — | 0 |
| **Total** | **68** | — | — | **1537** |

`ErrorType` = 18 operation replies + 1 self-copy inside `error_envelope.yaml` = 19.
`Error` = 18 operation replies (its canonical home, `error_envelope.yaml`, is not
counted). The per-shape lines sum exactly to 1537.

- The **`Error`+`ErrorType` envelope alone accounts for 844 of 1537 duplicated
  lines (55%)**.
- Adding the ProfileStep family (ProfileStep 161 + StrobeParameters 58 +
  TriggerParameters 50 + TriggerPolarity 28 + ChannelState 23 = 320) covers **76%**
  of all duplication. These two clusters are where any dedup effort earns its keep.

---

## 4. Independent findings beyond the two duplication seeds

Counts across the 31 files: 302 `title:` lines, 81 `additionalProperties: false`
lines, 81 `type: object` lines, 0 `$schema`, 18 `oneOf`, 18 `discriminator`,
88 `$ref`, 36 `enum:` blocks.

### 4.1 Auto-generated `title` fields — noise (FIX candidate)

302 `title:` lines, and **none carries hand-authored information**. Pydantic derives
them mechanically: field titles are the title-cased field name (`Current Max Ma`,
`Device Id`, `Time Us`), and model/enum titles echo the class name (`ErrorType`×20,
`Error`×19, `ProfileStep`×8). Every field already has a hand-written `description`
sitting directly beside the title, which is where the meaning lives — e.g.
`close_device.yaml` lines 8–11:

```yaml
device_id:
  description: Handle returned by open_device   # hand-written, meaningful
  title: Device Id                              # mechanical restatement of the key
  type: string
```

Roughly ~180 of the 302 title lines are field-level restatements. Suppressing
field titles is a single, verified generator change (a `GenerateJsonSchema`
subclass overriding `field_title_should_be_set(...) -> False`, or dropping the
`title` key in the dump post-process). Model/enum titles name the schema and are
worth keeping. Two non-working alternatives were noted: `field_title_generator`
returning `None` raises `TypeError` in pydantic 2.13.4, and per-field
`Field(title=...)` would require touching every model.

### 4.2 Missing `$schema` keyword — genuinely uncertain (KEEP for now)

No file declares a `$schema` (JSON Schema draft) keyword. Pydantic omits it; its
target dialect is draft 2020-12, which matches the emitted shapes. Adding it is a
trivial, zero-risk one-line-per-file generator change
(`js["$schema"] = self.schema_dialect`). But its benefit is **entirely contingent
on a JSON-Schema validator becoming a consumer**, and today there is none. A
`$schema` line no tool reads is decoration. This is the one issue where the
no-consumer fact neutralizes the value: correct, trivial, currently pointless.

### 4.3 Redundant `{SchemaName: {...}}` wrapper on component files — not a clear win (KEEP)

Every component file wraps its schema under a top-level `{SchemaName: {...}}`
mapping, even single-schema files. Collapsing it is safe (nothing addresses these
files by JSON pointer; the index points at whole files), but it would introduce a
**new inconsistency**: two component files legitimately hold multiple schemas —
`profile.yaml` (`ProfileStep` + `Profile`) and `error_envelope.yaml`
(`ErrorType` + `Error`) — and those *need* the mapping. Collapsing only
single-schema files gives component files two different root shapes (bare schema
vs. name→schema map), which a consumer would have to branch on. This is arguably
worse than the uniform-but-redundant status quo. The generator already flags this
as deferred (see §6).

### 4.4 The repeated `Error`/`ErrorType` reply envelope — real, but the same problem as the seed

Every operation `reply` is a discriminated `oneOf` of `{<Op>Ok, Error}` with
`discriminator.propertyName: status` and `mapping: {ok: ..., error: ...}`. The
`Error`+`ErrorType` envelope is identical across all 18 replies (byte-identical;
verified by diffing `read_parameters` and `close_device`). This is not a separable
issue — it is the highest-yield instance of the §1/§3 duplication, and factoring
it out requires the same cross-file-`$ref` mechanism (the discriminator `mapping`
value `#/$defs/Error` would become a cross-file pointer). See the plan document.

### 4.5 `operations.yaml` index advertises a modularity the operations don't use — uncertain

The index lists all 12 component files under a `components:` map (header line 58,
entries 59–70), yet **no operation schema `$ref`s any component file** — every
reply re-inlines its own `$defs`. The linkage exists only in the index, implying a
reuse that does not exist in the operation schemas. It is harmless
forward-looking scaffolding that becomes correct automatically once the cross-file
`$ref` refactor lands; flagged so it is tracked with that work rather than treated
as a defect.

### 4.6 Description normalization flattens multi-paragraph docstrings — deliberate (KEEP)

`_normalize_descriptions` in the generator does `" ".join(value.split())`,
collapsing every docstring (including deliberate paragraph breaks, e.g.
`ErrorType`'s multi-sentence rationale) into one run-on line. The inline
justification claims PyYAML can only encode embedded newlines via blank physical
lines — which is **overstated** (PyYAML can preserve newlines with a literal block
scalar `|`). So the flattening is a choice for dump simplicity/determinism, not a
hard PyYAML limit. It is a mild readability degradation, but preserving structure
would complicate deterministic dumping for cosmetic gain. Kept — with the caveat
that the docstring's stated reason should not be read as a hard constraint.

---

## 5. Investigated and judged NOT a real problem

- **`additionalProperties: false` on every object schema — KEEP (load-bearing).**
  It appears on exactly the 81 object schemas and nowhere else (absent on the 36
  enum blocks, which is correct — enums are not objects). It is the JSON-Schema
  encoding of `extra="forbid"` from `ContractModel` in
  `contract/mightex_contract/base.py`, a real validation rule at the client/server
  seam. It is uniform *because the rule is uniform*, not because it is filler.
  There is no single place to hoist it to (schemas live inlined under per-file
  `$defs`), and stripping it would make each schema silently permissive to any
  validator reading it in isolation — the opposite of intent. The redundancy is
  the price of each object schema being independently valid.

- **YAML anchors/aliases (`&`/`*`) as a dedup shortcut — REJECT (wrong tool).**
  (1) Anchors are document-scoped, so they cannot cross files — they do nothing for
  the primary cross-file duplication; they could only touch the two intra-file
  self-copies (§2). (2) They break the JSON-Schema story: a YAML loader *expands*
  every alias back into a duplicated node on load (the consumer sees no dedup), and
  a non-YAML resolver never sees them at all — while some strict loaders choke on
  `&`/`*`. Anchors also obscure structure for the human auditors the committed YAML
  exists for. JSON-Schema `$ref` is the native, tooling-portable, cross-file dedup
  mechanism and is strictly better here.

- **Enums lacking `additionalProperties` — non-finding.** Enums are
  `type: string`/`type: integer`, so `additionalProperties` is meaningless there.
  Its absence is correct, not an inconsistency.

- **`<Operation>Ok` reply wrappers having no canonical file — by design.** The 18
  `<Op>Ok` models (`CloseDeviceOk`, `ReadParametersOk`, …; 249 lines total) are
  genuinely unique per operation — each names its own `status: ok` + result shape —
  so they are correctly *not* counted in the 1537 duplicated lines, and a shared
  file for them would be artificial. This bounds how far the envelope factoring can
  go: `Error` can be externalized, the `Ok` wrappers cannot.

- **`Profile` array wrapper — dead weight, but not duplication.** `Profile`
  (`profile.yaml` lines 25–53) is never copied or `$ref`d anywhere; consumers embed
  `ProfileStep` directly via `items: {$ref: '#/$defs/ProfileStep'}` + `maxItems: 127`.
  It is genuinely unused, but it is a single dead shape, not a driver of the
  verbosity number.

---

## 6. Known & deferred (acknowledged debt, not oversights)

The generator itself already flags the two largest structural items as intentional
deferrals:

- **Cross-file `$ref` / inlined `$defs` duplication** — `generate_schemas.py`
  docstring: *"each operation file is generated independently, so shared component
  schemas … are inlined under `$defs` in every file that references them. … This
  duplication is accepted for now: each operation file is self-contained and
  independently valid. Emitting a shared `$defs` with cross-file `$ref` (pydantic's
  default `ref_template` is intra-file only) is a noted later refinement."*

- **The redundant `{SchemaName}` wrapper** — `generate_schemas.py` `COMPONENTS`
  comment: *"each file keeps a top-level `{SchemaName: schema}` mapping … Collapsing
  that now redundant wrapper key is a deferred refinement, intentionally left out
  here so the generated component root shape stays unchanged by this split."*

- **Single-line descriptions** — the `_normalize_descriptions` flattening is
  deliberate (§4.6).

The `docs/temp_mightex_knowledge_transfer.md` knowledge-transfer note corroborates
both deferrals. These are acknowledged debt, not accidents.

---

## 7. Determinism context (why the timing matters)

RESOLVED (pinning): `pyproject.toml` now pins `pydantic==2.13.4` and
`schemas = ["pyyaml==6.0.3"]`, matching the versions that produced the committed
output — so a minor bump can no longer silently shift title generation, key
ordering, `$ref`/`$defs` shape, or line-wrapping. The generator docstring's
assumption of a pinned pydantic now holds.

Still open: **no `.github/` and no regenerate-and-diff test exist yet** (`tests/`
holds only `.gitkeep` files), so the staleness guard is not yet implemented. The
practical consequence for this audit stands: **regenerating/normalizing the output
is free today and becomes churn-expensive the moment a golden-file staleness test
lands** — so shape changes are best made before that test is written.

## 8. Honesty about uncertainty

- The `$schema` benefit (§4.2) and the index-vs-schema inconsistency (§4.5) are
  judged *uncertain*, not clear wins/defects — both hinge on a future consumer that
  does not exist today.
- All duplication counts were verified to 0 content mismatches; the only errors
  found in the source analysis were two non-load-bearing aggregate cells (now
  corrected to 69/55 in §1).
- Whether a downstream OpenAPI/JSON-Schema consumer would accept an *external*
  discriminator `mapping` target (relevant to the envelope factoring) could not be
  verified — no validator is installed and no consumer exists. This is carried
  forward as an open feasibility question in the refinement plan, not asserted to
  "just work."
