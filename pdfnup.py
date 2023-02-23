#!/bin/env/python
# -*- coding: utf-8 -*-

"""Layout multiple pages per sheet of a PDF document.

Pdfnup is a Python module and command-line tool for layouting multiple
pages per sheet of a PDF document. Using it you can take a PDF document
and create a new PDF document from it where each page contains a number
of minimized pages from the original PDF file.

This can be considered a sample tool for the excellent package pyPdf by
Mathieu Fenniak, see http://pybrary.net/pyPdf.

For further information please look into the file README.txt!
"""


import base64
import io
import math
import pathlib
import zlib

try:
    from pypdf import PdfWriter
    from pypdf import PdfReader
    from pypdf import PageObject
    from pypdf.generic import NameObject
    from pypdf.generic import DictionaryObject
    from pypdf.generic import ArrayObject
    from pypdf.generic import FloatObject
    from pypdf.generic import ContentStream
except ImportError:
    print("Please install pyPdf first, see http://pybrary.net/pyPdf")
    raise  # RuntimeError(_MSG)


__version__ = "0.4.1"
__license__ = "GPL 3"
__author__ = "Dinu Gherman"
__date__ = "2009-07-06"


# one empty A4 page as base64-encoded zipped PDF file
_mtA4PdfZip64 = """\
eJyVVV1z2joQfWeG/7CTDjcwbfA3mLY3MwFCyrRpUyDpbUOmI2wB7hiJWnKT9KF/oH3re39rVzI2
DrQPNzMO8mp1ztmjlVy76A+OrKZTrdR+/vj+C0Z0zRP5iszgjDKaEElDwBQIeZCuKJOwlHL91DBu
b2+bic6NyawZ8BUCwGGXiCgYcCbF4VMIYiKEWtyPAhlxRpJ7qFYsMIHPPqn0yZKCkISFJAlhrlZB
WKRWK8+fgzGwwMYFIzg+rlYoCzcrDwdWmWByv6aWokV8e4uvIy9o/IXKKCAZICqkOm6UJsA4ZQEP
I7YA413ETpiI8oCafE1WVElR43E6k8gGhuZUkYl+1Zg7Ii/Igj7QqQIo0dlK1JHdonuIRZUbbVW6
4jinYUS6/A6uwcR39Xgdr2m3vRYOfddq+n7HhxuVe0EStU+tfO2ICp4mARWgDVU6rXzuIuHBmEqE
NVCerobeSfU7XKGybjHqFaMh3Og6EZhLbA8txpgkhGmCzVxmiq5ux5SRW3akRySJ+QJNcbem9PNe
G3EuM0vepDKOGNbgF9IR+5yHyHIp6GvOaB4U29IzFTnHrhCvLGTI5hxVeLkKRXqSyiVPoE4YZ/cr
noqGAu0llKjt6qvi67Zp+mbH9i3PdCxbJ7yk97c8CQXUGxuPwzSgiLM9W387RI1Ni32igYR6ysSa
BtE8oqGemEQypios1SBs7FXU2m02gSW1tsau1X7IhNK8z1LVDFpzhHqvwdFn7ebhDoo9nnaZZ4yA
ZIVE7R0ioSc25ziKJVqAfXYy7g2HvteneL70ng1iNDJ7zZhfUbaQS2iZmjdHOSPrt0vz9N/BE/Ny
+sKJDq74+9Vn4/xx9+qD88/V0G043WdPhLh8vzo8mp2dHsiDyYeGfPTu47dj1J7DPCzELxdS9Fi1
4pfbILPJ3JpSJJZ9uUvovFoxoYP/ij9oeZ7jwbyIWRZarGdYEbPNzl7Madt7sZa7n9f29/E6HXc3
ZmFwL+aYJQ6ZkCimSVbxsI8eQK30MVj8+WNwdISXF3YINutfW1pBXdfZ1DHNqe26/eOpbTvx1Pba
U7ttv8WBNTUtGx8HH6v2XwP+V/YNqF1F0eoEe8Wth1cHuPnbOPpKobPpJ5LIbLMsx1PfvdrpG7z6
fgMis+cW
"""
_mtA4Pdf = zlib.decompress(base64.standard_b64decode(_mtA4PdfZip64))


def isSquare(n):
    "Is this a square number?"

    s = math.sqrt(n)
    lower, upper = math.floor(s), math.ceil(s)

    return lower == upper


def isHalfSquare(n):
    "Is this a square number, divided by 2?"

    return isSquare(n * 2)


def calcScalingFactors(w, h, wp, hp):
    wp, hp = map(float, (wp, hp))

    if w is None:
        xscale = h/hp
        yscale = h/hp
    elif h is None:
        xscale = w/wp
        yscale = w/wp
    else:
        xscale = w/wp
        yscale = h/hp

    return xscale, yscale


def calcRects(pageSize, numTiles, dirs="RD"):
    "Return list of sub rects for some rect."

    allowdDirs = [x+y for x in "RL" for y in "UD"]
    allowdDirs += [y+x for x in "RL" for y in "UD"]
    assert dirs in allowdDirs

    width, height = pageSize
    n = numTiles
    xDir, yDir = dirs

    if isSquare(n):
        s = math.sqrt(n)
        w, h = float(width)/float(s), float(height)/float(s)
        if "R" in dirs:
            xr = range(0, int(s))
        elif "L" in dirs:
            xr = range(int(s)-1, -1, -1)
        if "D" in dirs:
            yr = range(int(s)-1, -1, -1)
        elif "U" in dirs:
            yr = range(0, int(s))
        xs = [i*w for i in xr]
        ys = [j*h for j in yr]
    elif isHalfSquare(n):
        # should issue a warning for page ratios different from 1:sqr(2)
        s = math.sqrt(2*n)
        if width > height:
            w, h = float(width)/float(s), float(height)/float(s)*2
            if "R" in dirs:
                xr = range(0, int(s))
            elif "L" in dirs:
                xr = range(int(s)-1, -1, -1)
            if "D" in dirs:
                yr = range(int(s/2)-1, -1, -1)
            elif "U" in dirs:
                yr = range(0, int(s/2))
            xs = [i*w for i in xr]
            ys = [j*h for j in yr]
        else:
            w, h = float(width)/float(s)*2, float(height)/float(s)
            if "R" in dirs:
                xr = range(0, int(s/2))
            elif "L" in dirs:
                xr = range(int(s/2)-1, -1, -1)
            if "D" in dirs:
                yr = range(int(s)-1, -1, -1)
            elif "U" in dirs:
                yr = range(0, int(s))
            xs = [i*w for i in xr]
            ys = [j*h for j in yr]

    # decide order (first x, then y or first y then x)
    if dirs in "RD LD RU LU".split():
        rects = [(x, y, w, h) for y in ys for x in xs]
    elif dirs in "DR DL UR UL".split():
        rects = [(x, y, w, h) for x in xs for y in ys]

    return rects


def exP1multiN(pdf, newPageSize, n):
    "Extract page 1 of a PDF file, copy it n times resized."

    # create a file-like buffer object containing PDF code
    buf = io.BytesIO()
    buf.write(pdf)

    # extract first page and resize it as desired
    srcReader = PdfReader(buf)
    page1 = srcReader.pages[0]
    page1.mediabox.upper_right = newPageSize

    # create output and copy the first page n times
    output = PdfWriter()
    for i in range(n):
        output.add_page(page1)

    # create a file-like buffer object to hold the new PDF code
    buf2 = io.BytesIO()
    output.write(buf2)
    buf2.seek(0)

    return buf2


def generateNup(
    inPathOrFile: io.IOBase | pathlib.Path | str,
    n: int,
    outPathPatternOrFile: io.IOBase | pathlib.Path | str | None = None,
    dirs="RD",
    verbose: bool = False,
):
    """Generate a N-up document version.

    If outPathPatternOrFile is None, the output will be written
    in a file named after the input file.
    """

    assert isSquare(n) or isHalfSquare(n)

    if isinstance(inPathOrFile, str):
        inPathOrFile = pathlib.Path(inPathOrFile)

    inFile = inPathOrFile
    outFile = outPathPatternOrFile

    if outPathPatternOrFile is None:
        if isinstance(inPathOrFile, pathlib.Path):
            outFile = inPathOrFile.parent / f"{inPathOrFile.stem}-{n}up{inPathOrFile.suffix}"
        else:
            raise AssertionError("Must specify output for file input!")
    elif isinstance(outPathPatternOrFile, str):
        outFile = pathlib.Path(outPathPatternOrFile)

    # get info about source document
    if isinstance(inFile, io.IOBase):
        docReader = PdfReader(inFile)
    else:
        with inFile.open('rb') as file:
            docReader = PdfReader(inFile)
    numPages = len(docReader.pages)
    oldPageSize = docReader.pages[0].mediabox.upper_right

    # create empty output document buffer
    if isSquare(n):
        newPageSize = oldPageSize
    elif isHalfSquare(n):
        newPageSize = oldPageSize[1], oldPageSize[0]
    np = numPages // n + numPages % n
    buf = exP1multiN(_mtA4Pdf, newPageSize, np)

    # calculate mini page areas
    rects = calcRects(newPageSize, n, dirs)

    # combine
    mapping = {}
    # newPageNum = -1
    for i in range(numPages):
        # if i % n == 0:
        #     newPageNum += 1
        destPageNum = i//n
        op = (inPathOrFile, i, (0, 0, None, None), destPageNum, rects[i % n])
        if destPageNum not in mapping:
            mapping[destPageNum] = []
        mapping[destPageNum].append(op)

    if isinstance(inFile, io.IOBase):
        srcr = PdfReader(inFile)
    else:
        with inFile.open('rb') as file:
            srcr = PdfReader(inFile)

    outr = PdfReader(buf)
    output = PdfWriter()

    for destPageNum, ops in mapping.items():
        for op in ops:
            inPathOrFile, srcPageNum, srcRect, destPageNum, destRect = op
            page2 = srcr.pages[srcPageNum]
            page1 = outr.pages[destPageNum]
            pageWidth, pageHeight = page2.mediabox.upper_right
            destX, destY, destWidth, destHeight = destRect
            xScale, yScale = calcScalingFactors(
                destWidth, destHeight, pageWidth, pageHeight)

            newResources = DictionaryObject()
            rename = {}
            orgResources = page1["/Resources"].get_object()
            page2Resources = page2["/Resources"].get_object()

            names = "ExtGState Font XObject ColorSpace Pattern Shading"
            for res in names.split():
                res = "/" + res
                new, newrename = PageObject._merge_resources(
                    orgResources,
                    page2Resources,
                    res
                )
                if new:
                    newResources[NameObject(res)] = new
                    rename.update(newrename)

            newResources[NameObject("/ProcSet")] = ArrayObject(
                frozenset(
                    orgResources.get("/ProcSet", ArrayObject()).get_object()
                ).union(
                    frozenset(
                        page2Resources.get("/ProcSet", ArrayObject()).get_object()
                    )
                )
            )

            newContentArray = ArrayObject()
            orgContent = page1["/Contents"].get_object()
            newContentArray.append(PageObject._push_pop_gs(orgContent, page1.pdf))
            page2Content = page2['/Contents'].get_object()
            page2Content = PageObject._content_stream_rename(
                page2Content,
                rename,
                page1.pdf
            )
            page2Content = ContentStream(page2Content, page1.pdf)
            page2Content.operations.insert(0, [[], "q"])

            # handle rotation
            try:
                rotation = page2["/Rotate"].get_object()
            except KeyError:
                rotation = 0
            if rotation in (180, 270):
                dw, dh = destWidth, destHeight
                arr = [-xScale, 0, 0, -yScale, destX+dw, destY+dh]
            elif rotation in (0, 90):
                arr = [xScale, 0, 0, yScale, destX, destY]
            else:
                # treat any other (illegal) rotation as 0
                arr = [xScale, 0, 0, yScale, destX, destY]

            arr = [FloatObject(str(x)) for x in arr]
            page2Content.operations.insert(1, [arr, "cm"])
            page2Content.operations.append([[], "Q"])
            newContentArray.append(page2Content)
            page1[NameObject('/Contents')] = ContentStream(
                newContentArray,
                page1.pdf
            )
            page1[NameObject('/Resources')] = newResources

        output.add_page(page1)

    if isinstance(outFile, io.IOBase):
        output.write(outFile)
    else:
        with outFile.open('wb') as file:
            output.write(file)

    if verbose:
        print("written to file-like input parameter")
        # if isinstance(oppof, str):
        #     print(f"written: {outPath.name}")
        # elif isinstance(oppof, io.IOBase):
