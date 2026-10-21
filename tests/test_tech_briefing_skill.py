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

    def test_cross_job_window_and_safe_artifacts(self):
        for requirement in (
            "BOTH Monday and Thursday", "recorded coverage end",
            "DEGRADED edition must NOT advance", "seven days",
            "HHMMSS", "deduplication",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, self.content)

    def test_broad_discovery_and_editorial_limits(self):
        for requirement in (
            "eight distinct", "three independent", "at least twelve",
            "all four topics", "Home automation", "ONE story",
            "keep/reject reason", "blocked attempts do not count",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, self.content)

    def test_audit_evidence_and_honest_delivery(self):
        for requirement in (
            "research.json", "ledger.json", "EVERY citation command",
            "--strict --evidence --min-coverage 0.7", "published_at",
            "[CRON_FAILURE]", "scheduler delivers the FINAL RESPONSE",
            "actual briefing", "not just a temporary draft",
            'quote <id> --text "<verbatim quote>" --from',
            "watermark_eligible: false", "contiguously",
            "strict mode rejects uncited ledger entries",
            "Research coverage and delivery state are separate",
            "sanitized errors",
            "Do not modify provider configuration",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, self.content)


if __name__ == "__main__":
    unittest.main()
