"""Offline regression tests for the alternate guide generator."""
import unittest

from build_guide import ROOT, GuideSource, render_guide
from verify_materials import LabParser


class GuideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / 'index.html').read_text()

    def test_repeatable_generation(self):
        self.assertEqual(render_guide(self.source), render_guide(self.source))

    def test_source_edit_flows_through(self):
        modified = self.source.replace('fictional examples', 'fictional payer examples')
        self.assertIn('fictional payer examples', render_guide(modified))

    def test_preserves_encoded_sql_and_svg(self):
        output = render_guide(self.source)
        self.assertIn('WHERE AGE_AT_VISIT &gt;= 65', output)
        self.assertIn('viewBox="0 0 72 80"', output)
        self.assertEqual(output.count('class="coco-icon"'), 12)
        self.assertNotIn('{{MODULES}}', output)

    def test_module_order_and_heading_hierarchy(self):
        parsed = LabParser()
        parsed.feed(render_guide(self.source))
        self.assertEqual([section['id'] for section in parsed.sections], [
            'overview', 'tour', 'coco', 'load', 'sql', 'timetravel',
            'streamlit', 'wrapup', 'challenges', 'roles',
        ])
        self.assertEqual(parsed.headings.count(1), 1)
        self.assertEqual(parsed.headings.count(2), 10)
        self.assertTrue(all(section['practice_icons'] == 1 for section in parsed.sections))

    def test_void_and_self_closing_elements(self):
        parsed = GuideSource()
        parsed.feed('<section class="step" id="test" data-title="Test" data-mins="1">'
                    '<h1>One &amp; two</h1><p>Line<br>break<br /></p>'
                    '<svg class="coco-icon"><path d="M0 0" /></svg></section>')
        self.assertIn('<h2>One &amp; two</h2>', parsed.modules[0].body)
        self.assertIn('<br>break<br />', parsed.modules[0].body)
        self.assertIn('<path d="M0 0" />', ''.join(parsed.logo))

    def test_missing_logo_fails(self):
        with self.assertRaisesRegex(ValueError, 'missing CoCo logo'):
            render_guide(self.source.replace('class="coco-icon"', 'class="different-icon"'))

    def test_unbalanced_module_fails(self):
        with self.assertRaisesRegex(ValueError, 'Unclosed elements'):
            render_guide(self.source.replace('</section>', '<p></section>', 1))

    def test_unclosed_module_fails(self):
        with self.assertRaises(ValueError):
            render_guide(self.source.replace('</section>', '', 1))


if __name__ == '__main__':
    unittest.main()