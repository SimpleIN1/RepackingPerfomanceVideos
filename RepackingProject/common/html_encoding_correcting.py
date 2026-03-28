
def correct_symbol_html_encoding(name: str):
    return name.replace("&amp;", "&") \
        .replace("&quot;", '"')
