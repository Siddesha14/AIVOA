import os
from dotenv import load_dotenv
load_dotenv("../.env")
from langchain_groq import ChatGroq
from schemas import InvestigationSummary

llm = ChatGroq(model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"), temperature=0.1)
structured = llm.with_structured_output(InvestigationSummary)

text = ("Assay result for Metformin HCl API batch MFH260712A came out at 94.1% after drying "
        "in dryer DRY-03. A temperature excursion was logged. Batch quarantined.")

result = structured.invoke(
    "Extract investigation details. Use only facts in the text; unknown => null.\n\n" + text)
print(result.model_dump_json(indent=2))