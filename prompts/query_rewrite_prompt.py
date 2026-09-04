from langchain_core.prompts import PromptTemplate

QUERY_REWRITE_PROMPT = PromptTemplate.from_template(
    """
The following question did not retrieve useful results from a document
search. Rewrite it as a single, different search query that is more likely to
find relevant passages - use different wording, synonyms, or a more specific
or more general phrasing than the original.

Return ONLY the rewritten query. No explanation, no quotes.

Original question:
{question}

Rewritten query:
"""
)
