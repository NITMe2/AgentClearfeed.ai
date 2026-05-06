# AgentClearfeed Format Specification
**Version:** 0.1 — Draft  
**Author:** AgentClearfeed  
**Date:** May 2026

---

## What Is This

A format specification for agent-readable content. The goal is simple: define a document structure that an AI agent can consume with minimum token overhead and maximum accuracy. No visual chrome. No prose optimised for persuasion. No room for AEO manipulation.

Every field is explicit. Every document is self-describing. An agent reading an ACF document should never have to infer what something is.

---

## Core Principles

- **Token efficiency first** — every byte must earn its place
- **Structured over prose** — fields not paragraphs where possible
- **Explicit affordances** — an agent always knows what it can do and what it is reading
- **Ungameable by design** — structured fields leave no room for narrative manipulation
- **No visual layer** — no CSS, no images, no layout, no formatting for human eyes

---

## Document Structure

Every ACF document is a plain text file with a `.acf` extension or served as `application/acf+json` over HTTP.

A document has two parts: a **header** and a **body**.

---

## Header

The header is mandatory. It identifies the document and provides metadata an agent needs before reading the body.

```
ACF/0.1
id:           unique document identifier
type:         [article | definition | dataset | claim | action | index]
title:        plain text, no formatting
source:       original source URL or institution
author:       name or organisation
published:    ISO 8601 date
updated:      ISO 8601 date
confidence:   [verified | claimed | contested | unknown]
domain:       primary subject domain
tags:         comma separated keywords
conflicts:    any known conflicts of interest or none
license:      content license or none
---
```

### Header Field Reference

| Field | Required | Description |
|---|---|---|
| `id` | Yes | Unique identifier for this document |
| `type` | Yes | Document type — controls which body fields are expected |
| `title` | Yes | Plain text title, no markdown |
| `source` | Yes | Where this content originates |
| `author` | Yes | Who produced it |
| `published` | Yes | Original publication date in ISO 8601 |
| `updated` | No | Last update date if different from published |
| `confidence` | Yes | How verified this content is |
| `domain` | Yes | Primary subject area |
| `tags` | No | Comma separated terms for indexing |
| `conflicts` | Yes | Declared conflicts of interest, or `none` |
| `license` | No | Content license |

---

## Confidence Levels

| Level | Meaning |
|---|---|
| `verified` | Peer reviewed, institutionally confirmed, or primary source |
| `claimed` | Stated by a credible source but not independently confirmed |
| `contested` | Multiple credible sources disagree |
| `unknown` | Origin or accuracy cannot be established |

Agents must surface confidence level in any output derived from ACF content.

---

## Body Types

The body format depends on the `type` field in the header.

---

### type: definition

For concepts, terms, and explanations.

```
DEFINITION
term:         the term being defined
plain:        one sentence plain language definition
technical:    technical definition if different from plain
domain:       field this definition applies within
related:      comma separated related terms
misconception: common misconception about this term, or none
source_quote: direct quote from primary source if available (max 30 words)
---
NOTES
Any additional context in plain prose. Keep under 100 words.
```

---

### type: article

For news, research summaries, and factual reports.

```
ARTICLE
summary:      2-3 sentence factual summary, no opinion
claims:
  - [claim 1]
  - [claim 2]
  - [claim n]
evidence:     what supports these claims
limitations:  what this article does not establish
methodology:  how the information was gathered if relevant
---
NOTES
Additional context under 100 words.
```

---

### type: dataset

For structured data descriptions.

```
DATASET
name:         dataset name
size:         number of records
features:     comma separated column names
target:       prediction target if applicable
source:       where to obtain the dataset
year:         year collected or published
known_biases:
  - [bias 1]
  - [bias 2]
limitations:
  - [limitation 1]
use_cases:    what this dataset is appropriate for
avoid:        what this dataset should not be used for
---
NOTES
Additional context under 100 words.
```

---

### type: claim

For individual assertions that can be evaluated.

```
CLAIM
statement:    the claim in one sentence
status:       [supported | unsupported | contested | unknown]
evidence_for:
  - [evidence 1]
evidence_against:
  - [evidence 1]
source:       primary source for this claim
qualifier:    any important caveats or scope limitations
---
```

---

### type: action

For exposing things an agent can do on a service. This is the ACF equivalent of a form or button.

```
ACTION
name:         action identifier
description:  what this action does in plain language
method:       [GET | POST | DELETE]
endpoint:     full URL
parameters:
  - name: param_name
    type: [string | integer | boolean | date]
    required: [yes | no]
    description: what this parameter does
returns:      description of what the response contains
errors:
  - code: 404
    meaning: resource not found
auth:         [none | bearer | apikey]
example:
  request:  example parameter values
  response: example response structure
---
```

---

### type: index

A directory of other ACF documents. Used for discovery.

```
INDEX
description:  what this index covers
documents:
  - id:       document id
    title:    document title
    type:     document type
    domain:   subject domain
    updated:  last updated date
  - id:       ...
---
```

---

## Full Example — Definition Document

```
ACF/0.1
id:           acf-def-demographic-parity
type:         definition
title:        Demographic Parity
source:       Barocas, Hardt, Narayanan — Fairness and Machine Learning
author:       AgentClearfeed
published:    2026-05-18
confidence:   verified
domain:       AI Fairness
tags:         fairness, bias, classification, metrics
conflicts:    none
license:      CC-BY-4.0
---
DEFINITION
term:         Demographic Parity
plain:        A model satisfies demographic parity if it produces positive predictions at equal rates across demographic groups.
technical:    P(Ŷ=1 | A=0) = P(Ŷ=1 | A=1) where A is a protected attribute and Ŷ is the model prediction.
domain:       Machine learning fairness
related:      equalised odds, individual fairness, calibration, COMPAS, disparate impact
misconception: Demographic parity does not guarantee equal accuracy across groups — a model can satisfy demographic parity while being less accurate for one group.
source_quote: "Statistical parity requires that the proportion of people receiving a positive outcome is the same in each group."
---
NOTES
Demographic parity is one of the most commonly cited group fairness metrics but is frequently in tension with equalised odds and calibration. Satisfying all three simultaneously is mathematically impossible in most real-world scenarios. The choice of which metric to optimise for is a value judgement, not a technical one.
```

---

## Full Example — Dataset Document

```
ACF/0.1
id:           acf-dataset-compas
type:         dataset
title:        COMPAS Recidivism Dataset
source:       ProPublica — Machine Bias Investigation
author:       AgentClearfeed
published:    2026-05-18
confidence:   verified
domain:       AI Fairness
tags:         recidivism, criminal justice, bias, COMPAS, ProPublica
conflicts:    none
license:      CC-BY-4.0
---
DATASET
name:         COMPAS Recidivism Dataset
size:         7214 records
features:     age, sex, race, prior_counts, charge_degree, compas_score, two_year_recid
target:       two_year_recid (binary recidivism within two years)
source:       https://github.com/propublica/compas-analysis
year:         2016
known_biases:
  - Black defendants scored higher risk at nearly twice the rate of white defendants who did not reoffend
  - White defendants who did reoffend were more frequently scored lower risk than Black defendants who did not
  - Age is a strong predictor and correlates with race in this dataset
limitations:
  - Single jurisdiction (Broward County, Florida)
  - Two year follow-up window only
  - COMPAS score methodology is proprietary and not fully disclosed
use_cases:    Fairness metric benchmarking, bias auditing research, classifier evaluation
avoid:        Production recidivism prediction, jurisdictions outside original study context
---
NOTES
The COMPAS dataset became the central evidence in ProPublica's 2016 Machine Bias investigation. It subsequently became a standard benchmark in algorithmic fairness research. Northpointe (now Equivant) disputed ProPublica's analysis, arguing their metric choices were inappropriate. This dispute itself became a landmark case study in how metric selection shapes fairness conclusions.
```

---

## Query Interface

An ACF server exposes a minimal HTTP interface.

```
GET /acf/query?q={natural language query}
GET /acf/document/{id}
GET /acf/index
GET /acf/domain/{domain}
```

Responses are plain ACF format. No JSON wrapper. No HTML. No pagination chrome. Just the document.

---

## What ACF Deliberately Excludes

| Excluded | Reason |
|---|---|
| Images | Zero information value for agents |
| CSS / styling | Irrelevant to agent consumption |
| Navigation | Agents query directly, don't browse |
| Ads | Incompatible with the format's purpose |
| Cookie notices | No tracking, no consent required |
| Promotional language | Structured fields leave no room for it |
| Ambiguous prose | Everything is labelled explicitly |

---

## Versioning

The version string `ACF/0.1` in the header identifies the spec version. Agents should check this before parsing. Breaking changes increment the major version. Additive changes increment the minor version.

---

## Status

This is a draft specification. The format is intentionally minimal at v0.1. Fields will be added as real agent consumption patterns reveal what is missing.

The goal is not a comprehensive standard on day one. The goal is the minimum viable format that proves the concept and generates real usage data to inform v0.2.

---

*AgentClearfeed — May 2026 — Draft*
