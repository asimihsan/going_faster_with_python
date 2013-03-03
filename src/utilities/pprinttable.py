def pprinttable(rows):
    """ Pretty print namedtuple's as an ASCII table.

    >>> from collections import namedtuple
    >>> Row = namedtuple('Row',['first','second','third'])
    >>> data = Row(1,2,3)
    >>> data
    Row(first=1, second=2, third=3)
    >>> pprinttable([data])
     first = 1
    second = 2
     third = 3
    >>> pprinttable([data,data])
    first | second | third
    ------+--------+------
        1 |      2 |     3
        1 |      2 |     3

    References:
    -   http://stackoverflow.com/questions/5909873/python-pretty-printing-ascii-tables
    """

    headers = rows[0]._fields
    lens = []
    for i in range(len(rows[0])):
        lens.append(len(max([x[i] for x in rows] + [headers[i]],key=lambda x:len(str(x)))))
    formats = []
    hformats = []
    for i in range(len(rows[0])):
        if isinstance(rows[0][i], int):
            formats.append("%%%dd" % lens[i])
        else:
            formats.append("%%-%ds" % lens[i])
        hformats.append("%%-%ds" % lens[i])
    pattern = " | ".join(formats)
    hpattern = " | ".join(hformats)
    separator = "-+-".join(['-' * n for n in lens])
    print hpattern % tuple(headers)
    print separator
    for line in rows:
        print pattern % tuple(line)

if __name__ == "__main__":
    # ---------------------------------------------------------------
    #   pprinttable().
    # ---------------------------------------------------------------
    from collections import namedtuple
    Row = namedtuple('Row',['min', 'Q1', 'median', 'mean', 'Q2', 'max'])
    data = Row(0,1,2,3,4,5)
    pprinttable([data])
    # ---------------------------------------------------------------

