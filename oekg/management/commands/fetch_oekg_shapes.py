"""Fetch the OEKG SHACL shape and generate the OEO label subset.

The single seam through which the platform obtains the artifacts the OEKG REST
API validates against. Run it at image-build time, after the OEO release has
been unpacked:

    python manage.py fetch_oekg_shapes

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from oekg.shape_artifacts import (
    ArtifactWrite,
    PinnedRef,
    ShapeArtifactError,
    extract_label_subset,
    fetch_shape,
    raw_github_url,
)
from ontology.utils import get_ontology_version


class Command(BaseCommand):
    help = (
        "Fetch the canonical OEKG SHACL shape from a pinned revision of the "
        "oekg repository and generate the rdfs:label subset the validator "
        "needs from the OEO release on disk. Safe to re-run; reports whether "
        "either artifact changed."
    )

    def add_arguments(self, parser):
        source = parser.add_mutually_exclusive_group()
        source.add_argument(
            "--commit",
            help=(
                "Commit sha in the oekg repository to fetch the shape from. "
                f"Defaults to settings.OEKG_SHAPES_PINNED_COMMIT "
                f"({settings.OEKG_SHAPES_PINNED_COMMIT[:12]}...)."
            ),
        )
        source.add_argument(
            "--tag",
            help=(
                "Git tag in the oekg repository to fetch the shape from. A "
                "branch or a moving name such as 'latest' is refused: an "
                "unpinned fetch changes the validator without a deploy."
            ),
        )
        parser.add_argument(
            "--repo",
            default=settings.OEKG_SHAPES_SOURCE_REPO,
            help="owner/name of the repository holding the shape.",
        )
        parser.add_argument(
            "--oeo-version",
            help=(
                "OEO release directory to take labels from. Defaults to the "
                "newest release present under settings.ONTOLOGY_ROOT."
            ),
        )

    def handle(self, *args, **options):
        ref = self._pinned_ref(options)
        url = raw_github_url(options["repo"], ref, settings.OEKG_SHAPES_SOURCE_FILE)

        # Resolved before the fetch, so a missing ontology fails without a
        # network call and without half of the pair being replaced.
        oeo_full_owl = self._oeo_full_owl(options["oeo_version"])

        self.stdout.write(f"shape source: {ref} -> {url}")

        try:
            shape = fetch_shape(url, Path(settings.OEKG_SHAPES_PATH))
            labels = extract_label_subset(
                oeo_full_owl, Path(settings.OEKG_SHAPE_LABELS_PATH)
            )
        except ShapeArtifactError as error:
            raise CommandError(str(error)) from error
        except OSError as error:
            # Network and filesystem failures alike: requests' exceptions are
            # OSError subclasses. Either way the prior artifact is untouched.
            raise CommandError(
                f"Could not obtain the OEKG shape artifacts: {error}. Any "
                "previously fetched artifact is unchanged."
            ) from error

        self._report("shape", shape)
        self._report("labels", labels)

        if shape.changed or labels.changed:
            self.stdout.write(self.style.SUCCESS("OEKG shape artifacts updated."))
        else:
            self.stdout.write(
                self.style.SUCCESS("OEKG shape artifacts already up to date.")
            )

    def _pinned_ref(self, options) -> PinnedRef:
        # argparse enforces this on the command line, but call_command bypasses
        # the parser for a non-required group, so state it here as well.
        if options.get("tag") and options.get("commit"):
            raise CommandError("Pass either --commit or --tag, not both.")
        try:
            if options.get("tag"):
                return PinnedRef.tag(options["tag"])
            return PinnedRef.commit(
                options.get("commit") or settings.OEKG_SHAPES_PINNED_COMMIT
            )
        except ShapeArtifactError as error:
            raise CommandError(str(error)) from error

    def _oeo_full_owl(self, version) -> Path:
        # Resolved from settings at call time rather than from the derived
        # settings constants, so a test can point ONTOLOGY_ROOT elsewhere.
        oeo_root = Path(settings.ONTOLOGY_ROOT) / settings.OPEN_ENERGY_ONTOLOGY_NAME
        if not oeo_root.is_dir():
            raise CommandError(
                f"No OEO release found under {oeo_root}. Download the ontology "
                "release before generating the label subset; this command "
                "never fetches the ontology itself."
            )
        version = get_ontology_version(oeo_root, version=version)
        oeo_full_owl = oeo_root / version / settings.OPEN_ENERGY_ONTOLOGY_FULL_OWL_NAME
        if not oeo_full_owl.is_file():
            raise CommandError(
                f"{oeo_full_owl} is missing, so the label subset cannot be "
                "generated. Download the ontology release before running this "
                "command; it never fetches the ontology itself."
            )
        return oeo_full_owl

    def _report(self, label: str, write: ArtifactWrite) -> None:
        style = self.style.SUCCESS if write.changed else self.style.NOTICE
        self.stdout.write(style(f"{label}: {write}"))
