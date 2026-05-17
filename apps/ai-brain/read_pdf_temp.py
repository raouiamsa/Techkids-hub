import sys
try:
    from langchain_community.document_loaders import PyPDFLoader
    loader = PyPDFLoader(r'C:\Users\raoui\OneDrive\Bureau\TechKids\pfe (5).pdf')
    docs = loader.load()
    for d in docs:
        print("---PAGE---")
        print(d.page_content)
except Exception as e:
    print("Error:", e)
