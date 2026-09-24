from pathlib import Path
import re
import unittest

import yaml


class TechBriefingSkillTests(unittest.TestCase):
    def setUp(self):
        self.content = Path("tech-briefing/SKILL.md").read_text(encoding="utf-8")
        end = re.search(r"\n---\s*\n", self.content[3:])
        if end is None:
            self.fail("SKILL.md frontmatter is not closed")
        self.frontmatter = yaml.safe_load(self.content[3 : end.start() + 3])

    def test_frontmatter_is_loadable_and_searchable(self):
        self.assertTrue(self.content.startswith("---"))
        self.assertEqual(self.frontmatter["name"], "tech-briefing")
        self.assertLessEqual(len(self.frontmatter["description"]), 60)
        self.assertTrue(self.frontmatter["description"].endswith("."))
        self.assertEqual(
            self.frontmatter["platforms"], ["linux", "macos", "windows"]
        )

    def test_skill_requires_live_window_and_citation_verification(self):
        self.assertIn("previous 72 hours", self.content)
        self.assertIn("grounded-citations", self.content)
        self.assertIn("strict citation verifier passes", self.content)
        self.assertIn("tech-briefing-YYYY-MM-DD.md", self.content)


if __name__ == "__main__":
    unittest.main()
