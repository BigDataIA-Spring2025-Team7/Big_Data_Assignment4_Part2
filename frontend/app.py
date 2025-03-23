import streamlit as st
import requests

# Backend FastAPI URL (update if running remotely)
FASTAPI_URL = "http://backend:8000"

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["🏠 Landing Page", "📄 PDF Extraction"])

# --- LANDING PAGE ---
if page == "🏠 Landing Page":
    st.title("AI-Powered NVIDIA Report Extraction")
    st.write(
        """
        This application extracts **financial reports** from NVIDIA's investor portal 
        and allows users to **select and download** them from AWS S3. 
        
        🔹 **Features**
        - Scrape reports using Selenium.
        - Store extracted PDFs in **AWS S3**.
        - Retrieve PDFs dynamically via **FastAPI**.
        - Interactive **Streamlit UI** for selection and download.
        """
    )

# 📄 PDF EXTRACTION PAGE
elif page == "📄 PDF Extraction":
    st.title("📄 NVIDIA Financial Reports")
    
    # Get available years from FastAPI
    response = requests.get(f"{FASTAPI_URL}/get_available_years")
    if response.status_code == 200:
        years = response.json().get("years", [])
    else:
        st.error("Failed to load years.")
        years = []

    # User selects year
    selected_year = st.selectbox("Select Year", years)

    if selected_year:
        # Get available quarters for the selected year
        response = requests.get(f"{FASTAPI_URL}/get_available_quarters/{selected_year}")
        if response.status_code == 200:
            quarters = response.json().get("quarters", [])
        else:
            st.error("Failed to load quarters.")
            quarters = []

        # User selects quarter
        selected_quarter = st.selectbox("Select Quarter", quarters)

        if selected_quarter:
            # Fetch PDF URL from FastAPI
            response = requests.get(f"{FASTAPI_URL}/get_pdf_url/{selected_year}/{selected_quarter}")
            if response.status_code == 200:
                pdf_url = response.json().get("pdf_url", None)

                if pdf_url:
                    st.success(f"✅ Report Found: {selected_year} - {selected_quarter}")
                    st.markdown(f"[📥 Download PDF]({pdf_url})", unsafe_allow_html=True)

                    parser_choice = st.selectbox("Select Parser", ["Docling", "Mistral"])

                    # ➕ PROCESS PDF BUTTON
                    if st.button("⚙️ Process PDF"):
                        if parser_choice == "Docling":
                            process_response = requests.post(f"{FASTAPI_URL}/trigger_docling_dag/{selected_year}/{selected_quarter}")
                        else:
                            process_response = requests.post(f"{FASTAPI_URL}/process_pdf_mistral/{selected_year}/{selected_quarter}")

                        if process_response.status_code == 200:
                            st.success(f"✅ PDF successfully parsed using {parser_choice} and uploaded to S3!")
                            if parser_choice == "Docling":
                                run_id = process_response.json().get("run_id", "N/A")
                                st.markdown(f"Airflow DAG Run ID: `{run_id}`")
                            else:
                                st.markdown("You can now access the converted Markdown and images.")
                            
                        else:
                            st.error(f"❌ Failed to process with {parser_choice}.")
                else:
                    st.warning("No PDF found for the selected quarter.")
            else:
                st.error("Error fetching PDF URL.")

