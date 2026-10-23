from Utils.prediction import (
    predict_startup_success
)


# =========================================================
# TEST STARTUP
# =========================================================

description = """
An online platform that connects students
with affordable tutors using technology.
Students can find tutors based on their
subjects, budget and learning requirements.
"""


print("=" * 70)
print("AI STARTUP SUCCESS PREDICTION TEST")
print("=" * 70)


# =========================================================
# RUN PREDICTION
# =========================================================

result = predict_startup_success(
    description
)


# =========================================================
# DISPLAY RESULT
# =========================================================

print("\nPREDICTION:")
print(
    result["status"]
)


print("\nSUCCESS PROBABILITY:")
print(
    f'{result["success_probability"]}%'
)


print("\nFAILURE PROBABILITY:")
print(
    f'{result["failure_probability"]}%'
)


print("\nRAW PREDICTION:")
print(
    result["prediction"]
)


print("\n" + "=" * 70)
print("TEST COMPLETED")
print("=" * 70)