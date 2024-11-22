

import html2text


def html_to_text(html: str, ignore_links: int =True) -> str:
    """
    Call to `HTML2Text` class with basic args.

    Args:
        html (str): HTML text extracted from the web.
        ignore_links (bool, optional): Option to ignore links in HTML when parsing.
            Defaults to True.

    Returns:
        str: Text extracted from the input HTML.
    """
    h = html2text.HTML2Text()
    h.ignore_links = ignore_links
    h.ignore_images = True
    h.bypass_tables = True
    return h.handle(html)
