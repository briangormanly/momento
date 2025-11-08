import unittest

from src.graph.models import ContentBlock, Entity, SystemLabel
from src.graph.providers.local_provider import LocalLLMProvider


class LocalProviderTest(unittest.TestCase):
    def test_extracts_person_entities(self):
        provider = LocalLLMProvider()
        entry = Entity(
            name="Test Entry",
            system_labels=[SystemLabel.ENTRY],
            content=ContentBlock(body="Brian met Yoli at Twilight Florist."),
        )

        result = provider.extract(entry, metadata={"text": entry.content.body})

        self.assertGreaterEqual(len(result.entities), 1)
        self.assertTrue(any(entity.system_labels for entity in result.entities))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
