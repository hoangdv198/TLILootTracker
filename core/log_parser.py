"""
Log Parser Module
=================

Mục đích:
    Module này chứa các utility functions để parse và xử lý file log của game.
    Chuyển đổi cấu trúc log từ text format sang nested dictionary để dễ dàng xử lý.

Tác dụng:
    - Parse structured log text thành nested dictionary
    - Tìm và extract các drop item blocks từ log
    - Chuyển đổi log format để các module khác có thể xử lý

Các function chính:
    - convert_from_log_structure(): Chuyển đổi log text thành dict structure
    - log_to_json(): Wrapper function để convert log
    - scanned_log(): Tìm và extract các drop blocks từ log text
"""
import re


def convert_from_log_structure(log_text: str, verbose: bool = False):
    """
    Convert structured log text to nested dictionary

    Parameters:
        log_text: Text containing structured logs
        verbose: Whether to output detailed log information

    Returns:
        Converted nested dictionary
    """
    # Split and filter empty lines
    lines = [line.strip() for line in log_text.split('\n') if line.strip()]
    stack  = []
    root = {}

    if verbose:
        print("=== Starting parsing ===")

    for line in lines:
        # Calculate level (number of '|')
        level = line.count('|')
        # Extract content (remove all '|' and trim)
        content = re.sub(r'\|+', '', line).strip()

        if verbose:
            print(f"\nProcessing: '{line}'")
            print(f"  Level: {level}, Content: '{content}'")

        # Adjust stack to match current level
        while len(stack) > level:
            stack.pop()

        # Determine parent node
        if not stack:
            parent = root
        else:
            parent = stack[-1]

        # Skip empty parent nodes
        if parent is None:
            continue

        # Parse key-value pairs (including [] cases)
        if '[' in content and ']' in content:
            # Extract key part and value part
            key_part = content[:content.index('[')].strip()
            value_part = content[content.index('[') + 1: content.rindex(']')].strip()

            # Convert value type
            if value_part.lower() == 'true':
                value = True
            elif value_part.lower() == 'false':
                value = False
            elif re.match(r'^-?\d+$', value_part):
                value = int(value_part)
            else:
                value = value_part

            # Process multi-level keys (separated by '+')
            keys = [k.strip() for k in key_part.split('+') if k.strip()]

            current_node = parent

            for i in range(len(keys)):
                key = keys[i]
                # Skip empty keys
                if not key:
                    continue

                # Check if current node is valid
                if current_node is None:
                    continue

                if i == len(keys) - 1:
                    # Last key, set value
                    current_node[key] = value
                else:
                    # Not the last key, ensure it's a dict and create child node
                    if not isinstance(current_node, dict):
                        break

                    if key not in current_node:
                        current_node[key] = {}
                    current_node = current_node[key]

                    # Check if new node is valid
                    if current_node is None:
                        break

            # Add current node to stack
            stack.append(current_node)

        # Handle keys without values (e.g., +SpecialInfo)
        else:
            key_part = content.strip()
            keys = [k.strip() for k in key_part.split('+') if k.strip()]

            current_node = parent

            for key in keys:
                # Skip empty keys
                if not key:
                    continue

                # Check if current node is valid
                if current_node is None:
                    continue

                # Ensure current node is a dictionary
                if not isinstance(current_node, dict):
                    break

                # Create child node (if it doesn't exist)
                if key not in current_node:
                    current_node[key] = {}
                current_node = current_node[key]

                # Check if new node is valid
                if current_node is None:
                    break

            # Add current node to stack
            stack.append(current_node)

    if verbose:
        print("\n=== Parsing completed ===")

    return root


def log_to_json(log_text):
    """Convert log text to JSON string"""
    parsed_data = convert_from_log_structure(log_text)
    #return json.dumps(parsed_data, indent=4, ensure_ascii=False)
    return parsed_data


def scanned_log(changed_text):
    """
    Scan log text for drop item blocks
    
    Returns:
        List of drop blocks as strings
    """
    lines = changed_text.split('\n')
    drop_blocks = []
    i = 0
    line_count = len(lines)

    while i < line_count:
        line = lines[i]
        # Match start marker: +DropItems+1+ (case-sensitive matching)
        if re.search(r'\+DropItems\+1\+', line):
            # Initialize current block, including start line
            current_block = [line]
            j = i + 1

            # Collect subsequent lines until end marker is encountered
            while j < line_count:
                current_line = lines[j]

                # When encountering a line containing "Display:", end current block (include this line)
                if 'Display:' in current_line:
                    current_block.append(current_line)
                    j += 1
                    break

                # Collect all related lines (including child lines and sibling lines)
                current_block.append(current_line)
                j += 1

            # Join all lines of current block with newline and add to result list
            drop_blocks.append('\n'.join(current_block))
            # Move index to next line after current block ends
            i = j
        else:
            # Start marker not found, continue checking next line
            i += 1
    return drop_blocks

