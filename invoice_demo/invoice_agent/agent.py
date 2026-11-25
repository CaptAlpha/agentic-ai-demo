import os
from pypdf import PdfReader
from google.adk.agents import Agent

def read_pdf(file_path: str) -> dict:
    """Extracts all text from a local PDF file.

    Args:
        file_path: The relative or absolute path to the PDF file.
    """
    if not os.path.exists(file_path):
        return {"status": "error", "message": f"File not found: {file_path}"}

    try:
        reader = PdfReader(file_path)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        return {
            "status": "success",
            "page_count": len(reader.pages),
            "content": text.strip(),
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def calculate_stats(numbers: list[float]) -> dict:
    """Calculates sum, average, min, and max for a list of numbers.

    Args:
        numbers: A list of numeric values extracted from the document.
    """
    if not numbers:
        return {"status": "error", "message": "No numbers provided."}

    return {
        "status": "success",
        "count": len(numbers),
        "total": round(sum(numbers), 2),
        "average": round(sum(numbers) / len(numbers), 2),
        "min": min(numbers),
        "max": max(numbers),
    }


root_agent = Agent(
    name="pdf_analyst_agent",
    model="gemini-3.5-flash",
    description="Reads local PDF files and performs calculations or analysis on their contents.",
    instruction="""
        When the user provides a PDF file path:
        1. Call read_pdf to extract the text.
        2. Identify the relevant data or numbers requested by the user.
        3. If calculations are needed, pass the extracted numbers to calculate_stats.
        4. Present a clear summary of the results.
    """,
    tools=[read_pdf, calculate_stats],
)