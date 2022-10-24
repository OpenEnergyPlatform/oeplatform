import logging
import re

import pandas as pd
from numpy import nan

logger = logging.getLogger("oeplatform")


def parse_csv(str_buffer):
    df = pd.read_csv(
        str_buffer,
        # encoding=encoding,
        # sep=delimiter,
        na_values=[""],
        keep_default_na=False,
    )
    # fix column names
    columns = [fix_column_name(n) for n in df.columns]
    # replace nan
    df = df.replace({nan: None})
    data = df.values.tolist()
    # create list of dicts
    data = [dict(zip(columns, row)) for row in data]
    return data


def fix_column_name(name):
    name_new = re.sub("[^a-z0-9_]+", "_", name.lower())
    return name_new
