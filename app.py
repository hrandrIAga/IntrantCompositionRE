import streamlit as st
import pandas as pd
from fuzzywuzzy import fuzz
import gspread
#from oauth2client.service_account import ServiceAccountCredentials
from google.oauth2.service_account import Credentials
#from streamlit_gsheets import GSheetsConnection

st.set_page_config(
    page_title="Products nutritional input Internal Search Engine",
    page_icon="📝",
    layout="centered",
    initial_sidebar_state="expanded",
)

# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
#creds = ServiceAccountCredentials.from_json_keyfile_name("/home/hrandria/Maya_Projet_CompoOCR/SearchEngineFrance/.streamlit/fertilizersearchengine-keys.json", scope)
skey = st.secrets["GSHEETS_CONNECTION"]
creds = Credentials.from_service_account_info(skey, scopes = scope)
client = gspread.authorize(creds)

# Open the Google Sheet
sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1XXoxv6Ux4cw1DgvAp4DAkaz6RlJPSxTMI32bxIxKfeI/edit#gid=0")
worksheet = sheet.sheet1

# Load the data into a DataFrame
def load_data():
    data = worksheet.get_all_records()
    return pd.DataFrame(data)

# Save a new row to the Google Sheets
def save_data(new_row):
    worksheet.append_row(new_row)

# Delete a row from the Google Sheets
def delete_row(row_number):
    worksheet.delete_row(row_number)

# Search for approximate product matches and return results with scores
def search_products(query, df, column, threshold=80):
    results = []
    for index, row in df.iterrows():
        product = row[column]
        match_score = fuzz.partial_ratio(query, product)
        if match_score >= threshold:
            results.append((row, match_score))
    # Sort results by match score in descending order
    results.sort(key=lambda x: x[1], reverse=True)
    return results

# Generate the "Detailed Name" field
def generate_detailed_name(row):
    return f"{row['Marque']} {row['Produit']} {row['N-P-K | N-P2O5-K2O']} {row['Details']}"

#######################################################################################################
# Streamlit app
#######################################################################################################

def main():
    st.title("Product's composition (internal) Search Engine")

    # User input
    product_query = st.text_input("Enter a product name and infos (NPK, details,...)")

    # Load data
    data = load_data()

    # State to store the row being edited
    if 'edit_row' not in st.session_state:
        st.session_state.edit_row = None
        st.session_state.edit_row_index = None


    if product_query:
        results = search_products(product_query, data, 'Detailed Name')
        if results:
            st.write(f"{len(results)} results found with matching score > 79%")
            for row_index, (row, score) in enumerate(results):
                matching_rows = data[(data == row).all(axis=1)]
                data_index = matching_rows.index[0]  # Get the index of the matching row
                st.dataframe(pd.DataFrame([row]))

                if st.button(f"Delete {str(row['Detailed Name'])} at index {row_index}"):
                    delete_row(int(data_index) + 2)  # Convert back to int before deleting row
                    st.write("Row deleted successfully!")
                    st.rerun()

                if st.button(f"Edit {str(row['Detailed Name'])} at index {row_index}"):
                    st.session_state.edit_row = row.copy()
                    st.session_state.edit_row_index = int(data_index) + 2
                    st.rerun()

                if st.session_state.edit_row is not None:
                    with st.form(key='edit_product_form'):
                        st.write(f"Edit {str(st.session_state.edit_row['Detailed Name'])} at index {st.session_state.edit_row_index}")
                        
                        new_product = {}
                        for column in data.columns:
                            if column != "Detailed Name":
                                new_product[column] = st.text_input(column, value=str(st.session_state.edit_row[column]))
                        
                        submit_button = st.form_submit_button(label='Save edit')
                        
                        if submit_button:
                            # Generate "Detailed Name" and add new product to dataframe
                            new_product["Detailed Name"] = generate_detailed_name(new_product)
                            new_row = [new_product.get(col, "") for col in data.columns]
                            save_data(new_row)
                            delete_row(st.session_state.edit_row_index)
                            st.write(f"{str(st.session_state.edit_row['Detailed Name'])} edited successfully")
                            st.session_state.edit_row = None
                            st.session_state.edit_row_index = None
                            st.rerun()
        else:
            st.write('No product found, please look for it on internet')
            st.write('if your research is successful, please fill the form below to complete DB')
        
        st.divider()
        st.divider()

        with st.form(key='new_product_form'):
            st.write("Add a new product to the database")
                
            new_product = {}
            for column in data.columns:
                if column != "Detailed Name":
                    new_product[column] = st.text_input(column)
                
            submit_button = st.form_submit_button(label='Save input')

            
        if submit_button:
                # Generate "Detailed Name" and add new product to dataframe
            new_product["Detailed Name"] = generate_detailed_name(new_product)
            new_row = [new_product.get(col, "") for col in data.columns]
            save_data(new_row)
            st.write("New product added successfully!")
            st.rerun()

if __name__ == '__main__':
    main()
