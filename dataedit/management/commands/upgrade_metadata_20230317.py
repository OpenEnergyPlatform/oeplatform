"""
NOTE: this is a very ugly ONE TIME script to fix all existing legacy metadata
in the oep to the latest version 1.5

After migration, this code should be banished from the code base

"""

import json
import logging
import os
import re

import jsonschema.validators
from django.core.management.base import BaseCommand
from inflection import camelize
from omi.dialects.oep import OEP_V_1_5_Dialect
from omi.dialects.oep.compiler import compile_date_or_none
from omi.dialects.oep.parser import parse_date_or_none

from api.actions import get_table_metadata, set_table_metadata
from api.connection import _get_engine
from dataedit.models import Table
from dataedit.views import schema_whitelist

# ------------------------------------------------------------------------------------
# helper functions
# ------------------------------------------------------------------------------------


def flatten(obj) -> dict:
    def _flatten(x, path=""):
        if isinstance(x, list):
            x = enumerate(x)
        elif isinstance(x, dict):
            x = x.items()
        else:
            # assert isinstance(x, str)  # TODO remove
            yield (path, x)
            return
        for k, v in x:
            yield from _flatten(v, f"{path}{k}/")

    res_l = list(_flatten(obj))
    res_d = dict(res_l)
    assert len(res_l) == len(res_d)  # TODO remove
    return res_d


def unflatten(obj: dict):
    # recursion end
    if len(obj) == 1 and "" in obj:
        x = obj[""]
        # assert isinstance(x, str)  # TODO remove
        return x
    result = {}  # group by first part of path
    for path, x in obj.items():
        assert path.endswith("/"), path  # TODO REMOVE
        prefix, rest_path = path.split("/", maxsplit=1)
        if prefix not in result:
            result[prefix] = {}
        assert rest_path not in result[prefix]  # TODO remove
        result[prefix][rest_path] = x
    # recursion
    result = dict((p, unflatten(x)) for p, x in result.items())
    # convert to list
    if all(x.isnumeric() for x in result):
        result = dict((int(k), v) for k, v in result.items())
        max_id = max(result)
        lst = [None] * (max_id + 1)
        for i, x in result.items():
            lst[i] = x
        result = lst
    return result


def create_json_validator():

    schema_path = os.path.dirname(__file__) + "/../../static/metaedit/schema.json"

    with open(schema_path, "r", encoding="utf-8") as file:
        schema = json.load(file)

    validator_cls = jsonschema.validators.validator_for(schema)
    validator_cls.check_schema(schema)
    validator = validator_cls(schema)
    return validator


def omi_dump_and_parse(metadata_obj):
    dialect = OEP_V_1_5_Dialect()

    metadata_str = json.dumps(metadata_obj, ensure_ascii=False)
    metadata_oep = dialect.parse(metadata_str)
    metadata_obj_new = dialect.compile(metadata_oep)

    # omi sometimes creates tuples instead of lists
    metadata_obj_new = json.loads(json.dumps(metadata_obj_new))
    metadata_obj_new = remove_nulls(metadata_obj_new)

    return metadata_obj_new


def is_date_path(path):
    """check if path in object structure contains a date"""
    try:
        key = path.split("/")[-2]
    except IndexError:
        return False

    if "date" in key.lower() and "dates" not in key.lower():
        return True
    elif key in ["start", "end"]:
        return True
    else:
        return False


def fix_date(val, path=None):
    """fix date strings."""

    if not isinstance(val, str):
        raise Exception(val)
    elif re.match("^[0-9-]+T0$", val):
        return val[:-2]  # remove T0
    elif re.match("^[0-9-]+T00$", val):
        return val[:-3]  # remove T00
    elif re.match("^[0-9-]+T00:$", val):
        return val[:-4]  # remove T00
    elif re.match("^[0-9-]+T[0-9]{2}:$", val):
        return val[:-4]  # (FIXME)
    elif re.match("^[0-9]{2}-[0-9]{2}$", val):
        # only monath/day add dummy year (FIXME)
        return "1000-" + val
    elif re.match(r"^[0-9]{2}\.[0-9]{2}\.[0-9]{4}$", val):  # german date
        d, m, y = re.match(r"^([0-9]{2})\.([0-9]{2})\.([0-9]{4})$", val).groups()
        return f"{y}-{m}-{d}"
    elif re.match(r"^[0-9]{4}\.[0-9]{2}\.[0-9]{2}$", val):
        # iso date, but . instead of -
        y, m, d = re.match(r"^([0-9]{4})\.([0-9]{2})\.([0-9]{2})$", val).groups()
        return f"{y}-{m}-{d}"
    elif re.match(r"^[0-9]{4}-[0-9]{2}-?$", val):
        # missing day
        y, m = re.match(r"^([0-9]{4})-([0-9]{2})-?$", val).groups()
        return f"{y}-{m}-01"
    else:
        try:  # see if it goes through omi parsing
            val_d = parse_date_or_none(val)
            val_s = compile_date_or_none(val_d)
            return val_s or ""  # always return str
        except Exception:
            logging.warning(f"Not a date: {val} ({path})")
            return ""  # always return str


def fix_key(k):
    """fix old key names"""
    k = k.strip()
    k = k.replace(" ", "_")
    if k == "":
        return k
    k = camelize(k, uppercase_first_letter=False)
    if k == "uRL":
        k = "url"
    elif k == "licence":
        k = "license"
    elif k == "extend":
        k = "extent"
    elif k == "discription":
        k = "description"
    elif k == "fromat":
        k = "format"
    return k


def split_list(lst):
    assert isinstance(lst, list)
    for item in lst:
        for x in item.replace(";", ",").split(","):
            x = x.strip()
            if x:
                yield x


def fix_keywords(keywords):
    result = []
    for k in split_list(keywords):
        k = k[:40]
        result.append(k)
    return result


def fix_languages(languages):
    return [
        {
            "ger": "de-DE",
            "eng": "en-US",
            "english": "en-US",
            "en": "en-US",
            "en-g": "en-GB",
            "fre": "fr-FR",
            "de_de": "de-DE",
        }.get(lng.lower(), lng)
        for lng in split_list(languages)
    ]


def remove_nulls(obj):
    """recursively remove empty structures"""
    if isinstance(obj, list):
        # recursion
        obj_new = [remove_nulls(x) for x in obj]
        # drop None
        obj_new = [x for x in obj_new if x is not None]
        # if empty list: return None
        if not obj_new:
            obj_new = None
        return obj_new
    elif isinstance(obj, dict):
        # recursion
        obj_new = dict((k, remove_nulls(v)) for k, v in sorted(obj.items()))
        # drop None
        obj_new = dict((k, v) for k, v in sorted(obj_new.items()) if v is not None)
        # if empty list: return None
        if not obj_new:
            obj_new = None
        return obj_new
    elif obj is None:
        return None
    elif isinstance(obj, str):
        obj_new = obj.strip()
        if obj_new.lower() in ["", "null", "none", "..."]:
            obj_new = None
        return obj_new
    else:
        raise Exception((obj, type(obj)))


def find(meta, pat):
    pat = re.compile(pat)
    res = []
    for k in meta.keys():
        m = pat.match(k)
        if m:
            res.append(m)
    return res


# ------------------------------------------------------------------------------------
# main function
# ------------------------------------------------------------------------------------


def fix_metadata(metadata, table_name):
    """main function to fix metadata

    Args:

    metadata(object): python object with metadata
    table_name(str): name of table (fallback for missing mandatory id)

    Returns:
        python object with fixed metadata
        that should pass through the omi compiler/parser
        with minimal data loss
    """

    # recursively clean empty structures
    metadata = remove_nulls(metadata)
    metadata = flatten(metadata)

    # fix keys
    metadata = dict(
        ("/".join(fix_key(x) for x in k.split("/")), v) for k, v in metadata.items()
    )

    # check that values all are non empty stings
    # for v in metadata.values():
    #    assert isinstance(v, str) and v
    # check keys not case sensitivity
    # assert len(metadata) == len(set(k.lower() for k in metadata.keys()))

    # ----------------------------------------------------------------------------------

    def rm(val_old):
        del metadata[val_old.group()]

    def drop(val_old, val_new):
        return val_old

    def merge(val_old, val_new):
        return f"{val_old}; {val_new}"

    def err(val_old, val_new):
        raise Exception()

    def mov(match, key_new, on_conflict=err):
        key_old = match.group()
        if not isinstance(key_new, str):  # function
            key_new = key_new(match)
        elif "%" in key_new:
            key_new = key_new % match.groups()

        val = metadata.pop(key_old)
        if key_new in metadata:
            try:
                val = on_conflict(metadata[key_new], val)
            except Exception:
                raise Exception(f"{key_old} => {key_new}: {val} in {metadata[key_new]}")

        # logging.info(f"{key_old} => {key_new}: {val}")
        metadata[key_new] = val

    idx = "([0-9]+)"

    # ----------------------------------------------------------------------------------

    for m in find(metadata, "^(metadataVersion|metaVersion)/$"):
        rm(m)
    for m in find(metadata, "^metaMetadata/.*$"):
        rm(m)
    for m in find(metadata, f"^resources/{idx}/metaVersion/$"):
        rm(m)
    for m in find(metadata, "^_comment/.*$"):
        rm(m)

    # ----------------------------------------------------------------------------------

    for m in find(metadata, f"^source/{idx}/(name|url)/$"):
        mov(m, "sources/%s/%s/")
    for m in find(metadata, f"^source/{idx}/$"):
        mov(m, "sources/%s/name/")
    for m in find(metadata, "^sources/(copyright|license|name|url)/$"):  # NOT array
        mov(m, "sources/0/%s/")
    for m in find(metadata, "^originalFile/$"):
        mov(m, "sources/0/path/")
    for m in find(metadata, f"^originalFile/{idx}/$"):
        mov(m, "sources/%s/path/")
    for m in find(metadata, f"^retrieved/{idx}/$"):
        mov(m, "sources/%s/description/", merge)
    for m in find(metadata, "^dateOfCollection/$"):
        mov(m, "sources/0/description/", merge)
    for m in find(metadata, f"^dateOfCollection/{idx}/$"):
        mov(m, "sources/%s/description/", merge)
    for m in find(metadata, f"^sources/{idx}/copyright/$"):
        mov(m, "sources/%s/licenses/0/attribution/")
    for m in find(metadata, f"^sources/{idx}/license/$"):
        mov(m, "sources/%s/licenses/0/name/")
    for m in find(metadata, f"^sources/{idx}/url/$"):
        mov(m, "sources/%s/licenses/0/path/")
    for m in find(metadata, f"^sources/{idx}/name/$"):
        mov(m, "sources/%s/title/")
    for m in find(metadata, f"^sources/{idx}/comment/$"):
        mov(m, "sources/%s/description/", drop)

    for m in find(
        metadata, f"^license/{idx}/(copyright|name|url|version|id|instruction)/$"
    ):
        mov(m, "licenses/%s/%s/")
    for m in find(metadata, "^license/(copyright|name|url|version|id|instruction)/$"):
        mov(m, "licenses/0/%s/")
    for m in find(metadata, f"^license/{idx}/$"):
        mov(m, "licenses/%s/name/")
    for m in find(metadata, f"^instructionsForProperUse/{idx}/$"):
        mov(m, "licenses/0/instruction/")
    for m in find(metadata, f"^licenses/{idx}/copyright/$"):
        mov(m, "licenses/%s/attribution/")
    for m in find(metadata, f"^licenses/{idx}/url/$"):
        mov(m, "licenses/%s/path/")
    for m in find(metadata, f"^licenses/{idx}/version/$"):
        mov(m, "licenses/%s/title/")
    for m in find(metadata, f"^licenses/{idx}/id/$"):
        mov(m, "licenses/%s/name/", drop)

    for m in find(metadata, "^changes/(comment|date|mail|name)/$"):
        mov(m, "contributors/0/%s/")
    for m in find(metadata, f"^changes/{idx}/(comment|date|mail|name)/$"):
        mov(m, "contributors/%s/%s/")
    for m in find(metadata, f"^contributors/{idx}/mail/$"):
        mov(m, "contributors/%s/email/")
    for m in find(metadata, f"^contributors/{idx}/name/$"):
        mov(m, "contributors/%s/title/")

    for m in find(metadata, f"^label/{idx}/$"):
        mov(m, "keywords/%s/")

    for m in find(metadata, f"^description/{idx}/$"):
        mov(m, "description/", merge)
    for m in find(metadata, "^comment/$"):
        mov(m, "description/", merge)
    for m in find(metadata, "^notes?/$"):
        mov(m, "description/", merge)
    for m in find(metadata, f"^notes/{idx}/$"):
        mov(m, "description/", merge)
    for m in find(metadata, "^version/$"):
        mov(m, "description/", merge)
    for m in find(metadata, f"^toDo/{idx}/$"):
        mov(m, "description/", merge)

    for m in find(metadata, "^temporal/timeseries/([^/0-9]+)/$"):
        mov(m, "temporal/timeseries/0/%s/")
    for m in find(metadata, "^temporal/(start|end|resolution)/$"):
        mov(m, "temporal/timeseries/0/%s/")
    for m in find(metadata, "^temporal/timestamp/$"):
        mov(m, "temporal/timeseries/0/resolution/", drop)
    for m in find(metadata, "^referenceDate/$"):
        mov(m, "temporal/referenceDate/")
    for m in find(metadata, f"^referenceDate/{idx}/$"):
        mov(m, "temporal/referenceDate/")

    for m in find(metadata, f"^spatial/{idx}/extent/$"):
        mov(m, "spatial/extent/")
    for m in find(metadata, f"^spatial/{idx}/resolution/$"):
        mov(m, "spatial/resolution/")
    for m in find(metadata, f"^regionalLevel/{idx}/$"):
        mov(m, "spatial/resolution/")
    for m in find(metadata, f"^spatialResolution/({idx}/|)$"):
        mov(m, "spatial/resolution/", drop)

    for m in find(metadata, f"^resources/{idx}/fields/{idx}/(name|description|unit)/$"):
        mov(m, "resources/%s/schema/fields/%s/%s/")
    for m in find(metadata, f"^resources/{idx}/fields/{idx}/url/$"):
        mov(m, "resources/%s/schema/fields/%s/description/", drop)
    for m in find(metadata, f"^column/{idx}/(description|name|unit)/$"):
        mov(m, "resources/0/schema/fields/%s/%s/")
    for m in find(metadata, f"^fields/{idx}/(name|type|description)/$"):
        mov(m, "resources/0/schema/fields/%s/%s/", drop)
    for m in find(metadata, f"^tableFields/{idx}/(name|type|description|unit)/$"):
        mov(m, "resources/0/schema/fields/%s/%s/")
    for m in find(metadata, f"^tableFields/{idx}/descriptionGerman/$"):
        mov(m, "resources/0/schema/fields/%s/description/", drop)

    # ----------------------------------------------------------------------------------

    # id
    if not find(metadata, "^id/$"):
        metadata["id/"] = table_name

    # fix all dates
    for k, v in metadata.items():
        if is_date_path(k):
            metadata[k] = fix_date(v, k)

    metadata = unflatten(metadata)

    # fix keywords
    if "keywords" in metadata:
        metadata["keywords"] = fix_keywords(metadata["keywords"])

    # fix language codes
    if "language" in metadata:
        metadata["language"] = fix_languages(metadata["language"])

    metadata = remove_nulls(metadata)

    return metadata


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--fix", action="store_true", help="without this, only run checks"
        )

    def handle(self, *args, **options):

        logging.basicConfig(
            format="[%(levelname)7s] %(message)s",
            level=logging.INFO,
        )

        json_validator = create_json_validator()

        # DRY RUN: TEST ALL

        logging.info("---------------------------------------------------------------")
        logging.info("DRY RUN: check conversion for all tables")
        logging.info("---------------------------------------------------------------")

        for t in Table.objects.all():
            table_name = t.name
            schema_name = t.schema.name

            whitelisted = schema_name in schema_whitelist

            logging.info("")  # empty line
            logging.info(f"{schema_name}.{table_name} (whitelist={whitelisted})")

            # load metadata
            metadata_orig = get_table_metadata(schema_name, table_name)

            if not metadata_orig:
                logging.info("empty metadata")
                continue

            metadata_fixed = fix_metadata(metadata_orig, table_name)

            # validate with json schema
            json_validator.validate(metadata_fixed)

            # roundtrip omi to check if migration will work
            metadata_omi = omi_dump_and_parse(metadata_fixed)

            # compare (so we know omi round trip does not drop data)
            del metadata_omi["_comment"]
            del metadata_omi["metaMetadata"]
            assert json.dumps(metadata_fixed, sort_keys=True) == json.dumps(
                metadata_omi, sort_keys=True
            )

        logging.info("---------------------------------------------------------------")

        if not options["fix"]:
            logging.info("use --fix to actually save metadata")
            return

        logging.info("FIXING METADATA")
        logging.info("---------------------------------------------------------------")

        engine = _get_engine()

        for t in Table.objects.all():
            table_name = t.name
            schema_name = t.schema.name

            whitelisted = schema_name in schema_whitelist
            logging.info(f"{schema_name}.{table_name} (whitelist={whitelisted})")

            # load metadata from comment string
            metadata_orig = get_table_metadata(schema_name, table_name)

            if not metadata_orig:
                logging.info("empty metadata")
                continue

            metadata_fixed = fix_metadata(metadata_orig, table_name)

            with engine.connect() as con:
                with con:
                    cursor = con.connection.cursor()
                    set_table_metadata(table_name, schema_name, metadata_fixed, cursor)
                    con.connection.commit()
