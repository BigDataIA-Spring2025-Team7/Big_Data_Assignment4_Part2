# **Assignment 4.2**: **Building a RAG Pipeline with  Airflow**

**Vemana Anil Kumar**  
**Ashwin Badamikar**  
**Madhura Sunil Adadande**

# INTRODUCTION

In this project, we aimed to automate and scale our document analysis pipeline using Apache Airflow, while improving its flexibility through multi-parser support and advanced retrieval options. Building on top of our previous assignment, we implemented a complete Retrieval-Augmented Generation (RAG) system that supports real-time question answering on quarterly reports using LLMs.

Our solution integrates Airflow for orchestration, Docling and Mistral OCR for parsing, and supports three chunking strategies and multiple retrieval options (manual, Pinecone, ChromaDB). We also developed a Streamlit frontend and a FastAPI backend, all containerized using Docker and deployed on DigitaL Ocean for production readiness. This modular setup ensures reusability, low latency, and intelligent document interaction.

Technologies:

1. **Pipeline Orchestration**: Apache Airflow

2. **PDF Scraping**: Selenium

3. **PDF Parsing**: PyMuPDF, Docling, Mistral OCR

4. **Chunking**: Overlap-based, sentence-based, token-length

5. **Embeddings**: OpenAI

6. **RAG Methods**: Manual cosine similarity, Pinecone, ChromaDB

7. **LLMs**: OpenAI GPT-4o, Claude

8. **Backend**: FastAPI

9. **Frontend**: Streamlit

10. **Storage**: AWS S3

11. **Containerization**: Docker \+ Docker Compose

12. **Deployment**: Digital Ocean

# PROBLEM STATEMENT

Manually navigating and analyzing large PDF documents like NVIDIA’s quarterly reports is time-consuming and inefficient. Traditional solutions lack context-awareness and real-time interactivity. The challenge was to build a modular, scalable pipeline that not only automates PDF scraping and processing but also enables intelligent querying using advanced LLMs. The system must support multiple parsing techniques, chunking strategies, and retrieval backends to offer maximum flexibility and performance.

# PROOF OF CONCEPT

Our solution consists of the following components, structured to function as an end-to-end RAG pipeline:

**1. Document Ingestion & Parsing (Airflow DAG)**

* Scrapes NVIDIA quarterly reports using Selenium.

* Uses either PyMuPDF, Docling, or Mistral OCR to parse PDF content.

* Parsed content is converted into structured markdown format and saved locally or to S3.

**2\. Chunking & Embedding (Airflow)**

* Markdown content is split using one of three strategies:

  * Heading

  * Semantic

  * Recursive

* OpenAI Embeddings are generated

**3\. Retrieval Storage**

* Embeddings are stored using:

  * Manual vectors for cosine similarity

  * Pinecone

  * ChromaDB  
    

**4\. RAG Interaction Layer**

* Users interact via Streamlit UI to upload PDFs or select parsed markdowns.

* Choose preferred parser, chunking strategy, and vector storage.

* Queries are routed through FastAPI to the appropriate retrieval module.

* Top-k relevant chunks are passed to selected LLM (via LiteLLM) for response.

**5\. Deployment**

* All components are containerized using Docker and run via docker-compose.

* The app is deployed on a Digital Ocean Droplet and publicly accessible.

**CHALLENGES AND OPTIMIZATIONS**

1\. Parsing inconsistencies across reports

Some NVIDIA reports were clean text-based, while others were scanned or had tables embedded in strange formats. Mistral OCR often gave broken outputs for scanned files. To handle this, we gave users the option to switch between PyMuPDF, Docling, and Mistral OCR so they could pick the most accurate parser based on the document.

2\. Token overload in LLM queries

In some cases, too many chunks were sent to the LLM, resulting in high token usage and cost. We optimized the backend to limit the number of chunks sent (top-k filtering based on similarity score) and experimented with chunk sizes to find a balance between context and efficiency.

3\. Dimension mismatch in Pinecone embeddings

When we first integrated Pinecone, we encountered errors due to mismatched vector dimensions. This was resolved by switching to OpenAI’s text-embedding-3-small model, which produces 1536-dim vectors that are compatible with Pinecone’s default setup.

4\. Slow retrieval on large datasets

Retrieval performance degraded when querying across all documents. To fix this, we introduced quarter-based filtering, allowing users to restrict the context to specific quarterly reports. This significantly reduced retrieval time and improved result relevance.

# ARCHITECTURE DIAGRAM:

![Assignment4_Part2](https://github.com/user-attachments/assets/3e0b0cd9-f473-4609-8e1d-ab0f4cfdad52)


# WALKTHROUGH OF THE APPLICATION

**Frontend**: http://198.211.105.31:8501/

* Upload your PDF or choose a pre-parsed markdown

* Select your parser and chunking strategy

* Choose your RAG pipeline: manual / Pinecone / ChromaDB

* Pick the quarter(s) of interest

* Ask your question and view answer

**Backend API (FastAPI)**: http://198.211.105.31:8000/docs

* Try endpoints for parsing, chunking, answering questions

* Easily test RAG logic with Swagger UI

airflow: http://198.211.105.31:8082

**Codelabs Link** : https://codelabs-preview.appspot.com/?file_id=1BpU-AyUBABAziM_lYuxOj-JaInIaaq86dNB_8TkBjqg#0

# APPLICATION WORKFLOW 

1. **User Uploads Selects Year and Quarter**  
   The frontend allows the user to select year and quarter

2. **Select PDF Parser**  
   The user chooses between PyMuPDF, Docling, or Mistral OCR depending on the quality and type of the PDF.

3. **Parse the Document**  
   The selected parser extracts text from the PDF and converts it into markdown format.

4. **Choose Chunking Strategy**  
   The markdown text is split into chunks using one of the three strategies:  
   \* Heading 
   \* Semantic
   \* Recursive

5. **Generate Embeddings**  
   Each chunk is embedded using OpenAI’s embedding model

6. **Select RAG Method**  
   The user picks a retrieval strategy:  
   \* Manual cosine similarity (no DB)  
   \* Pinecone  
   \* ChromaDB

8. **Ask a Question / Request a Summary**  
   The user submits a query through the Streamlit UI.

9. **Retrieve Relevant Chunks**  
   Based on the selected retrieval method, the backend fetches the top relevant chunks.

10. **Send Chunks to LLM (via LiteLLM)**  
    The retrieved chunks and question are sent to the selected LLM (GPT-4o, Claude)

# DIRECTORY STRUCTURE
```
Big\_Data\_Assignment4\_Part2-main/  
├── .gitignore  
├── README.md  
├── docker-compose.yaml  
├── requirements.txt  
├── selenium\_scrape.py  
│  
├── airflow/  
│   ├── Dockerfile  
│   ├── docker-compose.yaml  
│   ├── requirements.txt  
│   └── dags/  
│       └── dag\_main\_rag\_pipeline.py  
│  
├── backend/  
│   ├── Dockerfile  
│   ├── main.py  
│   ├── requirements.txt  
│   └── chromadb\_store/  
│       ├── chroma.sqlite3  
│       ├── chromadb\_chunks\_export.xlsx  
│       ├── test.py  
│       └── \[UUID folders with ChromaDB binary files\]  
│  
├── chunking/  
│   ├── Q1 (1).md  
│   ├── \_\_init\_\_.py  
│   └── chunks.py  
│  
├── docling\_service/  
│   ├── Dockerfile  
│   ├── docling\_extract.py  
│   ├── main.py  
│   └── requirements.txt  
│  
├── embedding/  
│   ├── chromadb.py  
│   ├── manual.py  
│   └── pinecone.py  
│  
├── frontend/  
│   ├── Dockerfile  
│   ├── app.py  
│   ├── requirements.txt  
│   └── .streamlit/  
│       └── config.toml  
│  
├── pdf\_processing/  
│   ├── \_\_init\_\_.py  
│   ├── mistral.py  
│   ├── test\_docling.py  
│   └── test\_mistral.py
```

# REFERENCES

Apache Airflow Docs  
Official Documentation: http://airflow.apache.org/docs/

Streamlit  
 Official Documentation: [https://docs.streamlit.io/](https://docs.streamlit.io/)

FastAPI  
 Official Documentation: [https://fastapi.tiangolo.com/](https://fastapi.tiangolo.com/)  
 Request Handling & Pydantic Models: https://fastapi.tiangolo.com/tutorial/body/

LiteLLM  
 LiteLLM GitHub: [https://github.com/BerriAI/litellm](https://github.com/BerriAI/litellm)  
 Documentation: https://docs.litellm.ai/

OpenAI Embeddings  
 https://platform.openai.com/docs/guides/embeddings

Pinecone – Cloud Vector Database  
https://docs.pinecone.io/

ChromaDB – Local Vector Store  
[https://docs.trychroma.com/](https://docs.trychroma.com/)

Docling – Structured PDF Parsing  
[https://github.com/docling/docling](https://github.com/docling/docling)

Mistral OCR – OCR for scanned PDFs  
[https://mistral.ai/news/mistral-ocr](https://mistral.ai/news/mistral-ocr)

AWS S3 – Object Storage for PDF/Markdown files  
[https://docs.aws.amazon.com/s3/](https://docs.aws.amazon.com/s3/)

Docker – Containerization Tool  
https://docs.docker.com/

# DISCLOSURES

WE ATTEST THAT WE HAVEN’T USED ANY OTHER STUDENTS’ WORK IN OUR ASSIGNMENT AND ABIDE BY THE POLICIES LISTED IN THE STUDENT HANDBOOK

**AI USAGE DISCLOSURE**  
For this project, we used AI tools like ChatGPT, DeepSeek, and Claude to enhance various aspects of development debugging code, optimizing SQL queries, and generating explanations for complex concepts. These tools were leveraged to improve clarity, efficiency, and accuracy in our work, but all final decisions, implementations, and analyses were conducted by us.

Contributions
Vemana Anil Kumar - 50%<br>
Ashwin Badamikar - 20%<br>
Madhura Adadande - 30%<br>
WE ATTEST THAT WE HAVEN’T USED ANY OTHER STUDENTS’ WORK IN OUR ASSIGNMENT AND ABIDE BY THE POLICIES LISTED IN THE STUDENT HANDBOOK
