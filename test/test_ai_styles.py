import json
import sys
import unittest
from dataclasses import FrozenInstanceError

sys.path.insert(0, "src")

from doctranslate.ai.styles import StyleError, StyleLibrary, compose_policy


class StyleLibraryTests(unittest.TestCase):
    def test_builtin_catalog_is_available_and_stable(self):
        library = StyleLibrary()
        ids = library.validate_all()
        self.assertEqual(len(ids), 11)
        self.assertEqual(ids, tuple(sorted(ids)))
        self.assertEqual(len(library.list("cs")), 11)

    def test_auto_is_implicit_and_explicit_profile_is_language_checked(self):
        library = StyleLibrary()
        self.assertEqual(library.resolve_variant(None, "cs"), "auto")
        self.assertEqual(library.resolve_variant("", "cs"), "auto")
        self.assertEqual(library.resolve_variant("auto", "cs"), "auto")
        self.assertEqual(library.resolve_variant("cs-expert", "cs"), "cs-expert")
        with self.assertRaises(StyleError):
            library.resolve_variant("cs-expert", "de")
        with self.assertRaises(StyleError):
            library.load("auto")

    def test_profiles_are_immutable_and_round_trip(self):
        library = StyleLibrary()
        profile = library.load("cs-modern-standard")
        with self.assertRaises(FrozenInstanceError):
            profile.id = "changed"
        self.assertEqual(profile.to_dict()["id"], profile.id)

    def test_dialect_profiles_contain_guardrails(self):
        library = StyleLibrary()
        for style_id in (
            "cs-dialect-plzen",
            "cs-colloquial-prague",
            "cs-colloquial-ostrava",
            "cs-hantec",
        ):
            profile = library.load(style_id)
            self.assertTrue(profile.lexicon)
            self.assertTrue(profile.transformations)
            self.assertTrue(any("polsk" in text for text in profile.prompt.avoid))
            self.assertEqual(profile.policy.caricature_intensity, 2)

    def test_invalid_catalog_is_rejected(self):
        library = StyleLibrary()
        payload = json.loads(
            json.dumps(
                {
                    "profiles": [
                        library.load("cs-expert").to_dict(),
                        library.load("cs-expert").to_dict(),
                    ]
                }
            )
        )
        with self.assertRaises(StyleError):
            StyleLibrary(payload)
        bad = library.load("cs-expert").to_dict()
        bad["policy"]["caricature_intensity"] = 4
        with self.assertRaises(StyleError):
            StyleLibrary({"profiles": [bad]})

    def test_auto_policy_preserves_author_style_without_sample(self):
        policy = compose_policy("en", "cs", "auto")
        self.assertIn("preserve the source author's register", policy)
        self.assertNotIn("Style sample", policy)

    def test_explicit_policy_contains_profile_rules_and_sample(self):
        policy = compose_policy("en", "cs", "cs-expert")
        self.assertIn("cs-expert", policy)
        self.assertIn("Style sample", policy)
        self.assertIn("terminologii", policy)
        with self.assertRaises(StyleError):
            compose_policy("en", "de", "cs-expert")

    def test_fingerprint_changes_when_profile_content_changes(self):
        library = StyleLibrary()
        profile = library.load("cs-expert")
        changed = profile.to_dict()
        changed["description"] += " changed"
        changed_library = StyleLibrary({"profiles": [changed]})
        self.assertNotEqual(
            library.fingerprint("cs-expert"),
            changed_library.fingerprint("cs-expert"),
        )
        self.assertEqual(library.fingerprint("auto"), "auto-v1")


if __name__ == "__main__":
    unittest.main()
