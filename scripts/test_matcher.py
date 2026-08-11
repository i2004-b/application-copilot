# Test script for matching

from src.extractor.schemas import ExtractedJob
from src.matcher.match import match_job_to_resume


def print_matches(job: ExtractedJob):
    print("\n" + "=" * 80)
    print(f"JOB: {job.company} — {job.title}")
    print(f"ROLE TYPE: {job.role_type}")
    print("=" * 80)

    matches = match_job_to_resume(job, k=5)

    if not matches:
        print("No resume matches returned.")
        return

    for i, match in enumerate(matches, start=1):
        print(f"\n{i}. Score: {match['score']:.4f}")
        print(f"Tracks: {match['tracks']}")
        print(f"Bullet: {match['text']}")


def main():
    jobs = [
        ExtractedJob(
            company="Aquatic Capital Management",
            title="Software Engineer, Intern",
            organization=None,
            location="Chicago, IL",
            role_type="SWE",
            required_skills=[
                "Python",
                "C++",
                "Algorithms",
                "Systems",
                "Computer Architecture",
            ],
            preferred_skills=[],
            min_years_experience=None,
            is_internship=True,
            summary=(
                "Software engineering internship focused on building high-performance "
                "systems and solving technical problems involving algorithms, systems, "
                "and computer architecture."
            ),
        ),

        ExtractedJob(
            company="PlusAI",
            title="Machine Learning Engineer Intern",
            organization=None,
            location="Santa Clara, CA",
            role_type="AI/ML Engineer",
            required_skills=[
                "Python",
                "Pandas",
                "NumPy",
                "Temporal Data",
                "Classification",
                "Supervised Learning",
            ],
            preferred_skills=[
                "Spark",
                "Ray",
                "Autonomous Driving",
            ],
            min_years_experience=None,
            is_internship=True,
            summary=(
                "Machine learning engineering internship focused on building and "
                "evaluating models and data pipelines for autonomous driving."
            ),
        ),

        ExtractedJob(
            company="XTX Markets",
            title="AI Research Internship - XTY Labs",
            organization="XTY Labs",
            location="New York, NY",
            role_type="AI/ML Researcher",
            required_skills=[
                "Deep Learning",
                "Transformers",
                "Data Science",
                "Optimization",
                "Statistics",
                "Programming",
            ],
            preferred_skills=[
                "Foundation Models",
                "Large Language Models",
                "Time Series Forecasting",
            ],
            min_years_experience=None,
            is_internship=True,
            summary=(
                "AI research internship focused on original machine learning research, "
                "deep learning, transformers, and large-scale model development."
            ),
        ),

        ExtractedJob(
            company="Tessera Labs",
            title="Product Manager, Intern",
            organization=None,
            location="San Jose, CA or Remote",
            role_type="TPM/PM",
            required_skills=[
                "Analytical Problem Solving",
                "Communication",
                "Organization",
                "Collaboration",
                "Ambiguity Management",
            ],
            preferred_skills=[
                "User Research",
                "Data Analysis",
                "AI",
                "SaaS",
                "Enterprise Software",
            ],
            min_years_experience=None,
            is_internship=True,
            summary=(
                "Product management internship focused on solving ambiguous product "
                "problems, coordinating stakeholders, and working with AI products."
            ),
        ),

        ExtractedJob(
            company="Common Sense Privacy",
            title="Account Executive",
            organization=None,
            location="Remote",
            role_type="Other",
            required_skills=[
                "B2B SaaS Sales",
                "Pipeline Generation",
                "CRM",
                "Forecasting",
            ],
            preferred_skills=[
                "Privacy Sales",
                "Security Sales",
            ],
            min_years_experience=5,
            is_internship=False,
            summary=(
                "Enterprise sales role focused on pipeline generation, account growth, "
                "forecasting, and B2B SaaS sales."
            ),
        ),
    ]

    for job in jobs:
        print_matches(job)


if __name__ == "__main__":
    main()