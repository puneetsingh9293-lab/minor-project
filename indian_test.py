from Utils.indian_startups import (
    retrieve_similar_indian_startups
)


description = """
An online platform that connects students
with affordable tutors using technology.
Students can find tutors based on their
subjects, budget and learning requirements.
"""


print("=" * 70)
print("SIMILAR INDIAN STARTUPS")
print("=" * 70)


results = retrieve_similar_indian_startups(
    description,
    top_k=5
)


for i, result in enumerate(
    results,
    start=1
):

    print(
        f"\n{i}. {result['startup_name']}"
    )

    print(
        f"Similarity: "
        f"{result['similarity_percentage']}%"
    )

    print(
        "Details:",
        result["details"]
    )


print("\n" + "=" * 70)
print("TEST COMPLETED")
print("=" * 70)