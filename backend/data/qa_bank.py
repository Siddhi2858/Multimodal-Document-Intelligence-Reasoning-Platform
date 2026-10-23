"""
data/qa_bank.py
---------------
Sample question-and-answer pairs used by the /ask endpoint.

When a user submits a question that matches one of the known questions
(case-insensitive), the pre-written answer is returned.

For any unknown question, a fallback "not found" response is generated
so the frontend can display the correct empty state.
"""

from models.qa import QuestionSource, QuestionResponse

# ---------------------------------------------------------------------------
# Known Q&A pairs (mirrors frontend mockQuestions.ts)
# ---------------------------------------------------------------------------

_KNOWN_QA: list[dict] = [
    {
        "question": "how does the cross-attention kernel isolate multi-column tabular delimiters",
        "response": QuestionResponse(
            found=True,
            answer=(
                "The model enforces an anisotropic spatial bias matrix aligned "
                "directly with detected white-space channels. Rather than treating "
                "visual layout as an isotropic patch grid, the horizontal projection "
                "matrices compress token affinity along the horizontal reading axis, "
                "forcing the attention distribution to saturate when crossing vertical "
                "boundary margins."
            ),
            sources=[
                QuestionSource(
                    page_number=4,
                    chunk_id="chk-4-02",
                    snippet=(
                        "\u201c...horizontal projection matrices restrict spatial "
                        "receptive fields, producing high boundary gradients at "
                        "structural gutters.\u201d"
                    ),
                    score=0.88,
                    top_offset=120,
                ),
                QuestionSource(
                    page_number=8,
                    chunk_id="chk-8-01",
                    snippet=(
                        "\u201cIn tabular regimes (Table 2), cross-attention heads "
                        "suppress cross-column bleed by 34.2% over isotropic ViT "
                        "configurations.\u201d"
                    ),
                    score=0.81,
                    top_offset=240,
                ),
            ],
        ),
    },
    {
        "question": "what were the empirical results on low-contrast scanned documents",
        "response": QuestionResponse(
            found=True,
            answer=(
                "When evaluated on scanned document test sets where pages 18 through "
                "20 underwent optical character recognition (OCR), character error "
                "rates fell from 14.2% to 3.8% after applying layout-aware correction. "
                "Tabular structures preserved multi-column cells accurately."
            ),
            sources=[
                QuestionSource(
                    page_number=18,
                    chunk_id="chk-18-04",
                    snippet=(
                        "\u201cOCR degradation benchmarks: table extraction F1 score "
                        "increased to 0.912 when OCR bounding boxes were fused prior "
                        "to attention projection.\u201d"
                    ),
                    score=0.79,
                    top_offset=160,
                ),
                QuestionSource(
                    page_number=19,
                    chunk_id="chk-19-02",
                    snippet=(
                        "\u201cAppendix B: OCR confusion matrix and synthetic "
                        "degradation parameters for scanned ledger facsimiles.\u201d"
                    ),
                    score=0.74,
                    top_offset=210,
                ),
            ],
        ),
    },
    {
        "question": "what loss formulation weights multi-scale reading order",
        "response": QuestionResponse(
            found=True,
            answer=(
                "The training objective combines a standard cross-entropy layout "
                "classification loss with a secondary reading-order consistency term. "
                "The multi-scale term penalises inversions in predicted token sequence "
                "across pyramid levels using a margin-based ranking loss weighted at "
                "\u03bb\u2082 = 0.35."
            ),
            sources=[
                QuestionSource(
                    page_number=6,
                    chunk_id="chk-6-03",
                    snippet=(
                        "\u201cThe reading-order ranking loss \u2113\u1d2c\u1d52 is "
                        "applied at all FPN levels and weighted by the inverse "
                        "pyramid scale factor.\u201d"
                    ),
                    score=0.83,
                    top_offset=180,
                ),
                QuestionSource(
                    page_number=12,
                    chunk_id="chk-12-01",
                    snippet=(
                        "\u201cAblation Table 3 confirms that removing the "
                        "multi-scale reading loss degrades order accuracy by 9.1 "
                        "percentage points on the DocBank-L benchmark.\u201d"
                    ),
                    score=0.77,
                    top_offset=90,
                ),
            ],
        ),
    },
    {
        "question": "does the architecture support rtl or vertical cjk typography",
        "response": QuestionResponse(
            found=True,
            answer=(
                "Yes. The model includes a bidirectional reading-order head that "
                "explicitly handles right-to-left (RTL) and vertical CJK scripts. "
                "The spatial bias matrices are rotated 90\u00b0 for vertical text "
                "blocks detected via the script-classification branch."
            ),
            sources=[
                QuestionSource(
                    page_number=2,
                    chunk_id="chk-2-05",
                    snippet=(
                        "\u201cSupport for RTL and vertical CJK is provided through "
                        "a dedicated script-direction head trained on the M-SHOT "
                        "multilingual document corpus.\u201d"
                    ),
                    score=0.85,
                    top_offset=300,
                ),
            ],
        ),
    },
]

# ---------------------------------------------------------------------------
# Public lookup function
# ---------------------------------------------------------------------------

_FALLBACK = QuestionResponse(
    found=False,
    answer="",
    sources=[],
)


def lookup_answer(question: str) -> QuestionResponse:
    """
    Return the pre-written answer for a recognised question, or a
    not-found response for anything else.
    """
    normalised = question.strip().lower().rstrip("?.")

    for entry in _KNOWN_QA:
        if entry["question"] in normalised or normalised in entry["question"]:
            return entry["response"]

    return _FALLBACK
