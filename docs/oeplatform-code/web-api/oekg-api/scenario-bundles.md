<!--
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut

SPDX-License-Identifier: CC0-1.0
-->

# Writing scenario bundles

A scenario bundle is the OEKG's record of a study: its scenarios, the study
reports it was published in, and the data those scenarios consumed and produced.
The [API Reference](../api-reference.md#/Scenario%20Bundles) lists every
endpoint that reads and writes one. It is generated from the code, so it is the
place to look up an address, a header or a status code.

This page is the other half: the rules that decide what a request **does**,
which no endpoint signature can state. They are the ones a client author would
otherwise learn from a `400` — or, worse, never learn, because the request
succeeded and did something other than what was meant.

There are nine. Eight describe the API as it is today; **rule 3** waits on an
endpoint that is still being built, and is named here rather than left out. A
reader who meets eight rules about what a write does, and no rule saying where
omission starts deleting things, has been misled by the silence rather than
served by it.

!!! Info "What is not on this page"

    `If-Match`, `ETag`, `?confirm=`, `?expand=`, the `428`/`412`/`409` refusals
    and the RDF forms a read can serve are described operation by operation in
    the [reference](../api-reference.md#/Scenario%20Bundles). They are
    mechanical, that description is generated from the code, and a test in the
    suite fails when the two come apart — so this page links there instead of
    keeping a second copy that could quietly go stale.

## Reading the examples

Every exchange below is a real one, recorded from the API running against a real
graph store, and the responses are reproduced as they came back. Where a body is
long it is shown as a marked excerpt, with nothing inside it edited. Host names
are written as they appear on `openenergyplatform.org`, and `<token>` stands for
your own API token — you will find it on your profile page under _Settings_.
Reads need no token.

Most of the page follows one bundle, `NEMO-2030`, from its creation to its
deletion.

---

## Rule 1 — a key you do not send is a key you do not change

Under every verb. A `PATCH` that names `label` changes the label and nothing
else: the abstract, the sectors and the technologies are not reset, not
re-minted, not touched.

This is worth stating because the opposite convention is common enough that
clients are written defensively — read the whole object, change one field, send
it all back. Here that is unnecessary, and against a bundle it does not even
work: a read carries the bundle's scenarios and study reports, and a `PATCH`
refuses them, as
[rule 4](#rule-4-a-bundle-post-accepts-nested-sub-resources-a-patch-does-not)
explains.

The other half of the same rule: a key you **do** send replaces what is there.
For a list-valued field, the list you send becomes the list the bundle has — so
sending `[]` is how a value is removed.

**Request**

```http
PATCH /api/v0/scenario-bundles/a195633f-3cf3-474e-8647-3f27c76d7cfa/ HTTP/1.1
If-Match: "1"
Content-Type: application/json
Authorization: Token <token>

{ "label": "The NEMO 2030 scenario study, second edition" }
```

**Response** — `200 OK`, `ETag: "2"`

```json
{
  "label": "The NEMO 2030 scenario study, second edition",
  "acronym": "NEMO-2030",
  "abstract": "Three pathways for the German power sector to 2030.",
  "descriptors": ["https://openenergyplatform.org/ontology/oeo/OEO_00000143"],
  "sector_divisions": [
    "https://openenergyplatform.org/ontology/oeo/OEO_00000368"
  ],
  "sectors": ["https://openenergyplatform.org/ontology/oeo/OEO_00000367"],
  "technologies": ["https://openenergyplatform.org/ontology/oeo/OEO_00000407"],
  "energy_carriers": [],
  "contacts": [],
  "organisations": [],
  "funders": [],
  "frameworks": [],
  "models": [],
  "_meta": {
    "uid": "a195633f-3cf3-474e-8647-3f27c76d7cfa",
    "iri": "https://openenergyplatform.org/ontology/oekg/a195633f-3cf3-474e-8647-3f27c76d7cfa",
    "version": 2
  },
  "scenarios": [],
  "study_reports": []
}
```

Everything the request did not mention came back as it was. The same holds one
level down, on a scenario or a study report of its own — here on a scenario that
carries an abstract and two years:

**Request**

```http
PATCH /api/v0/scenario-bundles/a195633f-.../scenarios/c0f1a112-.../ HTTP/1.1
If-Match: "5"
Content-Type: application/json
Authorization: Token <token>

{ "label": "A very high renewables scenario" }
```

**Response** — `200 OK`, `ETag: "6"`

```json
{
  "label": "A very high renewables scenario",
  "acronym": "HIGH-RE",
  "abstract": "Renewables reach 80% of generation by 2030.",
  "scenario_types": [
    "https://openenergyplatform.org/ontology/oeo/OEO_00000364"
  ],
  "study_regions": [],
  "interacting_regions": [],
  "years": ["2025-01-01T01:00:00+01:00", "2030-01-01T01:00:00+01:00"],
  "_meta": {
    "uid": "c0f1a112-431a-4c65-999a-c98fff76b5b2",
    "iri": "https://openenergyplatform.org/ontology/oekg/scenario/c0f1a112-431a-4c65-999a-c98fff76b5b2",
    "type": "https://openenergyplatform.org/ontology/oeo/OEO_00000365",
    "bundle": "a195633f-3cf3-474e-8647-3f27c76d7cfa"
  }
}
```

The `ETag` is the **bundle's** version, not the scenario's: a scenario has no
independent existence to guard, so every write below a bundle moves the one
version and the next request carries that.

In the reference:
[`PATCH /scenario-bundles/{uid}/`](../api-reference.md#/Scenario%20Bundles/scenario_bundles_partial_update).

---

## Rule 2 — `_meta` is read-only, and ignored on write

Everything a client cannot set lives under one key: the identifier, the IRI, the
version, the counts, the resolution of a dataset link, the labels an expansion
resolved. A write that sends `_meta` back is not refused — the key is dropped
before validation. That is what lets a client send back what it read without
stripping anything first.

The container is not a hole in the closed shape, it is what keeps the shape
closed: the **top** level of a payload is exactly the fields of the resource, so
an unknown key there is a `400` (see
[rule 8](#rule-8-the-server-mints-the-identifier)), and everything read-only
sits one level down where that check does not have to make exceptions.

**Request** — the `_meta` values here are nonsense on purpose

```http
PATCH /api/v0/scenario-bundles/a195633f-3cf3-474e-8647-3f27c76d7cfa/ HTTP/1.1
If-Match: "2"
Content-Type: application/json
Authorization: Token <token>

{
  "abstract": "Three pathways, now including a demand-side variant.",
  "_meta": {
    "uid": "not-this",
    "version": 99,
    "iri": "http://example.org/x"
  }
}
```

**Response** — `200 OK`, `ETag: "3"` (excerpt)

```json
{
  "label": "The NEMO 2030 scenario study, second edition",
  "abstract": "Three pathways, now including a demand-side variant.",
  "_meta": {
    "uid": "a195633f-3cf3-474e-8647-3f27c76d7cfa",
    "iri": "https://openenergyplatform.org/ontology/oekg/a195633f-3cf3-474e-8647-3f27c76d7cfa",
    "version": 3
  }
}
```

The abstract changed. The identifier is still the server's, the version is 3 and
not 99, and the version this write was guarded against came from the `If-Match`
header — never from the body.

In the reference:
[`GET /scenario-bundles/{uid}/`](../api-reference.md#/Scenario%20Bundles/scenario_bundles_retrieve).

---

## Rule 3 — delete-by-omission will exist on `replace/`, and nowhere else

!!! Warning "This endpoint is not built yet"

    `POST /api/v0/scenario-bundles/{uid}/replace/` does not exist on the
    platform today. The rule is stated here because the rest of this page tells
    you that leaving a key out is safe, and that will stop being true at exactly
    one address. Until it lands, **nothing in this API deletes anything because
    a key was left out**: the only way to remove something is to name it — send
    a shorter list, or call `DELETE` on the sub-resource's own URL.

```http
POST /api/v0/scenario-bundles/a195633f-3cf3-474e-8647-3f27c76d7cfa/replace/ HTTP/1.1
Content-Type: application/json
Authorization: Token <token>

{}
```

```
404 Not Found
```

`replace/` is the declarative endpoint a pipeline wants: it will take the
complete bundle you mean to see, sub-resources included, and make the graph
match it in one atomic write. That is why it is an address of its own rather
than a `PUT` on the bundle. Everywhere else, a key you do not send is a key you
do not change; there, a sub-resource you do not send is a sub-resource you have
deleted. Two behaviours that different should not share one URL, and the one
that can destroy data should be the one you ask for by name.

The endpoint is tracked as
[issue #2477](https://github.com/OpenEnergyPlatform/oeplatform/issues/2477).
This page gains the worked example when it lands.

In the reference: nothing yet. When `replace/` ships it joins the
[Scenario Bundles](../api-reference.md#/Scenario%20Bundles) section with
everything else.

---

## Rule 4 — a bundle `POST` accepts nested sub-resources; a `PATCH` does not

A create may carry its scenarios and study reports with it, so a pipeline can
publish a whole bundle in one request — and, because one request is one
transaction, either all of it lands or none of it does. A `PATCH` on the bundle
cannot reach them at all: `scenarios` is not a field of the bundle payload, so
sending one is an unknown key.

The asymmetry looks like an oversight and is the opposite. If a bundle `PATCH`
took a `scenarios` list, every `PATCH` would have to decide what an omitted list
means — and the answer that keeps a one-field edit safe (leave them alone) is
the answer that makes the list useless for removing anything. Sub-resources get
their own URLs instead, and
[rule 1](#rule-1-a-key-you-do-not-send-is-a-key-you-do-not-change) holds without
exception.

**Request** — a bundle and its scenario in one call

```http
POST /api/v0/scenario-bundles/ HTTP/1.1
Content-Type: application/json
Authorization: Token <token>

{
  "label": "The ALTERNATIVE 2040 study",
  "acronym": "ALT-2040",
  "abstract": "A slower-transition counterfactual.",
  "descriptors": ["https://openenergyplatform.org/ontology/oeo/OEO_00000143"],
  "sector_divisions": [
    "https://openenergyplatform.org/ontology/oeo/OEO_00000368"
  ],
  "sectors": ["https://openenergyplatform.org/ontology/oeo/OEO_00000367"],
  "technologies": ["https://openenergyplatform.org/ontology/oeo/OEO_00000407"],
  "scenarios": [
    {
      "label": "A high renewables scenario",
      "acronym": "HIGH-RE",
      "scenario_types": [
        "https://openenergyplatform.org/ontology/oeo/OEO_00000364"
      ]
    }
  ]
}
```

**Response** — `201 Created`,
`Location: /api/v0/scenario-bundles/5913a078-1bd2-4a81-91df-c83b56fd3681/`,
`ETag: "1"` (excerpt)

```json
{
  "label": "The ALTERNATIVE 2040 study",
  "acronym": "ALT-2040",
  "_meta": {
    "uid": "5913a078-1bd2-4a81-91df-c83b56fd3681",
    "iri": "https://openenergyplatform.org/ontology/oekg/5913a078-1bd2-4a81-91df-c83b56fd3681",
    "version": 1
  },
  "scenarios": [
    {
      "label": "A high renewables scenario",
      "acronym": "HIGH-RE",
      "abstract": null,
      "scenario_types": [
        "https://openenergyplatform.org/ontology/oeo/OEO_00000364"
      ],
      "study_regions": [],
      "interacting_regions": [],
      "years": [],
      "_meta": {
        "uid": "2db5def3-13dd-4abf-be7f-3bf30cb48ca8",
        "iri": "https://openenergyplatform.org/ontology/oekg/scenario/2db5def3-13dd-4abf-be7f-3bf30cb48ca8",
        "type": "https://openenergyplatform.org/ontology/oeo/OEO_00000365",
        "bundle": "5913a078-1bd2-4a81-91df-c83b56fd3681"
      }
    }
  ],
  "study_reports": []
}
```

The nested scenario has an identifier of its own, and from here it is edited at
its own URL. Sending another one through the bundle is refused:

**Request**

```http
PATCH /api/v0/scenario-bundles/5913a078-1bd2-4a81-91df-c83b56fd3681/ HTTP/1.1
If-Match: "1"
Content-Type: application/json
Authorization: Token <token>

{
  "scenarios": [
    {
      "label": "A low renewables scenario",
      "acronym": "LOW-RE",
      "scenario_types": [
        "https://openenergyplatform.org/ontology/oeo/OEO_00000364"
      ]
    }
  ]
}
```

**Response** — `400 Bad Request`

```json
{ "scenarios": "Unknown field. The bundle shape is closed." }
```

In the reference:
[`POST /scenario-bundles/`](../api-reference.md#/Scenario%20Bundles/scenario_bundles_create)
and
[`POST /scenario-bundles/{uid}/scenarios/`](../api-reference.md#/Scenario%20Bundles/scenario_bundles_scenarios_create).

---

## Rule 5 — the delete's two guards catch two different accidents

Deleting a whole bundle needs both an `If-Match` version and a
`?confirm=<acronym>`. That reads like ceremony until you notice that each
catches a mistake the other cannot see.

- `If-Match` catches **stale state**: you are deleting the bundle you meant, but
  it has changed since you read it, so what you would destroy is not what you
  looked at.
- `?confirm=` catches the **wrong bundle**: your state is perfectly fresh and
  the identifier in the URL is somebody else's. This is the accident a looping
  pipeline actually commits, and no version check can notice it, because the
  version it is handed is that bundle's own current version.

The acronym is compared exactly. Normalising it would let `nemo-2030` confirm
the deletion of `NEMO-2030`, which is the class of mistake the check exists for.

The four exchanges below are the same bundle, `NEMO-2030`, at version 6.

**Missing confirmation** — the version was right

```http
DELETE /api/v0/scenario-bundles/a195633f-3cf3-474e-8647-3f27c76d7cfa/ HTTP/1.1
If-Match: "6"
Authorization: Token <token>
```

`400 Bad Request`

```json
{
  "detail": "Deleting a whole scenario bundle is irreversible, so it has to be confirmed: repeat the bundle's acronym as ?confirm=<acronym>. Read the bundle first -- the acronym is in the response, and so is the version this delete also needs."
}
```

**Wrong confirmation** — the version was still right

```http
DELETE /api/v0/scenario-bundles/a195633f-.../?confirm=NEMO-2031 HTTP/1.1
If-Match: "6"
Authorization: Token <token>
```

`400 Bad Request`

```json
{
  "detail": "The confirmation 'NEMO-2031' is not this bundle's acronym, so nothing was deleted. Check that this is the bundle you meant to delete before retrying."
}
```

**Stale version** — the confirmation was right

```http
DELETE /api/v0/scenario-bundles/a195633f-.../?confirm=NEMO-2030 HTTP/1.1
If-Match: "1"
Authorization: Token <token>
```

`412 Precondition Failed`

```json
{
  "detail": "The bundle is not at the version this request expects, so nothing was written. It is at \"6\". Read it again and apply the change to what you get back."
}
```

**Both right**

```http
DELETE /api/v0/scenario-bundles/a195633f-.../?confirm=NEMO-2030 HTTP/1.1
If-Match: "6"
Authorization: Token <token>
```

`200 OK`. The bundle had one scenario.

```json
{
  "deleted": [
    {
      "iri": "https://openenergyplatform.org/ontology/oekg/a195633f-3cf3-474e-8647-3f27c76d7cfa",
      "type": "https://openenergyplatform.org/ontology/oeo/OEO_00020227"
    },
    {
      "iri": "https://openenergyplatform.org/ontology/oekg/scenario/c0f1a112-431a-4c65-999a-c98fff76b5b2",
      "type": "https://openenergyplatform.org/ontology/oeo/OEO_00000365"
    }
  ],
  "unlinked": [],
  "_meta": {
    "uid": "a195633f-3cf3-474e-8647-3f27c76d7cfa",
    "iri": "https://openenergyplatform.org/ontology/oekg/a195633f-3cf3-474e-8647-3f27c76d7cfa",
    "acronym": "NEMO-2030",
    "version_before": 6
  }
}
```

A delete answers with a body rather than an empty `204`, and the body carries
two lists because a delete has two outcomes. **`deleted`** is what is gone.
**`unlinked`** is what survived: a scenario, a study report or a dataset link
that another bundle also cites is detached from this bundle rather than
destroyed, because deleting your own study must not damage somebody else's
record. Nodes that are shared by design — organisations, funders, contact
persons, study regions — are never deleted by this API at all; the bundle simply
stops referring to them, and they appear in neither list.

Repeating the delete answers `404`, and a client may treat that as success. The
bundle's history outlives it: `GET .../history/` still answers, with one line
recording the deletion and the payloads of the earlier entries pruned.

In the reference:
[`DELETE /scenario-bundles/{uid}/`](../api-reference.md#/Scenario%20Bundles/scenario_bundles_destroy).

---

## Rule 6 — a write is judged by the violations it introduces

Every bundle is validated against the canonical OEKG shape before it is written.
For a change to a bundle that already exists, the **pre-state is validated
too**, and the write is refused only for violations it adds. A defect that was
already there is left alone: not repaired, and not standing between you and a
change to an unrelated field.

Without this the API could not write to most of the graph. Bundles written
through the browser over the years are missing content the shape requires —
which sector a study covers, who wrote a publication — and that missing content
is exactly what a person would supply _by patching_. A rule of "the result must
conform" would make the defect unfixable through the API: you would need a patch
to add the missing sector, and the patch would be refused because the sector is
missing.

A **create has no pre-state**, so it is strict: everything a create produces is
new, and nothing excuses it. A `400` on a create where the same field was
accepted by a `PATCH` is this asymmetry, not a bug.

How the comparison is made, and why the two states have to be assembled the same
way for it to mean anything, is on the
[architecture guide](../../features/scenario-bundles/architecture.md#the-api-write-path),
which is the page for somebody changing this rather than calling it.

**A patch of a bundle that already violates the shape.** `NEMO-2020` was written
in the browser and names no technology, which the shape requires.

```http
PATCH /api/v0/scenario-bundles/3f2b91c4-7d8e-4a15-9c63-0e5a77b21d48/ HTTP/1.1
If-Match: "0"
Content-Type: application/json
Authorization: Token <token>

{ "label": "The NEMO 2020 study, corrected" }
```

**Response** — `200 OK`, `ETag: "1"` (excerpt). It still names no technology
afterwards: the API does not repair what it did not break.

```json
{
  "label": "The NEMO 2020 study, corrected",
  "acronym": "NEMO-2020",
  "technologies": [],
  "_meta": {
    "uid": "3f2b91c4-7d8e-4a15-9c63-0e5a77b21d48",
    "version": 1
  }
}
```

**A patch of the same bundle that would remove its sectors**

```http
PATCH /api/v0/scenario-bundles/3f2b91c4-7d8e-4a15-9c63-0e5a77b21d48/ HTTP/1.1
If-Match: "1"
Content-Type: application/json
Authorization: Token <token>

{ "sectors": [] }
```

**Response** — `400 Bad Request`

```json
{
  "detail": "This change would add violations of the OEKG shape.",
  "violations": [
    {
      "message": "Study target: This should cover at least one sector.",
      "focus_node": "https://openenergyplatform.org/ontology/oekg/3f2b91c4-7d8e-4a15-9c63-0e5a77b21d48",
      "path": "https://openenergyplatform.org/ontology/oeo/OEO_00020439",
      "value": null
    }
  ],
  "pre_existing_violations": 1
}
```

`violations` lists only what this request would add — the missing technology is
not in it, or you could not tell which of them is your own doing.
`pre_existing_violations` counts the rest, so the bundle's condition is stated
rather than hidden.

**The same omission on a create**

```http
POST /api/v0/scenario-bundles/ HTTP/1.1
Content-Type: application/json
Authorization: Token <token>

{
  "label": "The NEMO 2045 study",
  "acronym": "NEMO-2045",
  "abstract": "Three pathways for the German power sector to 2030.",
  "descriptors": ["https://openenergyplatform.org/ontology/oeo/OEO_00000143"],
  "sector_divisions": [
    "https://openenergyplatform.org/ontology/oeo/OEO_00000368"
  ],
  "sectors": ["https://openenergyplatform.org/ontology/oeo/OEO_00000367"]
}
```

**Response** — `400 Bad Request`. Note the wording: not _would add_, but _does
not conform_. There is no `pre_existing_violations`, because there is no
pre-state.

```json
{
  "detail": "The bundle does not conform to the OEKG shape.",
  "violations": [
    {
      "message": "Study target: This should cover at least one technology.",
      "focus_node": "https://openenergyplatform.org/ontology/oekg/c4bb832d-39e4-4642-954b-e223d9ce8df7",
      "path": "https://openenergyplatform.org/ontology/oeo/OEO_00020438",
      "value": null
    }
  ]
}
```

In the reference:
[`POST /scenario-bundles/`](../api-reference.md#/Scenario%20Bundles/scenario_bundles_create).

---

## Rule 7 — `ref: table` is reproducible, `ref: dataset` is current, and a dead link stays

A dataset link records that a scenario consumed or produced data on this
platform. It has three fields, and `ref` decides which kind of thing is cited:

- **`ref: "table"`** names one OEP table. It is the **reproducible** citation:
  the table it names is the table it will always name.
- **`ref: "dataset"`** names a catalogue entry that groups tables. It is the
  **current** citation: it resolves to whatever that entry holds today, which is
  the reason to cite the entry rather than its members.

Neither is checked when it is written, and a citation never keeps its target
alive. A bundle is a published research record, so "this scenario used table X"
stays true after X is deleted — and letting a stranger's citation block your own
table's deletion would invert the permission model. Instead, every read resolves
the link and says in `_meta` what it means **now**. Nothing is stored, so
nothing can go stale.

**A table that is there.** Every link below is added to one scenario of one
bundle, each write carrying the version the one before it returned.

```http
POST /api/v0/scenario-bundles/bbb19b1c-.../scenarios/a93baabe-.../datasets/ HTTP/1.1
If-Match: "2"
Content-Type: application/json
Authorization: Token <token>

{ "type": "input", "ref": "table", "name": "nemo_2030_capacities" }
```

`201 Created`, `ETag: "3"` (excerpt)

```json
{
  "type": "input",
  "ref": "table",
  "name": "nemo_2030_capacities",
  "_meta": {
    "target_iri": "https://openenergyplatform.org/database/tables/nemo_2030_capacities",
    "resolvable": true,
    "tables": [{ "name": "nemo_2030_capacities", "peer_review": null }]
  }
}
```

**A catalogue entry**, resolved to the two tables it holds today

```http
POST /api/v0/scenario-bundles/bbb19b1c-.../scenarios/a93baabe-.../datasets/ HTTP/1.1
If-Match: "3"
Content-Type: application/json
Authorization: Token <token>

{ "type": "output", "ref": "dataset", "name": "nemo_2030_results" }
```

`201 Created`, `ETag: "4"` (excerpt)

```json
{
  "type": "output",
  "ref": "dataset",
  "name": "nemo_2030_results",
  "_meta": {
    "target_iri": "https://openenergyplatform.org/database/datasets/nemo_2030_results",
    "resolvable": true,
    "tables": [
      { "name": "nemo_2030_emissions", "peer_review": null },
      { "name": "nemo_2030_generation", "peer_review": null }
    ]
  }
}
```

**A table that has since been deleted.** The write is not refused: a link is
never checked against its target.

```http
POST /api/v0/scenario-bundles/bbb19b1c-.../scenarios/a93baabe-.../datasets/ HTTP/1.1
If-Match: "4"
Content-Type: application/json
Authorization: Token <token>

{ "type": "input", "ref": "table", "name": "nemo_2020_capacities" }
```

`201 Created`, `ETag: "5"` (excerpt). `resolvable: false` is the correct answer
about a citation, not a broken link in your bundle — and the same link reads
`true` again if a table of that name reappears.

```json
{
  "type": "input",
  "ref": "table",
  "name": "nemo_2020_capacities",
  "_meta": {
    "target_iri": "https://openenergyplatform.org/database/tables/nemo_2020_capacities",
    "resolvable": false,
    "tables": []
  }
}
```

`peer_review` on a table is three-valued — `"finished"`, `"in_progress"` or
`null`. It is not a boolean because most of the platform's data predates the
Open Peer Review process, and `false` would present all of it as having failed a
review it was never submitted to.

!!! Warning "A link written before this API cannot be sent back"

    `ref` is derived from the stored address, and the payload has no way to say
    "an address somewhere else". A link written by the older route to an
    off-platform address therefore reads back with `ref: null`, and `resolvable`
    and `tables` read `null` rather than `false` — nothing was deleted, there is
    simply nothing here to resolve. Such a body is not accepted back by a write.
    `_meta.target_iri` says where it actually points. Read back from
    `GET …/datasets/` (excerpt):

    ```json
    {
      "type": "input",
      "ref": null,
      "name": "WS_23_24",
      "_meta": {
        "target_iri": "https://databus.openenergyplatform.org/koubaa/LLEC_Dataset/WS_23_24",
        "resolvable": null,
        "tables": null
      }
    }
    ```

In the reference:
[`POST /scenario-bundles/{uid}/scenarios/{sid}/datasets/`](../api-reference.md#/Scenario%20Bundles/scenario_bundles_scenarios_datasets_create).

---

## Rule 8 — the server mints the identifier

There is no key to supply one through. `uid` at the top level of a payload is
not ignored, it is refused, so a client that tries to choose its own identifier
is told rather than quietly overridden.

```http
POST /api/v0/scenario-bundles/ HTTP/1.1
Content-Type: application/json
Authorization: Token <token>

{
  "label": "The NEMO 2030 scenario study",
  "acronym": "NEMO-2030-B",
  "uid": "my-own-id"
}
```

**Response** — `400 Bad Request`

```json
{ "uid": "Unknown field. The bundle shape is closed." }
```

A successful create says where the bundle now lives, in the `Location` header
and in `_meta.uid`:

```
201 Created
Location: /api/v0/scenario-bundles/a195633f-3cf3-474e-8647-3f27c76d7cfa/
ETag: "1"
```

Which leaves the question a stateless pipeline actually has: it ran last month,
it kept no file, and it needs the bundle it wrote. **Re-identify it by
acronym.** That is why acronyms are unique, and why creating or renaming onto a
taken one is refused.

**Request** — no token needed; reads are public

```http
GET /api/v0/scenario-bundles/?acronym=NEMO-2030 HTTP/1.1
```

**Response** — `200 OK`

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "label": "The NEMO 2030 scenario study",
      "acronym": "NEMO-2030",
      "_meta": {
        "uid": "a195633f-3cf3-474e-8647-3f27c76d7cfa",
        "iri": "https://openenergyplatform.org/ontology/oekg/a195633f-3cf3-474e-8647-3f27c76d7cfa",
        "version": 1,
        "counts": { "scenarios": 0, "study_reports": 0 }
      }
    }
  ]
}
```

One request returns both things the next write needs: the identifier for the
URL, and the version for the precondition. The header form of the version is the
number in double quotes, so the run continues with `If-Match: "1"` without ever
reading the bundle itself.

In the reference:
[`GET /scenario-bundles/`](../api-reference.md#/Scenario%20Bundles/scenario_bundles_list).

---

## Rule 9 — `_meta.history_recorded: false` inside a `200` is an audit gap, not a status

Every write is recorded in the bundle's history. The graph store and this
platform's database cannot share a transaction, and the graph commits first — so
there is a narrow window in which the write has landed and the record of it has
not.

When that happens the response says so and stays a success. Answering with an
error would be worse, because the write did happen; writing a history entry the
graph does not support would be worse still, because it looks like truth. The
key appears **only when something was lost**, so on an ordinary write there is
nothing to check for.

**Request** — an ordinary patch, with nothing about it to say that anything will
go wrong

```http
PATCH /api/v0/scenario-bundles/a195633f-3cf3-474e-8647-3f27c76d7cfa/ HTTP/1.1
If-Match: "3"
Content-Type: application/json
Authorization: Token <token>

{ "abstract": "Three pathways for the German power sector to 2030." }
```

**Response** — `200 OK`, `ETag: "4"` (excerpt). The abstract was changed; the
history row was not written, and the bundle's history has no entry for
version 4.

```json
{
  "label": "The NEMO 2030 scenario study, second edition",
  "abstract": "Three pathways for the German power sector to 2030.",
  "_meta": {
    "uid": "a195633f-3cf3-474e-8647-3f27c76d7cfa",
    "version": 4,
    "history_recorded": false
  }
}
```

Two siblings behave the same way, for the same reason:

| key                          | appears on | means                                                                                   |
| ---------------------------- | ---------- | --------------------------------------------------------------------------------------- |
| `history_recorded: false`    | any write  | the change is in the graph; the history has no entry for it                             |
| `ownership_recorded: false`  | a create   | the bundle exists but no owner was recorded, so it is administrator-only until repaired |
| `ownership_forgotten: false` | a delete   | the bundle is gone; the row naming you its owner is not                                 |

A client that sees one of these has a successful write and something for a
maintainer to repair. `GET .../history/` is where to check what the ledger does
hold.

In the reference:
[`PATCH /scenario-bundles/{uid}/`](../api-reference.md#/Scenario%20Bundles/scenario_bundles_partial_update)
and
[`GET /scenario-bundles/{uid}/history/`](../api-reference.md#/Scenario%20Bundles/scenario_bundles_history_list).
