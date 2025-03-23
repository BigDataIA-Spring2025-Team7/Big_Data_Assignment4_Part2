import streamlit as st
import requests

# FastAPI endpoint
FASTAPI_URL = "http://localhost:8000"

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["🏠 Landing Page", "📄 PDF Extraction"])

# --- LANDING PAGE ---
if page == "🏠 Landing Page":
    st.title("AI-Powered NVIDIA Report Extraction")
    st.write("""
        This application extracts **financial reports** from NVIDIA's investor portal
        and allows users to **select and download** them from AWS S3.

        🔹 **Features**
        - Scrape reports using Selenium.
        - Store extracted PDFs in **AWS S3**.
        - Retrieve PDFs dynamically via **FastAPI**.
        - Interactive **Streamlit UI** for selection and download.
    """)

# --- PDF EXTRACTION PAGE ---
elif page == "📄 PDF Extraction":
    st.title("📄 NVIDIA Financial Reports")

    if "processed" not in st.session_state:
        st.session_state.processed = False
    if "chunked" not in st.session_state:
        st.session_state.chunked = False
    if "vector_store" not in st.session_state:
        st.session_state.vector_store = None

    response = requests.get(f"{FASTAPI_URL}/get_available_years")
    years = response.json().get("years", []) if response.status_code == 200 else []
    selected_year = st.selectbox("Select Year", years)

    if selected_year:
        response = requests.get(f"{FASTAPI_URL}/get_available_quarters/{selected_year}")
        quarters = response.json().get("quarters", []) if response.status_code == 200 else []
        selected_quarter = st.selectbox("Select Quarter", quarters)

        if selected_quarter:
            response = requests.get(f"{FASTAPI_URL}/get_pdf_url/{selected_year}/{selected_quarter}")
            pdf_url = response.json().get("pdf_url", None) if response.status_code == 200 else None

            if pdf_url:
                st.success(f"✅ Report Found: {selected_year} - {selected_quarter}")
                st.markdown(f"[📥 Download PDF]({pdf_url})", unsafe_allow_html=True)

                parser_choice = st.selectbox("Select Parser", ["Docling", "Mistral"])

                if st.button("⚙️ Process PDF"):
                    if parser_choice == "Docling":
                        process_response = requests.post(f"{FASTAPI_URL}/process_pdf_docling/{selected_year}/{selected_quarter}")
                    else:
                        process_response = requests.post(f"{FASTAPI_URL}/process_pdf_mistral/{selected_year}/{selected_quarter}")

                    if process_response.status_code == 200:
                        st.success(f"✅ PDF successfully parsed using {parser_choice} and uploaded to S3!")
                        st.session_state.processed = True
                        st.session_state.parser_choice = parser_choice
                    else:
                        st.error(f"❌ Failed to process with {parser_choice}")

            if st.session_state.processed:
                st.markdown("🧩 You can now run chunking on the markdown file below.")
                strategy = st.selectbox("Select Chunking Strategy", ["heading", "semantic", "recursive"])

                if st.button("🔪 Run Chunking"):
                    chunk_response = requests.post(
                        f"{FASTAPI_URL}/chunk_markdown",
                        json={
                            "year": selected_year,
                            "quarter": selected_quarter,
                            "parser": st.session_state.parser_choice.lower(),
                            "strategy": strategy
                        }
                    )
                    if chunk_response.status_code == 200:
                        chunks = chunk_response.json().get("chunks", [])
                        st.success(f"✅ Chunking complete! Total Chunks: {len(chunks)}")
                        st.session_state.chunked = True
                        st.session_state.strategy = strategy

                        with st.expander("📄 View All Chunks"):
                            for idx, chunk in enumerate(chunks, 1):
                                st.markdown(f"**Chunk {idx}:**\n\n```markdown\n{chunk}\n```")
                    else:
                        st.error("❌ Chunking failed.")

            if st.session_state.chunked:
                st.markdown("📦 Choose a vector database to upload the chunks:")
                vector_store = st.selectbox("Select Vector Store", ["Pinecone", "ChromaDB", "Manual"])
                st.session_state.vector_store = vector_store

                if st.button("🚀 Upload to Vector DB"):
                    if vector_store == "Pinecone":
                        upload_endpoint = "/upload_to_pinecone"
                    elif vector_store == "ChromaDB":
                        upload_endpoint = "/upload_to_chromadb"
                    else:
                        upload_endpoint = "/upload_to_manual"

                    upload_response = requests.post(
                        f"{FASTAPI_URL}{upload_endpoint}",
                        json={
                            "year": selected_year,
                            "quarter": selected_quarter,
                            "parser": st.session_state.parser_choice.lower(),
                            "strategy": st.session_state.strategy
                        }
                    )

                    if upload_response.status_code == 200:
                        res = upload_response.json()
                        st.success(f"✅ Uploaded {res['chunks_uploaded']} chunks to {vector_store} successfully!")
                    else:
                        st.error(f"❌ Failed to upload chunks to {vector_store}.")

            # Step 7: Ask Questions or Generate Summary
            if st.session_state.vector_store:
                st.markdown("🧠 Ask questions about the uploaded document:")
                user_query = st.text_input("Enter your question")

                if user_query and st.button("🔍 Ask LLM"):
                    if st.session_state.vector_store == "Pinecone":
                        query_route = "/query_pinecone"
                    elif st.session_state.vector_store == "ChromaDB":
                        query_route = "/query_chromadb"
                    else:
                        query_route = "/query_manual"

                    response = requests.post(
                        f"{FASTAPI_URL}{query_route}",
                        json={
                            "query": user_query,
                            "year": selected_year,
                            "quarter": selected_quarter,
                            "parser": st.session_state.parser_choice.lower(),
                            "strategy": st.session_state.strategy
                        }
                    )

                    if response.status_code == 200:
                        result = response.json()
                        st.success("💬 LLM Response:")
                        st.markdown(result["answer"])

                        with st.expander("📎 Context Chunks Used"):
                            for i, chunk in enumerate(result["sources"], 1):
                                st.markdown(f"**Chunk {i}:**\n\n```markdown\n{chunk}\n```")
                    else:
                        st.error("❌ Failed to get response from LLM.")

                # ✨ Summary Button
                st.markdown("📝 Or generate a summary of the entire document:")
                if st.button("🧾 Generate Summary"):
                    if st.session_state.vector_store == "Pinecone":
                        summary_route = "/generate_summary_pinecone"
                    elif st.session_state.vector_store == "ChromaDB":
                        summary_route = "/generate_summary_chromadb"
                    else:
                        summary_route = "/generate_summary_manual"

                    response = requests.post(
                        f"{FASTAPI_URL}{summary_route}",
                        json={
                            "year": selected_year,
                            "quarter": selected_quarter,
                            "parser": st.session_state.parser_choice.lower(),
                            "strategy": st.session_state.strategy
                        }
                    )

                    if response.status_code == 200:
                        summary = response.json().get("summary", "")
                        st.success("📘 Summary Generated:")
                        st.markdown(summary)
                    else:
                        st.error("❌ Failed to generate summary.")
