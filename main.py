#!/usr/bin/env python3

import argparse
import io
import logging
import pathlib

from itertools import islice

from pypdf import PdfReader  # type: ignore
from pypdf import PdfWriter
from pypdf import PaperSize

from pdfnup import generateNup  # type: ignore
from pdfnup import _mtA4Pdf


the_empty_page = io.BytesIO(_mtA4Pdf)


def batched(iterable, n: int):
    "Batch data into lists of length n. The last batch may be shorter."
    "Coming in Python 3.12, without pading"
    # batched('ABCDEFG', 3) --> ABC DEF G
    if n < 1:
        raise ValueError('n must be >= 1')
    it = iter(iterable)
    while (batch := list(islice(it, n))):
        yield batch


def empty_page_fill(pages: int, section_pages: int) -> int:
    page_count_per_section = section_pages * 4
    empty_pages_add = (
        page_count_per_section - (pages % page_count_per_section)
    )
    # if empty_pages_add % page_count_per_section == 0:
    #     return 0
    return empty_pages_add


def generate_page_order(
    page_count: int,
    section_count: int
) -> list[int]:
    # Right Order. But the even pages need to be roteted 180 degs.
    r_list = []
    for each_section in batched(range(page_count), section_count*4):
        while each_section:
            r_list.append(each_section.pop())
            r_list.append(each_section.pop(0))
    return r_list


def order_pages(
    file: io.BytesIO,
    section_count: int,
) -> io.BytesIO:
    # WIP: Should mix 'load_page_order' & 'generate_page_order'.
    # Right Order. But the even pages need to be roteted 180 degs.
    pdf_reader = PdfReader(file)
    page_count: int = len(pdf_reader.pages)
    pdf_writer = PdfWriter()

    for each_section in batched(range(page_count), section_count*4):
        for x in range((len(each_section)+1) // 2):
            first_page = each_section.pop()
            last_page = each_section.pop(0)
            if x % 2 != 0:
                pdf_writer.add_page(pdf_reader.pages[first_page].rotate(180))
                pdf_writer.add_page(pdf_reader.pages[last_page].rotate(180))
                continue

            pdf_writer.add_page(pdf_reader.pages[first_page])
            pdf_writer.add_page(pdf_reader.pages[last_page])

    ordered_page = io.BytesIO()

    pdf_writer.write(ordered_page)
    pdf_writer.close()
    ordered_page.seek(0)
    return ordered_page


def add_empty_pages_to_fit_section_count(
    input_file: pathlib.Path,
    section_count: int
) -> tuple[io.BytesIO, int]:
    with input_file.open('rb') as file:
        pdf_reader = PdfReader(file)
        page_count: int = len(pdf_reader.pages)

        empty_page_count = empty_page_fill(page_count, section_count)
        pdf_writer = PdfWriter()
        pdf_writer.append_pages_from_reader(pdf_reader)
        for _ in range(empty_page_count):
            pdf_writer.append(the_empty_page)

        page_w_empty_pages = io.BytesIO()

        pdf_writer.write(page_w_empty_pages)
        pdf_writer.close()
        page_w_empty_pages.seek(0)
        return page_w_empty_pages, page_count + empty_page_count


def load_order_pages(
    file: io.BytesIO,
    the_order: list[int]
) -> io.BytesIO:
    merger = PdfWriter()
    merger.append(file, pages=the_order)
    page_ordered = io.BytesIO()
    merger.write(page_ordered)
    merger.close()
    page_ordered.seek(0)
    return page_ordered


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog='bookbinder',
        description='A Bookbinding helper program.',
        # epilog = 'Text at the bottom of help'
    )

    parser.add_argument(
        'src',
        type=pathlib.Path,
        help="The source PDF file from which the section corrected file are make.",
    )

    parser.add_argument(
        'out',
        type=pathlib.Path,
        help="The section corrected file.",
    )

    parser.add_argument(
        '-s', '--section',
        type=int,
        help="The folded page Count for a section."
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable Debugging info.',
    )

    # parser.add_argument(
    #     '-f', '--folds',
    #     type=int,
    #     help="The count of fold per page.",
    # )
    folds: int = 2

    args = parser.parse_args()

    if not args.src.exists():
        print('Could not find the source file...')
        exit()

    page_w_empty_pages, page_count = add_empty_pages_to_fit_section_count(
        input_file=args.src,
        section_count=args.section,
    )

    # the_order = generate_page_order(
    #     page_count=page_count,
    #     section_count=args.section,
    # )

    ordered_file = order_pages(
        file=page_w_empty_pages,
        section_count=args.section,
    )

    # ordered_file = load_order_pages(
    #     file=page_w_empty_pages,
    #     the_order=the_order,
    # )

    generateNup(ordered_file, folds, str(args.out))
