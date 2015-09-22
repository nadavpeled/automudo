import re

TAG_CONTENTS_REGEX = r"<{0}.*?>(.*?)</{0}>"


def search_html_tag_by_type(tag_type, html_string):
    return re.search(
        TAG_CONTENTS_REGEX.format(tag_type),
        html_string, re.DOTALL
        ).group(1)


def find_html_tags_by_type(tag_type, html_string):
    return re.findall(
        TAG_CONTENTS_REGEX.format(tag_type),
        html_string, re.DOTALL
        )


def get_text(html_string):
    return re.sub("\s+", " ",
                  re.sub("<.*?>", "", html_string, re.DOTALL),
                  re.DOTALL).strip()
