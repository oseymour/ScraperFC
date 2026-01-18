from bs4.element import Tag, NavigableString


def xpath_soup(element: Tag | NavigableString) -> str:
    """ Generate xpath from BeautifulSoup4 element.

    I shamelessly stole this from https://gist.github.com/ergoithz/6cf043e3fdedd1b94fcf.

    Example
    -------
    >>> import bs4
    >>> html = (
    ...     "<html><head><title>title</title></head>"
    ...     "<body><p>p <i>1</i></p><p>p <i>2</i></p></body></html>"
    ... )
    >>> soup = bs4.BeautifulSoup(html, "html.parser")
    >>> xpath_soup(soup.html.body.p.i)
    "/html/body/p[1]/i"
    >>> import bs4
    >>> xml = "<doc><elm/><elm/></doc>"
    >>> soup = bs4.BeautifulSoup(xml, "lxml-xml")
    >>> xpath_soup(soup.doc.elm.next_sibling)
    "/doc/elm[2]"

    :param element: BeautifulSoup4 element.
    :type element: Tag | NavigableString
    :return: xpath
    :rtype: str
    """
    components = []
    child = element if element.name else element.parent  # type: ignore
    for parent in child.parents:  # type: ignore
        siblings = parent.find_all(child.name, recursive=False)  # type: ignore
        components.append(
            child.name if 1 == len(siblings) else "%s[%d]" % (  # type: ignore
                child.name,  # type: ignore
                next(i for i, s in enumerate(siblings, 1) if s is child)
            )
        )
        child = parent
    components.reverse()
    return "/%s" % "/".join(components)
