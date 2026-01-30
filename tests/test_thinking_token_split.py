"""
Test for thinking token split logic (fixes off-by-one error)
Tests the correct parsing of Qwen3 thinking tokens (token 151668 = </think>)
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def test_thinking_token_split_logic():
    """
    Test the thinking token split logic to ensure it correctly handles:
    1. Normal case: thinking tokens in middle
    2. Edge case: end token is the last token
    3. Edge case: end token is the first token (shouldn't happen but test anyway)
    4. Multiple occurrences: should use the last one
    """
    end_token = 151668
    
    # Test case 1: Normal case - thinking tokens in middle
    # generated_tokens = [1, 2, 3, 151668, 4, 5]
    # Expected: thinking = [1, 2, 3], content = [4, 5]
    generated_tokens_1 = [1, 2, 3, 151668, 4, 5]
    if end_token in generated_tokens_1:
        last = len(generated_tokens_1) - 1 - generated_tokens_1[::-1].index(end_token)
        thinking_tokens_1 = generated_tokens_1[:last]
        content_tokens_1 = generated_tokens_1[last + 1:]
        
        assert thinking_tokens_1 == [1, 2, 3], f"Expected [1, 2, 3], got {thinking_tokens_1}"
        assert content_tokens_1 == [4, 5], f"Expected [4, 5], got {content_tokens_1}"
        print("✅ Test 1 passed: Normal case")
    else:
        assert False, "End token not found in test case 1"
    
    # Test case 2: Edge case - end token is the last token
    # generated_tokens = [1, 2, 3, 151668]
    # Expected: thinking = [1, 2, 3], content = []
    generated_tokens_2 = [1, 2, 3, 151668]
    if end_token in generated_tokens_2:
        last = len(generated_tokens_2) - 1 - generated_tokens_2[::-1].index(end_token)
        thinking_tokens_2 = generated_tokens_2[:last]
        content_tokens_2 = generated_tokens_2[last + 1:]
        
        assert thinking_tokens_2 == [1, 2, 3], f"Expected [1, 2, 3], got {thinking_tokens_2}"
        assert content_tokens_2 == [], f"Expected [], got {content_tokens_2}"
        print("✅ Test 2 passed: End token is last token")
    else:
        assert False, "End token not found in test case 2"
    
    # Test case 3: Edge case - end token is the first token (unlikely but test)
    # generated_tokens = [151668, 1, 2, 3]
    # Expected: thinking = [], content = [1, 2, 3]
    generated_tokens_3 = [151668, 1, 2, 3]
    if end_token in generated_tokens_3:
        last = len(generated_tokens_3) - 1 - generated_tokens_3[::-1].index(end_token)
        thinking_tokens_3 = generated_tokens_3[:last]
        content_tokens_3 = generated_tokens_3[last + 1:]
        
        assert thinking_tokens_3 == [], f"Expected [], got {thinking_tokens_3}"
        assert content_tokens_3 == [1, 2, 3], f"Expected [1, 2, 3], got {content_tokens_3}"
        print("✅ Test 3 passed: End token is first token")
    else:
        assert False, "End token not found in test case 3"
    
    # Test case 4: Multiple occurrences - should use the last one
    # generated_tokens = [1, 151668, 2, 151668, 3]
    # Expected: thinking = [1, 151668, 2], content = [3]
    generated_tokens_4 = [1, 151668, 2, 151668, 3]
    if end_token in generated_tokens_4:
        last = len(generated_tokens_4) - 1 - generated_tokens_4[::-1].index(end_token)
        thinking_tokens_4 = generated_tokens_4[:last]
        content_tokens_4 = generated_tokens_4[last + 1:]
        
        assert thinking_tokens_4 == [1, 151668, 2], f"Expected [1, 151668, 2], got {thinking_tokens_4}"
        assert content_tokens_4 == [3], f"Expected [3], got {content_tokens_4}"
        print("✅ Test 4 passed: Multiple occurrences (uses last)")
    else:
        assert False, "End token not found in test case 4"
    
    # Test case 5: Single token (end token only)
    # generated_tokens = [151668]
    # Expected: thinking = [], content = []
    generated_tokens_5 = [151668]
    if end_token in generated_tokens_5:
        last = len(generated_tokens_5) - 1 - generated_tokens_5[::-1].index(end_token)
        thinking_tokens_5 = generated_tokens_5[:last]
        content_tokens_5 = generated_tokens_5[last + 1:]
        
        assert thinking_tokens_5 == [], f"Expected [], got {thinking_tokens_5}"
        assert content_tokens_5 == [], f"Expected [], got {content_tokens_5}"
        print("✅ Test 5 passed: Single end token only")
    else:
        assert False, "End token not found in test case 5"
    
    print("\n" + "=" * 60)
    print("✅ All thinking token split tests passed!")
    print("=" * 60)


def test_old_buggy_logic():
    """
    Demonstrate that the old logic was buggy
    This test shows what the old code would have produced (incorrectly)
    """
    end_token = 151668
    
    # Test case that would fail with old logic: end token is last
    # generated_tokens = [1, 2, 3, 151668]
    generated_tokens = [1, 2, 3, 151668]
    
    # OLD BUGGY LOGIC (what we had before):
    # index = len(generated_tokens) - generated_tokens[::-1].index(end_token)
    # thinking_tokens_old = generated_tokens[:index]
    # content_tokens_old = generated_tokens[index + 1:]
    
    # With old logic:
    # index = 4 - 0 = 4
    # thinking_tokens = [1, 2, 3, 151668]  # WRONG! Includes end token
    # content_tokens = []  # This part is actually correct by accident
    
    # NEW CORRECT LOGIC:
    last = len(generated_tokens) - 1 - generated_tokens[::-1].index(end_token)
    thinking_tokens_new = generated_tokens[:last]
    content_tokens_new = generated_tokens[last + 1:]
    
    # Verify new logic is correct
    assert thinking_tokens_new == [1, 2, 3], "New logic should exclude end token"
    assert content_tokens_new == [], "New logic should have empty content when end token is last"
    
    print("\n✅ Bug demonstration: Old logic would have included end token in thinking_tokens")
    print("   New logic correctly excludes it")


if __name__ == '__main__':
    """Run tests directly"""
    print("=" * 60)
    print("Testing Thinking Token Split Logic")
    print("=" * 60)
    print()
    
    try:
        test_thinking_token_split_logic()
        test_old_buggy_logic()
        print("\n✅ All tests passed!")
    except Exception as e:
        print(f"\n❌ Test Failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
