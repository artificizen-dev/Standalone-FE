import requests, os, time, ast, base64, uuid, json
import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()
root_dir = Path.cwd()

API_BASE_URL = "https://z6zxn9xjbg.us-east-1.awsapprunner.com/api"
# API_BASE_URL = "http://127.0.0.1:8080/api"
USER_ID = uuid.uuid4()

class SessionState:
    def __init__(self):
        self.logged_in = False
        self.role = None
        self.username = None
        self.messages = []
        self.user_id = None
        self.show_form = False
        self.list_users = []
        self.edit_user = {}
        self.show_edit_form = False
def init_session_state():
    if 'session_state' not in st.session_state:
        st.session_state.session_state = SessionState()

def login_page():
    st.title("Login")
    st.divider()
    username = st.text_input("Username")
    password = st.text_input("Password", type='password')
    
    if st.button("Login"):
        with st.spinner("Logging in..."):    
            response = requests.post(
                f"{API_BASE_URL}/login",
                json={"username": username, "password": password}
            )
            data = response.json()
            
            if data["status_code"] == 200:
                st.success(data["message"])
                st.session_state.session_state.logged_in = True
                st.session_state.session_state.role = data.get("role", "user")
                st.session_state.session_state.username = username
                st.session_state.session_state.user_id = f"{data.get('user_id', USER_ID)}"
                time.sleep(1)
                st.rerun()
            else:
                st.error(data["message"])
def signup_page():
    st.title("Register New User")
    st.divider()
    username = st.text_input("Username")
    password = st.text_input("Password", type='password')
    confirm_password = st.text_input("Confirm Password", type='password')
    if st.button("Register User"):
        if password != confirm_password:
            st.error("Passwords do not match")
            time.sleep(2)
            st.rerun()
        with st.spinner("Registering User..."):
            response = requests.post(
                f"{API_BASE_URL}/signup",
                json={"username": username, "password": password}
            )
            data = response.json()
            
            if data["status_code"] == 200:
                st.success("User registered successfully!")
            else:
                st.error(data["message"])
def logout_page():
    st.session_state.session_state.logged_in = False
    st.session_state.session_state.role = None
    st.session_state.session_state.username = None
    st.rerun()

def profile_page():
    st.title("User Profile")
    st.divider()
    st.markdown(f"**User:** {st.session_state.session_state.username}")
    st.markdown(f"**Role:** {st.session_state.session_state.role}")
    st.markdown(f"**User ID:** {st.session_state.session_state.user_id}")
    st.divider()
    ## Change Password
    old_password = st.text_input("Old Password", type='password')
    new_password = st.text_input("New Password", type='password')
    confirm_password = st.text_input("Confirm New Password", type='password')
    if st.button("Change Password"):
        if new_password != confirm_password:
            st.error("Passwords do not match")
        elif old_password == new_password:
            st.error("New password cannot be the same as old password")
        else:
            with st.spinner("Changing Password..."):
                response = requests.put(f"{API_BASE_URL}/change-password", json={"username": st.session_state.session_state.username, "old_password": old_password, "new_password": new_password})
                data = response.json()
                if data["status_code"] == 200:
                    st.success(data["message"])
                    time.sleep(2)
                    logout_page()
                    
                else:
                    st.error(data["message"])
def upload_documents_page():
    st.title("Upload Documents")
    uploaded_files = st.file_uploader("Upload a file", type=["pdf", "mp4"], accept_multiple_files=True)

    if uploaded_files:
          
        if st.button("Upload"):
            for file in uploaded_files:
                with st.spinner(f"Uploading {file.name}..."):
                    files = {"file": (file.name, file, file.type)}
                    response = requests.post(
                        f"{API_BASE_URL}/upload-document",
                        files=files
                    )
                    data = response.json()
                    print("data: ", data, type(data))
                    if data["status_code"] == 200:
                        st.success(f"{file.name} uploaded successfully!")
                    elif data["status_code"] == 400:
                        if "already exists" in data.get("message", ""):
                            st.warning(data["message"], icon="⚠️")
                            st.info("💡 Suggestion: Try adding a version number or date to make the filename unique. Example: 'document_v2' or 'document_1234'")
                        else:
                            st.error(data.get("message", "Error during upload"))
                    else:
                        st.error(data.get("message", "Error during upload"))
            st.success("All files uploaded successfully!")
    else:
        if not uploaded_files:
            st.warning("Please upload a file.")

def uploaded_documents_page():
    st.title("Uploaded Documents")

    response = requests.get(f"{API_BASE_URL}/uploaded-documents")
    
    if response and response.status_code == 200 and response.json():
        files = response.json()
        print(files)
        if isinstance(files, list) and all(isinstance(file, dict) for file in files):
            df = pd.DataFrame(files)

            col1, col2, col3, col4 = st.columns([3, 2, 3, 3])
            col1.write("**Document Name**")
            col2.write("**Document Type**")
            col3.write("**File Path**")
            col4.write("**Actions**")

            for idx, row in df.iterrows():
                col1, col2, col3, col4 = st.columns([3, 2, 3, 3])
                col1.write(row['document_name'])
                col2.write(row['document_type'])
                col3.write(row['bucket_path'])

                with col4:
                    button_col1, button_col2 = st.columns(2)
                     
                    if button_col1.button(f"Delete", key=f"delete_{row['document_name']}"):
                        with st.spinner(f"Deleting {row['document_name']}..."):
                            response = requests.delete(f"{API_BASE_URL}/delete-uploaded-document", json={"file_id": int(row['id']), "file_name": row['document_name'].split('.com/')[-1]})
                            
                            if response.status_code == 200:
                                
                                if response and response.status_code == 200:
                                    st.success(f"File {row['document_name']} deleted successfully!")
                                    st.rerun()
                            else:
                                st.error(f"Error deleting {row['document_name']}")
                    
        else:
            st.info("No files uploaded yet or invalid response format.")
    else:
        st.info("No files uploaded yet.")

def chatbot_page():
    st.title("🤖 Chatbot")
    st.divider()
    for message in st.session_state.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "sources" in message: 
                st.markdown("**Sources**")
                st.markdown(message["sources"], unsafe_allow_html=True)
    if prompt := st.chat_input("Ask me anything"):
        st.session_state.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        assistant_message_placeholder = st.empty() 
        with assistant_message_placeholder.chat_message("assistant"):
            stream_container = st.empty()
            
            with st.spinner("Thinking..."):
                response = requests.post(f"{API_BASE_URL}/query", json={"query": prompt, "user_id": f"{st.session_state.session_state.user_id}"}, stream=True)
                content_response = ""
                # Display translation result
                if response.status_code == 200:
                    for token in response.iter_content(512):
                        if token:
                            token = token.decode('utf-8')
                            content_response += token
                            stream_container.markdown(content_response)
                    
                else:
                    print(response)
            session_container_messages = {
                "role": "assistant", 
                "content": content_response
            }
            ### Checking the action of the user query
            response = requests.post(f"{API_BASE_URL}/logs/recent", json={"id": f"{st.session_state.session_state.user_id}", "llm_answer":content_response, "question": prompt})
            print(response, response.json())
            if response and response.status_code == 200:
                response_json = response.json()
                show_sources = response_json["show_sources"]
                source_url = response_json["source_url"]
                file_name = response_json["file_name"]
                file_type = response_json["file_type"]
                # st.success(f"Action: {action}")
                if show_sources:
                    with st.spinner("Fetching Reference..."):
                        if file_type == "pdf":
                            response = requests.post(f"{API_BASE_URL}/get-pdf-page", json={"file_name": file_name, "llm_answer": content_response, "question": prompt})
                            if response and response.status_code == 200:
                                page_number = response.json()["page_number"]
                            else:
                                page_number = -1

                            st.markdown(f"**Sources**")

                            st.markdown("""
                            <style>
                            .abbreviated-link {
                                white-space: nowrap;
                                overflow: hidden;
                                text-overflow: ellipsis;
                                max-width: 300px;
                                display: inline-block;
                            }
                            </style>
                            """, unsafe_allow_html=True)

                            url = f"{source_url}?#page={page_number}"
                            
                            sources = f"""<a href="{url}" class="abbreviated-link" title="{url}"> {file_name.split('/')[-1]}</a>"""
                            st.markdown(sources, unsafe_allow_html=True)   
                            session_container_messages["sources"] = sources

                        elif file_type == "video":
                            
                            response = requests.post(f"{API_BASE_URL}/get-video-start-time", json={"file_name": file_name, "llm_answer": content_response, "question": prompt})
                            if response and response.status_code == 200:
                                start_time = response.json()["start_time"]
                                
                                st.markdown(f"**Sources**")
                                st.markdown("""
                                <style>
                                .abbreviated-link {
                                    white-space: nowrap;
                                    overflow: hidden;
                                    text-overflow: ellipsis;
                                    max-width: 300px;
                                    display: inline-block;
                                }
                                </style>
                                """, unsafe_allow_html=True)

                                url = f"{source_url}#t={start_time}"
                                sources = f"""<a href="{url}" class="abbreviated-link" title="{url}"> {file_name.split('/')[-1]}</a>"""
                                st.markdown(sources, unsafe_allow_html=True)
                                session_container_messages["sources"] = sources
            else:
                st.error("Error logging action")

            st.session_state.session_state.messages.append(
                session_container_messages
            )

def toggle_form():
        st.session_state.session_state.show_form = not st.session_state.session_state.show_form
def fetch_users():
    response = requests.get(f"{API_BASE_URL}/get-users")
    if response.status_code == 200:
        st.session_state.session_state.list_users = response.json().get("users", [])
    else:
        st.session_state.session_state.list_users = []

def show_edit_form(user_data):
    st.session_state.session_state.show_edit_form = True
    st.session_state.session_state.edit_user = user_data

def manage_users():
    st.title("Manage Users")
    st.divider()
    col1, col2 = st.columns([8, 1])
    with col1:
        st.subheader("Create Users")
    with col2:
        if st.button("[+]"):
            toggle_form()

    if st.session_state.session_state.show_form:
        with st.form("user_form"):
            username = st.text_input("Username", key="username")
            email = st.text_input("Email", key="email")
            password = st.text_input("Password", type="password", key="password")
            role = st.selectbox("Role", ["user", "admin"], key="role")
            
            submit_button = st.form_submit_button("Add User")
            
            if submit_button:
                with st.spinner("Adding User..."):
                    if "@" not in email or "." not in email:
                        st.error("Please enter a valid email address")
                    else:
                        if username and email and password and role:
                            response = requests.post(f"{API_BASE_URL}/create-user", json={
                                "username": username,
                                "email": email,
                                "password": password,
                                "role": role
                            })
                            print(response.json())
                            message = response.json()["message"]
                            if response.json()["status_code"] == 200:
                                fetch_users()
                                st.success(message)
                                time.sleep(3)
                                toggle_form()
                            else:
                                st.error(message)
                        else:
                            st.error("All fields are mandatory!")
    st.divider()
    st.subheader("Users")

    # users = fetch_users()
    if "list_users" not in st.session_state:
        fetch_users()

    if st.session_state.session_state.list_users:
        df = pd.DataFrame(st.session_state.session_state.list_users)
        df = df[["id", "username", "email", "role", "last_modified"]]
        df.columns = ["User ID", "Name", "Email", "Role", "Last Modified"]
        
        # Display table headers
        header_cols = st.columns([2, 3, 2, 2, 2, 2, 4])
        header_cols[0].write("**Name**")
        header_cols[1].write("**Email**")
        header_cols[2].write("**Role**")
        header_cols[3].write("**Last Modified**")
        header_cols[4].write("**Edit**")
        header_cols[5].write("**Delete User**")
        header_cols[6].write("**Reset Password**")
        
        for index, row in df.iterrows():
            col1, col2, col3, col4, col5, col6, col7 = st.columns([2, 3, 2, 2, 2, 2, 4])
            col1.write(row["Name"])
            col2.write(row["Email"] if row["Email"] else "")
            col3.write(row["Role"])
            col4.write(row["Last Modified"])
            if col5.button("Edit", key=f"edit_{row['User ID']}"):
                show_edit_form(row.to_dict())

            if col6.button("Delete", key=f"delete_{row['User ID']}"):
                with st.spinner("Deleting user..."):
                    time.sleep(1)
                    payload = {
                        "id": int(row["User ID"])
                    }
                    response = requests.delete(f"{API_BASE_URL}/delete-user", json=payload)
                    message = response.json().get("message", "Operation completed")
                    if response.json()["status_code"] == 200:
                        st.success(message)
                        fetch_users()
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error(message)
                        time.sleep(4)
                        st.rerun()
            if col7.button("Reset Password", key=f"reset_{row['User ID']}"):
                with st.spinner("Sending Email..."):
                    payload = {
                        "email": row["Email"],
                        "username": row["Name"]
                    }
                    response = requests.post(f"{API_BASE_URL}/reset-password", json=payload)
                    message = response.json().get("message", "Operation completed")
                    if response.json()["status_code"] == 200:
                        st.success(message)
                        time.sleep(3)
                        st.rerun()
                    else:
                        st.error(message)
                        time.sleep(2)
                        st.rerun()

        # Show edit form separately, outside of the row loop
        if st.session_state.session_state.show_edit_form:
            edit_user = st.session_state.session_state.edit_user

            st.subheader(f"Edit User - {edit_user['Name']}")

            new_username = st.text_input("Username", value=edit_user["Name"], key="edit_username")
            new_email = st.text_input("Email", value=str(edit_user["Email"]), key="edit_email")
            new_role = st.selectbox("Role", ["user", "admin"],
                                    index=0 if edit_user["Role"] == "user" else 1,
                                    key="edit_role")

            update_col, cancel_col = st.columns([1, 1])
            if update_col.button("Update", key="update_user"):
                with st.spinner("Updating user..."):
                    payload = {
                        "id": int(edit_user["User ID"]),
                        "username": new_username,
                        "email": new_email,
                        "role": new_role
                    }
                    response = requests.put(f"{API_BASE_URL}/edit-user", json=payload)
                    message = response.json().get("message", "Operation completed")
                    if response.json()["status_code"] == 200:
                        st.success(message)
                        fetch_users()
                        time.sleep(2)
                        st.session_state.session_state.show_edit_form = False
                        st.session_state.session_state.edit_user = {}
                        st.rerun()
                    else:
                        st.error(message)
                        time.sleep(2)
                        st.rerun()

            if cancel_col.button("Cancel", key="cancel_user"):
                st.session_state.session_state.show_edit_form = False
                st.session_state.session_state.edit_user = {}
                st.rerun()
            


def main():
    init_session_state()
    with st.sidebar:
        if st.session_state.session_state.logged_in and st.session_state.session_state.role == "admin":
            ## Add a logo
            st.image("src/assets/Logo.png", width=200)
            st.divider()
            selected_page = option_menu("Main Menu", ["Profile", "Users", "Upload Documents", "Uploaded Documents", "Chatbot", "Logout"], 
                                    icons=["person-circle", "person-plus", "cloud-upload", "file-earmark-text", "chat-dots", "box-arrow-right"], 
                                    menu_icon="cast", default_index=4)
            
        elif st.session_state.session_state.logged_in and st.session_state.session_state.role != "admin":
            ## Add a logo
            st.image("src/assets/Logo.png", width=150)
            st.divider()
            selected_page = option_menu("Main Menu", ["Profile", "Chatbot", "Logout"], 
                                    icons=["person-circle", "chat-dots", "box-arrow-right"], 
                                    menu_icon="cast", default_index=1)
        else:
            ## Add a logo
            st.image("src/assets/Logo.png", width=300)
            st.divider()
            selected_page = option_menu("Main Menu", ["Login"], 
                                    icons=["box-arrow-in-right"], 
                                    menu_icon="cast", default_index=0)
            # selected_page = option_menu("Main Menu", ["Login", "Signup"], 
            #                         icons=["box-arrow-in-right", "person-plus"], 
            #                         menu_icon="cast", default_index=0)
    if selected_page == "Login":
        login_page()
    elif selected_page == "Signup":
        signup_page()
    elif selected_page == "Profile":
        profile_page()
    elif selected_page == "Users":
        manage_users()
    elif selected_page == "Upload Documents":
        upload_documents_page()
    elif selected_page == "Uploaded Documents":
        uploaded_documents_page()
    elif selected_page == "Chatbot":
        chatbot_page()
    elif selected_page == "Logout":
        logout_page()

if __name__ == "__main__":
    main()
