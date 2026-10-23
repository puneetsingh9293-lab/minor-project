from Utils.genai import generate_validation_report


# =========================================================
# TEST STARTUP
# =========================================================

description = """
An online platform that connects students with affordable
tutors using technology. Students can find tutors based
on their subjects, budget and learning requirements.
"""


# =========================================================
# MOCK ML RESULT
# =========================================================

prediction_result = {
    "prediction": 0,
    "status": "High Risk",
    "success_probability": 47.63,
    "failure_probability": 52.37
}


# =========================================================
# MOCK FAILURE RESULTS
# =========================================================

failure_results = [
    {
        "startup_name": "Kitchit",
        "similarity_percentage": 16.16,
        "details": {
            "dimension": "Competition",
            "description": "A marketplace connecting customers with home chefs.",
            "failure_reason": "The market became highly competitive."
        }
    },

    {
        "startup_name": "Munchery",
        "similarity_percentage": 12.82,
        "details": {
            "dimension": "Competition",
            "description": "An on-demand food delivery company.",
            "failure_reason": "It struggled to compete with larger competitors."
        }
    }
]


# =========================================================
# MOCK INDIAN STARTUPS
# =========================================================

indian_startups = [
    {
        "startup_name": "Teachmint",
        "similarity_percentage": 59.29,
        "details": {
            "field_2": "Bengaluru",
            "field_3": "Anshuman Kumar, Divyansh Bordia, Mihir Gupta, Payoj Jain",
            "field_4": "E-Learning, EdTech, Education",
            "field_5": "Teachmint is an online learning platform connecting tutors and students.",
            "field_6": "51-100"
        }
    },

    {
        "startup_name": "InterviewBit",
        "similarity_percentage": 52.67,
        "details": {
            "field_2": "Bengaluru",
            "field_3": "Abhimanyu Saxena, Anshuman Singh",
            "field_4": "E-Learning, Employment, Information Technology",
            "field_5": "An e-learning platform helping software professionals develop their careers.",
            "field_6": "101-250"
        }
    },

    {
        "startup_name": "Doubtnut",
        "similarity_percentage": 48.22,
        "details": {
            "field_2": "Gurgaon",
            "field_3": "Aditya Shankar, Tanushree Nagori",
            "field_4": "E-Learning, EdTech, Education",
            "field_5": "An e-learning platform where students can ask academic questions.",
            "field_6": "11-50"
        }
    }
]


# =========================================================
# GENERATE REPORT
# =========================================================

print("=" * 70)
print("AI STARTUP VALIDATION REPORT")
print("=" * 70)


report = generate_validation_report(
    startup_description=description,
    prediction_result=prediction_result,
    failure_results=failure_results,
    indian_startups=indian_startups
)


print("\n")
print(report)


print("\n")
print("=" * 70)
print("TEST COMPLETED")
print("=" * 70)