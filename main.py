import streamlit as st
import pandas as pd
import io

st.title("Party Planner")

# Number of expected guests
total_guests = st.number_input("Expected number of guests", min_value=1, value=60)

pl = st.number_input("P/L", min_value=-100, value=0)

# Import/Export section
st.sidebar.header("Import/Export Data")

# Import functionality first
uploaded_file = st.sidebar.file_uploader("Import Data (CSV)", type="csv")
if uploaded_file is not None:
    try:
        imported_data = pd.read_csv(uploaded_file)
        st.session_state['imported_data'] = imported_data
        st.sidebar.success("Data successfully imported!")
    except Exception as e:
        st.sidebar.error(f"Error importing data: {e}")

# Input for drink options
st.header("Shopping List")

# Use imported data if available, otherwise use default
initial_data = st.session_state.get('imported_data') if 'imported_data' in st.session_state else pd.DataFrame({
    "Item": ["Beer", "Wine", "Soda", "Water"],
    "Quantity p.P": [6, 2, 0.01, 0.5],
    "Price per Unit CHF": [1.5, 4.0, 1.0, 0.5],
})

drink_data = st.data_editor(
    initial_data,
    num_rows="dynamic",
    use_container_width=True
)

# Now define the export function AFTER drink_data is defined
def get_csv_download():
    csv_buffer = io.StringIO()
    drink_data.to_csv(csv_buffer, index=False)
    return csv_buffer.getvalue()

# Create a download button in the sidebar
st.sidebar.download_button(
    label="Export Data (CSV)",
    data=get_csv_download(),
    file_name="party_planner_data.csv",
    mime="text/csv"
)

# Clear imported data button (to go back to default)
if 'imported_data' in st.session_state:
    if st.sidebar.button("Clear Imported Data"):
        del st.session_state['imported_data']
        st.sidebar.success("Reverted to default data")
        st.rerun()

# Calculate total cost
drink_data["Total Cost"] = drink_data["Quantity p.P"] * drink_data["Price per Unit CHF"] * total_guests
drink_data["Total Cost"] = drink_data["Total Cost"].apply(lambda x: round(x, 2) if pd.notna(x) else 0)
drink_data["Total Items"] = drink_data["Quantity p.P"] * total_guests
drink_data["Total Items"] = drink_data["Total Items"].apply(lambda x: int(x) if pd.notna(x) else 0)
total_cost = drink_data["Total Cost"].sum()
total_items = drink_data["Total Items"].sum()

# Create a formatted copy of the data for display
display_df = drink_data.copy()

# Define a safer conversion function
def safe_format(x, format_type="float", decimal_places=2):
    try:
        if pd.isna(x) or str(x).strip() == "":
            return ""
        if format_type == "float":
            return f"{float(x):.{decimal_places}f}"
        elif format_type == "int":
            return f"{int(float(x))}"
        else:
            return str(x)
    except (ValueError, TypeError):
        return ""

# Apply the safer formatting to all columns
display_df["Price per Unit CHF"] = display_df["Price per Unit CHF"].apply(lambda x: safe_format(x, "float", 2))
display_df["Total Cost"] = display_df["Total Cost"].apply(lambda x: safe_format(x, "float", 2))
display_df["Total Items"] = display_df["Total Items"].apply(lambda x: safe_format(x, "int"))
display_df["Quantity p.P"] = display_df["Quantity p.P"].apply(lambda x: safe_format(x,  "float"))

# Convert to string after safe formatting
for col in display_df.columns:
    display_df[col] = display_df[col].astype(str)

# Create the summary row with properly formatted values
summary_row = pd.DataFrame([{
    "Item": "TOTAL", 
    "Quantity p.P": "", 
    "Price per Unit CHF": "", 
    "Total Items": f"{int(total_items)}", 
    "Total Cost": f"{total_cost:.2f}",
}])

# Concatenate the formatted display data with the summary row
display_df = pd.concat([display_df, summary_row], ignore_index=True)

# Display the table with all items and the summary row
st.header("Inventory")
st.table(display_df)

# No-show rates
st.header("Guest Contribution Based on No-Show Rates")
no_show_rates = [0, 0.05, 0.10, 0.15, 0.20, 0.25]

# No-show rates table with consistent formatting
results = []
for rate in no_show_rates:
    actual_guests = total_guests * (1 - rate)
    cost_per_guest = (total_cost + pl) / actual_guests if actual_guests > 0 else 0
    results.append({
        "No-Show Rate": f"{int(rate * 100)}%",
        "Expected Guests": int(round(actual_guests)),
        "Cost per Guest CHF": f"{cost_per_guest:.2f}"  # Format with 2 decimal places
    })

st.table(pd.DataFrame(results))
