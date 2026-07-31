from rag.loader import load_pdf
documents= load_pdf("uploads/Pushp_Goel_Bonafide.pdf")

print(f"Total Pages: {len(documents)}")

print("\nFirst Page:\n")
print(documents[0].page_content)

print("\nMetadata:\n")
print(documents[0].metadata)