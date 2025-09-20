import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any
import json

# Configuration
API_BASE_URL = "https://patient-management-system-api-fastapi.onrender.com"  # Change this to your FastAPI server URL

# Page configuration
st.set_page_config(
    page_title="Patient Management System",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .metric-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    
    .success-message {
        padding: 1rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        color: #155724;
        margin: 1rem 0;
    }
    
    .error-message {
        padding: 1rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        color: #721c24;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def make_api_request(endpoint: str, method: str = "GET", data: Dict[Any, Any] = None, params: Dict[str, Any] = None) -> Dict[Any, Any]:
    """Make API request with error handling"""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        
        if method == "GET":
            response = requests.get(url, params=params)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "PUT":
            response = requests.put(url, json=data)
        elif method == "DELETE":
            response = requests.delete(url)
        
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        elif response.status_code == 201:
            return {"success": True, "data": response.json()}
        else:
            return {"success": False, "error": response.json().get("detail", "Unknown error")}
    
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Cannot connect to API server. Make sure FastAPI is running."}
    except Exception as e:
        return {"success": False, "error": str(e)}

def display_patient_card(patient_data: Dict[str, Any], patient_id: str):
    """Display patient information in a card format"""
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        st.markdown(f"**Patient ID:** {patient_id}")
        st.markdown(f"**Name:** {patient_data.get('name', 'N/A')}")
        st.markdown(f"**City:** {patient_data.get('city', 'N/A')}")
        st.markdown(f"**Age:** {patient_data.get('age', 'N/A')}")
        st.markdown(f"**Gender:** {patient_data.get('gender', 'N/A')}")
    
    with col2:
        st.markdown(f"**Height:** {patient_data.get('height', 'N/A')} m")
        st.markdown(f"**Weight:** {patient_data.get('weight', 'N/A')} kg")
        if 'bmi' in patient_data:
            st.markdown(f"**BMI:** {patient_data['bmi']}")
        if 'verdict' in patient_data:
            verdict = patient_data['verdict']
            if verdict == "Normal":
                st.markdown(f"**Status:** :green[{verdict}]")
            elif verdict in ["Underweight", "Overweight"]:
                st.markdown(f"**Status:** :orange[{verdict}]")
            else:
                st.markdown(f"**Status:** :red[{verdict}]")
    
    with col3:
        if st.button(f"Edit {patient_id}", key=f"edit_{patient_id}"):
            st.session_state.edit_patient_id = patient_id
            st.session_state.page = "Edit Patient"
            st.rerun()
        
        if st.button(f"Delete {patient_id}", key=f"delete_{patient_id}", type="secondary"):
            if st.session_state.get(f"confirm_delete_{patient_id}", False):
                # Perform deletion
                result = make_api_request(f"/delete/{patient_id}", method="DELETE")
                if result["success"]:
                    st.success("Patient deleted successfully!")
                    st.session_state[f"confirm_delete_{patient_id}"] = False
                    st.rerun()
                else:
                    st.error(f"Error: {result['error']}")
            else:
                st.session_state[f"confirm_delete_{patient_id}"] = True
                st.rerun()
        
        if st.session_state.get(f"confirm_delete_{patient_id}", False):
            st.warning("Click Delete again to confirm")

def main():
    # Initialize session state
    if 'page' not in st.session_state:
        st.session_state.page = "Dashboard"
    
    # Header
    st.markdown('<h1 class="main-header">🏥 Patient Management System</h1>', unsafe_allow_html=True)
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    
    # Check API connection
    api_status = make_api_request("/")
    if api_status["success"]:
        st.sidebar.success("✅ API Connected")
    else:
        st.sidebar.error("❌ API Disconnected")
        st.error("Cannot connect to the API. Please make sure your FastAPI server is running on http://localhost:8000")
        st.stop()
    
    # Navigation buttons
    pages = ["Dashboard", "View All Patients", "Add Patient", "Search Patient", "Analytics"]
    
    for page in pages:
        if st.sidebar.button(page, key=f"nav_{page}"):
            st.session_state.page = page
    
    # Handle edit patient page
    if st.session_state.page == "Edit Patient":
        edit_patient_page()
    elif st.session_state.page == "Dashboard":
        dashboard_page()
    elif st.session_state.page == "View All Patients":
        view_all_patients_page()
    elif st.session_state.page == "Add Patient":
        add_patient_page()
    elif st.session_state.page == "Search Patient":
        search_patient_page()
    elif st.session_state.page == "Analytics":
        analytics_page()

def dashboard_page():
    st.header("📊 Dashboard")
    
    # Get all patients data
    result = make_api_request("/view")
    if not result["success"]:
        st.error(f"Error loading data: {result['error']}")
        return
    
    patients_data = result["data"]
    
    if not patients_data:
        st.info("No patients in the system yet. Add some patients to see statistics.")
        return
    
    # Calculate statistics
    total_patients = len(patients_data)
    
    # Convert to DataFrame for easier analysis
    df_list = []
    for patient_id, data in patients_data.items():
        data['id'] = patient_id
        df_list.append(data)
    
    df = pd.DataFrame(df_list)
    
    # Display key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Patients", total_patients)
    
    with col2:
        if 'age' in df.columns:
            avg_age = round(df['age'].mean(), 1)
            st.metric("Average Age", f"{avg_age} years")
    
    with col3:
        if 'bmi' in df.columns:
            avg_bmi = round(df['bmi'].mean(), 1)
            st.metric("Average BMI", avg_bmi)
    
    with col4:
        if 'verdict' in df.columns:
            normal_count = len(df[df['verdict'] == 'Normal'])
            st.metric("Normal BMI", f"{normal_count}/{total_patients}")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        if 'gender' in df.columns:
            st.subheader("Gender Distribution")
            gender_counts = df['gender'].value_counts()
            fig_gender = px.pie(values=gender_counts.values, names=gender_counts.index, 
                              title="Patient Gender Distribution")
            st.plotly_chart(fig_gender, use_container_width=True)
    
    with col2:
        if 'verdict' in df.columns:
            st.subheader("BMI Categories")
            verdict_counts = df['verdict'].value_counts()
            colors = {'Normal': 'green', 'Underweight': 'orange', 
                     'Overweight': 'orange', 'Obese': 'red'}
            fig_bmi = px.bar(x=verdict_counts.index, y=verdict_counts.values,
                            title="BMI Category Distribution",
                            color=verdict_counts.index,
                            color_discrete_map=colors)
            st.plotly_chart(fig_bmi, use_container_width=True)
    
    # Recent patients
    st.subheader("All Patients Overview")
    for patient_id, patient_data in list(patients_data.items())[:5]:  # Show first 5
        with st.expander(f"Patient {patient_id} - {patient_data.get('name', 'Unknown')}"):
            display_patient_card(patient_data, patient_id)

def view_all_patients_page():
    st.header("👥 All Patients")
    
    # Sorting options
    col1, col2 = st.columns([2, 1])
    
    with col1:
        sort_by = st.selectbox("Sort by:", ["name", "age", "bmi", "height", "weight"])
    
    with col2:
        sort_order = st.selectbox("Order:", ["asc", "desc"])
    
    if st.button("Apply Sorting"):
        # Get sorted data from API
        params = {"sort_by": sort_by, "order": sort_order}
        result = make_api_request("/sort", params=params)
        
        if result["success"]:
            sorted_patients = result["data"]
            st.success(f"Patients sorted by {sort_by} in {sort_order} order")
            
            for i, patient_data in enumerate(sorted_patients):
                # Need to find patient ID (this is a limitation of the current API)
                st.subheader(f"Patient {i+1}")
                col1, col2 = st.columns([3, 1])
                with col1:
                    for key, value in patient_data.items():
                        st.write(f"**{key.title()}:** {value}")
                st.divider()
        else:
            st.error(f"Error: {result['error']}")
    else:
        # Show all patients without sorting
        result = make_api_request("/view")
        if result["success"]:
            patients_data = result["data"]
            
            if not patients_data:
                st.info("No patients found in the system.")
                return
            
            for patient_id, patient_data in patients_data.items():
                with st.expander(f"Patient {patient_id} - {patient_data.get('name', 'Unknown')}"):
                    display_patient_card(patient_data, patient_id)
        else:
            st.error(f"Error: {result['error']}")

def add_patient_page():
    st.header("➕ Add New Patient")
    
    with st.form("add_patient_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            patient_id = st.text_input("Patient ID*", placeholder="P001", help="Unique identifier for the patient")
            name = st.text_input("Name*", placeholder="John Doe")
            city = st.text_input("City*", placeholder="New York")
            age = st.number_input("Age*", min_value=0, max_value=120, value=25)
        
        with col2:
            gender = st.selectbox("Gender*", ["male", "female", "Other"])
            height = st.number_input("Height (meters)*", min_value=0.0, max_value=3.0, value=1.7, step=0.01)
            weight = st.number_input("Weight (kg)*", min_value=0.0, max_value=500.0, value=70.0, step=0.1)
        
        submitted = st.form_submit_button("Add Patient", type="primary")
        
        if submitted:
            if not all([patient_id, name, city, age, height, weight]):
                st.error("Please fill in all required fields marked with *")
            else:
                patient_data = {
                    "id": patient_id,
                    "name": name,
                    "city": city,
                    "age": age,
                    "gender": gender,
                    "height": height,
                    "weight": weight
                }
                
                result = make_api_request("/create", method="POST", data=patient_data)
                
                if result["success"]:
                    st.success("Patient added successfully! 🎉")
                    # Calculate and show BMI
                    bmi = round(weight / (height ** 2), 2)
                    if bmi < 18.5:
                        verdict = "Underweight"
                    elif 18.5 <= bmi < 30:
                        verdict = "Normal"
                    else:
                        verdict = "Overweight"
                    
                    st.info(f"Calculated BMI: {bmi} ({verdict})")
                else:
                    st.error(f"Error: {result['error']}")

def search_patient_page():
    st.header("🔍 Search Patient")
    
    patient_id = st.text_input("Enter Patient ID", placeholder="P001")
    
    if st.button("Search", type="primary") and patient_id:
        result = make_api_request(f"/patient/{patient_id}")
        
        if result["success"]:
            patient_data = result["data"]
            st.success("Patient found!")
            
            # Display patient information
            display_patient_card(patient_data, patient_id)
            
        else:
            st.error(f"Error: {result['error']}")
    
    elif patient_id == "":
        st.info("Enter a Patient ID to search")

def edit_patient_page():
    st.header("✏️ Edit Patient")
    
    if 'edit_patient_id' not in st.session_state:
        st.error("No patient selected for editing")
        if st.button("Back to Dashboard"):
            st.session_state.page = "Dashboard"
            st.rerun()
        return
    
    patient_id = st.session_state.edit_patient_id
    
    # Get current patient data
    result = make_api_request(f"/patient/{patient_id}")
    
    if not result["success"]:
        st.error(f"Error loading patient data: {result['error']}")
        return
    
    current_data = result["data"]
    
    st.info(f"Editing Patient: {patient_id}")
    
    with st.form("edit_patient_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Name", value=current_data.get('name', ''))
            city = st.text_input("City", value=current_data.get('city', ''))
            age = st.number_input("Age", min_value=0, max_value=120, value=current_data.get('age', 25))
        
        with col2:
            gender = st.selectbox("Gender", ["male", "female", "Other"], 
                                index=["male", "female", "Other"].index(current_data.get('gender', 'male')))
            height = st.number_input("Height (meters)", min_value=0.0, max_value=3.0, 
                                   value=current_data.get('height', 1.7), step=0.01)
            weight = st.number_input("Weight (kg)", min_value=0.0, max_value=500.0, 
                                   value=current_data.get('weight', 70.0), step=0.1)
        
        col1, col2 = st.columns(2)
        
        with col1:
            submitted = st.form_submit_button("Update Patient", type="primary")
        
        with col2:
            cancelled = st.form_submit_button("Cancel")
        
        if cancelled:
            st.session_state.page = "Dashboard"
            if 'edit_patient_id' in st.session_state:
                del st.session_state.edit_patient_id
            st.rerun()
        
        if submitted:
            update_data = {}
            
            # Only include changed fields
            if name != current_data.get('name', ''):
                update_data['name'] = name
            if city != current_data.get('city', ''):
                update_data['city'] = city
            if age != current_data.get('age', 0):
                update_data['age'] = age
            if gender != current_data.get('gender', ''):
                update_data['gender'] = gender
            if height != current_data.get('height', 0):
                update_data['height'] = height
            if weight != current_data.get('weight', 0):
                update_data['weight'] = weight
            
            if not update_data:
                st.info("No changes detected.")
            else:
                result = make_api_request(f"/edit/{patient_id}", method="PUT", data=update_data)
                
                if result["success"]:
                    st.success("Patient updated successfully! 🎉")
                    st.session_state.page = "Dashboard"
                    if 'edit_patient_id' in st.session_state:
                        del st.session_state.edit_patient_id
                    st.rerun()
                else:
                    st.error(f"Error: {result['error']}")

def analytics_page():
    st.header("📈 Analytics")
    
    result = make_api_request("/view")
    if not result["success"]:
        st.error(f"Error loading data: {result['error']}")
        return
    
    patients_data = result["data"]
    
    if not patients_data:
        st.info("No data available for analytics.")
        return
    
    # Convert to DataFrame
    df_list = []
    for patient_id, data in patients_data.items():
        data['id'] = patient_id
        df_list.append(data)
    
    df = pd.DataFrame(df_list)
    
    # Age distribution
    if 'age' in df.columns:
        st.subheader("Age Distribution")
        fig_age = px.histogram(df, x='age', nbins=10, title="Age Distribution of Patients")
        st.plotly_chart(fig_age, use_container_width=True)
    
    # BMI vs Age scatter plot
    if 'age' in df.columns and 'bmi' in df.columns:
        st.subheader("BMI vs Age Analysis")
        fig_scatter = px.scatter(df, x='age', y='bmi', color='gender', 
                               title="BMI vs Age by Gender",
                               hover_data=['name', 'verdict'])
        st.plotly_chart(fig_scatter, use_container_width=True)
    
    # City distribution
    if 'city' in df.columns:
        st.subheader("Patients by City")
        city_counts = df['city'].value_counts().head(10)
        fig_city = px.bar(x=city_counts.index, y=city_counts.values,
                         title="Top 10 Cities by Patient Count")
        st.plotly_chart(fig_city, use_container_width=True)
    
    # Summary statistics
    st.subheader("Summary Statistics")
    
    numeric_columns = ['age', 'height', 'weight', 'bmi']
    available_columns = [col for col in numeric_columns if col in df.columns]
    
    if available_columns:
        st.dataframe(df[available_columns].describe())

if __name__ == "__main__":
    main()