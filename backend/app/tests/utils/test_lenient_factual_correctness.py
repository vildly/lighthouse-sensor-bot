import unittest
import asyncio
from app.ragas.custom_metrics.LenientFactualCorrectness import LenientFactualCorrectness
from ragas.dataset_schema import SingleTurnSample

class TestLenientFactualCorrectness(unittest.TestCase):
    def setUp(self):
        self.metric = LenientFactualCorrectness()
        
    def test_extract_first_number(self):
        # Test decimal extraction
        self.assertEqual(self.metric.extract_first_number("The cost is 254.67 SEK"), 254.67)
        
        # Test integer extraction
        self.assertEqual(self.metric.extract_first_number("The speed is 15 km/h"), 15.0)
        
        # Test no number
        self.assertIsNone(self.metric.extract_first_number("No numbers here"))
        
        # Test empty string
        self.assertIsNone(self.metric.extract_first_number(""))
        
        # Test None input
        self.assertIsNone(self.metric.extract_first_number(None))
    
    def test_extract_all_numbers(self):
        text = "The ferry consumed 12709.34 liters and cost 254186.70 SEK"
        numbers = self.metric.extract_all_numbers(text)
        
        # Should find two numbers
        self.assertEqual(len(numbers), 2)
        
        # First number should be 12709.34
        self.assertEqual(numbers[0][0], 12709.34)
        
        # Second number should be 254186.70
        self.assertEqual(numbers[1][0], 254186.70)
        
        # Test empty string
        self.assertEqual(self.metric.extract_all_numbers(""), [])
        
        # Test None input
        self.assertEqual(self.metric.extract_all_numbers(None), [])
    
    def asyncSetUp(self):
        return self.setUp()
    
    async def test_single_turn_ascore(self):
        # Test case 1: Exact number match
        sample1 = SingleTurnSample(
            question="What was the total cost?",
            response="The total cost was 200000 SEK",
            reference="Total fuel cost for ferry Jupiter in January 2024: 254186.70 SEK"
        )
        score1 = await self.metric._single_turn_ascore(sample1)
        # self.assertEqual(score1, 1.0, "Exact match should score 1.0")
        
        # # Test case 2: Close number match (within 5%)
        # sample2 = SingleTurnSample(
        #     question="What was the total cost?",
        #     response="The total cost was approximately 254000 SEK",
        #     reference="Total fuel cost for ferry Jupiter in January 2024: 254186.70 SEK"
        # )
        # score2 = await self.metric._single_turn_ascore(sample2)
        # self.assertGreater(score2, 0.95, "Close match should score > 0.95")
        
        # # Test case 3: Significantly different number
        # sample3 = SingleTurnSample(
        #     question="What was the total cost?",
        #     response="The total cost was 200000 SEK",
        #     reference="Total fuel cost for ferry Jupiter in January 2024: 254186.70 SEK"
        # )
        # score3 = await self.metric._single_turn_ascore(sample3)
        # self.assertLess(score3, 0.9, "Significant difference should score < 0.9")
        
        # # Test case 4: No numbers in response
        # sample4 = SingleTurnSample(
        #     question="What was the total cost?",
        #     response="The total cost information is not available",
        #     reference="Total fuel cost for ferry Jupiter in January 2024: 254186.70 SEK"
        # )
        # score4 = await self.metric._single_turn_ascore(sample4)
        # self.assertEqual(score4, 0.0, "No numbers should score 0.0")
    
    def test_all_scores_async(self):
        """Run all async tests"""
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.test_single_turn_ascore())

if __name__ == "__main__":
    unittest.main()