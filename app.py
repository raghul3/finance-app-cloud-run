import streamlit as st
from streamlit_option_menu import option_menu
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud import secretmanager
import json

def get_secret(secret_name):
    client = secretmanager.SecretManagerServiceClient()
    project_id = 'prj-meg-dev-fin-01'
    secret_version = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
    response = client.access_secret_version(name=secret_version)
    return response.payload.data.decode('UTF-8')

# Retrieve the Firebase credentials from Secret Manager
firebase_credentials_json = get_secret("firebase-credentials")

# Parse the JSON string into a dictionary
firebase_credentials_dict = json.loads(firebase_credentials_json)

# Initialize Firebase if it hasn't been initialized yet
if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_credentials_dict)  # Pass the dictionary directly
    firebase_admin.initialize_app(cred)

# Initialize Firestore DB
db = firestore.client()

# App Configuration
st.set_page_config(page_title="Finance App", layout="wide")

# Categories Definition
categories = {
    "Assets": ["Equity", "Mutual Funds"],
    "Real Estate": ["Residential", "Yielding", "Commercial", "Non-Yielding"],
    "Debt": ["Bank RD", "FD", "PF", "Savings Account", "SSY", "Debt Funds", "PPF"],
    "Alternate Investments": ["Physical Gold", "Digital Gold", "P2P Lending"],
    "Liabilities": ["Home Loan", "Personal Loan"],
}

# Initialize session state keys for dynamic rows
for category, types in categories.items():
    for t in types:
        key = f"{category}_{t}_rows"
        st.session_state.setdefault(key, 1)

# Initialize Passive Income Assets
st.session_state.setdefault("Passive_Income_Assets_rows", 1)

# Function to add rows
def add_row(category, type_option=None):
    key = f"{category}_{type_option}_rows" if type_option else f"{category}_rows"
    st.session_state[key] += 1

# Function to remove rows
def remove_row(category, type_option=None):
    key = f"{category}_{type_option}_rows" if type_option else f"{category}_rows"
    if st.session_state[key] > 1:
        st.session_state[key] -= 1

# Styles for Option Menu
styles = {
    "container": {"background-color": "#F96167"},
    "nav-link": {"font-size": "20px", "color": "black", "font-weight": "bold"},
    "nav-link-selected": {"background-color": "#F9E795"},
    "icon": {"font-size": "20px"},
}

# Navigation Bar
selected = option_menu(
    menu_title="Finance App",
    options=["Home", "About", "User"],
    icons=["house", "info-circle", "person-circle"],
    menu_icon="bank2",
    default_index=0,
    orientation="horizontal",
    styles=styles,
)

st.header("Details")
user_name = st.text_input("Enter your Name", key="user_name")
user_email = st.text_input("Enter your Email", key="user_email")

# Iterate through categories and display inputs
for category, types in categories.items():
    st.header(category)
    type_option = st.selectbox(f"Choose a {category} Type:", types, key=f"{category}_type")

    for i in range(st.session_state[f"{category}_{type_option}_rows"]):
        st.text_input(f"{type_option} {i + 1} Name", key=f"{category}_{type_option}_name_{i}")
        st.number_input(f"{type_option} {i + 1} Value", min_value=0.0, step=1000.0, key=f"{category}_{type_option}_value_{i}")

    # Add and Remove Buttons
    button_col1, button_col2 = st.columns([1, 4])
    with button_col1:
        st.button(
            f"Add {type_option} Row",
            on_click=add_row,
            args=(category, type_option),
        )
    with button_col2:
        st.button(
            f"Remove {type_option} Row",
            on_click=remove_row,
            args=(category, type_option),
        )

# Passive Income Assets Section
st.header("Passive Income Assets")
for i in range(st.session_state["Passive_Income_Assets_rows"]):
    st.text_input(f"Passive Income Asset {i + 1} Name", key=f"Passive_Income_Assets_name_{i}")
    st.number_input(
        f"Passive Income Asset {i + 1} Value", min_value=0.0, step=1000.0, key=f"Passive_Income_Assets_value_{i}"
    )

# Add and Remove Buttons for Passive Income
button_col1, button_col2 = st.columns([1, 4])
with button_col1:
    st.button("Add Passive Income Row", on_click=add_row, args=("Passive_Income_Assets",))
with button_col2:
    st.button("Remove Passive Income Row", on_click=remove_row, args=("Passive_Income_Assets",))

if st.button("Submit Data"):
    if not user_name or not user_email:
        st.error("Name and email are required!")
    else:
        data_to_store = {
            "user_name": user_name,
            "user_email": user_email,
        }

        # Collect data for all categories
        for category, types in categories.items():
            for type_option in types:
                key = f"{category}_{type_option}_rows"
                entries = []
                for i in range(st.session_state[key]):
                    name = st.session_state.get(f"{category}_{type_option}_name_{i}", "")
                    value = st.session_state.get(f"{category}_{type_option}_value_{i}", 0.0)
                    entries.append({"name": name, "value": value})
                data_to_store[f"{category}_{type_option}"] = entries

        # Collect Passive Income Assets
        passive_income_entries = []
        for i in range(st.session_state["Passive_Income_Assets_rows"]):
            name = st.session_state.get(f"Passive_Income_Assets_name_{i}", "")
            value = st.session_state.get(f"Passive_Income_Assets_value_{i}", 0.0)
            passive_income_entries.append({"name": name, "value": value})
        data_to_store["Passive_Income_Assets"] = passive_income_entries

        # Store data in Firestore
        db.collection("finance_data").add(data_to_store)
        st.success("Data successfully submitted!")