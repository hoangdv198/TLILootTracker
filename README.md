# FurTorch
 FurTorch Torchlight Loot Statistics Tool (Beta)

# Archive Notice
Due to official log structure updates, the original log identification method needs to be changed. After comprehensive consideration, since Tkinter components do not support mouse transparency, future updates will use PyQt5 and adopt visual methods for loot identification. We temporarily do not recommend development based on this project, so the project is temporarily set to read-only.

The project is expected to be updated in 1-2 days.

## Build Instructions
``` 
pip install -r requirements.txt
python setup.py py2exe
```

## Code Documentation
~~Since this was originally intended only for personal use, the code isn't exactly messy, but it's definitely scattered. To prevent a future where only God knows what each section means, and to facilitate secondary development, this section was written.~~

### Global Variables
| Variable Name | Description               |
|--------------|--------------------------|
| `t` | Timestamp when map starts, used for calculating map duration |
| `show_all`| Display current map loot / total loot |
| `is_in_map`| Whether currently in a map |

### UI Component Names
| Component Name        | Description              |
|----------------------|--------------------------|
| `label_time`     | Display map duration, label       |
| `label_drop`     | Display loot, label         |
| `label_drop_all` | Display loot value in Primordial Fire Essence, label |
| `button_change`  | Toggle between current map loot / total loot display, button |

### Function Descriptions
| Function Name               | Description                                                             |
|---------------------------|------------------------------------------------------------------------|
| `parse_log_structure`| Parse log structure into JSON format (mainly AI-generated, then modified)                                       |
| `scanned_log`| Search for loot-related sections in log files, pass to parse function                                      |
| `deal_change`| Search for map enter/exit information<br>Pass to scanner_log to search for loot<br>Parse loot item types and quantities<br>Write information to array |
| `change_states`| Triggered by `button_change`, changes loot display |
| `get_price_info`| When checking prices in the exchange, automatically reads log files<br>Updates currency prices (average of top 30 sell orders) |

### Configuration File Structure
### id_table.conf 
Matches log file IDs with loot item names
```
<Item ID>[Space]<Item Name>
Example:
100200 Primordial Fire Sand
100300 Primordial Fire Essence
```

### price.json
Item price file
```json
{
    "<Item Name>":<Item Price>,
    "Primordial Fire Sand":999,
    "Primordial Fire Essence":0
}
```

If you find that a loot item does not exist in id_table.conf or there are significant price changes, please create an ISSUE or send a PUSH after making changes. Thank you.

