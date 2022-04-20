import re
from django.test import TestCase
from tutorials.views import formattedMarkdown

def md_to_html(md):
    # if md is list: assume these are lines and join them
    if isinstance(md, list):
        md = '\n'.join(md)
    html = formattedMarkdown(md)
    # remove linebreaks spaces for test comparison
    html = re.sub('\s+', '', html).strip()
    return html

class TestMarkdown(TestCase):    
    def test_formatted_markdown(self):
        """simple test that basic conversion works"""
        html = md_to_html("# header")
        self.assertTrue(re.match(".*<h1>header</h1>.*", html, re.IGNORECASE), html)
    

    def test_raw_html(self):
        # https://spec.commonmark.org/0.30/#raw-html        
        # usually, the result is enclosed in a <p> tag

        # inline
        html = md_to_html("text<b>bold</b>")
        self.assertTrue(re.match(".*text<b>bold</b>.*", html, re.IGNORECASE), html)

        # block
        html = md_to_html(["<table>", "    <tr></tr>", "</table>"])
        self.assertTrue(re.match(".*<table><tr></tr></table>.*", html, re.IGNORECASE), html)
    
    def test_blockquote(self):
        # https://spec.commonmark.org/0.30/#raw-html
        # usually, the result is enclosed in a <p> tag
        html = md_to_html(["> block line 1", "> block line 2"])
        self.assertTrue(re.match("<blockquote>blockline1<br/>blockline2</blockquote>", html, re.IGNORECASE), html)
