import logging
import json
import pandas as pd

logger = logging.getLogger(__name__)

def normalize_json_to_df(json_obj):
    """
    Attempts to normalize a JSON object (list or dict) into a pandas DataFrame.
    Returns a DataFrame if successful, or None if no suitable tabular structure found.
    """
    try:
        # Case 1: Top-level list
        if isinstance(json_obj, list):
            # If empty list, return empty DF
            if not json_obj:
                return pd.DataFrame()
            
            # Use pandas json_normalize
            df = pd.json_normalize(json_obj)
            logger.info("Normalized top-level JSON list.")
            return df
            
        # Case 2: Top-level dict
        elif isinstance(json_obj, dict):
            # Potential keys that might hold the data
            candidate_keys = ['rows', 'data', 'items', 'records', 'invoices', 'customers', 'transactions', 'products']
            
            # Find the best key
            # We look for a key whose value is a list of objects/dicts
            found_key = None
            max_len = 0
            
            for key in candidate_keys:
                if key in json_obj and isinstance(json_obj[key], list):
                    # Check if list content looks like records (dicts)
                    val = json_obj[key]
                    if len(val) > 0 and isinstance(val[0], dict):
                        if len(val) > max_len:
                            max_len = len(val)
                            found_key = key
            
            # Also check generic keys if no candidate found?
            # Or iterate all keys and find the largest list of dicts
            if not found_key:
                for key, val in json_obj.items():
                    if isinstance(val, list) and len(val) > 0 and isinstance(val[0], dict):
                        if len(val) > max_len:
                            max_len = len(val)
                            found_key = key
            
            if found_key:
                logger.info(f"Normalizing JSON using key: '{found_key}'")
                df = pd.json_normalize(json_obj[found_key])
                return df
                
            # If no array found, but it's a flat dict, maybe it's a single row? 
            # But the prompt says "If top-level element is an object, attempt to find the most plausible array... or detect no table path."
            # We can treat a single dict as a 1-row DataFrame if it looks flat-ish? 
            # Let's be strict: if no array, return None (or maybe 1 row if it's flat).
            # Usually users expect a dataset. A single object is rarely a dataset.
            # But maybe we try to normalize the whole object?
            # pd.json_normalize(dict) returns a 1-row DF.
            # But we might end up with deeply nested columns.
            # Let's assume if we didn't find a list, we fail to find a "Table".
            return None
            
        else:
            return None
            
    except Exception as e:
        logger.error(f"Error normalizing JSON to DataFrame: {e}")
        return None
