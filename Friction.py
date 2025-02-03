import os
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
import pandas as pd 

def calculate_average(file_path):
    
    right_column_values = []
    with open(file_path, 'r') as file:
        for line in file:
            try:
                columns = line.strip().split()
                value = float(columns[-1])
                right_column_values.append(value)
            except (ValueError, IndexError):
                continue

    if right_column_values:
        return sum(right_column_values) / len(right_column_values)
    return None

def process_folder(folder_path, selected_side):
    
    side_folder = os.path.join(folder_path, "Friction", selected_side)
    if not os.path.exists(side_folder):
        return None

    torque_files = [
        os.path.join(side_folder, f)
        for f in os.listdir(side_folder)
        if f.startswith("DriveTorque") and f.endswith(".txt")
    ]

    return torque_files

def extract_label(folder_path):
   
    parts = folder_path.strip(os.sep).split(os.sep)
    for part in reversed(parts):
        if part.startswith("RW-"):
            return part
    return "Unknown"

def analyze_rotating_wedges(base_folder, start_rw, end_rw, selected_side):
   
    averages = {"DriveTorque0.5rads": [], "DriveTorque1rads": [], "DriveTorque1.5rads": []}
    labels = []

    for rw_num in range(start_rw, end_rw + 1):
        folder_name = f"RW-{rw_num}"
        folder_path = os.path.join(base_folder, folder_name)

        if os.path.isdir(folder_path):
            torque_files = process_folder(folder_path, selected_side)

            if torque_files:
                folder_has_data = False  # To track if this folder has valid data
                for file in torque_files:
                    avg_current = calculate_average(file)
                    if avg_current is not None:
                        file_key = os.path.basename(file).replace(".txt", "")
                        if file_key in averages:
                            averages[file_key].append(avg_current)
                            folder_has_data = True
                        else:
                            st.warning(f"Skipping unexpected file: {file}")

                if folder_has_data:
                    labels.append(rw_num) 
            else:
                st.warning(f"No valid 'DriveTorque' files found in {folder_name}.")
        else:
            st.warning(f"Folder {folder_name} does not exist. Skipping.")

    # Generate plots for each file type
    for file_key, avg_values in averages.items():
        if len(avg_values) != len(labels):
            st.warning(f"Mismatch between labels and data for {file_key}. Skipping plot.")
            continue

        fig, ax = plt.subplots()
        ax.scatter(labels, avg_values, color="blue")
        
        if len(labels) > 1:
            z = np.polyfit(labels, avg_values, 1)
            p = np.poly1d(z)
            ax.plot(labels, p(labels), color="red", linestyle="-", label="Fitted Average Line")

        
        ax.set_xlabel("Rotating Wedge Index")
        ax.set_ylabel("Average Current")
        ax.set_title(f"{file_key}")
        ax.grid(True)
        ax.set_ylim(-90, 0)  
        ax.set_yticks(range(0, -91, -5)) 

        st.pyplot(fig)


    for file_key, avg_values in averages.items():
        if len(avg_values) == len(labels):
            df = pd.DataFrame({"RW ID": labels, file_key: avg_values})
            csv_file = f"{file_key}.csv"
            df.to_csv(csv_file, index=False)
            with open(csv_file, "rb") as f:
                st.download_button(
                    label=f"Download {file_key}.csv",
                    data=f,
                    file_name=csv_file,
                    mime="text/csv"
                )

def main():
    st.title("Rotating Wedge Friction Test Analysis")

    
    base_folder = st.text_input("Enter the base folder path containing rotating wedge folders:")

    if base_folder and os.path.isdir(base_folder):
       
        col1, col2 = st.columns(2)
        with col1:
            start_rw = st.number_input("Start RW Number", min_value=1, step=1, value=1)
        with col2:
            end_rw = st.number_input("End RW Number", min_value=1, step=1, value=100)
        selected_side = st.selectbox("Select the Side to Analyze", ["SideA", "SideB"])
        analyze_rotating_wedges(base_folder, start_rw, end_rw, selected_side)

    elif base_folder:
        st.error("The specified base path is not valid.")

if __name__ == "__main__":
    main()