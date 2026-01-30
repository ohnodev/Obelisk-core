"""
Test for thinking token split logic (fixes off-by-one error)
Tests the correct parsing of Qwen3 thinking tokens (token 151668 = </think>)
"""
from pathlib import Path
import sys

# Add parent directory to path to import the utility function
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.llm.thinking_token_utils import split_thinking_tokens


def test_thinking_token_split_logic():
    """
    Test the thinking token split logic to ensure it correctly handles:
    1. Normal case: thinking tokens in middle
    2. Edge case: end token is the last token
    3. Edge case: end token is the first token (shouldn't happen but test anyway)
    4. Multiple occurrences: should use the last one
    5. Single token: end token only
    """
    # Test case 1: Normal case - thinking tokens in middle
    # generated_tokens = [1, 2, 3, 151668, 4, 5]
    # Expected: thinking = [1, 2, 3], content = [4, 5]
    generated_tokens_1 = [1, 2, 3, 151668, 4, 5]
    thinking_tokens_1, content_tokens_1 = split_thinking_tokens(generated_tokens_1)
    
    assert thinking_tokens_1 == [1, 2, 3], f"Expected [1, 2, 3], got {thinking_tokens_1}"
    assert content_tokens_1 == [4, 5], f"Expected [4, 5], got {content_tokens_1}"
    print("✅ Test 1 passed: Normal case")
    
    # Test case 2: Edge case - end token is the last token
    # generated_tokens = [1, 2, 3, 151668]
    # Expected: thinking = [1, 2, 3], content = []
    generated_tokens_2 = [1, 2, 3, 151668]
    thinking_tokens_2, content_tokens_2 = split_thinking_tokens(generated_tokens_2)
    
    assert thinking_tokens_2 == [1, 2, 3], f"Expected [1, 2, 3], got {thinking_tokens_2}"
    assert content_tokens_2 == [], f"Expected [], got {content_tokens_2}"
    print("✅ Test 2 passed: End token is last token")
    
    # Test case 3: Edge case - end token is the first token (unlikely but test)
    # generated_tokens = [151668, 1, 2, 3]
    # Expected: thinking = [], content = [1, 2, 3]
    generated_tokens_3 = [151668, 1, 2, 3]
    thinking_tokens_3, content_tokens_3 = split_thinking_tokens(generated_tokens_3)
    
    assert thinking_tokens_3 == [], f"Expected [], got {thinking_tokens_3}"
    assert content_tokens_3 == [1, 2, 3], f"Expected [1, 2, 3], got {content_tokens_3}"
    print("✅ Test 3 passed: End token is first token")
    
    # Test case 4: Multiple occurrences - should use the last one
    # generated_tokens = [1, 151668, 2, 151668, 3]
    # Expected: thinking = [1, 151668, 2], content = [3]
    generated_tokens_4 = [1, 151668, 2, 151668, 3]
    thinking_tokens_4, content_tokens_4 = split_thinking_tokens(generated_tokens_4)
    
    assert thinking_tokens_4 == [1, 151668, 2], f"Expected [1, 151668, 2], got {thinking_tokens_4}"
    assert content_tokens_4 == [3], f"Expected [3], got {content_tokens_4}"
    print("✅ Test 4 passed: Multiple occurrences (uses last)")
    
    # Test case 5: Single token (end token only)
    # generated_tokens = [151668]
    # Expected: thinking = [], content = []
    generated_tokens_5 = [151668]
    thinking_tokens_5, content_tokens_5 = split_thinking_tokens(generated_tokens_5)
    
    assert thinking_tokens_5 == [], f"Expected [], got {thinking_tokens_5}"
    assert content_tokens_5 == [], f"Expected [], got {content_tokens_5}"
    print("✅ Test 5 passed: Single end token only")
    
    print("\n" + "=" * 60)
    print("✅ All thinking token split tests passed!")
    print("=" * 60)




if __name__ == '__main__':
    """Run tests directly"""
    print("=" * 60)
    print("Testing Thinking Token Split Logic")
    print("=" * 60)
    print()
    
    try:
        test_thinking_token_split_logic()
        print("\n✅ All tests passed!")
    except Exception as e:
        print(f"\n❌ Test Failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
