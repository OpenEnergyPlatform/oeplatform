"""What the committed description has to say about the scenario-bundle API.

The guard beside this one (``test_openapi_schema``) keeps the artifact equal to
what the code produces. That is necessary and not sufficient: a description can
be perfectly current and still tell a client nothing, which is what it did
before this. These checks are the other half -- they read the committed
document and assert that the client-visible half of the contract is *in* it.

They are written against the artifact rather than against the annotations for
one reason: the artifact is what a client reads. An assertion about
``extend_schema`` would pass while the generator quietly dropped the operation
it decorated, which is a failure this project has already had.

Two of them are deliberately strict in a way that looks pedantic:

- **The auth expectation is cross-checked against the operation's own
  ``security`` block**, so the words and the padlock cannot disagree. They
  currently *look* like they disagree: Swagger UI draws a closed padlock when
  an operation's security is already satisfied, so a public read renders locked
  and a write requiring a token renders open. The icon is not wrong, it answers
  a different question -- and the sentence is there because no reader should
  have to know that.
- **An operation id may not end in a numeral.** A numeral there is the
  generator resolving a collision between two operations it could not tell
  apart, and the resulting name is one no reader can map back to an endpoint.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: E501

import re

import yaml
from django.test import SimpleTestCase

from api.tests.test_openapi_schema import ARTIFACT, REGENERATE

#: Everything below this prefix is this slice's subject. The OEDB table, row
#: and ``advanced/`` endpoints are described by the hand-written
#: ``schema.json`` and are explicitly out of scope (#2454).
PREFIX = "/api/v0/scenario-bundles"

WRITE_METHODS = ("post", "patch", "delete")

#: The one write with no ``If-Match``: there is no bundle yet to have read a
#: version of, and no owner yet to be.
CREATE = (PREFIX + "/", "post")

#: Where ``?expand=`` is offered. Written out rather than derived, because the
#: artifact cannot say which operations *act* on it -- and being tolerated is
#: not being offered. The parameter is parsed per view, so the four deletes
#: accept one and so does the bundle `PATCH`; none of them resolves anything,
#: so none of them says it does.
EXPANDS = {
    (PREFIX + "/{uid}/", "get"),
    (PREFIX + "/{uid}/history/", "get"),
    (PREFIX + "/{uid}/scenarios/", "get"),
    (PREFIX + "/{uid}/scenarios/", "post"),
    (PREFIX + "/{uid}/scenarios/{pid}/", "get"),
    (PREFIX + "/{uid}/scenarios/{pid}/", "patch"),
    (PREFIX + "/{uid}/study-reports/", "get"),
    (PREFIX + "/{uid}/study-reports/", "post"),
    (PREFIX + "/{uid}/study-reports/{pid}/", "get"),
    (PREFIX + "/{uid}/study-reports/{pid}/", "patch"),
    (PREFIX + "/{uid}/scenarios/{sid}/datasets/", "get"),
    (PREFIX + "/{uid}/scenarios/{sid}/datasets/", "post"),
    (PREFIX + "/{uid}/scenarios/{sid}/datasets/{did}/", "get"),
}

#: The three responses that carry no entity tag, and why each does not: a
#: listing is not one bundle, a history is a ledger rather than a state, and a
#: deleted bundle has no version left to name.
NO_ENTITY_TAG = {
    (PREFIX + "/", "get"),
    (PREFIX + "/{uid}/history/", "get"),
    (PREFIX + "/{uid}/", "delete"),
}

#: The bundle read is the one operation that serves RDF, because it is the one
#: whose response *is* a subgraph.
RDF_MEDIA_TYPES = ("text/turtle", "application/ld+json")


def _operations():
    """Every scenario-bundle operation in the committed description."""
    document = yaml.safe_load(ARTIFACT.read_text(encoding="utf-8"))
    for path, methods in document["paths"].items():
        if not path.startswith(PREFIX):
            continue
        for method, operation in methods.items():
            yield path, method, operation


def _parameter(operation, name, location):
    for parameter in operation.get("parameters", []):
        if parameter.get("name") == name and parameter.get("in") == location:
            return parameter
    return None


def _is_public(operation):
    """Whether this operation's security says anonymous access is allowed.

    An empty requirement object in the list is OpenAPI's way of saying *no
    authentication is also acceptable*. It is the same entry Swagger UI reads
    to decide the padlock, which is the point of asking it here.
    """
    return {} in operation.get("security", [])


class ScenarioBundleDescriptionTest(SimpleTestCase):
    """The facts a client needs, asserted where a client would read them."""

    def setUp(self):
        self.operations = list(_operations())
        self.assertTrue(self.operations, f"no {PREFIX} operations described")

    def advice(self, path, method, complaint):
        return f"{method.upper()} {path}: {complaint}\n    {REGENERATE}"

    def test_no_operation_declares_only_a_success(self):
        """A document promising `200` and nothing else describes no contract."""
        for path, method, operation in self.operations:
            codes = set(operation.get("responses", {}))
            refusals = {code for code in codes if code[0] in "45"}
            self.assertTrue(
                refusals,
                self.advice(
                    path,
                    method,
                    f"declares only {sorted(codes)}. Every one of these "
                    "operations can refuse, and a client written against a "
                    "document that says otherwise handles none of it.",
                ),
            )

    def test_every_guarded_write_requires_if_match(self):
        """`If-Match` is required on every write to a bundle that exists."""
        for path, method, operation in self.operations:
            if method not in WRITE_METHODS:
                continue
            header = _parameter(operation, "If-Match", "header")
            if (path, method) == CREATE:
                self.assertIsNone(
                    header,
                    self.advice(
                        path,
                        method,
                        "declares If-Match, but a create has no version to "
                        "match: there is no bundle yet.",
                    ),
                )
                continue
            self.assertIsNotNone(
                header,
                self.advice(
                    path,
                    method,
                    "does not declare the If-Match header. It is required on "
                    "every write, with no opt-out.",
                ),
            )
            self.assertTrue(
                header.get("required"),
                self.advice(path, method, "declares If-Match as optional."),
            )

    def test_every_guarded_write_declares_its_three_precondition_refusals(self):
        """428, 412 and 409 mean three different things, so all three are said."""
        for path, method, operation in self.operations:
            if method not in WRITE_METHODS or (path, method) == CREATE:
                continue
            codes = set(operation.get("responses", {}))
            for code in ("428", "412", "409"):
                self.assertIn(
                    code,
                    codes,
                    self.advice(
                        path,
                        method,
                        f"does not declare {code}. The precondition refusals "
                        "are what a client has to act on differently.",
                    ),
                )

    def test_every_write_declares_who_may_not_write(self):
        """401 for no credentials, 403 for credentials that are not an owner."""
        for path, method, operation in self.operations:
            if method not in WRITE_METHODS:
                continue
            codes = set(operation.get("responses", {}))
            self.assertIn("401", codes, self.advice(path, method, "no 401"))
            if (path, method) == CREATE:
                self.assertNotIn(
                    "403",
                    codes,
                    self.advice(
                        path,
                        method,
                        "declares 403, but any authenticated account may "
                        "create a bundle -- there is no owner yet to fail.",
                    ),
                )
                continue
            self.assertIn(
                "403",
                codes,
                self.advice(
                    path,
                    method,
                    "does not declare 403. Only an owner may write to a "
                    "bundle, and a client cannot learn that from anywhere else.",
                ),
            )

    def test_every_operation_declares_the_two_refusals_none_of_them_chooses(self):
        """Throttling and an unreachable store can answer any of these."""
        for path, method, operation in self.operations:
            codes = set(operation.get("responses", {}))
            for code in ("429", "503"):
                self.assertIn(
                    code,
                    codes,
                    self.advice(
                        path,
                        method,
                        f"does not declare {code}. Every endpoint here is "
                        "throttled and every one of them reads the graph "
                        "store, so either can answer.",
                    ),
                )

    def test_expand_is_declared_on_exactly_the_operations_that_expand(self):
        declared = {
            (path, method)
            for path, method, operation in self.operations
            if _parameter(operation, "expand", "query") is not None
        }
        self.assertEqual(
            EXPANDS,
            declared,
            "?expand= is documented on a different set of operations than the "
            "one that acts on it. Adding an endpoint that expands means adding "
            "it to EXPANDS above -- being tolerated is not being offered.",
        )

    def test_every_description_states_its_auth_expectation(self):
        """And states the one the operation's own security block implies.

        Cross-checked rather than merely present: the words and the padlock are
        then two renderings of one fact instead of two claims that can drift.
        """
        for path, method, operation in self.operations:
            description = operation.get("description", "")
            public = _is_public(operation)
            expected = "Public" if public else "Requires authentication"
            unexpected = "Requires authentication" if public else "Public"
            self.assertIn(
                expected,
                description,
                self.advice(
                    path,
                    method,
                    f"has security {operation.get('security')}, which means "
                    f"{expected.lower()}, and its description does not say so.",
                ),
            )
            self.assertNotIn(
                unexpected,
                description,
                self.advice(
                    path,
                    method,
                    f"says {unexpected.lower()!r} while its security block "
                    "says the opposite.",
                ),
            )

    def test_no_operation_id_carries_a_collision_numeral(self):
        """A trailing numeral is a name no reader can map back to an endpoint."""
        for path, method, operation in self.operations:
            operation_id = operation.get("operationId", "")
            self.assertIsNone(
                re.search(r"_\d+$", operation_id),
                self.advice(
                    path,
                    method,
                    f"is called {operation_id!r}. The generator appends a "
                    "numeral when two operations would share a name; give this "
                    "one an operation_id of its own.",
                ),
            )

    def test_every_response_that_carries_an_entity_tag_declares_it(self):
        for path, method, operation in self.operations:
            headers = set()
            for response in operation.get("responses", {}).values():
                headers |= set(response.get("headers", {}))
            if (path, method) in NO_ENTITY_TAG:
                self.assertNotIn(
                    "ETag",
                    headers,
                    self.advice(
                        path,
                        method,
                        "declares an ETag it does not return.",
                    ),
                )
                continue
            self.assertIn(
                "ETag",
                headers,
                self.advice(
                    path,
                    method,
                    "returns an ETag and does not declare it. It is the value "
                    "the next write has to send back in If-Match.",
                ),
            )

    def test_a_create_says_where_it_put_the_resource(self):
        for path, method, operation in self.operations:
            if method != "post":
                continue
            created = operation.get("responses", {}).get("201", {})
            self.assertIn(
                "Location",
                set(created.get("headers", {})),
                self.advice(
                    path,
                    method,
                    "does not declare the Location header of its 201.",
                ),
            )

    def test_every_write_that_takes_a_payload_describes_it(self):
        """And no delete claims to take one: its guards are in the URL."""
        for path, method, operation in self.operations:
            if method in ("post", "patch"):
                self.assertIn(
                    "requestBody",
                    operation,
                    self.advice(
                        path,
                        method,
                        "takes a payload and the description does not say "
                        "what shape it has.",
                    ),
                )
            elif method == "delete":
                self.assertNotIn(
                    "requestBody",
                    operation,
                    self.advice(path, method, "claims to take a request body."),
                )

    def test_every_success_declares_the_body_it_returns(self):
        """A `200` with no schema describes half an answer.

        This is also what catches the one thing the shared part handlers
        cannot get right by themselves: a scenario factsheet and a study report
        are served by one implementation, so the body is filled in by the
        subclass that knows which serializer it is (`part_operations` in
        `oekg/part_views.py`). A subclass that forgot would ship the handler's
        own generic description -- true, and with nothing a client can read.
        """
        for path, method, operation in self.operations:
            for code, response in operation.get("responses", {}).items():
                if not code.startswith("2"):
                    continue
                schema = response.get("content", {}).get("application/json", {})
                self.assertIn(
                    "$ref",
                    schema.get("schema", {}),
                    self.advice(
                        path,
                        method,
                        f"describes its {code} in prose and gives no schema "
                        "for the body. Every success here is a serializer in "
                        "oekg/read_serializers.py.",
                    ),
                )

    def test_no_refusal_is_offered_in_a_form_it_cannot_arrive_in(self):
        """The bundle read serves three forms. Its refusals serve one.

        `GraphRenderer` hands an error body to JSON and corrects the response's
        own content type, so a `404` never arrives as turtle. The generator
        applies a view's renderers to every response it declares, which is what
        makes this worth pinning: the honest document takes an extra argument.
        """
        for path, method, operation in self.operations:
            for code, response in operation.get("responses", {}).items():
                if code[0] not in "45":
                    continue
                self.assertEqual(
                    ["application/json"],
                    list(response.get("content", {})) or ["application/json"],
                    self.advice(
                        path,
                        method,
                        f"offers its {code} in a form an error body is never "
                        "rendered in.",
                    ),
                )

    def test_the_bundle_read_offers_the_rdf_forms_it_serves(self):
        operation = dict(
            ((path, method), operation) for path, method, operation in self.operations
        )[(PREFIX + "/{uid}/", "get")]
        offered = set(operation["responses"]["200"].get("content", {}))
        for media_type in RDF_MEDIA_TYPES:
            self.assertIn(
                media_type,
                offered,
                self.advice(
                    PREFIX + "/{uid}/",
                    "get",
                    f"serves {media_type} on Accept and does not offer it.",
                ),
            )
