#!/usr/bin/env python3
"""
Debug script to inspect Phoenix traces and understand their format.
Run this to see what data is available for evaluation.
"""

import os
import sys
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    phoenix_url = os.getenv("PHOENIX_URL", "http://localhost:6007")
    print(f"Connecting to Phoenix at: {phoenix_url}")
    print("=" * 60)

    try:
        import phoenix as px
        client = px.Client(endpoint=phoenix_url)
        print("Successfully connected to Phoenix!")
    except Exception as e:
        print(f"ERROR: Could not connect to Phoenix: {e}")
        print("\nMake sure Phoenix is running:")
        print("  docker-compose up -d")
        print("  OR")
        print("  python -c 'import phoenix as px; px.launch_app()'")
        return

    # Get spans
    print("\nFetching spans from Phoenix...")
    try:
        spans_df = client.get_spans_dataframe()
    except Exception as e:
        print(f"ERROR: Could not fetch spans: {e}")
        return

    if spans_df.empty:
        print("\nNo spans found in Phoenix!")
        print("\nTo generate traces:")
        print("1. Run the FinnIE app: make run")
        print("2. Chat with the agent (ask questions)")
        print("3. Traces will be sent to Phoenix automatically")
        return

    print(f"\nFound {len(spans_df)} spans!")
    print("\n" + "=" * 60)
    print("SPAN COLUMNS:")
    print("=" * 60)
    for col in spans_df.columns:
        print(f"  - {col}")

    print("\n" + "=" * 60)
    print("SAMPLE SPAN DATA (first span):")
    print("=" * 60)

    first_span = spans_df.iloc[0]
    for col in spans_df.columns:
        value = first_span[col]
        # Truncate long values
        str_value = str(value)
        if len(str_value) > 200:
            str_value = str_value[:200] + "..."
        print(f"\n{col}:")
        print(f"  {str_value}")

    # Check for attributes column specifically
    print("\n" + "=" * 60)
    print("ATTRIBUTES INSPECTION:")
    print("=" * 60)

    if 'attributes' in spans_df.columns:
        attrs = first_span.get('attributes', {})
        if isinstance(attrs, str):
            try:
                attrs = json.loads(attrs)
            except:
                pass

        if isinstance(attrs, dict):
            print("\nAttribute keys found:")
            for key in attrs.keys():
                value = attrs[key]
                str_value = str(value)
                if len(str_value) > 100:
                    str_value = str_value[:100] + "..."
                print(f"  - {key}: {str_value}")
        else:
            print(f"  Attributes type: {type(attrs)}")
            print(f"  Value: {attrs}")
    else:
        print("  No 'attributes' column found")

    # Look for input/output patterns
    print("\n" + "=" * 60)
    print("SEARCHING FOR INPUT/OUTPUT DATA:")
    print("=" * 60)

    input_cols = [c for c in spans_df.columns if 'input' in c.lower()]
    output_cols = [c for c in spans_df.columns if 'output' in c.lower()]

    print(f"\nInput-related columns: {input_cols}")
    print(f"Output-related columns: {output_cols}")

    # Check each span for input/output
    print("\n" + "=" * 60)
    print("SPANS WITH INPUT/OUTPUT (first 5):")
    print("=" * 60)

    count = 0
    for idx, row in spans_df.iterrows():
        if count >= 5:
            break

        # Try to extract input/output
        attrs = row.get('attributes', {})
        if isinstance(attrs, str):
            try:
                attrs = json.loads(attrs)
            except:
                attrs = {}

        input_val = None
        output_val = None

        # Try different paths
        if isinstance(attrs, dict):
            input_val = (
                attrs.get('input.value') or
                attrs.get('input') or
                attrs.get('openinference.span.input') or
                None
            )
            output_val = (
                attrs.get('output.value') or
                attrs.get('output') or
                attrs.get('openinference.span.output') or
                None
            )

        # Also check direct columns
        for col in input_cols:
            if input_val is None and row.get(col):
                input_val = row.get(col)
        for col in output_cols:
            if output_val is None and row.get(col):
                output_val = row.get(col)

        if input_val or output_val:
            count += 1
            print(f"\nSpan {idx}:")
            print(f"  Name: {row.get('name', 'N/A')}")
            if input_val:
                str_input = str(input_val)[:100] + "..." if len(str(input_val)) > 100 else str(input_val)
                print(f"  Input: {str_input}")
            if output_val:
                str_output = str(output_val)[:100] + "..." if len(str(output_val)) > 100 else str(output_val)
                print(f"  Output: {str_output}")

    if count == 0:
        print("\nNo spans with input/output found!")
        print("\nThe spans might have a different format. Check the attribute keys above.")

    print("\n" + "=" * 60)
    print("RECOMMENDATION:")
    print("=" * 60)
    print("""
If you see spans but no input/output:
1. Check the attribute key names shown above
2. The evaluation runner may need to be updated to match your trace format

If you see no spans:
1. Make sure Phoenix is running: docker-compose up -d
2. Use the FinnIE chat interface to generate some traces
3. Run this script again
""")


if __name__ == "__main__":
    main()
