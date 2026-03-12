import json
import urllib.request
import urllib.error

def check_authorization(res_id, name):
    """
    Checks if a given RES-ID and Name match a row in the specific Google Sheet.
    Returns: bool (True if authorized, False otherwise)
    """
    if not res_id or not name:
        return False
        
    res_id_clean = str(res_id).strip().lower()
    name_clean = str(name).strip().lower()

    # Public Google Sheet link (Anyone with the link can view)
    # The Sheet is expected to have 'RES ID' in column A, 'Name' in column B
    SHEET_ID = "1FTY5vfhuB8zjVhMFkmM5u_Uo-Hsi0zox_nqFn482r10"
    # Using gviz endpoint to get JSON representation
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:json"

    try:
        # Create a request object with a standard User-Agent to avoid blocking
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        
        # Set a timeout so we don't freeze the app if internet is down
        with urllib.request.urlopen(req, timeout=5) as response:
            data = response.read().decode('utf-8')
            
            # The gviz response is wrapped in a prefix and suffix
            # e.g., /*O_o*/ google.visualization.Query.setResponse({"version":"0.6"...});
            prefix = 'google.visualization.Query.setResponse('
            start = data.find(prefix)
            if start != -1:
                start += len(prefix)
                end = data.rfind(');')
                if end != -1:
                    json_str = data[start:end]
                    json_data = json.loads(json_str)
                    
                    # Parse the rows
                    # Google visualizing JSON structure:
                    # table -> rows -> list of c (cells) -> v (value)
                    if 'table' in json_data and 'rows' in json_data['table']:
                        for row in json_data['table']['rows']:
                            if not row or 'c' not in row or not row['c']:
                                continue
                                
                            # Assuming RES ID is col 0, Name is col 1
                            cells = row['c']
                            if len(cells) >= 2 and cells[0] and cells[1]:
                                row_res_id = str(cells[0].get('v', '')).strip().lower()
                                row_name = str(cells[1].get('v', '')).strip().lower()
                                
                                if row_res_id == res_id_clean and row_name == name_clean:
                                    return True
    except urllib.error.URLError:
        pass # Handle timeout or no internet gracefully, default to False
    except Exception:
        pass # Catch potential parsing or other errors, default to False
        
    return False
