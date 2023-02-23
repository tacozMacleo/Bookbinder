import io
import pathlib
# https://pypdf.readthedocs.io/en/latest/user/merging-pdfs.html

from itertools import islice

from pypdf import PdfReader
from pypdf import PdfWriter
from pypdf import PaperSize

from pdfnup import generateNup

input_file = pathlib.Path("test_page.pdf")
page_file_w_empty = pathlib.Path("midtle_page.pdf")
ordered_file = pathlib.Path("ordered_pages.pdf")
output_file = pathlib.Path("test_output.pdf")

empty_page = pathlib.Path('latex/empty_page.pdf')

page_count: int = 0
page_per_section: int = 5

def batched(iterable, n):
    "Batch data into lists of length n. The last batch may be shorter."
    "Coming in Python 3.12"
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

def generate_page_order(page_count, page_per_section) -> list[int | None]:
    r_list = []
    for each_section in batched(range(page_count), page_per_section*4):
        while each_section:
            r_list.append(each_section.pop())
            r_list.append(each_section.pop(0))
    return r_list


# pdf_writer.add_blank_page(PaperSize.A4.width, PaperSize.A4.height)

with input_file.open('rb') as file:
    pdf_reader = PdfReader(file)
    page_count = len(pdf_reader.pages)

    empty_page_count = empty_page_fill(page_count, page_per_section)
    pdf_writer = PdfWriter()
    pdf_writer.append_pages_from_reader(pdf_reader)
    for _ in range(empty_page_count):
        pdf_writer.append(empty_page)
        # pdf_writer.add_blank_page(PaperSize.A4.width, PaperSize.A4.height)

    # Adding Empty pages fails.

    # page_file_w_empty = io.BytesIO()
    with page_file_w_empty.open('wb') as midtle_file:
        pdf_writer.write(midtle_file)
        pdf_writer.close()

print(f'{page_count=} {empty_page_count=}')
page_order: list[int] = generate_page_order(page_count+empty_page_count, page_per_section)

# Open to count pages
# Generate the page order
# Load PDF, with the given order, and add empty pages until the count fits.
# Save to a file-like object.
# parse the file-like object to the pdfnup.
# Save the output to the output file.

with ordered_file.open('wb') as page_ordered:
    merger = PdfWriter()
    
    merger.append(page_file_w_empty, pages=page_order)
    
    # page_ordered = io.BytesIO()
    
    merger.write(page_ordered)
    merger.close()

    # Can not take empty pages and N them up.
generateNup(ordered_file, 2, str(output_file))
