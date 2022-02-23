import typing
from pathlib import Path

import xlrd
from openpyxl import load_workbook

from .. import utils
from ..cache import Cache

__authors__ = [
    "palewire",
]
__tags__ = [
    "excel",
]


def scrape(
    data_dir: Path = utils.WARN_DATA_DIR,
    cache_dir: Path = utils.WARN_CACHE_DIR,
) -> Path:
    """
    Scrape data from Kentucky.

    Arguments:
    output_dir -- the Path were the result will be saved

    Keyword arguments:
    data_dir -- the Path were the result will be saved (default WARN_DATA_DIR)
    cache_dir -- the Path where results can be cached (default WARN_CACHE_DIR)

    Returns: the Path where the file is written
    """
    # Get the latest workbook
    cache = Cache(cache_dir)
    latest_url = "https://kcc.ky.gov/WARN%20notices/WARN%20NOTICES%202022/WARN%20Notice%20Report%2001262022.xls"
    latest_path = cache.download("ky/latest.xls", latest_url)

    # Open it up
    latest_workbook = xlrd.open_workbook(latest_path)

    # Loop through the worksheets
    dict_list = []
    for sheet in latest_workbook.sheet_names():
        # Get the data as a list of lists
        sheet_obj = latest_workbook.sheet_by_name(sheet)
        sheet_list = parse_xls(sheet_obj)

        # Convert to list of dicts
        headers = sheet_list[0]
        for row in sheet_list[1:]:
            d = {}
            for x, value in enumerate(row):
                d[headers[x]] = value
            dict_list.append(d)

    # Same thing for the archived file
    archive_url = "https://kcc.ky.gov/WARN%20notices/2017%20WARN%20docs/Kentucky%20%20WARN%20Report%20-Tracking%20Form%20%281998-2016%29.xlsx"
    archive_path = cache.download("ky/archive.xlsx", archive_url)

    # Open it up
    archive_workbook = load_workbook(filename=archive_path)

    # Loop through the worksheets
    for sheet in archive_workbook.worksheets:
        # Get the data as a list of lists
        sheet_list = parse_xlsx(sheet)

        # Convert to list of dicts
        headers = sheet_list[0]
        for row in sheet_list[1:]:
            d = {}
            for i, value in enumerate(row):
                d[headers[i]] = value
            dict_list.append(d)

    # Write out the results
    data_path = data_dir / "ky.csv"
    all_headers = list({value for dic in dict_list for value in dic.keys()})
    utils.write_dict_rows_to_csv(
        data_path, all_headers, dict_list, extrasaction="ignore"
    )

    # Pass it out
    return data_path


def parse_xls(worksheet) -> typing.List[typing.List]:
    """Parse the Excel xls file at the provided path.

    Args:
        worksheet: An xlrd worksheet ready to parse

    Returns: List of dicts ready to write.
    """
    row_list = []
    for i in range(0, worksheet.nrows):
        row = worksheet.row_values(i)
        row_list.append(row)
    return row_list


def parse_xlsx(worksheet) -> typing.List[typing.List]:
    """Parse the Excel xlsx file at the provided path.

    Args:
        worksheet: An openpyxl worksheet ready to parse

    Returns: List of values ready to write.
    """
    # Convert the sheet to a list of lists
    row_list = []
    for r in worksheet.rows:
        # Parse cells
        cell_list = [cell.value for cell in r]

        # Skip empty rows
        try:
            # A list with only empty cells will throw an error
            next(c for c in cell_list if c)
        except StopIteration:
            continue

        # Add to the master list
        row_list.append(cell_list)

    # Pass it back
    return row_list


if __name__ == "__main__":
    scrape()
