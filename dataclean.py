import os
import math
import string
import csv
from collections import Counter

# Import the appropriate library for your PCB file format (replace 'pcbnew' if needed)
import pcbnew


def calculate_entropy(data):
    """
    Calculates Shannon entropy of the given data.

    Args:
        data (bytes): The data to calculate entropy for.

    Returns:
        float: The calculated entropy value.
    """
    counter = Counter(data)  # Count occurrences of each byte
    # Calculate probabilities
    probs = [count / len(data) for count in counter.values()]
    # Shannon entropy formula
    return -sum(p * math.log2(p) for p in probs if p > 0)


def unscramble_data(data, key_length=None):
    """
    Attempts to unscramble data using common techniques.

    Args:
        data (bytes): The data to unscramble.
        key_length (int, optional): Key length for XOR decryption (if known).

    Returns:
        bytes: The unscrambled data (or original data if unscrambling fails).
    """

    # Try simple rotations/shifts (brute-force)
    for shift in range(256):  # Try all possible shifts
        shifted_data = bytes(
            [(byte + shift) % 256 for byte in data])  # Apply shift
        # Heuristic threshold for "readable" data
        if calculate_entropy(shifted_data) < 7.0:
            return shifted_data

    # Try XOR with common keys (brute-force)
    common_keys = [0x00, 0xFF, 0x55, 0xAA]  # Add more as needed
    for key in common_keys:
        xored_data = bytes([byte ^ key for byte in data])  # Apply XOR
        if calculate_entropy(xored_data) < 7.0:
            return xored_data

    # If key_length is provided, attempt XOR with repeating key
    if key_length:
        key = data[:key_length]  # Extract key from the beginning
        # Apply XOR with repeating key
        xored_data = bytes([data[i] ^ key[i % key_length]
                           for i in range(len(data))])
        if calculate_entropy(xored_data) < 7.0:
            return xored_data

    return data  # Return original data if no successful unscrambling


def scrub_entropy_and_output_csv_from_pcb(pcb_file_path, output_csv_path, key_length=None):
    """
    Scrubs entropy from a .pcb file, extracts readable data, and outputs to a CSV file.

    Args:
        pcb_file_path (str): Path to the .pcb file.
        output_csv_path (str): Path to the output CSV file.
        key_length (int, optional): Key length for XOR decryption (if known).
    """

    try:
        # Load the PCB file
        board = pcbnew.LoadBoard(pcb_file_path)

        # Extract relevant data from the PCB (adapt this to your needs)
        data_to_process = ""
        for item in board.GetFootprints():  # Iterate through footprints (components)
            data_to_process += item.GetReference() + " " + item.GetValue() + \
                "\n"  # Extract reference and value
        for track in board.GetTracks():  # Iterate through tracks (traces)
            data_to_process += track.GetNetname() + "\n"  # Extract net name
        # ... extract other relevant text data as needed

        # Attempt to unscramble the data
        unscrambled_data = unscramble_data(
            data_to_process.encode(), key_length)

        # Calculate entropy
        entropy = calculate_entropy(unscrambled_data)

        # Extract printable characters
        readable_data = "".join(filter(lambda x: chr(
            x) in string.printable, unscrambled_data))

        # Find memory locations of readable characters
        memory_locations = [hex(id(unscrambled_data) + i)
                            for i, char in enumerate(unscrambled_data) if chr(char) in string.printable]

        # Write to CSV
        with open(output_csv_path, "w", newline="") as csvfile:
            fieldnames = ["Memory Location", "Character"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for location, value in zip(memory_locations, readable_data):
                writer.writerow(
                    {"Memory Location": location, "Character": value})

        print(f"Entropy: {entropy}")
        print(f"CSV output saved to: {output_csv_path}")

    except Exception as e:
        print(f"An error occurred: {e}")


# Example usage
pcb_file_path = "path/to/your/pcb/file.pcb"
output_csv_path = "output.csv"
key_length = None  # Set this if you know the XOR key length
scrub_entropy_and_output_csv_from_pcb(
    pcb_file_path, output_csv_path, key_length)
