# Migrating off `fprime-python-model`

`fprime-python-model` is deprecated. The final supported release will be for F Prime 4.4.0 (fpp 3.4.0).

It translated the JSON that `fpp-to-json` emitted
— an AST dump, a location map and an analysis dump — into Python data structures, and
carried a port of `fpp-to-cpp`'s Scala `CppDoc` writer alongside it.

Both halves have been replaced, and the JSON pipeline is gone:

| What you used it for | Use instead | Import as |
| --- | --- | --- |
| Reading the FPP model | [`fprime-fpp-python`](https://pypi.org/project/fprime-fpp-python/) | `fpp` |
| Writing C++ | [`fprime-cpp-codegen`](https://pypi.org/project/fprime-cpp-codegen/) | `fprime_cpp_codegen` |
| Listing an autocoder's output files at CMake configure time | `fprime-fpp-query` | `fpp-query` (a binary) |

`fprime-fpp-python` binds the Rust FPP compiler in-process through PyO3. There is no
JVM, no `fpp-to-json` step, no JSON on disk, and no
`FPRIME_ENABLE_JSON_MODEL_GENERATION`. You hand it `.fpp` files and get a typed,
navigable object graph with real cross-references, compiler diagnostics you can extend,
and full type stubs.

`fprime-cpp-codegen` is the C++ writer, extracted and rebuilt as a builder API. It has
no dependency on `fpp` or on any FPP model — it generates general-purpose C++.

Most of the model API survives under a new spelling; the parts that genuinely change
shape are the AST node wrapper, cross-references, and the visitor.

---

## Contents

- [Migrating off `fprime-python-model`](#migrating-off-fprime-python-model)
  - [Contents](#contents)
  - [Install](#install)
    - [Drop the JSON pipeline](#drop-the-json-pipeline)
  - [Loading a model](#loading-a-model)
  - [API map](#api-map)
    - [Model and analysis](#model-and-analysis)
    - [AST nodes, annotations and locations](#ast-nodes-annotations-and-locations)
    - [Cross-references](#cross-references)
    - [Visitors](#visitors)
    - [Symbols, types and values](#symbols-types-and-values)
    - [Topologies and connections](#topologies-and-connections)
    - [Dictionaries](#dictionaries)
    - [Diagnostics](#diagnostics)
  - [The C++ writer](#the-c-writer)
    - [Mechanical renames](#mechanical-renames)
    - [New capabilities worth adopting](#new-capabilities-worth-adopting)
    - [Behaviour changes to check for](#behaviour-changes-to-check-for)
  - [Autocoders: the two phases](#autocoders-the-two-phases)
    - [Configure time with `fpp-query`](#configure-time-with-fpp-query)
    - [Configure time in Python](#configure-time-in-python)
    - [Build time](#build-time)
    - [The CMake shim](#the-cmake-shim)
  - [A worked autocoder](#a-worked-autocoder)
  - [Tools outside the build](#tools-outside-the-build)
  - [Testing an autocoder](#testing-an-autocoder)
  - [Known gaps](#known-gaps)
  - [Checklist](#checklist)

---

## Install

```sh
pip install fprime-fpp-python fprime-cpp-codegen fprime-fpp-query
```

Pin them, as you would any autocoder dependency — a generated-code toolchain that
floats will change your build output under you:

```
# requirements.txt
fprime-fpp-python==3.3.24
fprime-cpp-codegen==0.2.0
fprime-fpp-query==3.3.24
```

`fprime-fpp-python`'s version tracks the FPP language version it implements (`3.3.x`),
so pinning it pins the grammar and the semantics your autocoder was written against.
It ships as an `abi3` wheel usable on CPython ≥ 3.10, with `py.typed` and a complete
`fpp/__init__.pyi`. `fprime-cpp-codegen` is pure Python, also ≥ 3.10, with no runtime
dependencies. `fprime-fpp-query` is a wheel that installs the `fpp-query` executable —
there is no Python module in it.

Both Python packages are fully typed, and running `mypy --strict` over your autocoder is
the cheapest way to find everything this guide describes. That is how most of the
renames below were caught during the first port.

The CMake side assumes F Prime ≥ v4.0.0, which is where the
`AUTOCODER_GENERATED_*` return-value contract used in
[The CMake shim](#the-cmake-shim) was introduced.

### Drop the JSON pipeline

Delete every trace of the old artifacts. In particular:

```cmake
# Delete this. It adds an `fpp_to_json` target to the `info-cache` sub-build (between
# `fpp_depend` and `module_info`), which the main configure builds on every run;
# `fpp-to-json` — a JVM launch — then re-runs for every module whose FPP closure changed.
set(FPRIME_ENABLE_JSON_MODEL_GENERATION ON)
```

Also remove it from `default_cmake_options` in `settings.ini` and from any `-D` on the
`cmake` command line. Then delete the code that located `fpp-ast.json`,
`fpp-loc-map.json` and `fpp-analysis.json` in the build tree — there is nothing to
locate any more.

---

## Loading a model

**Before** — three JSON files, produced by a separate tool, found by guessing at build
tree layout:

```python
from fprime_python_model.model import FprimePythonModel

model = FprimePythonModel(
    str(json_dir / "fpp-ast.json"),
    str(json_dir / "fpp-loc-map.json"),
    str(json_dir / "fpp-analysis.json"),
)
```

**After** — the sources themselves:

```python
import sys

import fpp


def main() -> int:
    model = fpp.analyze(["MyComponent.fpp"], imports=["Fw/Fw.fpp"])

    for diagnostic in model.diagnostics:
        print(diagnostic.render(color=sys.stderr.isatty()), file=sys.stderr)
    if model.has_errors:
        return 1
    ...
    return 0
```

`imports=` is the counterpart of `fpp-to-cpp -i`: those units are analyzed together
with yours but are not part of what you asked about, so
`[u.uri for u in model.ast if u.is_source]` gives back exactly your own inputs. A bare
string is a path; `source=` is text, which makes every example in this guide runnable
without a build tree:

```python
model = fpp.analyze(source="module M { array Arr = [4] U32 }")
```

`fpp.analyze` returns a `Model`. There is also `fpp.parse`, the fast front end, which
stops after `include` resolution and returns a `SyntaxTree` — syntax only, nothing
resolved, and no `imports=` parameter because nothing at that depth reads another
translation unit. It is what the configure-time half of an autocoder wants; see
[Configure time in Python](#configure-time-in-python).

**Diagnostics are now yours to report.** The old package raised Python exceptions out
of its translators. `analyze` collects compiler diagnostics into `model.diagnostics`
and tells you whether any were errors. Print them and exit non-zero; never let a
`fpp.DiagnosticError` reach the user as a traceback.

---

## API map

### Model and analysis

| Before | After |
| --- | --- |
| `FprimePythonModel(fpp_ast_json_file, fpp_locations_json_file, fpp_analysis_json_file)` | `fpp.analyze(paths=None, *, source=None, uri='<string>', imports=None)` |
| — | `fpp.parse(paths=None, *, source=None, uri='<string>')` → `SyntaxTree` |
| `model.ast` → `List[TransUnit]` | `model.ast` → `list[TransUnit]` |
| `model.analysis` | `model.analysis` |
| `model.location_map`, `model.get_location(node)` | `node.location` / `node.span` — see [locations](#ast-nodes-annotations-and-locations) |
| `model.ast_id_map`, `model.annotated_ast_id_map` | gone — cross-references are objects |
| — | `model.diagnostics`, `model.has_errors`, `model.error_count` |
| — | `model.lookup(qualified_name, *, kind=None)`, `model.lookup_all(...)` |
| `fpp_version.check_version(...)` | gone — pin the package instead |

`Analysis` keeps the same flat-bag-of-maps shape, but **the entity maps are now keyed
by `Symbol`, not by `AstId`**:

| Before (`Dict[AstId, T]`) | After (`dict[Symbol, T]`) |
| --- | --- |
| `analysis.component_map` | `analysis.component_map` |
| `analysis.component_instance_map` | `analysis.component_instance_map` |
| `analysis.interface_map` | `analysis.interface_map` |
| `analysis.topology_map` | `analysis.topology_map` |
| `analysis.state_machine_map` | `analysis.state_machine_map` |
| `analysis.dictionary_map` | `analysis.dictionary_map` |
| — | `analysis.system_map` |

`use_def_map`, `type_map` and `value_map` are still keyed by the integer node id, as are
the new `symbol_map` and `implied_use_map`. `parent_symbol_map` and `symbol_scope_map`
were keyed by `AstId` and are now keyed by `Symbol`. `location_specifier_map` is keyed
by a `(SpecLocKind, QualifiedName)` tuple.

Two consequences worth knowing:

```python
# Iterating is the same shape as before.
for component in model.analysis.component_map.values():
    ...

# But lookup by name no longer needs a hand-rolled qualified-name walk.
symbol = model.lookup("Ref.Producer")          # -> Symbol | None
component = model.analysis.component_map[symbol]
```

`lookup` takes an optional `kind=` because a qualified name is not unique — `Fw.Time`
is both a type and a port in F Prime's own `Time.fpp`. Pass the `Symbol` subclass you
want, or use `lookup_all` and decide yourself.

> **`Analysis.get_component` and friends resolve a *use site*, not a definition.**
> `get_component`, `get_component_instance`, `get_topology`, `get_interface`,
> `get_dictionary`, `get_interface_symbol` and `get_topology_symbol` look their argument
> up through the use-def map, so they want the `Ident` / `Qualified` that *names* the
> definition — `instance.node.component`, `system.node.topology` — not the
> `DefComponent` / `DefTopology` itself. Handed a definition node they return `None`,
> and because they are all `Optional`, the failure is silent. To go from a definition to
> its entity, use `model.lookup(...)` or `component_map[symbol]`.

### AST nodes, annotations and locations

This is the largest change in day-to-day feel. The old AST wrapped every node:

```python
AstNode(Generic[T])          # .data is the payload, .get_id() is the AstId
Annotated[T] = Tuple[List[str], T, List[str]]    # (pre, node, post)
```

so you wrote `component.a_node[1].data.name` to reach a name, `component.a_node[0]` to
reach the annotations, and `model.get_location(component.a_node[1])` to reach a
location. The new AST has one class per node kind, with the payload, the annotations
and the location all on the node:

| Before | After |
| --- | --- |
| `node.data` (the payload) | the node itself — `node.name`, `node.members`, … |
| `node.get_id()` / `node._id` | `node.node_id` |
| `annotated[0]` (pre-annotation list) | `node.pre_annotation` → `list[str]` |
| `annotated[2]` (post-annotation list) | `node.post_annotation` → `list[str]` |
| `annotated[1]` (the node) | the node — there is no tuple |
| `model.get_location(node)` → `Location` | `node.location` → `Loc` |
| — | `node.span` → `Span`, which is what `Diagnostic(span=…)` takes |
| — | `node.in_source`, `node.children` |
| `isinstance(node.data, fpp_ast.DefComponent)` | `isinstance(node, fpp.DefComponent)` |

> **`Loc` and `Span` line/column numbers are 0-indexed.** `Loc` has `uri`, `line`,
> `column`, `end_line`, `end_column` and `display`; `Span` has the same getters plus
> `resolve()`. The four line/column fields are **0-indexed** — only `display` is the
> 1-indexed `file:line:col` string a compiler prints. Use `display` (or `span.display`)
> for anything a human reads, and add 1 yourself if you need the numbers separately.
> Every node has a location; none of this is `Optional`.

Annotation lines arrive with the `@` or `@<` sigil stripped and the line trimmed, one
list element per line — which is what makes the annotation-driven autocoder pattern
work:

```python
def annotated_components(model, annotation):
    """Yield every Component carrying `@ <annotation>` on its own line."""
    for component in model.analysis.component_map.values():
        if (annotation in component.node.pre_annotation
                or annotation in component.node.post_annotation):
            yield component
```

Note `in` is list membership over whole lines, so the marker must sit on its own `@`
line, with any human-readable prose on the line below it.

### Cross-references

The old model stored cross-references as `AstId`s and made you resolve them through
`model.ast_id_map` or one of the `Analysis` maps. They are now direct object
references, and the three universal resolvers live on every AST node:

| Before | After |
| --- | --- |
| `analysis.use_def_map[node.get_id()]` | `node.definition` → `Optional[Symbol]` |
| `analysis.type_map[node.get_id()]` | `node.resolved_type` → `Optional[Type]` |
| `analysis.value_map[node.get_id()]` | `node.resolved_value` → `Optional[Value]` (then `.value` for the payload) |
| `analysis.get_qualified_name_from_map(Symbol.construct(c.a_node))` | `component.symbol.qualified_name` |
| `instance.ci.component` | `instance.component` |

```python
model = fpp.analyze(source="module M { array Arr = [4] U32\n constant answer = 6 * 7 }")

model.lookup("M.Arr").definition.resolved_type.array_size        # 4
model.lookup("M.answer").definition.value.resolved_value.value   # 42
```

The maps are still there when you want them; the getters are the spelling to reach for.

### Visitors

The old `AstVisitor` was a Scala-style dispatch table: an ABC generic in
`(In, Out)`, one abstract `default(_in)` you had to implement, and one snake-case
method per node kind that threaded a state value. `AstStateVisitor` layered the
state-threading helpers on top.

```python
# Before
class Mine(AstVisitor[State, State]):
    def default(self, s): return s
    def def_component_annotated_node(self, s, node): ...
```

`fpp.AstVisitor` is the Python `ast.AstVisitor` shape: one `visit_<ClassName>` per
node kind, and **traversal is deep by default**.

```python
# After
class Components(fpp.AstVisitor):
    def __init__(self):
        self.names = []

    def visit_DefComponent(self, node):
        self.names.append(node.name)
        super().visit_DefComponent(node)      # descend; omit to prune
```

| Before | After |
| --- | --- |
| `AstVisitor[In, Out]`, abstract `default` | `fpp.AstVisitor`, no abstract members |
| `def_component_annotated_node(self, _in, node)` | `visit_DefComponent(self, node)` |
| snake_case, `_annotated_node` suffix | `visit_` + the exact class name |
| you drove the walk and threaded state | `visit()` drives it; keep state on `self` |
| `AstStateVisitor`, `visit_list` | no counterpart — state lives on `self` |
| — | `generic_visit(node)`, `visit_Model`, `visit_SyntaxTree`, `visit_TransUnit` |

`visit()` accepts a `Model`, a `SyntaxTree`, a `TransUnit` or any node, so the same
visitor runs over an analyzed model and over a `parse` result. Calling `super()` in a
`visit_*` method descends; omitting it prunes that subtree. Overriding
`generic_visit` to a no-op inverts the default — the walk then stops everywhere except
the kinds you explicitly re-open, which is how you write a cheap shallow scan:

```python
class DeploymentTopologies(fpp.AstVisitor):
    """Find `deployment topology` definitions without descending into their bodies."""

    def __init__(self):
        self.found = []

    def generic_visit(self, node):
        pass                                  # shallow by default

    def visit_DefModule(self, node):
        super().generic_visit(node)           # but descend through modules

    def visit_DefTopology(self, node):
        if node.is_deployment:
            self.found.append(node)
```

One structural improvement worth knowing if you worked around it before: the walk no
longer stops at the component boundary, so per-component elements (commands, events,
telemetry channels, parameters, records, containers, ports, state-machine instances)
are reachable both by descending the AST and through `Component`'s own maps. The old
package needed those maps hoisted to analysis level by hand.

### Symbols, types and values

Symbol classes moved from a `*Symbol` suffix to a `Symbol*` prefix, and the type
symbols picked up the `Type` suffix the corresponding `Type` classes already had:

| Before | After |
| --- | --- |
| `Symbol` / `SymbolInterface` (bases) | `SymbolBase`; `Symbol` is the union of the concrete classes |
| `AbsTypeSymbol` | `SymbolAbsType` |
| `AliasTypeSymbol` | `SymbolAliasType` |
| `ArraySymbol` | `SymbolArrayType` |
| `StructSymbol` | `SymbolStructType` |
| `EnumSymbol` | `SymbolEnumType` |
| `EnumConstantSymbol` | `SymbolEnumConstant` |
| `ConstantSymbol` | `SymbolConstant` |
| `PortSymbol` | `SymbolPort` |
| `ModuleSymbol` | `SymbolModule` |
| `SystemSymbol` | `SymbolSystem` |
| `ComponentSymbol` | `SymbolComponent` |
| `ComponentInstanceSymbol` | `SymbolComponentInstance` |
| `InterfaceSymbol` | `SymbolInterface` |
| `StateMachineSymbol` | `SymbolStateMachine` |
| `TopologySymbol` | `SymbolTopology` |
| `TypeSymbol`, `InterfaceInstanceSymbol` (intermediate bases) | no counterpart — use `SymbolBase` |
| `symbol.get_node_id()` | `symbol.node_id` |
| `analysis.get_qualified_name_from_map(symbol)` | `symbol.qualified_name`, or `analysis.get_qualified_name(symbol)` |
| — | `symbol.unqualified_name`, `symbol.parent`, `symbol.is_dictionary_def` |

Semantic types are closed unions — narrow with `isinstance` or `match`, never a string
tag:

```python
match a_type:
    case fpp.StringType():
        ...
    case fpp.StructType() as s:
        for name, member in s.anon_struct.members:      # declaration order
            ...
    case fpp.ArrayType() as a:
        elt = a.anon_array.elt_type
    case fpp.AliasType() as a:
        underlying = a.alias_type
    case fpp.PrimitiveIntType() as i:
        i.value == fpp.IntegerKind.U32
```

| Before | After |
| --- | --- |
| `types_values.Type` and friends | `fpp.Type` and its subclasses, same names |
| `ty.get_underlying_type()` | `ty.underlying_type` |
| `alias.alias_type` | `alias.alias_type` (one hop; `underlying_type` resolves the chain) |
| `ty.get_def_symbol()` | `ty.def_symbol` |
| `ty.is_numeric()`, `ty.is_displayable()`, … | `ty.is_numeric`, `ty.is_displayable`, … (properties) |
| `ty.kind.name` for an int kind | `ty.value` → `fpp.IntegerKind`, with `.name` |
| `AnonStructType.members` as a name-keyed mapping | an ordered `list[tuple[str, Type]]`, plus `get_member(name)` / `has_member(name)` |
| — | `ty.serialized_size`, `ty.identical(other)` |

`Type` does define `__eq__` and `__hash__`, but not by structural shape: two separately
declared types of identical shape (`struct A { x: U32 }` versus `struct B { x: U32 }`)
are never equal. Compare named types through `def_symbol`, as the compiler does, or use
`ty.identical(other)`. Primitives are the exception — `U32 == U32` is `True` wherever
the two came from.

### Topologies and connections

`Topology` keeps the relational model almost name for name. What changed is the
accessors and two return types:

| Before | After |
| --- | --- |
| `topology.a_node` | `topology.node` → `DefTopology` |
| `topology.get_name()` | `topology.name` |
| `topology.get_unqualified_name()` | `topology.unqualified_name` |
| `topology.get_qualified_name()` | `topology.qualified_name` |
| `topology.component_instance_map()` (a **method**) | `topology.component_instance_map` (an attribute) |
| `get_connections_from/to/at/between(...)` → `Set[Connection]` | → `list[Connection]`, in a deterministic order |
| `topology.unconnected_port_set` → `Set` | → `list[PortInstanceIdentifier]` |
| — | `topology.symbol` |

The `Set` → `list` change is a break for code that did set arithmetic on the result, and
a quiet improvement for code that sorted it to stabilise generated output.

The pieces an autocoder reaches for:

```python
topology.name                      # "Top"
topology.qualified_name            # "Ref.Top"
topology.node                      # DefTopology
topology.symbol                    # Symbol, the key into the Analysis maps

topology.component_instance_map    # dict[ComponentInterfaceInstance, Span]
topology.instance_map              # dict[InterfaceInstance, Span]
topology.port_map                  # dict[str, TopologyPort]
topology.port_interface            # PortInterface
topology.pattern_map               # dict[ConnectionPatternKind, ConnectionPattern]
topology.unconnected_port_set      # list[PortInstanceIdentifier]

topology.get_connections_from(pii)     # list[Connection]
topology.get_connections_to(pii)
topology.get_connections_at(pii)
topology.get_connections_between(from_pii, to_pii)
topology.get_port_number(port_instance, connection)   # Optional[int]
```

> **`component_instance_map` is keyed by the entity.** It is
> `dict[ComponentInterfaceInstance, Span]` — the instance is the *key*. So
> `for ci in topology.component_instance_map:` yields instances, where every `Analysis`
> *entity* map is `dict[Symbol, Entity]` and needs `.values()`. This one asymmetry
> catches everybody once.

Walking the graph:

```python
producer = next(ci for ci in topology.component_instance_map
                if ci.unqualified_name == "producer")
pii = producer.get_port_instance_identifier("dataOut")

for connection in topology.get_connections_from(pii):
    source_port = connection.from_.underlying_endpoint.port.port_instance
    index = topology.get_port_number(source_port, connection)
    destination = connection.to.underlying_endpoint.port.interface_instance
    assert isinstance(destination, fpp.ComponentInterfaceInstance)   # unflattened
    print(f"dataOut[{index}] -> {destination.qualified_name} "
          f"base_id=0x{destination.base_id:x}")
```

> **`Endpoint.port_number` is not the resolved port number.** It is the index as
> *written in the source*, and it is `None` whenever the connection omits it. Only
> `Topology.get_port_number(port_instance, connection)` gives the number the compiler
> assigned. For `producer.dataOut -> consumerA.dataIn` with no index,
> `connection.from_.port_number` is `None` while `get_port_number` returns `0`. Always
> use `get_port_number`, and treat its `None` as a hard error rather than a zero.

`ComponentInterfaceInstance` resolves the placement attributes of its
`DefComponentInstance`. **`base_id` and `max_id` are always `int`, never `None`** — when
the source declares no `base id` they are `0` and `-1`, so test
`instance.node.base_id is not None` if you need to know whether one was written.
`queue_size`, `stack_size`, `priority` and `cpu` are `Optional[int]`, and `file` is
`Optional[str]`. Also `init_specifier_map`, `component`, `interface`, `qualified_name`
and `unqualified_name`.

`Component` exposes `command_map` (keyed by opcode), `tlm_channel_map`,
`tlm_channel_name_map`, `event_map`, `param_map`, `record_map`, `container_map`,
`state_machine_instance_map`, `port_map` (keyed by name), `special_port_map`,
`port_interface`, `port_matching_list`, `max_id`, the `has_commands` / `has_events` /
`has_telemetry` / `has_parameters` / `has_data_products` /
`has_state_machine_instances` flags, and the ID bases — `default_opcode` for commands,
plus `default_tlm_channel_id`, `default_event_id`, `default_param_id`,
`default_container_id` and `default_record_id`. These maps iterate in key order now
rather than in the insertion order the old dicts used, so output that depended on
declaration order will reorder once.

### Dictionaries

`Dictionary` is unchanged in shape — the seven maps keep their names, and only the
`dictionary_map` key moved from `AstId` to `Symbol`. The entry classes lost their
`Dictionary` prefix:

| Before | After |
| --- | --- |
| `DictionaryCommandEntry` | `CommandEntry` |
| `DictionaryTlmChannelEntry` | `TlmChannelEntry` |
| `DictionaryEventEntry` | `EventEntry` |
| `DictionaryParamEntry` | `ParamEntry` |
| `DictionaryRecordEntry` | `RecordEntry` |
| `DictionaryContainerEntry` | `ContainerEntry` |

```python
dictionary = model.analysis.dictionary_map[topology.symbol]

dictionary.command_entry_map        # dict[int, CommandEntry]
dictionary.tlm_channel_entry_map   # dict[int, TlmChannelEntry]
dictionary.event_entry_map
dictionary.param_entry_map
dictionary.record_entry_map
dictionary.container_entry_map
dictionary.tlm_packet_set_map      # dict[str, TlmPacketSet]
```

Each `*Entry` pairs the owning instance with the definition, so
`entry.instance.qualified_name` and `entry.tlm_channel.channel_type.serialized_size`
are both one hop away.

There is no `Topology.dictionary` — go through `dictionary_map` keyed by
`topology.symbol`. And do not gate on `Analysis.dictionary_generation`: it reports
whether the compiler ran in dictionary-generation mode, which `fpp.analyze` never does,
so it is always `False`. `dictionary_map` is populated regardless.

### Diagnostics

This has no predecessor. Findings of your own can be reported exactly the way the
compiler reports its own, with the source excerpt and the carets:

```python
node = model.lookup("Ref.Producer").definition

print(fpp.Diagnostic(
    "Producer must have at most one instance",
    span=node.span,
    children=[fpp.DiagnosticMessage("delete the extra instance")],
))
```

```
 --> Demo.fpp:7:3
  |
7 | /   passive component Producer {
8 | |     output port dataOut: [4] Data
9 | |   }
  | |___^ Producer must have at most one instance
  |
  = note: delete the extra instance
```

A child that carries its own `span=` renders its own `:::` excerpt below the note, which
is how you point at the other end of a problem:

```python
fpp.DiagnosticMessage("instance defined here", span=instance.node.span,
                      kind=fpp.DiagnosticMessageKind.Note)
```

`Diagnostic(message, *, level=DiagnosticLevel.Error, span=None, children=[])` — the
message is first and positional, the level defaults to `Error`. Every field stays
writable: `add_note`, `add_annotation`, `add_child` and `set_span` build one up.
`render(*, color=False)` gives the full rendering above; `display` gives the one-line
`file:line:col: error: message` form. `level` is a `DiagnosticLevel` enum whose
`.value` is the compiler's spelling — it does **not** compare equal to `"error"`, so
any filter written against the string silently matches nothing.

A check can raise its finding instead of returning it. `fpp.DiagnosticError` carries a
still-mutable `Diagnostic`, so each handler on the way out adds the context it knows:

```python
try:
    check_channel(channel)
except fpp.DiagnosticError as error:
    error.diagnostic.add_annotation("in this telemetry packet", span=packet.node.span)
    raise
```

and one handler at the top turns it into output:

```python
if __name__ == "__main__":
    try:
        sys.exit(main())
    except fpp.DiagnosticError as error:
        print(error.diagnostic.render(color=sys.stderr.isatty()), file=sys.stderr)
        sys.exit(1)
```

The compiler raises this too — `ComponentInterfaceInstance.get_port_instance_identifier`
on a name that is not a port, for instance — so the same handler covers your findings
and its own.

Two things to get right. `fpp.DiagnosticError` takes a `Diagnostic`, not a string — a
bare string constructs without complaint and then fails with a `TypeError` the moment
any handler touches `.diagnostic`. And `render(color=…)` defaults to `False` for a
reason: under CMake and Ninja your stdout is always a pipe, so gate colour on
`isatty()` rather than hardcoding `color=True`.

---

## The C++ writer

The old `fprime_python_model.codegen.cppwriter` was a transcription of `fpp-to-cpp`'s
Scala `CppDoc`: a wrapper-class IR (`MemberClass`, `ClassMemberFunction`, …), five
`*Qualifier` enums, a generic `CppDocVisitor[Input, Output]`, two writer singletons
whose only product was a `List[Line]`, and a `LineUtils` mixin you inherited to get
`self.line()`. There was no builder, no statement layer, no file writing, no
formatting and no validation.

`fprime_cpp_codegen` keeps that IR-plus-two-writers core almost name for name —
`CppDoc`, `HppFile`, `Class`, `Constructor`, `Destructor`, `Function`, `Namespace`,
`Type` and `Line` all survive at the top level, and `join_lists` and
`write_function_body` survive in `fprime_cpp_codegen.lines` / `.comments` — and puts a
builder layer on top and an output layer underneath.

**Before:**

```python
from fprime_python_model.codegen.cppwriter.cpp_doc import (
    CppDoc, HppFile, Class, Function, Type, Namespace, MemberNamespace,
    MemberClass, ClassMemberFunction, ClassMemberLines, ConstQualifier)
from fprime_python_model.codegen.cppwriter.cpp_doc_hpp_writer import cpp_doc_hpp_writer
from fprime_python_model.utils.line_utils import LineUtils, Lines

lu = LineUtils()
fn = Function(comment="Get n", name="getN", params=[], ret_type=Type("U32"),
              body=lu.lines("return m_n;"), const_qualifier=ConstQualifier.CONST)
cls = Class(comment="A demo", name="C", superclass_decls=None,
            members=[ClassMemberLines(Lines(lu.lines("public:"))),   # by hand
                     ClassMemberFunction(fn)])
doc = CppDoc(description="a demo", hpp_file=HppFile("C.hpp", "Fw_C_HPP"),
             cpp_file_name="C.cpp",
             members=[MemberNamespace(Namespace("Fw", [MemberClass(cls)]))])
text = "\n".join(str(l) for l in cpp_doc_hpp_writer.visit_cpp_doc(doc))
```

**After:**

```python
from fprime_cpp_codegen import CppDocBuilder

doc = CppDocBuilder("C", description="a demo", namespaces=["Fw"])
with doc.namespace("Fw") as ns:
    with ns.class_("C", comment="A demo") as cls:
        with cls.public("Public member functions"):
            cls.function("getN", ret="U32", const=True,
                         body="return m_n;", comment="Get n")
text = doc.render_hpp()
doc.write("build-artifacts")          # or doc.files() -> {name: text}
```

Access specifiers were hand-written `Lines` before; `cls.public()` / `protected()` /
`private()` are the replacement, and used as a `with` block a section that ends up empty
deletes its own label.

### Mechanical renames

| Before | After |
| --- | --- |
| `MemberClass(c)`, `ClassMemberFunction(f)`, … | gone — append the node itself, or use the builder |
| `Member`, `ClassMember` (ABCs) | union type aliases |
| `FinalQualifier.FINAL` | `final=True` |
| `ExplicitQualifier.EXPLICIT` | `explicit=True` |
| `VirtualQualifier.VIRTUAL` | `virtual=True` |
| `ConstQualifier.CONST` | `const=True` |
| `SVQualifier.NON_SV` | `SVQualifier.NONE` (or omit every flag) |
| `tool_name_opt=` | `tool_name=` |
| `file_banner_opt=` | `file_banner=` on `CppDocBuilder`; `banner=` on the `CppDoc` IR |
| `cpp_file_name_base_opt=` | `cpp_file=` |
| `LinesOutput.HPP/CPP/BOTH` | `Output.HPP/CPP/BOTH` |
| `FunctionParam(t, name, …)` | `Param(type, name, …)` |
| `Type.get_cpp_type()` | `Type.cpp` (and `Type.hpp`) |
| `CppDoc.get_file_banner()` | `CppDoc.file_banner` |
| `Line.get_size()` | `Line.size` |
| `Indentation(n)` | a plain `int` on `Line` |
| `LineUtils` mixin, `self.line()` / `self.lines()` | module functions `line()`, `lines()` |
| `LineUtils.indent_increment` | `INDENT_INCREMENT` |
| `LineUtils.q` | none — write `"` literally |
| `CppDocHppWriter` / `CppDocCppWriter` / `CppDocWriter` | `HppWriter` / `CppWriter` / `DocWriter` |
| `cpp_doc_hpp_writer.visit_cpp_doc(doc)` | `render_hpp(doc)` / `hpp_lines(doc)` / `HppWriter().visit_doc(doc)` |
| `cpp_doc_writer_utils.*` (singleton) | free functions in `fprime_cpp_codegen.comments` |
| `Input(...)`, `get_enclosing_class_*()` | `Context(...)`, `enclosing_class_*` properties |

`CppDocBuilder.banner()` is not the renamed `banner` field — it emits a banner comment
into the document. The file banner is the `file_banner=` constructor argument.

62 names are re-exported from the top level. Most of the line algebra
(`add_prefix`, `add_suffix`, `indent_lines`, `join_lists`, `blank_separated`, …) and all
of the comment helpers (`write_banner_comment`, `write_doxygen_comment`, …) are **not** —
import them from `fprime_cpp_codegen.lines` and `fprime_cpp_codegen.comments`. Use the
`from … import` form: the top-level package binds the *function* `lines`, which shadows
the submodule of the same name.

### New capabilities worth adopting

- **A statement layer.** `fn.body` is a live `Body` with `if_` / `elif_` / `else_` /
  `while_` / `do_while` / `for_` / `for_range` / `block` / `switch` (with `case`,
  `default`, automatic `break`) / `if_directive`. All context managers; the statement
  methods (`line`, `lines`, `add`, `blank`, `raw`, `extend`) return the `Body` and chain.
- **`Variable` and `enum` builders.** Class data members and namespace-scope constants,
  with the writers deciding where the initialiser goes.
- **File output.** `doc.write(directory, formatter=…)` creates the directory, renders
  everything before writing anything, and leaves byte-identical files alone so their
  mtime does not cascade a rebuild. `doc.files()` returns `{name: text}`.
- **Validation.** `strict=True` on `CppDocBuilder` rejects a definition that needs a
  body and has none; `emit_hpp=False` / `emit_cpp=False` give one-file documents and
  raise `ValidationError` for anything the dropped file was the only home for.
- **`attributes=`** on classes and functions — between the keyword and the name for a
  class, at the head of the declaration for a function, and on the header declaration
  only — which is what a shared object's exported symbols need.
- **`ClangFormat`**, optional and off by default. It discards the F Prime autocoder's
  own layout, so do not enable it on output you diff against `fpp-to-cpp` references.

### Behaviour changes to check for

- **Margin stripping is stricter, and that is a bug fix.** The old `lines()` cut at
  *any* `|` anywhere in the line, so `lines("x = a | b;")` yielded `" b;"`. The new
  `strip_margin` only strips when the first non-whitespace character is the margin.
  For text derived from your model — an FPP annotation used as a doc comment, a C++
  expression whose continuation starts with `|` — say `margin=None` explicitly:

  ```python
  doc.lines(expression, margin=None)      # no stripping
  body.line(expression)                   # one line, never stripped
  cls.function("f", comment=lines(text, margin=None))
  ```

- `lines("a\nb\n")` yields 2 lines now, 3 before. `render()` appends a trailing
  newline where `str(Lines)` did not.
- `left_align_directive` now only moves lines matching a recognised preprocessor
  directive, so a `#` inside a string literal keeps its indentation.
- `Context.class_names` is **outermost-first**; `Input.class_name_list` was
  innermost-first. A ported writer subclass must flip its indexing.
- `comments.write_banner()` takes a `FileBanner`, a file name and a description —
  `write_banner(doc.build().file_banner, name, description)`. On a `CppDocBuilder`,
  `file_banner` is the override you passed in and is `None` by default; it is the
  `CppDoc` IR that resolves it to `DefaultFileBanner`.
- `Output` and `IndentMode` enum *values* changed case (`"Hpp"` → `"hpp"`), so any
  comparison against `.value` breaks.
- `CppDocBuilder(namespaces=[...])` does **not** open those namespaces. It only feeds
  the derived include guard; you still call `doc.namespace(*names)`.
- Not ported, with no replacement: `Lines.join_with_break` (the backslash
  continuation for multi-line macros), `join_opt` and `join_opt_with_break`.
- There is no `default()` catch-all on the new writer. Subclass `HppWriter` /
  `CppWriter` rather than `DocWriter` unless you are genuinely rendering something
  other than C++.

---

## Autocoders: the two phases

An F Prime build autocoder is invoked twice, and the migration is easier if you keep
the two halves clearly separated.

1. **Configure time**, once per module, synchronously inside `cmake`: *declare which
   files you will generate*. CMake needs the exact path set up front to build the
   dependency graph; a declared output you never produce breaks the compile that
   consumes it, and an unconsumed one silently re-runs its edge on every build.
2. **Build time**, in parallel under Ninja: *generate them*.

Phase 1 needs only the syntactic model. Phase 2 needs the full analysis.

The framework contract is unchanged since F Prime v4.0.0 — `fprime/cmake/API.cmake` for
the registration, `fprime/cmake/autocoder/autocoder.cmake` for the return values.
Register with `register_fprime_build_autocoder("autocoder/<name>" OFF)`, call one of
`autocoder_setup_for_individual_sources()` / `autocoder_setup_for_multiple_sources()`
at file scope, and implement `<name>_is_supported(AC_INPUT_FILE)` and
`<name>_setup_autocode(MODULE_NAME AC_INPUT_FILES)`, where `<name>` is the basename of
your `.cmake` file. `setup_autocode` must define at least one of
`AUTOCODER_GENERATED_BUILD_SOURCES` (compiled into the module),
`AUTOCODER_GENERATED_AUTOCODER_INPUTS` (fed to the next autocoder in the set) or
`AUTOCODER_GENERATED_OTHER` (tracked, never compiled); `AUTOCODER_DEPENDENCIES` is
optional and is appended to the target's link libraries.

The second argument to `register_fprime_build_autocoder` is `TO_PREPEND`: `OFF` appends
your autocoder so it runs after F Prime's own `autocoder/fpp`; pass `ON` only if `fpp`
must consume `.fpp` files you generate. The call `include()`s your `.cmake` file
immediately, so it has to come before any `add_subdirectory`.

### Configure time with `fpp-query`

**This is the recommended way.** `fpp-query` answers the filename question from the
syntactic model, from a declarative rules file, without starting a Python interpreter.

```toml
# static-report.toml
[[group]]
node = "DefTopology"
where = '$.is_deployment'
generate = ["StaticReportAc.cpp"]
```

```sh
fpp-query --rules static-report.toml -d "$BUILD" --filenames "$BUILD/names.txt" -- Top/topology.fpp
```

Each `[[group]]` emits `<DIR>/<stem><SUFFIX>` for every definition of `node` that
satisfies `where`. Output is sorted and deduplicated across all groups.

| Key | Meaning |
| --- | --- |
| `node` | AST node kind to select, e.g. `DefTopology`. **Required.** |
| `where` | Predicate the definition must satisfy. Optional; must evaluate to a boolean. |
| `name` | Expression overriding the file stem. Optional. |
| `generate` | Suffixes appended to the stem. **Required, non-empty.** |

One file-wide key, `expand`, sits above the first `[[group]]` and decides whether module
templates and synthesized state enums are part of the model a query sees. Write it as
`expand = ["templates"]`, `expand = ["state-enums"]`, or both names in one list;
`expand = true` is every expansion and `expand = false` (the default) none. A bare
`expand = "templates"` is rejected, and because TOML binds a key to the table above it,
writing `expand` below the first `[[group]]` is an error rather than a silent no-op.

By default the stem is the definition's name, prefixed recursively by the names of
enclosing components and state machines — module nesting contributes nothing. That is
what `fpp-to-cpp` does, so the defaults reproduce its filenames.

The query language is small and strict. `$` is the matched definition, `$.field`
navigates (including `$.annotations.pre` on any nested node), `$@` is every annotation
line, `$@pre` / `$@post` one side, `$@kind`, `$@file`, `$@line`, `$@included`,
`$@scope`, `$@qualified`, `$@stem` are metadata, and `$^` / `$^Kind` reach the immediate
or nearest enclosing parent. Operators are `== != < <= > >=`, the word forms
`contains starts_with ends_with matches` (glob, not regex), `in` (whose right side is a
list — a literal set `["Active", "Queued"]` or a list-valued path like `$@`), `+`
(concatenation, or integer addition when both sides are integers), `&& || !`, plus
`len() lower() upper() join() replace()`. A list on the left of `contains` /
`starts_with` / `ends_with` / `matches` holds when any element does; `==` deliberately
does not lift, so use `in` for exact membership. There is no truthiness, and navigating
into an absent field is an error rather than `null` — guard optional fields with
`!= null`.

The annotation-driven pattern translates directly:

```toml
[[group]]
node = "DefComponent"
where = '"static-report" in $@'
generate = ["StaticReportAc.hpp"]
```

**Write every query as a TOML *literal* string** — single quotes. A query needs `"`
for its own string literals, and a literal string carries those unescaped; a basic
string with escapes in it is rejected rather than mis-reported.

Exit codes: `0` success (**no matches is not a failure** — a nonzero exit becomes a
CMake `FATAL_ERROR` that aborts configure, and a module with nothing to generate must
not do that); `1` diagnostics were emitted; `2` usage or I/O failure. The
`--filenames` file holds one absolute path per line, LF-terminated, with no blank
lines, and is written whenever the tool was asked for a file list — including on exit 1,
because `file(STRINGS)` on a missing file is a hard `FATAL_ERROR` and a missing file
would turn one diagnosable error into two. It is not written on exit 2, nor in
`--json` / `--fields` mode, neither of which a CMake shim uses.

`-i/--imports` is accepted and ignored, so one argv works for both phases. `--json`
dumps the model a query sees — pass `--rules` alongside it, or you get the model as
parsed, before `expand` runs. `--fields [KIND]` lists every kind, or one kind's
queryable fields; it greedily eats the next positional, so spell it
`--fields DefTopology model.fpp`.

Upstream's `fpp-filenames` modes are all expressible here, and ship as rules files in
the `fpp-tools` repository under `fpp_query/presets/` (`autocode.toml`,
`autocode-expanded.toml`, `template.toml`, `test.toml`, `test-auto-helpers.toml`,
`test-template.toml`, `test-template-auto-helpers.toml`). They are not in the wheel —
copy the one you want into your project, delete the groups you do not need, and keep its
`expand`.

Two things the query and your generator must agree on:

- **The path set, exactly.** This is what the rules file is for: it is one artifact
  both halves read, so the build-time generator can derive its own output names from it
  with `tomllib.load` rather than keeping a second copy of the suffixes in sync by
  hand.
- **Configure must re-run when the rules change.** Add the rules file to
  `CMAKE_CONFIGURE_DEPENDS`, or the declared output list goes stale.

`fpp_info` can be dropped from the configure-time half — it computes the import closure
and the generated-file list, and a syntax-only query needs neither. It is still worth
calling for the build-time command, where `FILE_DEPENDENCIES` and
`MODULE_DEPENDENCIES` come from; note it spawns nothing, reading the `fpp-depend` cache
the `info-cache` sub-build already wrote. `fpp_autocoder_variables` is what builds
`FPP_IMPORT_FLAGS`, which the query ignores — but it is also the only thing that
computes `FPP_OUTPUT_DIRECTORY`, so if you want that directory for `-d`, call it before
the query.

### Configure time in Python

If you would rather keep both phases in one Python tool, `fpp.parse` plus a shallow
visitor is the way:

```python
def write_filenames(options, suffix: str) -> int:
    """Write the paths `generate` would produce for the same inputs."""
    tree = fpp.parse(paths=options.files)

    class Topologies(fpp.AstVisitor):
        def __init__(self) -> None:
            self.found: list[fpp.DefTopology] = []

        def generic_visit(self, node):
            pass                              # shallow by default

        def visit_DefModule(self, node):
            super().generic_visit(node)       # descend to find namespaced topologies

        def visit_DefTopology(self, node):
            if node.is_deployment:            # the build-time half requires this
                self.found.append(node)

    visitor = Topologies()
    visitor.visit(tree)

    paths = [output_for(options.directory, node, suffix) for node in visitor.found]
    with open(options.filenames, "w") as handle:
        for path in paths:                    # one per line, newline-terminated
            handle.write(f"{path}\n")
    return 0
```

Two details that are easy to get wrong and both cost you a build failure: the
configure-time predicate must match the build-time one exactly (check
`is_deployment` in both, or CMake declares an output the generator will never write),
and the file must be newline-terminated per path (`writelines` over a list of paths
concatenates them into one garbage path).

Note there is no `-i` here: `fpp.parse` has no `imports=` parameter, because nothing
at this depth reads another translation unit. The filename question is answerable from
syntax alone, which is the same fact that makes `fpp-query` possible.

**It will slow down `fprime-util generate`.** Not because parsing is slow — because
the process is. Measured on a 3.14 interpreter, one invocation of a `--filenames` tool
like this costs about 49 ms, of which:

| | share |
| --- | --- |
| bare CPython startup | ~53% |
| stdlib + extension imports | ~37% |
| argparse | ~10% |
| `fpp.parse` + the visitor | **under 2%** |

`fpp.parse` is 0.05 ms for one file and 0.9 ms for eighteen; the shallow visit is
0.06 ms. Importing the extension is about 2.6 ms warm — emphatically not a JVM-style
penalty. Everything expensive is fixed per-process cost that no Python-side
optimisation can remove, because the cost *is* the process.

CMake calls it once per module per registered autocoder, serially, through
`execute_process` — there is no configure-time parallelism, unlike the build-time
`add_custom_command` runs that Ninja fans out. F Prime alone has a few hundred
`.fpp`-bearing modules, so a deployment with two such autocoders pays on the order of
**tens of seconds of serial configure time** — and almost all of it answers "nothing":
only the one deployment module has a topology, so nearly every invocation spends 49 ms
to write an empty file. The tool cannot know that without starting an interpreter.

If you do keep the Python path, two things help and neither is optional:

- **Import `fprime_cpp_codegen` lazily**, inside the generate function, behind an
  `if TYPE_CHECKING:` guard for the annotations. The `--filenames` path then never
  pays for it.
- **Do not reach for the analysis.** `fpp.analyze` over the same 18 files is 1.1 ms
  versus `parse`'s 0.9 ms, so the difference is noise next to startup — but `analyze`
  needs the `-i` closure, which drags `fpp_info` and the `fpp_depend` cache into the
  configure-time path and makes the command line O(closure) per module.

### Build time

Unchanged in shape — analyze, then generate:

```python
def generate_all(options, suffix, generate) -> int:
    imports = [path for path in options.imports.split(",") if path]
    model = fpp.analyze(paths=options.files, imports=imports)

    for diagnostic in model.diagnostics:
        print(diagnostic.render(color=sys.stderr.isatty()), file=sys.stderr)
    if model.has_errors:
        return 1

    for topology in model.analysis.topology_map.values():
        if topology.node.is_deployment and topology.node.in_source:
            output_for(options.directory, topology.node, suffix).write_text(
                generate(model, topology)
            )
    return 0
```
`in_source` excludes topologies that arrived only through `-i`. Iterate rather
than taking the first match and asserting: the two phases must agree on the set of
files, and an `assert` here is how they silently disagree.

### The CMake shim

With `fpp-query` doing phase 1:

```cmake
####
# autocoder/static_report.cmake
#
#     register_fprime_build_autocoder("autocoder/static_report" OFF)
####
include_guard()
include(utilities)
include(autocoder/helpers)
include(autocoder/fpp)

autocoder_setup_for_multiple_sources()

# Phase 1's tool. Nothing finds it for you.
find_program(FPP_QUERY fpp-query REQUIRED)

# Everything below is resolved at file scope, because CMAKE_CURRENT_LIST_DIR inside a
# function is the directory of the listfile being processed at the CALL site -- the
# module's CMakeLists.txt -- not this file's directory.
get_filename_component(STATIC_REPORT_PATH
    "${CMAKE_CURRENT_LIST_DIR}/../../tools/static-report" REALPATH)
set(STATIC_REPORT "${STATIC_REPORT_PATH}"
    CACHE INTERNAL "Path to static-report" FORCE)
set(STATIC_REPORT_RULES "${CMAKE_CURRENT_LIST_DIR}/static-report.toml"
    CACHE INTERNAL "static-report rules file" FORCE)
# Every Python file the tool imports, so editing a shared helper retriggers generation.
file(GLOB_RECURSE STATIC_REPORT_MODULES CONFIGURE_DEPENDS
    "${CMAKE_CURRENT_LIST_DIR}/../../tools/*.py")
set(STATIC_REPORT_MODULES "${STATIC_REPORT_MODULES}"
    CACHE INTERNAL "static-report Python sources" FORCE)

function(static_report_is_supported AC_INPUT_FILE)
    # TRUE marks every matched .fpp as a configure regenerator, so editing a model
    # re-runs configure and re-asks the query.
    autocoder_support_by_suffix(".fpp" "${AC_INPUT_FILE}" TRUE)
endfunction()

function(static_report_setup_autocode MODULE_NAME AC_INPUT_FILES)
    set(NAMES "${CMAKE_CURRENT_BINARY_DIR}/static-report-filenames.txt")
    # Editing the rules must re-run configure, or the declared output list goes stale.
    set_property(DIRECTORY APPEND PROPERTY
        CMAKE_CONFIGURE_DEPENDS "${STATIC_REPORT_RULES}")

    execute_process_or_fail(
        "[static_report] could not list generated files for ${MODULE_NAME}"
        "${FPP_QUERY}"
        "--rules" "${STATIC_REPORT_RULES}"
        "-d" "${CMAKE_CURRENT_BINARY_DIR}"
        "--filenames" "${NAMES}"
        "--" ${AC_INPUT_FILES}
    )
    file(STRINGS "${NAMES}" GENERATED_CPP)

    if (NOT GENERATED_CPP)
        # Defined-but-empty, not undefined: the contract requires one of the
        # AUTOCODER_GENERATED_* variables to exist in the caller's scope.
        set(AUTOCODER_GENERATED_BUILD_SOURCES "" PARENT_SCOPE)
        return()
    endif()
    set(AUTOCODER_GENERATED_BUILD_SOURCES "${GENERATED_CPP}" PARENT_SCOPE)

    # Only the build-time half needs the import closure.
    fpp_info("${MODULE_NAME}" "${AC_INPUT_FILES}")
    fpp_autocoder_variables("${FPP_IMPORTS}")
    # If the generated code includes another module's headers, hand them over:
    #   set(AUTOCODER_DEPENDENCIES "${MODULE_DEPENDENCIES}" PARENT_SCOPE)
    add_custom_command(
        OUTPUT ${GENERATED_CPP}
        COMMAND ${STATIC_REPORT} "-d" "${CMAKE_CURRENT_BINARY_DIR}"
            ${FPP_IMPORT_FLAGS} ${AC_INPUT_FILES}
        DEPENDS ${FILE_DEPENDENCIES} "${STATIC_REPORT}" ${STATIC_REPORT_MODULES}
        COMMENT "Generating static report code for ${MODULE_NAME}"
    )
endfunction()
```

Three things the `fprime-samd` originals get wrong and you should not copy:

- **`DEPENDS` must list every Python file your tool imports**, not just the entry
  point. Editing a shared helper module otherwise does not retrigger generation.
- **Set `AUTOCODER_DEPENDENCIES "${MODULE_DEPENDENCIES}"`** if your generated code
  includes another module's headers. `fpp_info` already computed it.
- **Hand both phases the same output directory string.** The query and the generator
  must agree on the declared path character for character. `${CMAKE_CURRENT_BINARY_DIR}`
  for both is fine. If you want fpp's symlink-resolved form
  (`FPP_OUTPUT_DIRECTORY`, which exists because the JVM-based tools resolve paths
  themselves), call `fpp_autocoder_variables` before the query and use it in both.

And one the originals share with most autocoders: **invoke your tool through a known
interpreter.** A `#!/usr/bin/env python3` shebang binds to whatever `python3` is first
on `PATH`, not to the environment where `fprime-fpp-python` is installed — and F Prime's
own `PYTHON` (from `find_program` in `cmake/required.cmake`) is no better for this,
while `Python_EXECUTABLE` is not defined in an F Prime build at all. Install your
autocoder as a console script in a pinned virtualenv and point the cache variable at
that path.

---

## A worked autocoder

Putting it together — an annotation-driven, topology-level autocoder. The component
declares the members; the autocoder defines them into a `.cpp` compiled with the
deployment.

```fpp
module Ref {
  @ static-report
  @ A demo component
  passive component Producer {
    output port dataOut: [4] Data
  }
}
```

```python
#!/usr/bin/env python3
"""static-report: generate a deployment-level port index table."""

import sys
from contextlib import nullcontext
from pathlib import Path
from typing import TYPE_CHECKING

import fpp

if TYPE_CHECKING:                       # keep the codegen import off the fast path
    from collections.abc import Iterator

    import fprime_cpp_codegen as cg

TOOL_NAME = "static-report"
GENERATED_STEM = "StaticReportAc"
GENERATED_SUFFIX = f"{GENERATED_STEM}.cpp"
ANNOTATION = "static-report"


def output_for(directory: str, node: fpp.DefTopology, suffix: str) -> Path:
    return Path(directory) / f"{node.name}{suffix}"


def annotated_components(
    model: fpp.Model, annotation: str
) -> "Iterator[fpp.Component]":
    for component in model.analysis.component_map.values():
        if (annotation in component.node.pre_annotation
                or annotation in component.node.post_annotation):
            yield component


def single_instance(
    topology: fpp.Topology, component: fpp.Component
) -> "fpp.ComponentInterfaceInstance | None":
    """The one instance of `component` in `topology`, or None."""
    instances = [ci for ci in topology.component_instance_map
                 if ci.component is not None
                 and ci.component.symbol == component.symbol]
    if len(instances) > 1:
        raise fpp.DiagnosticError(fpp.Diagnostic(
            f"{component.symbol.qualified_name} must have at most one instance",
            span=component.node.span,
            children=[fpp.DiagnosticMessage("instance defined here",
                                            span=instance.node.span,
                                            kind=fpp.DiagnosticMessageKind.Note)
                      for instance in instances],
        ))
    return instances[0] if instances else None


def generate(model: fpp.Model, topology: fpp.Topology) -> str:
    from fprime_cpp_codegen import CppDocBuilder, Output

    doc = CppDocBuilder(
        f"{topology.name}{GENERATED_STEM}",
        description=f"static report for {topology.qualified_name}",
        tool_name=TOOL_NAME,
    )
    doc.include(f"{topology.name}TopologyAc.hpp", output=Output.CPP)

    for component in annotated_components(model, ANNOTATION):
        emit(topology, component, doc)
    return doc.render_cpp()


def emit(
    topology: fpp.Topology, component: fpp.Component, doc: "cg.CppDocBuilder"
) -> None:
    instance = single_instance(topology, component)
    if instance is None:
        return                                  # not in this topology: nothing to do

    try:
        pii = instance.get_port_instance_identifier("dataOut")
    except fpp.DiagnosticError as error:
        error.diagnostic.add_note(
            f"{TOOL_NAME} requires a port named `dataOut` on the annotated component")
        raise

    # A component need not sit inside a module, and namespace() rejects an empty list.
    *namespaces, name = component.symbol.qualified_name.split(".")
    scope = doc.namespace(*namespaces) if namespaces else nullcontext(doc)

    with scope as ns:
        with ns.function(f"{name} ::lookupPort", ret="FwIndexType") as fn:
            fn.param("FwOpcodeType", "opCode")
            with fn.body as body:
                with body.switch("opCode") as switch:
                    for connection in topology.get_connections_from(pii):
                        source = connection.from_.underlying_endpoint.port.port_instance
                        index = topology.get_port_number(source, connection)
                        if index is None:
                            raise fpp.DiagnosticError(fpp.Diagnostic(
                                "unresolved port number",
                                span=connection.from_.loc))
                        destination = connection.to.underlying_endpoint.port.interface_instance
                        assert isinstance(destination, fpp.ComponentInterfaceInstance)
                        with switch.case(f"0x{destination.base_id:x}",
                                         braces=False) as arm:
                            arm.comment(destination.qualified_name)
                            arm.line(f"return {index};")
                    with switch.default(braces=False) as arm:
                        arm.line("return -1;")
```

which renders:

```cpp
// ======================================================================
// \title  TopStaticReportAc.cpp
// \author Generated by static-report
// \brief  cpp file for static report for Ref.Top
// ======================================================================

#include "TopTopologyAc.hpp"

namespace Ref {

  FwIndexType Producer ::lookupPort(FwOpcodeType opCode) {
    switch (opCode) {
      case 0x200:
        // Ref.consumerA
        return 0;
      case 0x300:
        // Ref.consumerB
        return 2;
      default:
        return -1;
    }
  }

}
```

The annotation marks the *definition*, so a component annotated in a library is picked
up by whatever deployment instantiates it, with no edit to the deployment — and
`component_map` is the analysis map, so it includes components that arrived through
`-i`. The flip side: the marker is a plain string with no namespace, and a misspelled
annotation produces an empty file rather than an error. Consider asserting that at
least one annotated component was found.

`fprime-samd` carries two fuller examples in this shape — `tools/static-tlm-packetizer`
(telemetry packet buffers and offsets, driven by the resolved `Dictionary`) and
`tools/static-cmd-dispatcher` (the topology connection graph) — with their CMake shims
in `cmake/autocoder/`.

---

## Tools outside the build

An analysis tool that is not a build step had the hardest dependency on the old
pipeline: it had to make the build produce JSON, then find it. Both problems disappear,
but one thing still has to come from the build — the import closure. A component's
`.fpp` almost never analyzes alone.

Three options, in increasing fidelity:

1. **Pass the whole project.** `fpp.analyze(every_fpp_file)` needs no closure at all,
   because nothing is missing. Fine for a whole-project sweep, and the simplest thing
   that works.
2. **Read the closure the build already computed.** Each module's build directory holds
   `fpp-cache/stdout.txt`, one absolute path per line, written by the `fpp_depend`
   sub-build — exactly what `-i` receives:

   ```python
   closure = (module_build_dir / "fpp-cache" / "stdout.txt").read_text().split()
   model = fpp.analyze(module_sources, imports=closure)
   ```

   The same directory holds `direct.txt`, `include.txt`, `framework.txt`,
   `generated.txt` and `unittest.txt` if you want a narrower set. This requires a
   configured build tree, but no JSON and no extra CMake option.
3. **Run `fpp-depend` yourself**, if you have no build tree.

To find each module's build directory, the CMake File API codemodel
(`.cmake/api/v1/query/codemodel-v2`, then each target's `paths.build`) is the supported
way; it is the same offset the old JSON was delivered to, so an existing tool's locator
carries over unchanged.

---

## Testing an autocoder

`fpp.analyze(source=…)` takes a model as a string, so a fixture is a triple-quoted
literal and a test needs no build tree, no JSON and no temporary files:

```python
def test_emits_one_case_per_connection():
    model = fpp.analyze(source="""
    module Ref {
      port Data
      @ static-report
      passive component Producer { output port dataOut: [4] Data }
      passive component Consumer { sync input port dataIn: Data }
      instance producer: Producer base id 0x100
      instance consumerA: Consumer base id 0x200
      deployment topology Top {
        instance producer
        instance consumerA
        connections Data { producer.dataOut[0] -> consumerA.dataIn }
      }
    }
    """)
    assert not model.has_errors
    (topology,) = [t for t in model.analysis.topology_map.values()
                   if t.node.is_deployment]
    assert "case 0x200:" in generate(model, topology)
```

Two things worth asserting in every such test: that `model.has_errors` is `False` (an
invalid fixture otherwise produces an empty model and a vacuously passing test), and
that the configure-time filename list matches the set of files the build-time half
actually writes. The second is the failure mode CMake punishes hardest, and it is
cheap to test directly.

---

## Known gaps

Two things reproduce on `fprime-fpp-python` 3.3.21 and are worth designing around.

**A synthesized `State` enum appears inside every state machine, unmarked.** `analyze`
inserts a `DefEnum` named `State` into every `DefStateMachine` that has a body, with
the state machine's own source location and a `__FPRIME_UNINITIALIZED` constant.
`AstVisitor` descends into it, so a traversal that generates one artifact per enum
generates one for a definition nobody wrote — and two state machines in one module both
synthesize a `State`, so their outputs collide. F Prime's own autocoder names it
`<Machine>_State`. Nothing on the node says it was synthesized. Prune it by overriding
`visit_DefStateMachine` and not calling `super()`.

**`Type` renders a name, not the FPP spelling.** `str(a_type)` gives `'boolean'` where
FPP — and the old package's `BooleanType.__str__` — wrote `bool`, so audit every
`str(ty)` on a boolean. It also drops the size from `string size 12` and gives a named
type unqualified, both of which the old package did too. Spelling a type still means
branching on its concrete class — string, bool, `PrimitiveIntType`, `FloatType`, then
`def_symbol.qualified_name` for everything named. That is a dozen lines, and a
generator has to own the *C++* mapping anyway.

From the old package, with no replacement and none planned:

- **`fpp-to-json` and the JSON artifacts.** There is no JSON emitter anywhere in the
  Rust compiler. If you had an out-of-build tool reading `fpp-analysis.json`, it now
  links the compiler in-process instead — which is strictly better, but it is a
  rewrite, not a shim. See [Tools outside the build](#tools-outside-the-build).
- **`FprimePythonModel` itself.** There is no compatibility layer. The old
  `Annotated[...]` tuples, `AstId` maps and `ast_id_map` indirection do not survive,
  because the whole point is that cross-references are now real object references.
- **`utils/fpp_writer.py`** (`FppWriter`, printing FPP source back out). Not part of
  the bindings; use `fpp-format` for formatted FPP.
- **`utils/fpp_ast_writer.py`** (`AstWriter`, the AST debug dump). No replacement —
  write a `fpp.AstVisitor` if you need one.
- **`utils/error.py`.** `InternalError`, `NotSupportedInFppToJsonException`,
  `InvalidFppToJsonField` and `InvalidFppToJsonDictionary` are gone. Compiler problems
  arrive as `model.diagnostics`, and the one exception type is `fpp.DiagnosticError`.
- **`utils/ast_state_visitor.py`.** `AstStateVisitor` and `visit_list` have no
  counterpart; `AstVisitor` drives the walk and you keep state on `self`.
- **`fpp_ast/fpp_reserved_words.py`.** Not exposed by the bindings; carry your own list
  if your generator mangles identifiers.
- **The three `Lines` combinators** listed under [the C++ writer](#the-c-writer).

---

## Checklist

1. Add `fprime-fpp-python`, `fprime-cpp-codegen` and `fprime-fpp-query` to your
   requirements, pinned. Remove `fprime-python-model` and `fprime-fpp`.
2. Delete `FPRIME_ENABLE_JSON_MODEL_GENERATION` from every `CMakeLists.txt`,
   `settings.ini` and `cmake` invocation, and remove the code that located the three
   JSON files.
3. Replace the `FprimePythonModel(...)` construction with `fpp.analyze(paths,
   imports=…)`, and add the `model.diagnostics` / `model.has_errors` reporting block.
4. Rewrite `AstVisitor` subclasses as `fpp.AstVisitor` subclasses: `visit_DefX`,
   state on `self`, `super()` to descend.
5. Replace `annotated[0]` / `annotated[1]` / `annotated[2]` with `node.pre_annotation`
   / the node / `node.post_annotation`; `node.data.x` with `node.x`;
   `model.get_location(node)` with `node.location` or `node.span` — and remember the
   line/column fields are 0-indexed, so switch user-facing output to `.display`.
6. Replace `AstId` map lookups with `node.definition` / `node.resolved_type` /
   `node.resolved_value`, and `get_qualified_name_from_map(...)` with
   `symbol.qualified_name`. Re-key the entity maps from `AstId` to `Symbol`, and rename
   the symbol classes from `*Symbol` to `Symbol*`.
7. Audit `Topology` use: `a_node`→`node`, `get_name()`→`name`,
   `component_instance_map()`→ an attribute, and the connection getters returning a
   `list` rather than a `Set`.
8. Port the C++ writer to `CppDocBuilder`. Set `strict=True`. Audit every
   model-derived string for margin stripping and add `margin=None`.
9. Move the configure-time filename answer to a `fpp-query` rules file, and have the
   build-time generator read its suffixes from the same file.
10. Turn every `assert` and bare exception on a model condition into a
    `fpp.DiagnosticError` carrying a `fpp.Diagnostic` with a span.
11. Write a test per generated artifact using `fpp.analyze(source=…)` fixtures, plus one
    that the configure-time file list matches what the build-time half writes.
12. Run `mypy --strict`. Both packages ship complete stubs, and the strict job is what
    catches the renames this guide lists.

`fpp/__init__.pyi` is the reference for everything not covered here — every class,
getter and return type — and the docstrings carry the contracts: `help(fpp.analyze)`,
`help(fpp.Model)`, `help(fpp.AstVisitor)`.
