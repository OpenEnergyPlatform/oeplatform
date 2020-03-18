###########
# Parsers #
###########
import decimal
import re
from datetime import datetime, date

import geoalchemy2  # Although this import seems unused is has to be here
import sqlalchemy as sa
from sqlalchemy import (
    Column,
    MetaData,
    Table,
    and_,
    not_,
    column,
    func,
    literal_column,
    or_,
    select,
    util,
    cast,
    null,
)
import dateutil
from sqlalchemy.dialects.postgresql.base import INTERVAL
from sqlalchemy.schema import Sequence
from sqlalchemy.sql import functions as fun
from sqlalchemy.sql.annotation import Annotated
from sqlalchemy.sql.elements import Slice
from sqlalchemy.sql.expression import ColumnClause, CompoundSelect
from sqlalchemy.sql.sqltypes import Interval, _AbstractInterval

from api.connection import _get_engine
from api.error import APIError, APIKeyError
from api.connection import _get_engine
from sqlalchemy.sql.sqltypes import Interval, _AbstractInterval
from sqlalchemy.dialects.postgresql.base import INTERVAL
from sqlalchemy import types as sqltypes

from . import DEFAULT_SCHEMA

__KNOWN_TABLES = {}

pgsql_qualifier = re.compile(r"^[\w\d_\.]+$")


def get_or_403(dictionary, key):
    try:
        return dictionary[key]
    except KeyError:
        raise APIKeyError(dictionary, key)


def parse_single(x, caster):
    try:
        return caster(x)
    except ValueError:
        raise APIError("Could not parse %s as %s" % (x, caster))


def is_pg_qual(x):
    if not isinstance(x, str):
        return False
    return pgsql_qualifier.search(x)


def read_pgvalue(x):
    # TODO: Implement check for valid values
    if x is None:
        return null()
    return x


class ValidationError(Exception):
    def __init__(self, message, value):
        self.message = message
        self.value = value


def read_bool(s):
    if isinstance(s, bool):
        return s
    if s.lower() in ["true", "false"]:
        return s.lower() == "true"
    elif s.lower() in ["yes", "no"]:
        return s.lower() == "true"
    else:
        raise APIError("Invalid value in binary field", s)


def read_pgid(s):
    if is_pg_qual(s):
        return s
    raise APIError("Invalid identifier: '%s'" % s)


def set_meta_info(method, user, message=None):
    val_dict = {}
    val_dict["_user"] = user  # TODO: Add user handling
    val_dict["_message"] = message
    val_dict["_type"] = method
    return val_dict


def parse_insert(d, context, message=None, mapper=None):
    table = Table(
        read_pgid(get_or_403(d, "table")),
        MetaData(bind=_get_engine()),
        autoload=True,
        schema=read_pgid(get_or_403(d, "schema")),
    )
    field_strings = []
    for field in d.get("fields", []):
        if not (
            (isinstance(field, dict) and "type" in field and field["type"] == "column")
            or isinstance(field, str)
        ):
            raise APIError("Only pure column expressions are allowed in insert")
        field_strings.append(parse_expression(field))

    query = table.insert()

    if not "method" in d:
        d["method"] = "values"
    if d["method"] == "values":
        if field_strings:
            raw_values = get_or_403(d, "values")
            if not isinstance(raw_values, list):
                raise APIError("{} is not a list".format(raw_values))
            values = (
                zip(
                    field_strings,
                    parse_expression(x, allow_untyped_dicts=True, escape_quotes=False),
                )
                for x in raw_values
            )
        else:
            values = get_or_403(d, "values")

        def clear_meta(vals):
            val_dict = dict(vals)
            # make sure meta fields are not compromised
            if context["user"].is_anonymous:
                username = "Anonymous"
            else:
                username = context["user"].name
            val_dict.update(set_meta_info("insert", username, message))
            return val_dict

        values = list(map(clear_meta, values))

        query = query.values(values)
    elif d["method"] == "select":
        values = parse_select(d["values"])
        query = query.from_select(field_strings, values)
    else:
        raise APIError("Unknown insert method: " + str(d["method"]))

    if "returning" in d:
        return_clauses = [parse_expression(x, mapper) for x in d["returning"]]
        query = query.returning(*return_clauses)

    return query, values


def parse_select(d):
    """
        Defintion of a select query according to
        http://www.postgresql.org/docs/9.3/static/sql-select.html

        not implemented:
            [ WITH [ RECURSIVE ] with_query [, ...] ]
            [ WINDOW window_name AS ( window_definition ) [, ...] ]
            [ FOR { UPDATE | NO KEY UPDATE | SHARE | KEY SHARE } [ OF table_name [, ...] ] [ NOWAIT ] [...] ]
    """
    distinct = d.get("distinct", False)

    L = None

    keyword = d.get("keyword")

    if keyword and keyword.lower() in ["union", "except", "intersect"]:
        partials = []
        for part_sel in d.get("selects", []):
            t = part_sel.get("type")
            if t == "grouping":
                grouping = get_or_403(part_sel, "grouping")
                if isinstance(grouping, dict):
                    partials.append(parse_select(grouping))
                elif isinstance(grouping, list):
                    partials = map(parse_select, grouping)
                else:
                    APIError(
                        "Cannot handle grouping type. Dictionary or list expected."
                    )
            elif t == "select":
                partials.append(parse_select(part_sel))
            else:
                raise APIError("Unknown select type: " + t)
        query = CompoundSelect(util.symbol(keyword), *partials)
    else:
        kwargs = dict(distinct=distinct)
        if "fields" in d and d["fields"]:
            L = []
            for field in d["fields"]:
                if isinstance(field, str):
                    field = dict(
                        type="column",
                        column=field
                    )
                col = parse_expression(field)
                if "as" in field:
                    col.label(read_pgid(field["as"]))
                L.append(col)
        if "from" in d:
            kwargs["from_obj"] = parse_from_item(get_or_403(d, "from"))
        else:
            kwargs["from_obj"] = []
        if not L:
            L = "*"
        kwargs["columns"] = L
        query = select(**kwargs)

        # [ WHERE condition ]
        if d.get("where", False):
            query = query.where(parse_condition(d["where"]))

    if "group_by" in d:
        query = query.group_by(*[parse_expression(f) for f in d["group_by"]])

    if "having" in d:
        query.having([parse_condition(f) for f in d["having"]])

    if "select" in d:
        for constraint in d["select"]:
            type = get_or_403(constraint, "type")
            subquery = parse_select(get_or_403(constraint, "query"))
            if type.lower() == "union":
                query.union(subquery)
            elif type.lower() == "intersect":
                query.intersect(subquery)
            elif type.lower() == "except":
                query.except_(subquery)
    if "order_by" in d:
        for ob in d["order_by"]:
            expr = parse_expression(ob)
            if isinstance(ob, dict):
                desc = ob.get("ordering", "asc").lower() == "desc"
                if desc:
                    expr = expr.desc()
            query = query.order_by(expr)

    if "limit" in d:
        if isinstance(d["limit"], int) or d["limit"].isdigit():
            query = query.limit(int(d["limit"]))
        else:
            raise APIError("Invalid LIMIT: Expected a digit")

    if "offset" in d:
        if isinstance(d["offset"], int) or d["offset"].isdigit():
            query = query.offset(int(d["offset"]))
        else:
            raise APIError("Invalid LIMIT: Expected a digit")
    return query


def parse_from_item(d):
    """
        Defintion of a from_item according to 
        http://www.postgresql.org/docs/9.3/static/sql-select.html
        
        return: A from_item string with checked psql qualifiers.
        
        Not implemented:
            with_query_name [ [ AS ] alias [ ( column_alias [, ...] ) ] ]
            [ LATERAL ] function_name ( [ argument [, ...] ] ) [ AS ] alias [ ( column_alias [, ...] | column_definition [, ...] ) ]
            [ LATERAL ] function_name ( [ argument [, ...] ] ) AS ( column_definition [, ...] )
    """
    # TODO: If 'type' is not set assume just a table name is present
    if isinstance(d, str):
        d = {"type": "table", "table": d}
    if isinstance(d, list):
        return [parse_from_item(f) for f in d]
    dtype = get_or_403(d, "type")
    if dtype == "table":
        schema_name = read_pgid(d["schema"]) if "schema" in d else None
        only = d.get("only", False)
        ext_name = table_name = read_pgid(get_or_403(d, "table"))
        tkwargs = dict(autoload=True)
        if schema_name:
            ext_name = schema_name + "." + ext_name
            tkwargs["schema"] = d["schema"]
        if ext_name in __PARSER_META.tables:
            item = __PARSER_META.tables[ext_name]
        else:
            try:
                item = Table(d["table"], __PARSER_META, **tkwargs)
            except sa.exc.NoSuchTableError as e:
                raise APIError("Table {table} not found".format(table=ext_name))

        engine = _get_engine()
        conn = engine.connect()
        exists = engine.dialect.has_table(conn, item.name, item.schema)
        conn.close()
        if not exists:
            raise APIError("Table not found: " + str(item), status=400)
    elif dtype == "select":
        item = parse_select(d)
    elif dtype == "join":
        left = parse_from_item(get_or_403(d, "left"))
        right = parse_from_item(get_or_403(d, "right"))
        is_outer = d.get("is_outer", False)
        full = d.get("is_full", False)
        on_clause = None
        if "on" in d:
            on_clause = parse_condition(d["on"])
        item = left.join(right, onclause=on_clause, isouter=is_outer, full=full)
    else:
        raise APIError("Unknown from-item: " + dtype)

    if "alias" in d:
        item = item.alias(read_pgid(d["alias"]))
    return item


__PARSER_META = MetaData(bind=_get_engine())


def load_table_from_metadata(table_name, schema_name=None):
    ext_name = table_name
    if schema_name:
        ext_name = schema_name + "." + ext_name
    if ext_name and ext_name in __PARSER_META.tables:
        return __PARSER_META.tables[ext_name]
    else:
        if _get_engine().dialect.has_table(
            _get_engine().connect(), table_name, schema=schema_name
        ):
            return Table(table_name, __PARSER_META, autoload=True, schema=schema_name)


def parse_column(d, mapper):
    name = get_or_403(d, "column")
    is_literal = parse_single(d.get("is_literal", False), bool)
    table_name = d.get("table")
    table = None
    if table_name:
        table_name = read_pgid(table_name)
        if mapper is None:
            mapper = dict()
        do_map = lambda x: mapper.get(x, x)
        if "schema" in d:
            schema_name = read_pgid(do_map(d["schema"]))
        else:
            schema_name = None
        table = load_table_from_metadata(table_name, schema_name=schema_name)
    if table is not None and name in table.c:
        col = table.c[name]
        if isinstance(col.type, INTERVAL):
            col.type = Interval(col.type)
        return col
    else:
        if is_literal:
            return literal_column(name)
        else:
            if table_name is not None:
                return literal_column(table_name + "." + name)
            else:
                return column(name)


def parse_type(dt_string, **kwargs):

    if isinstance(dt_string, dict):
        dt = parse_type(
            get_or_403(dt_string, "datatype"), **dt_string.get("kwargs", {})
        )
        return dt
    else:
        # Are you an array?
        dtarr_expression = r"(?P<dtname>[A-z_]+)\s*\[\]"
        arr_match = re.match(dtarr_expression, dt_string)
        if arr_match:
            is_array = True
            dt_string = arr_match.groups()[0]
            dt, autoincrement = parse_type(dt_string)
            return sa.ARRAY(dt), autoincrement

        # Is the datatypestring of form NAME(NUMBER)?
        dt_expression = r"(?P<dtname>[A-z_]+)\s*\((?P<cardinality>.*(,.*)?)\)"
        match = re.match(dt_expression, dt_string)
        if match:
            dt_string = match.groups()[0]
            if dt_string.lower() == "geometry":
                return geoalchemy2.Geometry(geometry_type=match.groups()[1]), False
            else:
                dt_cardinality = map(int, match.groups()[1].replace(" ", "").split(","))
            dt, autoincrement = parse_type(dt_string)
            return dt(*dt_cardinality, **kwargs), autoincrement

        # So it's a plain type
        autoincrement = False

        dt_string = dt_string.lower()

        if dt_string in ("int", "integer"):
            dt = sa.types.INTEGER
        elif dt_string in ("bigint", "biginteger"):
            dt = sa.types.BigInteger
        elif dt_string in ("bit",):
            dt = sa.types.Binary
        elif dt_string in ("boolean", "bool"):
            dt = sa.types.Boolean
        elif dt_string in ("char",):
            dt = sqltypes.CHAR
        elif dt_string in ("date",):
            dt = sqltypes.Date
        elif dt_string in ("datetime",):
            dt = sqltypes.DateTime
        elif dt_string in ("timestamp", "timestamp without time zone"):
            dt = sqltypes.TIMESTAMP
        elif dt_string in ("time", "time without time zone"):
            dt = sqltypes.TIME
        elif dt_string in ("float"):
            dt = sqltypes.FLOAT
        elif dt_string in ("decimal"):
            dt = sqltypes.DECIMAL
        elif dt_string in ("interval",):
            dt = sqltypes.Interval
        elif dt_string in ("json",):
            dt = sqltypes.JSON
        elif dt_string in ("nchar",):
            dt = sqltypes.NCHAR
        elif dt_string in ("numerical", "numeric"):
            dt = sa.types.Numeric
        elif dt_string in ["varchar", "character varying"]:
            dt = sqltypes.VARCHAR
        elif dt_string in ("real",):
            dt = sqltypes.REAL
        elif dt_string in ("smallint",):
            dt = sqltypes.SMALLINT
        elif hasattr(geoalchemy2, dt_string):
            dt = getattr(geoalchemy2, dt_string)
        elif dt_string in _POSTGIS_MAP:
            dt = _POSTGIS_MAP[dt_string]
        elif hasattr(sqltypes, dt_string.upper()):
            dt = getattr(sqltypes, dt_string.upper())
        elif dt_string == "bigserial":
            dt = sa.types.BigInteger
            autoincrement = True
        else:
            raise APIError("Unknown type (%s)." % dt_string)
        return dt, autoincrement


_POSTGIS_MAP = {
    "compositeelement": geoalchemy2.types.CompositeElement, 'geography': geoalchemy2.types.Geography , 'geometry': geoalchemy2.types.Geometry, 'raster': geoalchemy2.types.Raster, 'rasterelement':geoalchemy2.types.RasterElement
}

def parse_expression(d, mapper=None, allow_untyped_dicts=False, escape_quotes=True):
    # TODO: Implement
    if isinstance(d, dict):
        if allow_untyped_dicts and "type" not in d:
            return d
        dtype = get_or_403(d, "type")
        if dtype == "column":
            return parse_column(d, mapper)
        if dtype == "grouping":
            grouping = get_or_403(d, "grouping")
            if isinstance(grouping, list):
                return [parse_expression(e) for e in grouping]
            else:
                return parse_expression(grouping)
        if dtype == "operator":
            return parse_operator(d)
        if dtype == "case":
            return parse_case(d)
        if dtype == "modifier":
            return parse_modifier(d)
        if dtype == "function":
            return parse_function(d)
        if dtype == "slice":
            return parse_slice(d)
        if dtype == "star":
            return "*"
        if dtype == "value":
            if "value" in d:
                if "datatype" in d:
                    dt = d["datatype"]
                    if dt == "Decimal":
                        return decimal.Decimal(get_or_403(d, "value"))
                    elif dt == "date":
                        return dateutil.parser.parse(get_or_403(d, "value")).date()
                    elif dt == "datetime":
                        return dateutil.parser.parse(get_or_403(d, "value"))
                    elif dt == "time":
                        return dateutil.parser.parse(get_or_403(d, "value")).time()
                return read_pgvalue(get_or_403(d, "value"))
            else:
                return None
        if dtype == "label":
            return parse_label(d)
        if dtype == "sequence":
            schema = read_pgid(d["schema"]) if "schema" in d else DEFAULT_SCHEMA
            s = '"%s"."%s"' % (schema, get_or_403(d, "sequence"))
            return Sequence(get_or_403(d, "sequence"), schema=schema)
        if dtype == "select":
            return parse_select(d)
        if dtype == "cast":
            expr = parse_expression(get_or_403(d, "source"))
            t, _ = parse_type(get_or_403(d, "as"))
            return cast(expr, t)
        else:
            raise APIError("Unknown expression type: " + dtype)
    if isinstance(d, list):
        return [
            parse_expression(
                x, allow_untyped_dicts=allow_untyped_dicts, escape_quotes=escape_quotes
            )
            for x in d
        ]
    if isinstance(d, str):
        if escape_quotes:
            return d.replace('"', "")
        else:
            return d
    return d


def parse_label(d):
    element = parse_expression(get_or_403(d, "element"))
    if not isinstance(element, sa.sql.expression.ClauseElement):
        element = sa.literal(element)
    return element.label(get_or_403(d, "label"))


def parse_slice(d):
    kwargs = {"step": 1}
    if "start" in d:
        kwargs["start"] = d["start"]
    if "stop" in d:
        kwargs["stop"] = d["stop"]
    return Slice(**kwargs)


def _unpack_clauses(clauses):
    if isinstance(clauses, list):
        clean_clauses = []
        for clause in clauses:
            if isinstance(clause, list):
                clean_clauses += list(map(_unpack_clauses, clause))
            else:
                clean_clauses.append(clause)
        clauses = {
            "type": "operator",
            "operator": "AND",
            "operands": list(map(parse_expression, clean_clauses)),
        }
    return clauses


def parse_condition(dl):
    clean_dl = _unpack_clauses(dl)
    return parse_expression(clean_dl)

def parse_case(dl):
    else_clause=parse_expression(dl["else"])
    if "expression" in dl:
        return sa.case(
            {parse_expression(case["when"]): parse_expression(case["then"]) for case in dl.get("cases", [])},
            value=parse_expression(dl["expression"]),
            else_=else_clause
        )
    else:
        return sa.case(
            [(parse_expression(case["when"]), parse_expression(case["then"])) for case in dl.get("cases", [])],
            else_=else_clause)

def parse_operator(d):
    query = parse_sqla_operator(
        get_or_403(d, "operator"),
        *list(map(parse_expression, get_or_403(d, "operands")))
    )
    return query


def parse_modifier(d):
    query = parse_sqla_modifier(
        get_or_403(d, "operator"),
        *list(map(parse_expression, get_or_403(d, "operands")))
    )
    return query


def parse_function(d):
    fname = get_or_403(d, "function")

    operand_struc = get_or_403(d, "operands")
    if isinstance(operand_struc, list):
        operands = list(map(parse_expression, operand_struc))
    else:
        if (
            isinstance(operand_struc, dict)
            and operand_struc.get("type", None) == "grouping"
        ):
            operands = parse_expression(operand_struc)
        else:
            operands = [parse_expression(operand_struc)]

    if fname == "+":
        if len(operands) != 2:
            raise APIError(
                "Wrong number of arguments for function %s. Expected 2. Got %d"
                % (fname, len(operands))
            )
        x, y = operands
        return x + y
    else:
        if fname == "nextval":
            return func.next_value(*operands)
        else:
            function = getattr(func, fname)
            return function(*operands)


def parse_scolumnd_from_columnd(schema, table, name, column_description):
    # Migrate Postgres to Python Structures
    data_type = column_description.get("data_type")
    size = column_description.get("character_maximum_length")
    if size is not None and data_type is not None:
        data_type += "(" + str(size) + ")"

    notnull = column_description.get("is_nullable", False)

    return {
        "column_name": name,
        "not_null": notnull,
        "data_type": data_type,
        "new_name": column_description.get("new_name"),
        "c_schema": schema,
        "c_table": table,
    }


def parse_sconstd_from_constd(schema, table, name_const, constraint_description):
    defi = constraint_description.get("definition")
    return {
        "action": None,  # {ADD, DROP}
        "constraint_type": constraint_description.get(
            "constraint_typ"
        ),  # {FOREIGN KEY, PRIMARY KEY, UNIQUE, CHECK}
        "constraint_name": name_const,
        "constraint_parameter": constraint_description.get("definition")
        .split("(")[1]
        .split(")")[0],
        # Things in Brackets, e.g. name of column
        "reference_table": defi.split("REFERENCES ")[1].split("(")[2]
        if "REFERENCES" in defi
        else None,
        "reference_column": defi.split("(")[2].split(")")[1]
        if "REFERENCES" in defi
        else None,
        "c_schema": schema,
        "c_table": table,
    }


def replace_None_with_NULL(dictonary):
    # Replacing None with null for Database
    for key, value in dictonary.items():
        if value is None:
            dictonary[key] = "NULL"

    return dictonary


def split(string, seperator):
    if string is None:
        return None
    else:
        return str(string).split(seperator)


def replace(string, occuring_symb, replace_symb):
    if string is None:
        return None
    else:
        return str(string).replace(occuring_symb, replace_symb)


def alchemyencoder(obj):
    """JSON encoder function for SQLAlchemy special classes."""
    if isinstance(obj, datetime.date):
        return obj.isoformat()
    elif isinstance(obj, decimal.Decimal):
        return float(obj)


sql_operators = {
    "EQUALS": "=",
    "GREATER": ">",
    "LOWER": "<",
    "NOTEQUAL": "!=",
    "NOTGREATER": "<=",
    "NOTLOWER": ">=",
    "=": "=",
    ">": ">",
    "<": "<",
    "!=": "!=",
    "<>": "!=",
    "<=": "<=",
    ">=": ">=",
}


def parse_sql_operator(key: str) -> str:
    return sql_operators.get(key)


def parse_sqla_operator(raw_key, *operands):
    key = raw_key.lower().strip()
    if not operands:
        raise APIError("Missing arguments for '%s'." % (key))
    if key in ["and"]:
        query = and_(*operands)
        return query
    elif key in ["or"]:
        query = or_(*operands)
        return query
    elif key in ["not"]:
        x = operands[0]
        return not_(parse_condition(x))
    else:
        if len(operands) != 2:
            raise APIError(
                "Wrong number of arguments for '%s'. Expected: 2 Got: %s"
                % (key, len(operands))
            )
        x, y = operands
        if x is None:
            x = null()

        if key in ["equals", "="]:
            return x == y
        if key in ["greater", ">"]:
            return x > y
        if key in ["lower", "<"]:
            return x < y
        if key in ["notequal", "<>", "!="]:
            return x != y
        if key in ["notgreater", "<="]:
            return x <= y
        if key in ["notlower", ">="]:
            return x >= y
        if key in ["add", "+"]:
            return x + y
        if key in ["substract", "-"]:
            return x - y
        if key in ["multiply", "*"]:
            return x * y
        if key in ["divide", "/"]:
            return x / y
        if key in ["concatenate", "||"]:
            return fun.concat(x, y)
        if key in ["is"]:
            return x is y
        if key in ["is not"]:
            return x.isnot(y)
        if key in ["like"]:
            return x.match(y)
        if key in ["<->"]:
            return x.distance_centroid(y)
        if key in ["getitem"]:
            if isinstance(y, Slice):
                return x[parse_single(y.start, int) : parse_single(y.stop, int)]
            else:
                return x[read_pgid(y)]
        if key in ["in"]:
            return x.in_(y)

    raise APIError("Operator '%s' not supported" % key)


def parse_sqla_modifier(raw_key, *operands):
    key = raw_key.lower().strip()
    if not operands:
        raise APIError("Missing arguments for '%s'." % key)

    if len(operands) != 1:
        raise APIError(
            "Wrong number of arguments for '%s'. Expected: 1 Got: %s"
            % (key, len(operands))
        )
    x = operands[0]
    if key in ["asc"]:
        return x.asc()
    if key in ["desc"]:
        return x.desc()
    raise APIError("Operator %s not supported" % key)
