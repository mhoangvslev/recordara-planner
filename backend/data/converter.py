#!/usr/bin/env python3
"""
CSV to XLSX and XLSX to CSV converter with semicolon separator support.
Also supports merging two CSV files that share common columns.

This utility converts between CSV and XLSX formats, using semicolon (;) as the separator.
It preserves the data structure and handles encoding properly.

Usage:
    python converter.py <input_file> [output_file]
    python converter.py --merge <csv_file1> <csv_file2> [output_file]
    
Examples:
    # Convert CSV to XLSX (output file will be auto-generated)
    python converter.py data.csv
    
    # Convert CSV to XLSX with custom output name
    python converter.py data.csv data.xlsx
    
    # Convert XLSX to CSV
    python converter.py data.xlsx data.csv
    
    # Merge two CSV files (auto-detect common columns)
    python converter.py --merge file1.csv file2.csv
    
    # Merge two CSV files with custom output name
    python converter.py --merge file1.csv file2.csv merged_output.csv
    
    # Merge with specific merge type
    python converter.py --merge file1.csv file2.csv --merge-type inner
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Optional, List

import pandas as pd


def convert_csv_to_xlsx(csv_file: str, xlsx_file: Optional[str] = None) -> str:
    """
    Convert CSV file to XLSX format using semicolon separator.
    
    Args:
        csv_file: Path to input CSV file
        xlsx_file: Path to output XLSX file (optional, auto-generated if not provided)
    
    Returns:
        Path to the created XLSX file
    """
    if xlsx_file is None:
        # Generate output filename by replacing .csv with .xlsx
        xlsx_file = csv_file.rsplit('.', 1)[0] + '.xlsx'
    
    try:
        # Read CSV with semicolon separator
        df = pd.read_csv(csv_file, sep=';', encoding='utf-8')
        
        # Write to XLSX
        df.to_excel(xlsx_file, index=False, engine='openpyxl')
        
        print(f"✅ Successfully converted {csv_file} to {xlsx_file}")
        return xlsx_file
        
    except Exception as e:
        print(f"❌ Error converting CSV to XLSX: {e}")
        sys.exit(1)


def convert_xlsx_to_csv(xlsx_file: str, csv_file: Optional[str] = None) -> str:
    """
    Convert XLSX file to CSV format using semicolon separator.
    
    Args:
        xlsx_file: Path to input XLSX file
        csv_file: Path to output CSV file (optional, auto-generated if not provided)
    
    Returns:
        Path to the created CSV file
    """
    if csv_file is None:
        # Generate output filename by replacing .xlsx with .csv
        csv_file = xlsx_file.rsplit('.', 1)[0] + '.csv'
    
    try:
        # Read XLSX file
        df = pd.read_excel(xlsx_file, engine='openpyxl')
        
        # Write to CSV with semicolon separator
        df.to_csv(csv_file, sep=';', index=False, encoding='utf-8')
        
        print(f"✅ Successfully converted {xlsx_file} to {csv_file}")
        return csv_file
        
    except Exception as e:
        print(f"❌ Error converting XLSX to CSV: {e}")
        sys.exit(1)


def merge_csv_files(csv_file1: str, csv_file2: str, output_file: Optional[str] = None, 
                   merge_type: str = 'outer', on_columns: Optional[List[str]] = None) -> str:
    """
    Merge two CSV files that share common columns.
    
    Args:
        csv_file1: Path to first CSV file
        csv_file2: Path to second CSV file
        output_file: Path to output merged CSV file (optional, auto-generated if not provided)
        merge_type: Type of merge ('outer', 'inner', 'left', 'right')
        on_columns: List of column names to merge on (optional, auto-detected if not provided)
    
    Returns:
        Path to the created merged CSV file
    """
    if output_file is None:
        # Generate output filename
        base1 = Path(csv_file1).stem
        base2 = Path(csv_file2).stem
        output_file = f"{base1}_merged_{base2}.csv"
    
    try:
        # Auto-detect separator and read both CSV files
        # Try comma first, then semicolon
        try:
            df1 = pd.read_csv(csv_file1, sep=',', encoding='utf-8')
            df2 = pd.read_csv(csv_file2, sep=',', encoding='utf-8')
            separator = ','
        except:
            df1 = pd.read_csv(csv_file1, sep=';', encoding='utf-8')
            df2 = pd.read_csv(csv_file2, sep=';', encoding='utf-8')
            separator = ';'
        
        print(f"📊 First file: {csv_file1} ({len(df1)} rows, {len(df1.columns)} columns)")
        print(f"📊 Second file: {csv_file2} ({len(df2)} rows, {len(df2.columns)} columns)")
        
        # Find common columns if not specified
        if on_columns is None:
            common_columns = list(set(df1.columns) & set(df2.columns))
            if not common_columns:
                print("❌ Error: No common columns found between the two CSV files")
                print(f"   Columns in {csv_file1}: {list(df1.columns)}")
                print(f"   Columns in {csv_file2}: {list(df2.columns)}")
                sys.exit(1)
            
            print(f"🔗 Common columns found: {common_columns}")
            
            # Use the first common column as the merge key (or ask user to specify)
            if len(common_columns) == 1:
                on_columns = common_columns
                print(f"   Using '{common_columns[0]}' as merge key")
            else:
                # For multiple common columns, use all of them
                on_columns = common_columns
                print(f"   Using all common columns as merge keys: {on_columns}")
        
        # Perform the merge
        merged_df = pd.merge(df1, df2, on=on_columns, how=merge_type, suffixes=('_1', '_2'))
        
        # Write merged data to CSV with detected separator
        merged_df.to_csv(output_file, sep=separator, index=False, encoding='utf-8')
        
        print(f"✅ Successfully merged files into {output_file}")
        print(f"📊 Merged result: {len(merged_df)} rows, {len(merged_df.columns)} columns")
        
        # Show merge statistics
        print(f"📈 Merge statistics:")
        print(f"   - Merge type: {merge_type}")
        print(f"   - Merge keys: {on_columns}")
        print(f"   - Rows from file 1: {len(df1)}")
        print(f"   - Rows from file 2: {len(df2)}")
        print(f"   - Rows in merged result: {len(merged_df)}")
        
        return output_file
        
    except Exception as e:
        print(f"❌ Error merging CSV files: {e}")
        sys.exit(1)


def get_file_extension(filename: str) -> str:
    """Get file extension in lowercase."""
    return Path(filename).suffix.lower()


def main():
    """Main function to handle command line arguments and perform conversion."""
    parser = argparse.ArgumentParser(
        description="Convert between CSV and XLSX formats with semicolon separator, or merge CSV files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Conversion examples:
  %(prog)s data.csv                    # Convert CSV to XLSX (auto-named)
  %(prog)s data.csv output.xlsx        # Convert CSV to XLSX (custom name)
  %(prog)s data.xlsx                   # Convert XLSX to CSV (auto-named)
  %(prog)s data.xlsx output.csv        # Convert XLSX to CSV (custom name)
  
  # Merge examples:
  %(prog)s --merge file1.csv file2.csv                    # Merge CSV files (auto-named)
  %(prog)s --merge file1.csv file2.csv merged.csv         # Merge CSV files (custom name)
  %(prog)s --merge file1.csv file2.csv --merge-type inner # Merge with inner join
        """
    )
    
    # Add merge option
    parser.add_argument(
        '--merge',
        nargs=2,
        metavar=('CSV_FILE1', 'CSV_FILE2'),
        help='Merge two CSV files that share common columns'
    )
    
    # Add input file (only used in conversion mode)
    parser.add_argument(
        'input_file',
        nargs='?',
        help='Input file (CSV or XLSX) for conversion mode'
    )
    
    parser.add_argument(
        'output_file',
        nargs='?',
        help='Output file (optional, auto-generated if not provided)'
    )
    
    parser.add_argument(
        '--merge-type',
        choices=['outer', 'inner', 'left', 'right'],
        default='outer',
        help='Type of merge to perform (default: outer)'
    )
    
    parser.add_argument(
        '--on-columns',
        nargs='+',
        help='Specific columns to merge on (auto-detected if not provided)'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='CSV/XLSX Converter 2.0.0'
    )
    
    args = parser.parse_args()
    
    # Handle merge mode
    if args.merge:
        csv_file1, csv_file2 = args.merge
        
        # Validate input files exist
        if not os.path.exists(csv_file1):
            print(f"❌ Error: First CSV file '{csv_file1}' does not exist")
            sys.exit(1)
        if not os.path.exists(csv_file2):
            print(f"❌ Error: Second CSV file '{csv_file2}' does not exist")
            sys.exit(1)
        
        # Validate both files are CSV
        if get_file_extension(csv_file1) != '.csv':
            print(f"❌ Error: First file '{csv_file1}' is not a CSV file")
            sys.exit(1)
        if get_file_extension(csv_file2) != '.csv':
            print(f"❌ Error: Second file '{csv_file2}' is not a CSV file")
            sys.exit(1)
        
        # Perform merge
        merge_csv_files(csv_file1, csv_file2, args.output_file, args.merge_type, args.on_columns)
        
    # Handle conversion mode
    else:
        if not args.input_file:
            print("❌ Error: Input file is required for conversion mode")
            print("   Use --merge to merge CSV files or provide an input file for conversion")
            sys.exit(1)
        
        # Validate input file exists
        if not os.path.exists(args.input_file):
            print(f"❌ Error: Input file '{args.input_file}' does not exist")
            sys.exit(1)
        
        # Get file extension
        input_ext = get_file_extension(args.input_file)
        
        # Determine conversion type and perform conversion
        if input_ext == '.csv':
            if args.output_file and get_file_extension(args.output_file) != '.xlsx':
                print("⚠️  Warning: Converting CSV to XLSX, but output file doesn't have .xlsx extension")
            convert_csv_to_xlsx(args.input_file, args.output_file)
            
        elif input_ext == '.xlsx':
            if args.output_file and get_file_extension(args.output_file) != '.csv':
                print("⚠️  Warning: Converting XLSX to CSV, but output file doesn't have .csv extension")
            convert_xlsx_to_csv(args.input_file, args.output_file)
            
        else:
            print(f"❌ Error: Unsupported file format '{input_ext}'. Only .csv and .xlsx files are supported")
            sys.exit(1)


if __name__ == '__main__':
    main()
