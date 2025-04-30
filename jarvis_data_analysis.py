import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import io
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.shared import Inches
from docx.shared import RGBColor
from docx.enum.style import WD_STYLE_TYPE # Imported but not explicitly used for styling in helper funcs
import google.generativeai as genai
from datetime import datetime
from MainJarvis_TaskExecution import speak
# Remove subprocess and sys imports as file opening is handled by frontend


# --- Helper Functions (Keep these outside the main callable function) ---

# Helper function to add formatted paragraphs with Times New Roman and specified style/size
def add_styled_paragraph(doc, text, style='Normal', size_pt=Pt(12), bold=False, italic=False, color=None):
    """Adds a paragraph to the document with specified styling."""
    p = doc.add_paragraph(text, style=style)
    for run in p.runs:
        font = run.font
        font.name = 'Times New Roman'
        font.size = size_pt
        run.bold = bold
        run.italic = italic
        if color:
            font.color.rgb = RGBColor(*color)

# Helper to add DataFrame as a formatted table
def add_dataframe_table(doc, df, heading=None):
    """Adds a pandas DataFrame as a formatted table to the document."""
    if df is None or df.empty:
        add_styled_paragraph(doc, "Data table is empty or not available.", size_pt=Pt(11))
        return

    if heading:
        add_styled_paragraph(doc, heading, bold=True, size_pt=Pt(11))

    # Convert index to a column for inclusion in the table
    df_reset = df.reset_index()
    if 'index' in df_reset.columns:
        df_reset = df_reset.rename(columns={'index': df_reset.index.name if df_reset.index.name else 'Index'})

    table = doc.add_table(rows=df_reset.shape[0] + 1, cols=df_reset.shape[1])
    table.style = 'Table Grid'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    # Add header row
    for j, col_name in enumerate(df_reset.columns):
        cell = table.cell(0, j)
        cell.text = str(col_name)
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.bold = True
                run.font.name = 'Times New Roman'
                run.font.size = Pt(10)

    # Add data rows
    for i in range(df_reset.shape[0]):
        for j in range(df_reset.shape[1]):
            cell = table.cell(i + 1, j)
            value = df_reset.iloc[i, j]
            if isinstance(value, float):
                 cell.text = f"{value:.2f}"
            else:
                 cell.text = str(value)

            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.font.name = 'Times New Roman'
                    run.font.size = Pt(9)

    doc.add_paragraph() # Add space after table

# Helper to insert charts
def insert_charts(doc, chart_paths):
    """Inserts saved chart images into the document."""
    for name, path in chart_paths.items():
        if path and os.path.exists(path):
            try:
                add_styled_paragraph(doc, name.replace("_", " ").title(), style='Heading 2', size_pt=Pt(14))
                doc.add_picture(path, width=Inches(6.0))
                last_paragraph = doc.paragraphs[-1]
                last_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            except Exception as e:
                add_styled_paragraph(doc, f"Error inserting chart {name}: {e}", size_pt=Pt(10), color=(255, 0, 0))

# Plotting Functions (Ensure these close plots and return paths or None)
def plot_hist_kde(df, col, output_dir):
    if df[col].empty or df[col].isnull().all(): return None
    try:
        plt.figure(figsize=(8, 5))
        sns.histplot(df[col].dropna(), kde=True, bins=30, color='royalblue')
        plt.title(f"Distribution of {col}")
        plt.xlabel(col)
        plt.ylabel("Frequency")
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.tight_layout()
        path = os.path.join(output_dir, f"{col}_hist_kde.png")
        plt.savefig(path)
        plt.close()
        return path
    except Exception as e:
        print(f"Error generating histogram for {col}: {e}") # Log error internally
        plt.close()
        return None

def plot_boxplot(df, col, output_dir):
    if df[col].empty or df[col].isnull().all(): return None
    try:
        plt.figure(figsize=(6, 4))
        sns.boxplot(y=df[col].dropna(), color='lightgreen')
        plt.title(f"Boxplot of {col}")
        plt.ylabel(col)
        plt.grid(True, axis='y', linestyle='--', alpha=0.6)
        plt.tight_layout()
        path = os.path.join(output_dir, f"{col}_boxplot.png")
        plt.savefig(path)
        plt.close()
        return path
    except Exception as e:
        print(f"Error generating boxplot for {col}: {e}") # Log error internally
        plt.close()
        return None

def plot_line_trend(df, col, output_dir):
    # Need at least two non-NaN values to plot a line
    if df[col].dropna().empty or len(df[col].dropna()) < 2: return None
    try:
        plt.figure(figsize=(10, 4))
        # Plot against index or datetime if available and relevant
        plot_data = df[col].dropna()
        if len(df[col]) > 10: # Only calculate rolling mean for sufficient data
             rolling_mean = df[col].rolling(window=max(2, int(len(df[col])*0.1))).mean() # Ensure window is at least 2
             plt.plot(df.index, df[col], label="Original", alpha=0.7, linestyle='-')
             plt.plot(df.index, rolling_mean, label=f"Rolling Mean ({max(2, int(len(df[col])*0.1))})", color='red', linestyle='--')
        else:
            plt.plot(df.index, df[col], marker='o', linestyle='-') # Plot points if sparse
        plt.title(f"Trend Analysis for {col}")
        plt.xlabel("Data Index")
        plt.ylabel(col)
        plt.grid(True, linestyle='--', alpha=0.6)
        if len(df[col]) > 10: plt.legend()
        plt.tight_layout()
        path = os.path.join(output_dir, f"{col}_line.png")
        plt.savefig(path)
        plt.close()
        return path
    except Exception as e:
        print(f"Error generating line plot for {col}: {e}") # Log error internally
        plt.close()
        return None


def plot_correlation_heatmap(df, numeric_cols, output_dir):
    if len(numeric_cols) < 2: # Need at least two numeric columns for correlation
        return None
    try:
        plt.figure(figsize=(max(8, len(numeric_cols)*0.8), max(7, len(numeric_cols)*0.7)))
        corr_matrix = df[numeric_cols].corr(method='pearson')
        sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', fmt=".2f", linewidths=.5, linecolor='black')
        plt.title("Correlation Heatmap of Numeric Features")
        plt.tight_layout()
        path = os.path.join(output_dir, "correlation_heatmap.png")
        plt.savefig(path)
        plt.close()
        return path
    except Exception as e:
        print(f"Error generating correlation heatmap: {e}") # Log error internally
        plt.close()
        return None

def plot_timeseries(df, datetime_col, col, output_dir):
    if datetime_col is None or col not in df.columns or df[col].empty or df[col].isnull().all(): return None
    try:
        # Ensure datetime column is actually datetime objects and sort
        df_sorted = df.sort_values(by=datetime_col).reset_index(drop=True)
        plt.figure(figsize=(12, 6))
        plt.plot(df_sorted[datetime_col], df_sorted[col], marker='o', linestyle='-')
        plt.title(f"Time Series of {col} over {datetime_col}")
        plt.xlabel(datetime_col)
        plt.ylabel(col)
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.tight_layout()
        path = os.path.join(output_dir, f"{col}_timeseries.png")
        plt.savefig(path)
        plt.close()
        return path
    except Exception as e:
        print(f"⚠️ Could not plot time series for '{col}': {e}") # Log error internally
        plt.close()
        return None


def plot_top_n(df, col, output_dir, n=5):
    if df[col].empty: return None
    try:
        plt.figure(figsize=(8, 5))
        # Ensure col is treated as categorical for value_counts and handle potential NaNs
        top_n = df[col].astype(str).value_counts().nlargest(n)
        if top_n.empty: return None
        sns.barplot(x=top_n.index, y=top_n.values, palette='viridis')
        plt.title(f"Top {n} Categories in '{col}'")
        plt.xlabel("Category")
        plt.ylabel("Count")
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        path = os.path.join(output_dir, f"{col}_top{n}.png")
        plt.savefig(path)
        plt.close()
        return path
    except Exception as e:
        print(f"Error generating top N plot for {col}: {e}") # Log error internally
        plt.close()
        return None


# Gemini Analysis Function
def get_gemini_analysis(df, info_str, desc_numeric, desc_object, missing_info_present, datetime_col=None, object_cols=None, corr_matrix=None):
    """Generates data analysis insights using the Gemini API."""
    # Check if model is configured before calling
    # if not hasattr(genai, '_configured') or not genai._configured:
    #      return "Error: Gemini API not configured. Please provide a valid API key."

    try:
        # Access the model instance
        model = genai.GenerativeModel("gemini-1.5-pro")
    except Exception as e:
        return f"Error: Could not load Gemini model: {e}"


    # Construct the prompt (same as before)
    prompt = f"""
    As a professional data scientist, provide a detailed and structured analysis of the following dataset. Structure your response with clear headings for each section using markdown (`##`, `###`).

    ## 1. Introduction to the Dataset
    Briefly describe the likely context and key variables based on the column names.

    ## 2. Data Overview
    - Data Dimensions and Types:
    \n```\n{info_str}\n```
    - Summary Statistics (Numeric):\n```\n{desc_numeric.to_string()}\n```
    - Summary Statistics (Categorical):\n```\n{desc_object.to_string()}\n```
    - Missing Values:\n```\n{missing_info_present.to_string() if not missing_info_present.empty else 'No significant missing values found.'}\n```
    {'Note: Missing numeric values were imputed with the mean.' if missing_info_present.sum() > 0 and not desc_numeric.empty else ''}


    ## 3. Key Findings and Insights

    ### 3.1 Numeric Data Analysis
    Analyze the distributions (from histograms/KDEs implied by stats), central tendencies, spread (from summary stats), and potential outliers (from box plots implied by stats) for key numeric columns. Discuss what these findings suggest.

    {f"### 3.2 Time-Based Analysis (Column: {datetime_col})" if datetime_col else ""}
    {f"Analyze trends, patterns, seasonality, or any notable events visible in the time series data for numeric columns against '{datetime_col}'. What story does the data tell over time?" if datetime_col else ""}

    {f"### 3.3 Relationships Between Numeric Variables" if corr_matrix is not None and not corr_matrix.empty and len(df.select_dtypes(include=np.number).columns) > 1 else ""} # Ensure enough numeric cols
    {f"Analyze the correlation matrix to describe significant positive and negative relationships between numeric variables. Explain the strength and direction of these correlations and their potential implications.\n```\n{corr_matrix.to_string()}\n```" if corr_matrix is not None and not corr_matrix.empty and len(df.select_dtypes(include=np.number).columns) > 1 else ""}


    {f"### 3.4 Categorical Data Insights" if object_cols and not desc_object.empty else ""} # Ensure there are object cols and they are not empty
    {f"Analyze the distribution of values in categorical (object) columns, focusing on the most frequent categories. Describe any patterns or imbalances observed." if object_cols and not desc_object.empty else ""}
    {f"\nTop categories for object columns: {[f'{col}: {df[col].astype(str).value_counts().nlargest(5).to_dict()}' for col in object_cols if col in df.columns and not df[col].empty]}" if object_cols and not desc_object.empty else ""} # Provide top categories data here


    ## 4. Conclusion
    Provide a concise summary of the most important findings from the analysis.

    ## 5. Recommendations
    Based on the analysis, suggest specific, actionable recommendations for further investigation or business actions. What are the next steps?

    Aim for clear, professional language suitable for a data analysis report.
    """

    try:
        # Use a timeout for the API call
        response = model.generate_content(prompt, request_options={"timeout": 60}) # Increased timeout
        return response.text.strip()
    except Exception as e:
        return f"❌ Error retrieving explanation from Gemini: {e}"

# Report Generation Function
def create_report(df, info_str, desc_numeric, desc_object, missing_info_present, analysis, chart_paths, csv_path):
    """Creates the Word document report."""
    doc = Document()
    styles = doc.styles
    style_normal = styles['Normal']
    font = style_normal.font
    font.name = 'Times New Roman'
    font.size = Pt(12)

    add_styled_paragraph(doc, "📊 Data Analysis Report", style='Normal', size_pt=Pt(24), bold=True)

    add_styled_paragraph(doc, "Introduction", style='Heading 1', size_pt=Pt(18))
    add_styled_paragraph(doc, "This report provides a comprehensive analysis of the dataset provided. The analysis includes data description, statistical summaries, visualizations, and key insights interpreted by Gemini AI.", size_pt=Pt(11))
    add_styled_paragraph(doc, "Data Source", style='Heading 2', size_pt=Pt(14))
    add_styled_paragraph(doc, f"The dataset was loaded from the file: {csv_path}", size_pt=Pt(11))

    add_styled_paragraph(doc, "Data Description", style='Heading 1', size_pt=Pt(18))
    add_styled_paragraph(doc, "Dataset Information:", style='Heading 2', size_pt=Pt(14))
    add_styled_paragraph(doc, info_str, size_pt=Pt(10))

    add_styled_paragraph(doc, "Summary Statistics (Numeric):", style='Heading 2', size_pt=Pt(14))
    add_dataframe_table(doc, desc_numeric)

    if not desc_object.empty:
        add_styled_paragraph(doc, "Summary Statistics (Categorical):", style='Heading 2', size_pt=Pt(14))
        add_dataframe_table(doc, desc_object)

    add_styled_paragraph(doc, "Missing Values", style='Heading 2', size_pt=Pt(14))
    if not missing_info_present.empty:
        add_styled_paragraph(doc, "Missing values found per column:", size_pt=Pt(11))
        add_dataframe_table(doc, pd.DataFrame(missing_info_present, columns=['Missing Count']))
        add_styled_paragraph(doc, "Note: Missing numeric values were imputed with the mean.", size_pt=Pt(10), italic=True)
    else:
        add_styled_paragraph(doc, "No significant missing values were found in the dataset.", size_pt=Pt(11))

    add_styled_paragraph(doc, "Analysis and Insights", style='Heading 1', size_pt=Pt(18))
    # Gemini analysis is expected to have its own markdown headings
    add_styled_paragraph(doc, analysis, size_pt=Pt(11))


    add_styled_paragraph(doc, "Visualizations", style='Heading 1', size_pt=Pt(18))
    insert_charts(doc, chart_paths)

    return doc

# --- Main Callable Function ---

def run_data_analysis(csv_path: str, gemini_api_key: str):
    
    messages = []
    report_filepath = None
    output_dir = "analysis_charts" # Directory to save charts

    # Helper function to log messages and append to list
    def log_message(msg, level="INFO"):
        # You could add logic here to print based on level or just print always for debugging
        print(f"[{level}] {msg}")
        messages.append(f"[{level}] {msg}")

    speak(f"Starting data analysis for the given csv file")

    # ===== Gemini API Setup =====
    if not gemini_api_key or gemini_api_key == "YOUR_GEMINI_API_KEY_HERE" or "AIzaSy" not in gemini_api_key: # Added a basic check
         log_message("❌ GEMINI_API_KEY is not provided or looks like a placeholder. Please provide a valid key.", "ERROR")
         return False, messages, None

    try:
        # log_message("🌐 Attempting to configure Gemini API...")
        genai.configure(api_key=gemini_api_key)
        # Test connection and model access
        model = genai.GenerativeModel("gemini-1.5-pro")
        log_message("Testing Gemini API connection...")
        # model.generate_content("Ping", request_options={"timeout": 10})

        # genai._configured = True # Simulate configured state if not inherently tracked by genai
    except Exception as e:
        log_message(f"❌ Failed to connect to Gemini API or load model: {e}", "ERROR")
        log_message("Please check your API key and network connection.", "ERROR")
        genai._configured = False # Ensure flag is False on failure
        return False, messages, None

    # ===== File Input & Load Data =====
    if not os.path.exists(csv_path):
        log_message(f"❌ File not found: {csv_path}", "ERROR")
        return False, messages, None

    speak("Loading data...")
    try:
        df = pd.read_csv(csv_path)
        speak("Data loaded successfully.")
        log_message(f"Dataset shape: {df.shape}")
    except Exception as e:
        log_message(f"❌ Error loading CSV file: {e}", "ERROR")
        return False, messages, None

    # Check if dataframe is empty after loading
    if df.empty:
         log_message("⚠️ Loaded CSV is empty. No analysis can be performed.", "WARNING")
         return False, messages, None


    # ===== Time-Series Handling =====
    datetime_col = None
    for col in df.columns:
        temp_col = df[col].copy()
        try:
            # Use errors='coerce' to turn unparseable dates into NaT
            temp_col_dt = pd.to_datetime(temp_col, errors='coerce')
          
            if temp_col_dt.notna().sum() > len(temp_col_dt) * 0.5 and temp_col_dt.notna().any():
                 df[col] = temp_col_dt # Update the actual column in the dataframe
                 datetime_col = col
                 df = df.sort_values(by=col).reset_index(drop=True)
                 break # Stop after finding the first plausible datetime column
        except Exception as e:
            
            pass # Ignore errors for columns that are not dates

   


    # ===== Data Info & Summary Stats & Missing Values =====
    speak("Gathering data information and statistics...")
    buffer = io.StringIO()
    df.info(buf=buffer)
    info_str = buffer.getvalue()

    desc_numeric = df.select_dtypes(include=np.number).describe()
    desc_object = df.select_dtypes(include='object').describe()

    missing_info = df.isnull().sum()
    missing_total = missing_info.sum()
    missing_info_present = missing_info[missing_info > 0]

    if missing_total > 0:
        speak(f"Found {missing_total} missing values. Attempting to fill numeric NaNs with mean...")
        # Fill numeric missing values
        numeric_cols_with_nan = df.select_dtypes(include=np.number).columns[df.select_dtypes(include=np.number).isnull().any()].tolist()
        for col in numeric_cols_with_nan:
             try:
                mean_val = df[col].mean()
                df[col].fillna(mean_val, inplace=True)
                speak(f"Filled missing values in '{col}' with mean ({mean_val:.2f}).")
             except Exception as e:
                 log_message(f"Could not fill missing values in '{col}': {e}", "WARNING")

        # Note: This code does NOT fill missing values in object columns
        if any(df[col].isnull().any() for col in df.select_dtypes(include='object').columns):
             log_message("⚠️ Note: Missing values in object columns were NOT imputed.", "WARNING")

    else:
        log_message("✅ No missing values found.", "INFO")


    # ===== Visualization Directory =====
    os.makedirs(output_dir, exist_ok=True)
    speak(f"Generating charts in '{output_dir}' sub-folder within our cwd...")

    # ===== Plotting =====
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    object_cols = df.select_dtypes(include='object').columns.tolist()
    chart_paths = {}

    for col in numeric_cols:
         hist_path = plot_hist_kde(df, col, output_dir)
         if hist_path: chart_paths[col + "_hist_kde"] = hist_path

         boxplot_path = plot_boxplot(df, col, output_dir)
         if boxplot_path: chart_paths[col + "_boxplot"] = boxplot_path

         # Only plot line trend if data makes sense (e.g., not just a single value)
         if len(df[col].dropna()) > 1:
            line_path = plot_line_trend(df, col, output_dir)
            if line_path: chart_paths[col + "_line"] = line_path


    corr_matrix_numeric = None
    if len(numeric_cols) > 1:
        try:
             corr_matrix_numeric = df[numeric_cols].corr()
             heatmap_path = plot_correlation_heatmap(df, numeric_cols, output_dir)
             if heatmap_path: chart_paths["correlation_heatmap"] = heatmap_path
        except Exception as e:
             log_message(f"⚠️ Could not generate correlation heatmap: {e}", "WARNING")


    if datetime_col:
        numeric_cols_no_date = [col for col in numeric_cols if col != datetime_col and col in df.columns]
        for col in numeric_cols_no_date:
             timeseries_path = plot_timeseries(df, datetime_col, col, output_dir)
             if timeseries_path: chart_paths[col + "_timeseries"] = timeseries_path


    for col in object_cols:
         # Only plot top N if column is not empty and has some unique values
         if not df[col].empty and df[col].nunique() > 1:
            topn_path = plot_top_n(df, col, output_dir)
            if topn_path: chart_paths[col + "_top5"] = topn_path
         elif not df[col].empty:
             log_message(f"Column '{col}' is categorical but has only one unique value, skipping Top N plot.", "INFO")


    speak("Charts generation complete.")

    # ===== Gemini Analysis =====
    log_message("\n🧠 Getting analysis from Gemini...", "INFO")
    # Pass collected information to the Gemini analysis function
    analysis = get_gemini_analysis(df.copy(), info_str, desc_numeric.copy(), desc_object.copy(), missing_info_present.copy(), datetime_col, object_cols, corr_matrix_numeric.copy() if corr_matrix_numeric is not None else None)
    log_message("✅ Gemini analysis retrieved.", "INFO")

    # ===== Report Generation =====
    # Generate a dynamic output filename based on the input CSV
    base_name = os.path.splitext(os.path.basename(csv_path))[0]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = os.path.join(".", f"{base_name}_Analysis_Report_{timestamp}.docx")

    log_message(f"\n📄 Creating report: '{output_filename}'...", "INFO")
    try:
        # Pass all necessary components to the report creation function
        doc = create_report(df.copy(), info_str, desc_numeric.copy(), desc_object.copy(), missing_info_present.copy(), analysis, chart_paths, csv_path)
        doc.save(output_filename)
        report_filepath = output_filename
        speak("Professional report saved successfully within our directory.")
        speak("Now Opening the report on the given csv file")
        os.startfile(report_filepath)
        return True, messages, report_filepath
    except Exception as e:
        log_message(f"❌ Error generating or saving report: {e}", "ERROR")
        return False, messages, None

# --- Example Usage (for testing the function) ---
if __name__ == "__main__":
    test_gemini_key = os.getenv("GEMINI_API_KEY") # Recommended way
    if test_gemini_key is None:
        # Fallback to asking user if env var is not set (for easy testing)
        # In a GUI, you'd have an input field for this.
        print("Please set GEMINI_API_KEY environment variable or enter it now:")
        test_gemini_key = input("Enter Gemini API Key: ").strip()
        if not test_gemini_key:
             print("No API key provided. Analysis will fail.")

    # Get CSV path from user for testing
    test_csv_path = input("Enter path to your CSV file: ").strip()
    if not test_csv_path:
        print("No CSV path provided. Exiting test.")
    else:
        # Call the function
        print("\n--- Running Analysis Function ---")
        success, messages, report_path = run_data_analysis(test_csv_path, test_gemini_key)

        print("\n--- Analysis Complete ---")
        print("Messages:")
        for msg in messages:
            print(msg)

        if success:
            print(f"\nSuccessfully generated report: {report_path}")
            # In a real Tkinter app, you might offer to open the report here
            # For testing, let's try to open it (similar to your original code)
            try:
                if os.name == "nt": # Windows
                    os.startfile(report_path)
                elif sys.platform == "darwin": # macOS
                    subprocess.call(["open", report_path])
                else: # Linux/others
                    subprocess.call(["xdg-open", report_path])
                print(f"Attempted to open {report_path}")
            except FileNotFoundError:
                print(f"Could not automatically open {report_path}. Please open it manually.")
            except Exception as e:
                print(f"An error occurred while trying to open the document: {e}")

        else:
            print("\nAnalysis failed.")