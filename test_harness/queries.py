"""Test queries and their expected key facts for accuracy grading."""

QUERIES = [
    {
        "id": "q1",
        "question": "What is demographic parity in machine learning?",
        "acf_doc": "acf-def-demographic-parity",
        "html_file": "demographic_parity.html",
        "expected_facts": [
            "equal positive prediction rates across groups",
            "does not guarantee equal accuracy across groups",
            "also known as statistical parity",
        ],
    },
    {
        "id": "q2",
        "question": "What are the known biases in the COMPAS recidivism dataset?",
        "acf_doc": "acf-dataset-compas",
        "html_file": "compas_dataset.html",
        "expected_facts": [
            "Black defendants scored higher risk at nearly twice the rate",
            "single jurisdiction Broward County",
            "proprietary methodology",
        ],
    },
    {
        "id": "q3",
        "question": "Can a machine learning model satisfy calibration and equalised odds at the same time?",
        "acf_doc": "acf-article-impossibility-theorem",
        "html_file": "impossibility_theorem.html",
        "expected_facts": [
            "cannot be simultaneously satisfied when base rates differ",
            "mathematical impossibility not algorithmic limitation",
            "choice of metric is a normative decision",
        ],
    },
]
