"""
Test script for production modules.
"""

import sys
from pathlib import Path

# Add yoga_assistant to path
sys.path.insert(0, str(Path(__file__).parent))

print("Testing production modules...\n")

# Test 1: Data ingestion
print("=" * 60)
print("Test 1: Data Ingestion")
print("=" * 60)

try:
    from yoga_assistant.ingest import load_yoga_data, validate_pose_data

    pose_dict = load_yoga_data("data/yoga_data_merged.csv")
    print(f"✓ Loaded {len(pose_dict)} poses")

    validate_pose_data(pose_dict)
    print("✓ Data validation passed")

    # Check a sample pose
    sample_pose = pose_dict[1]
    print(f"✓ Sample pose: {sample_pose['pose_name']}")

except Exception as e:
    print(f"✗ Data ingestion failed: {e}")
    sys.exit(1)

print()

# Test 2: Retrieval system
print("=" * 60)
print("Test 2: Retrieval System")
print("=" * 60)

try:
    from yoga_assistant.retrieval import create_retrieval_system

    print("Creating retrieval system...")
    retrieval_system = create_retrieval_system(pose_dict)
    print("✓ Retrieval system created")

    # Test search
    test_query = "poses for balance"
    results = retrieval_system.search(test_query, top_k=3)
    print(f"✓ Search for '{test_query}' returned {len(results)} results")

    for i, pose_id in enumerate(results, 1):
        pose = pose_dict[pose_id]
        print(f"  {i}. {pose['pose_name']} (ID: {pose_id})")

except Exception as e:
    print(f"✗ Retrieval system failed: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

print()

# Test 3: RAG pipeline (without LLM call)
print("=" * 60)
print("Test 3: RAG Module (Context Assembly)")
print("=" * 60)

try:
    from yoga_assistant.rag import assemble_context, create_structured_prompt

    # Test context assembly
    test_ids = [1, 2, 3]
    context = assemble_context(test_ids, pose_dict)
    print(f"✓ Context assembled for {len(test_ids)} poses")
    print(f"  Context length: {len(context)} characters")

    # Test prompt creation
    test_question = "What are good poses for beginners?"
    prompt = create_structured_prompt(test_question, context[:500])
    print("✓ Prompt created")
    print(f"  Prompt length: {len(prompt)} characters")

except Exception as e:
    print(f"✗ RAG module failed: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

print()

# Test 4: Full RAG pipeline (mock LLM)
print("=" * 60)
print("Test 4: RAG Pipeline Integration")
print("=" * 60)

try:
    # Test that all components work together
    question = "What poses help with flexibility?"

    # Step 1: Retrieve
    retrieved_ids = retrieval_system.search(question, top_k=5)
    print(f"✓ Retrieved {len(retrieved_ids)} poses")

    # Step 2: Assemble context
    context = assemble_context(retrieved_ids, pose_dict)
    print(f"✓ Context assembled ({len(context)} chars)")

    # Step 3: Create prompt
    prompt = create_structured_prompt(question, context)
    print(f"✓ Prompt created ({len(prompt)} chars)")

    print("\n✓ All components integrate successfully")

except Exception as e:
    print(f"✗ Integration failed: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

print()
print("=" * 60)
print("✓ ALL TESTS PASSED")
print("=" * 60)
print("\nProduction modules are ready!")
print("\nNote: LLM API calls not tested (requires API key)")
