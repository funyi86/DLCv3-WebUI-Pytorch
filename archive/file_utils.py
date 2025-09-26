import os
import streamlit as st

def create_new_folder(folder_path):
    try:
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            st.success(f"Created folder: {folder_path}")
        else:
            st.info(f"Folder already exists: {folder_path}")
    except Exception as e:
        st.error(f"Error creating folder: {e}")

def upload_files(folder_path):
    """
    Handles the upload of files to the specified directory and saves them without any additional processing.
    """
    uploaded_files = st.file_uploader("Choose a file", type="mp4", accept_multiple_files=True)
    if uploaded_files:
        for uploaded_file in uploaded_files:
            file_path = os.path.join(folder_path, uploaded_file.name)
            if not os.path.exists(file_path):
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                    st.success(f'File "{uploaded_file.name}" uploaded successfully!')
            else:
                st.info(f'File "{uploaded_file.name}" already exists.')

def list_directories(root_directory):
    try:
        directories = [d for d in os.listdir(root_directory) if os.path.isdir(os.path.join(root_directory, d))]
        directories.sort()
    except Exception as e:
        st.error(f"Failed to list directories: {e}")
    return directories

def display_folder_contents(folder_path, selected_files):
    """
    Displays the contents of the specified folder, sorted by file extension and then by filename.
    Marks the files that have been selected.
    """
    files = os.listdir(folder_path)
    files_dict = {}

    # Group files by extension
    for file in files:
        ext = os.path.splitext(file)[1]
        if ext not in files_dict:
            files_dict[ext] = []
        files_dict[ext].append(file)

    # Sort files within each extension group
    for ext in sorted(files_dict.keys()):
        files_dict[ext].sort()

    st.write(f"Contents of the folder '{folder_path}':")
    for ext in sorted(files_dict.keys()):
        st.write(f"**{ext} files:**")
        for file in files_dict[ext]:
            full_path = os.path.join(folder_path, file)
            if full_path in selected_files:
                st.write(f"Selected: {file}")
            else:
                st.write(file)
                
def create_folder_if_not_exists(folder_path):
    """
    Checks if the specified folder exists and creates it if it does not.
    Provides user feedback through Streamlit about the status of the folder.
    """
    if st.button("新建文件夹/New Folder"):
        try:
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
                st.success(f"Created folder: {folder_path}")
            else:
                st.info(f"Folder already exists: {folder_path}")
        except Exception as e:
            st.error(f"Error creating folder: {e}")
            
def select_video_files(folder_path):
    """
    Displays a multi-select widget with video files sorted by name for user to select for processing.
    """
    files = [f for f in os.listdir(folder_path) if os.path.splitext(f)[1].lower() == '.mp4']
    files.sort()
    selected_files = st.multiselect("Select video files for analysis", files)
    return [os.path.join(folder_path, f) for f in selected_files]

def select_python_files(folder_path):
    """
    Display a multiselect widget to let the user choose Python script files from a specified directory.

    Args:
    folder_path (str): Path to the directory from which Python files are to be listed.

    Returns:
    list: List of selected Python script file paths.
    """
    if not os.path.exists(folder_path):
        st.error("Specified folder does not exist.")
        return []

    try:
        files = [f for f in os.listdir(folder_path) if os.path.splitext(f)[1] == '.py']
        files.sort()
        selected_files = st.multiselect("Select Python files for run", files)
        return [os.path.join(folder_path, f) for f in selected_files]
    except Exception as e:
        st.error(f"Error reading from the directory: {e}")
        return []