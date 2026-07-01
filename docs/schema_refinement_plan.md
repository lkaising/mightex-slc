# Contract Schema Refinement — Loose Plan

## Direction and why

The audit (`docs/schema_verbosity_audit.md`) found that **1537 of 2727 lines
(56.4%)** across the 30 generated schema files are verbatim copies of shapes that
already own a canonical component file, dominated by the `Error`/`ErrorType`
envelope inlined into all 18 replies (844 lines, 55% of the total). The goal of
this plan is to make `contract/schemas/` **tighter and less redundant while keeping
it a trustworthy generated + CI-diffed artifact**: every change is a generator
change (never a hand-edit of the YAML), deterministic, and re-derivable from the
Pydantic models.

Two facts shape the sequencing:

1. **No consumer window.** Nothing reads `contract/schemas/` today, and no
   regenerate-and-diff CI job exists yet (no `.github/`; `tests/` is empty
   `.gitkeep`s). Changing the output shape is essentially free right now and becomes
   churn-expensive once a golden-file staleness test freezes it. This plan front-
   loads the cheap generator passes to land *before* that test.

2. **Feasibility is proven for the hard part, but one downstream question is open.**
   A cross-file-`$ref` externalization was prototyped end-to-end and independently
   reproduced: it produces deterministic, dangling-free output across all 30 files.
   The one unverified point — whether a strict future consumer accepts an *external*
   discriminator `mapping` target — is called out per-task rather than assumed away.

Tasks are grouped as **cheap-and-safe** (independent, low-risk generator passes)
and **the larger cross-file-`$ref` change** (one coherent refactor covering the
bulk of the duplication).

---

## Cheap-and-safe tasks (independent; land these first)

### Task A — Suppress auto-generated field `title`s

**Rationale (audit §4.1):** ~180 of 302 `title:` lines are mechanical restatements
of the field key, sitting next to a real hand-written `description`. They are pure
diff/review noise.

**Before / after:**

```yaml
# before — close_device.yaml
device_id:
  description: Handle returned by open_device
  title: Device Id            # drop this
  type: string
# after
device_id:
  description: Handle returned by open_device
  type: string
```

Implement via a `GenerateJsonSchema` subclass overriding
`field_title_should_be_set(...) -> False` (verified to remove field titles while
keeping model/enum titles), or by dropping `title` keys in the dump post-process.
Keep model/enum-level titles (they name the schema). Do **not** use
`field_title_generator` returning `None` (raises `TypeError` in pydantic 2.13.4).

**Costs vs buys:** Costs — a small generator subclass/override and a one-time full
regeneration; determinism unaffected (deletion only). Buys — removes ~180 noise
lines and the case-mangled `Current Max Ma`/`Device Id` restatements from every
review diff.

### Task B — Pin pydantic and pyyaml exactly

**Rationale (audit §7):** the docstring assumes a "pinned pydantic," but
`pyproject.toml` has `pydantic>=2,<3` (a range) and `pyyaml` unpinned. Either bump
can silently change generated output — the exact drift the future staleness test is
meant to police.

**Before / after:**

```toml
# before                         # after
"pydantic>=2,<3"                 "pydantic==2.13.4"
schemas = ["pyyaml"]             schemas = ["pyyaml==6.0.3"]
```

**Costs vs buys:** Costs — routine dependency-bump friction (must regenerate when
bumping). Buys — makes the committed bytes reproducible, which is a precondition for
the staleness diff to be meaningful rather than flaky. **Do this before any other
task and before the CI diff is written.**

### Task C — Add `$schema` (deferred; do NOT do now)

**Rationale (audit §4.2):** a one-line, zero-risk add of the draft-2020-12
identifier (`js["$schema"] = self.schema_dialect`) would let a validator self-
identify the dialect — but no validator consumes these files, so it is currently
decoration.

**Before / after (for when a consumer appears):**

```yaml
# before (file head)              # after
ErrorType:                        $schema: https://json-schema.org/draft/2020-12/schema
  ...                             ErrorType:
                                    ...
```

**Costs vs buys:** Costs — trivial; adds one line per file to the diff for no
present reader. Buys — nothing today; removes dialect ambiguity the moment a
JSON-Schema validator becomes a consumer. **Recommendation: skip until a real
consumer exists, then bundle into the same generator pass.**

### Task D — Leave the `{SchemaName}` wrapper and description flattening as-is (explicit no-ops)

**Rationale (audit §4.3, §4.6):** collapsing the single-schema wrapper would split
component files into two different root shapes (multi-schema `profile.yaml` /
`error_envelope.yaml` still need the map), trading uniform redundancy for an
inconsistency a consumer must branch on. Description flattening is a deliberate
determinism choice. Both are generator-flagged deferrals. Recorded here so they are
not silently "fixed."

**Costs vs buys:** Not acting buys uniform file shape and dump simplicity; the cost
is one redundant wrapper key per component file and single-line descriptions —
accepted. Revisit the wrapper only if the project commits to one-schema-per-file
everywhere.

---

## The larger change — cross-file `$ref` externalization

This single refactor covers the bulk of the audit's headline number: the §3 catalog
(the `Error`/`ErrorType` envelope, the ProfileStep family, `ModuleType`, etc.) and
both intra-file self-copies. It is one coherent task with sub-parts; the sub-parts
share the same mechanism and should ship together, because externalizing only part
of a reply's `$defs` leaves the rest duplicated.

**Approach (recommended: post-processing rewrite, prototyped and independently
verified).** Generate each schema normally with pydantic, then run an externalize
pass over the emitted dict: for every pointer — both `{$ref: ...}` **and every
`discriminator.mapping` value** — if it is `#/$defs/<Name>` and `<Name>` owns a
component file, rewrite it to `<prefix><stem>.yaml#/<Name>` (or `#/<Name>` for a
same-file sibling), mark `<Name>` for deletion from `$defs`, then delete and
iteratively GC any inline def no longer referenced. `prefix` is `../components/`
from operation files and `` between sibling component files. Drive it from a static
`name → component-file-stem` table derivable from the existing `COMPONENTS` map.

A `GenerateJsonSchema` subclass produces byte-identical output but leans on
semi-private pydantic internals (`get_cache_defs_ref_schema`, the
`core_to_json_refs`/`json_to_defs_refs` bookkeeping) — riskier under the version-
pinned determinism regime, so the post-processor is preferred.

### Sub-task E1 — Externalize the `Error`/`ErrorType` reply envelope (highest yield)

**Rationale (audit §3, §4.4):** the envelope is 844 of 1537 duplicated lines (55%),
identical across all 18 replies.

**Before / after (reply of `close_device.yaml`):**

```yaml
# before — full Error + ErrorType inlined under reply.$defs (lines 29-74)
reply:
  $defs:
    CloseDeviceOk: { ... }
    Error: { ...30 lines... }
    ErrorType: { ...16 lines... }
  discriminator:
    mapping: {error: '#/$defs/Error', ok: '#/$defs/CloseDeviceOk'}
    propertyName: status
  oneOf:
  - {$ref: '#/$defs/CloseDeviceOk'}
  - {$ref: '#/$defs/Error'}
# after — Error/ErrorType gone; only the local Ok remains
reply:
  $defs:
    CloseDeviceOk: { ... }
  discriminator:
    mapping: {error: ../components/error_envelope.yaml#/Error, ok: '#/$defs/CloseDeviceOk'}
    propertyName: status
  oneOf:
  - {$ref: '#/$defs/CloseDeviceOk'}
  - {$ref: ../components/error_envelope.yaml#/Error}
```

### Sub-task E2 — Externalize the remaining shared components (replies and requests)

**Rationale (audit §3):** the ProfileStep family (ProfileStep, StrobeParameters,
TriggerParameters, TriggerPolarity, ChannelState) plus `ModuleType`,
`OperatingMode`, `NormalParameters`, `DeviceDescriptor`, `DeviceInfo`,
`ControllerCapabilities` make up the rest. Request-side too:
`configure_strobe`/`configure_trigger` → `profile.yaml#/ProfileStep`,
`set_active_mode` → `operating_mode.yaml#/OperatingMode`.

**Before / after (reply of `read_parameters.yaml`):**

```yaml
# before — 9 shared shapes inlined (183 of 230 lines)
reply:
  $defs:
    ChannelState: {...}  NormalParameters: {...}  StrobeParameters: {...}
    TriggerParameters: {...}  OperatingMode: {...}  ProfileStep: {...}
    TriggerPolarity: {...}  Error: {...}  ErrorType: {...}
    ReadParametersOk: {properties: {result: {$ref: '#/$defs/ChannelState'}}}
# after — only the local Ok remains
reply:
  $defs:
    ReadParametersOk:
      properties:
        result: {$ref: ../components/channel_state.yaml#/ChannelState}
```

### Sub-task E3 — Decompose two-layer component embeds and intra-file self-copies

**Rationale (audit §2):** `channel_state.yaml` re-inlines 6 siblings (114/140
lines); `error_envelope.yaml` and `profile.yaml` each carry a shape twice.

**Before / after (`channel_state.yaml`, and the double-`ErrorType` fix):**

```yaml
# before — channel_state.yaml embeds 6 sibling components under ChannelState.$defs
# after  — each field refs its direct child; no nested $defs
ChannelState:
  properties:
    active_mode: {$ref: ../operating_mode.yaml#/OperatingMode}
    normal:      {$ref: ../normal_parameters.yaml#/NormalParameters}
    strobe:      {$ref: ../strobe_parameters.yaml#/StrobeParameters}
    trigger:     {$ref: ../trigger_parameters.yaml#/TriggerParameters}
# error_envelope.yaml: nested Error.$defs.ErrorType copy removed
Error:
  properties:
    error_type: {$ref: '#/ErrorType'}   # sibling ref, no re-inlined enum
```

The chain decomposes file-by-file (`channel_state → strobe_parameters → profile`),
each file ref-ing only its direct children. Verified: after this pass every
component file carries no nested `$defs` (members either flatten or use intra-file
`#/<Name>` sibling refs), and 0 dangling pointers remain.

### Sub-task E4 — (Optional) Remove the dead `Profile` wrapper

**Rationale (audit §5):** `Profile` (`profile.yaml` lines 25–53) is never copied or
`$ref`d; consumers embed `ProfileStep` directly. Low priority, orthogonal to the
duplication number; only worth doing if `profile.yaml` is being touched anyway.

---

### Costs, risks, and feasibility notes for the cross-file change (E1–E4)

- **Verified feasible and deterministic.** Prototyped end-to-end and independently
  reproduced: residual `$defs` = exactly the per-operation `<Op>Ok` model (requests
  and component files end with none), 0 dangling pointers, byte-identical output
  across two runs. Determinism holds because the pass only deletes keys and rewrites
  string values in place, and pydantic pre-sorts `$defs`/`mapping` keys while
  `oneOf` is order-preserving.
- **Load-bearing implementation caveat:** the walker MUST rewrite
  `discriminator.mapping` values, not just `$ref` keys — the mapping values are bare
  pointer strings, and a `$ref`-only walker leaves them dangling
  (`mapping.error: '#/$defs/Error'` after `Error` is deleted). Add an assertion that
  no `#/$defs/<X>` survives for an externalized `<X>` in either location, plus the
  iterative GC of orphaned inline defs.
- **Cost — loss of single-file portability:** each operation file stops being
  independently valid; validating `read_parameters.yaml` now requires resolving
  `../components/…`, which chain further. A validator must be pointed at the whole
  `schemas/` tree with relative-file `$ref` resolution. This breaks **no current
  contract** (no consumer exists) and is reversible (regenerated, not hand-kept).
- **Open feasibility question — external discriminator target (UNVERIFIED):**
  whether a strict OpenAPI/JSON-Schema consumer accepts an *external* `mapping`
  value (`../components/error_envelope.yaml#/Error`) could not be tested — no
  validator is installed and no consumer exists. Pure JSON-Schema validators ignore
  `discriminator` and validate via `oneOf` + standard external `$ref`, which
  resolves; OpenAPI permits a `$ref`-style mapping target. But if a future consumer
  requires locally-resolvable discriminator targets, the safe fallback is to **keep
  `Error`/`ErrorType` inline in replies** (skip E1) while still externalizing all
  non-discriminator refs (E2/E3). Do not assert E1 "just works" against an unknown
  consumer.
- **Pre-existing wrapping caveat (unchanged by this work):** the internal
  `#/$defs/<Ok>` refs resolve only if each `request`/`reply` is treated as its own
  document root; resolved against the whole operation-file root they would need
  `#/reply/$defs/<Ok>`. This is already true of the *current* committed files and is
  not introduced by externalization — but state it alongside the "resolve the whole
  tree" note so a future consumer is not surprised.
- **Buys:** eliminates the bulk of the 1537 duplicated lines — E1 alone removes
  844, E1–E3 together reach ~76% of all duplication — collapsing review/diff burden
  and the drift risk of N hand-syncable copies down to one canonical definition per
  shape.

---

## How the tasks move the schemas toward the goal

Task B makes the output reproducible so a staleness diff can be trusted; Task A
strips the largest class of pure noise; Tasks C and D are recorded, deliberate
holds. The cross-file-`$ref` refactor (E1–E4) then converts the artifact from "18
self-contained files that each re-inline every shape they touch" into "one canonical
definition per shape, referenced everywhere" — cutting the duplication from 56.4% of
lines toward the ~24% floor of genuinely unique content (per-operation requests,
`<Op>Ok` wrappers, and the discriminator glue). All of it stays generator-produced
and deterministic, so the schemas remain a trustworthy, CI-diffable projection of
the Pydantic source of truth — just a much tighter one. Doing the cheap passes and
the refactor **now**, in the no-consumer window and before a golden-file test
freezes the shape, is what makes this cheap rather than a churn-heavy migration
later.
