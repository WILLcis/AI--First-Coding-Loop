import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SKILL_NAMES = ("context-economy", "slice-policy")


class SkillDirectoryTest(unittest.TestCase):
    def read_frontmatter(self, path: Path) -> dict[str, str]:
        text = path.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\n"), f"{path} must start with YAML frontmatter")
        match = re.match(r"---\n(.*?)\n---\n", text, flags=re.DOTALL)
        self.assertIsNotNone(match, f"{path} must close YAML frontmatter")
        fields: dict[str, str] = {}
        for line in match.group(1).splitlines():
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip()
        return fields

    def test_standard_skill_directories_exist(self) -> None:
        for name in SKILL_NAMES:
            with self.subTest(name=name):
                skill_file = ROOT / "skills" / name / "SKILL.md"
                self.assertTrue(skill_file.exists(), f"missing {skill_file}")
                fields = self.read_frontmatter(skill_file)
                self.assertEqual(fields["name"], name)
                self.assertGreater(len(fields["description"]), 80)

    def test_legacy_skill_files_point_to_canonical_skill(self) -> None:
        for name in SKILL_NAMES:
            with self.subTest(name=name):
                legacy = ROOT / "skills" / f"{name}.md"
                text = legacy.read_text(encoding="utf-8")
                self.assertIn(f"skills/{name}/SKILL.md", text)


if __name__ == "__main__":
    unittest.main()
