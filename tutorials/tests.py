import re
from django.test import TestCase
from tutorials.views import formattedMarkdown

def md_to_html(md):
    # if md is list: assume these are lines and join them
    if isinstance(md, list):
        md = '\n'.join(md)
    html = formattedMarkdown(md)
    # make lowercase for comparison
    html = html.lower()
    # remove tag attributes for testing
    html = re.sub('<([^> ]+)(|[^>]*)>', r'<\1>', html)
    # remove additional <p> and <br> tags for testing
    html = re.sub('</?p>', '', html)
    # <br/> to <br>
    html = re.sub('<br/>', '<br>', html)
    # remove linebreaks spaces for test comparison
    html = re.sub('\s+', '', html).strip()

    return html

class TestMarkdown(TestCase):

    
    def test_formatted_markdown(self):
        """simple test that basic conversion works"""
        html = md_to_html("# header")
        self.assertEqual(html, "<h1>header</h1>")    

    def test_raw_html(self):
        # https://spec.commonmark.org/0.30/#raw-html        
        # usually, the result is enclosed in a <p> tag

        # inline
        html = md_to_html("text<b>bold</b>")
        self.assertEqual("text<b>bold</b>", html)

        # block
        html = md_to_html(["<table>", "    <tr></tr>", "</table>"])
        self.assertEqual("<table><tr></tr></table>", html)
    
    def test_blockquote(self):
        # https://spec.commonmark.org/0.30/#raw-html
        html = md_to_html(["> block line 1", "> block line 2"])
        self.assertEqual("<blockquote>blockline1<br>blockline2</blockquote>", html)
    
    def test_codeblock(self):
        html = md_to_html(["```python", "code", "```"])
        self.assertRegexpMatches(html, ".*<pre>.*<code>")

    def test_script(self):
        html = md_to_html(["<script>alert('hi');</script>", "text", "<script>alert('hi');</script>"])
        self.assertRegexpMatches(html, "text")
