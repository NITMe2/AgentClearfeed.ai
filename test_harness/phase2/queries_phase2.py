"""Phase 2 test queries: multi-document retrieval across 10 diverse Wikipedia topics."""

PHASE2_TOPICS = [
    {"id": "photosynthesis", "html_file": "photosynthesis.html", "acf_doc": "acf-wiki-photosynthesis"},
    {"id": "roman_empire", "html_file": "roman_empire.html", "acf_doc": "acf-wiki-roman-empire"},
    {"id": "tcp_ip", "html_file": "tcp_ip.html", "acf_doc": "acf-wiki-tcp-ip"},
    {"id": "jazz", "html_file": "jazz.html", "acf_doc": "acf-wiki-jazz"},
    {"id": "great_wall", "html_file": "great_wall_of_china.html", "acf_doc": "acf-wiki-great-wall"},
    {"id": "crispr", "html_file": "crispr.html", "acf_doc": "acf-wiki-crispr"},
    {"id": "relativity", "html_file": "theory_of_relativity.html", "acf_doc": "acf-wiki-relativity"},
    {"id": "impressionism", "html_file": "impressionism.html", "acf_doc": "acf-wiki-impressionism"},
    {"id": "volcanic_eruptions", "html_file": "volcanic_eruptions.html", "acf_doc": "acf-wiki-volcanic-eruptions"},
    {"id": "bitcoin", "html_file": "bitcoin.html", "acf_doc": "acf-wiki-bitcoin"},
]

PHASE2_QUERIES = [
    {
        "id": "p2q1",
        "question": "What are the two main stages of photosynthesis and where does each occur?",
        "target_topic": "photosynthesis",
        "expected_facts": [
            "light-dependent reactions occur in the thylakoid membranes",
            "Calvin cycle or light-independent reactions occur in the stroma",
            "light reactions produce ATP and NADPH",
        ],
    },
    {
        "id": "p2q2",
        "question": "How does the TCP three-way handshake establish a connection?",
        "target_topic": "tcp_ip",
        "expected_facts": [
            "SYN packet sent by client to initiate connection",
            "server responds with SYN-ACK",
            "client sends final ACK to complete handshake",
        ],
    },
    {
        "id": "p2q3",
        "question": "How does CRISPR-Cas9 identify and cut a specific location in DNA?",
        "target_topic": "crispr",
        "expected_facts": [
            "guide RNA directs Cas9 to the target sequence",
            "Cas9 creates a double-strand break in the DNA",
            "PAM sequence adjacent to target is required for recognition",
        ],
    },
    {
        "id": "p2q4",
        "question": "What distinguishes Impressionist painting from earlier academic art?",
        "target_topic": "impressionism",
        "expected_facts": [
            "visible brush strokes and open composition",
            "emphasis on light and its changing qualities",
            "ordinary subject matter and outdoor painting en plein air",
        ],
    },
    {
        "id": "p2q5",
        "question": "How does Bitcoin prevent double-spending without a central authority?",
        "target_topic": "bitcoin",
        "expected_facts": [
            "proof of work consensus mechanism",
            "transactions verified by network of miners",
            "blockchain is a distributed public ledger",
        ],
    },
]
