from graph import graph
from schemas import FormState


form = FormState().model_dump()
form["summary"].update(
    {
        "product_name": "Metformin HCl API",
        "batch_number": "MFH260712A",
        "process_step": "drying",
        "equipment_id": "DRY-03",
        "problem_statement": "Assay was 94.1% after drying.",
    }
)

confirmed_cause = {
    "id": "human-1",
    "text": "Confirmed cause from QA review.",
    "category": "Machine",
    "is_probable_root": True,
    "confidence": "high",
    "source_quote": "QA confirmed this cause.",
    "status": "confirmed",
}
form["analysis"]["causes"] = [confirmed_cause]

result = graph.invoke(
    {
        "message": "Please update the affected quantity to 50 kg.",
        "document_text": "",
        "form": form,
        "changed": [],
    }
)

causes_after = result["form"]["analysis"]["causes"]
preserved_cause = next(
    (cause for cause in causes_after if cause["id"] == "human-1"),
    None,
)

print("Confirmed cause preserved exactly:", preserved_cause == confirmed_cause)
print("Preserved cause status:", preserved_cause["status"] if preserved_cause else None)
print("Updated quantity:", result["form"]["summary"]["affected_quantity"])