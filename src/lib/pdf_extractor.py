import logging
import pdfplumber
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

def extract_tables_from_pdf(file_path):
    """
    Extracts tables from a PDF file using pdfplumber.
    Returns a list of candidate pandas DataFrames.
    """
    candidate_dfs = []
    
    try:
        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages):
                # Try extracting multiple tables from the page
                tables = page.extract_tables()
                
                for table in tables:
                    if not table:
                        continue
                        
                    # Convert to DataFrame
                    # Heuristic: First row is header?
                    # basic check: if all strings in first row
                    df = pd.DataFrame(table[1:], columns=table[0])
                    
                    # Clean headers
                    if all(isinstance(c, str) for c in df.columns):
                        df.columns = [c.strip().lower().replace(' ', '_').replace('\n', '_') for c in df.columns]
                    else:
                        # Fallback if headers are mixed types or empty? 
                        # pdfplumber usually returns None for empty cells.
                        # Make headers string
                        df.columns = [str(c) if c is not None else f"col_{j}" for j, c in enumerate(df.columns)]

                    # Fallback if the extracted table has the header as the first row of data (common issue)
                    # For now, rely on pdfplumber's split.
                    
                    # Basic cleanup
                    df = df.replace(r'^\s*$', np.nan, regex=True) # Replace empty whitespace with NaN
                    
                    candidate_dfs.append(df)
                    
    except Exception as e:
        logger.error(f"Error extracting tables from PDF {file_path}: {e}")
        # We don't raise here, we just return whatever we found (empty list likely)

    return candidate_dfs

def extract_text_from_pdf(file_path, max_chars=5000):
    """
    Extracts text from a PDF file.
    Returns a string trimmed to max_chars.
    """
    text_content = []
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_content.append(text)
                
                # Check if we have enough
                current_len = sum(len(t) for t in text_content)
                if current_len > max_chars:
                    break
    except Exception as e:
        logger.error(f"Error extracting text from PDF {file_path}: {e}")
        return ""

    full_text = "\n".join(text_content)
    return full_text[:max_chars]

def score_table(df):
    """
    Scores a table DataFrame based on suitability for analysis.
    Higher score is better.
    """
    score = 0
    rows, cols = df.shape
    
    # Minimal requirement
    if rows < 2 or cols < 2:
        return 0
        
    # Favor more rows (up to a point) and suitable column count
    score += min(rows, 100) * 1  # 1 point per row up to 100
    score += cols * 2            # 2 points per column
    
    # Check for meaningful data
    # Fraction of non-null cells
    non_null_count = df.count().sum()
    total_cells = rows * cols
    fill_rate = non_null_count / total_cells if total_cells > 0 else 0
    score += fill_rate * 50
    
    # Check for numeric-like content
    numeric_cols = 0
    for col in df.columns:
        try:
            # Try converting to numeric to check if it's potentially numeric
            pd.to_numeric(df[col].dropna(), errors='raise')
            numeric_cols += 1
        except:
            pass
            
    if cols > 0:
        numeric_fraction = numeric_cols / cols
        score += numeric_fraction * 30
        
    # Penalize generic headers if possible? 
    # (Not easy to detect without knowing context, but 'null', 'none' columns is bad)
    
    return score
