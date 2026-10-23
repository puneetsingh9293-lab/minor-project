from Utils.failure_analysis import retrieve_similar_failures


# ---------------------------------------------------------
# TEST STARTUP IDEA
# ---------------------------------------------------------

startup_description = """
An online platform that connects local home cooks with
customers looking for affordable homemade meals. Customers
can discover meals from nearby cooks, place orders through
the platform, and local cooks can earn money by selling
their homemade food.
"""


# ---------------------------------------------------------
# RUN ANALYSIS
# ---------------------------------------------------------

results = retrieve_similar_failures(
    startup_description,
    top_k=5
)


# ---------------------------------------------------------
# DISPLAY RESULTS
# ---------------------------------------------------------

print("\n")
print("=" * 70)
print("SIMILAR HISTORICAL STARTUP FAILURES")
print("=" * 70)


if not results:

    print("\nNo similar startups found.")

else:

    for i, result in enumerate(results, start=1):

        print(f"\n{i}. {result['startup_name']}")

        print(
            f"   Similarity: "
            f"{result['similarity_percentage']}%"
        )

        print(
            f"   Details: "
            f"{result['details']}"
        )


print("\n")
print("=" * 70)
print("TEST COMPLETED")
print("=" * 70)