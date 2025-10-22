"""
Step 8: Extract Stock Mentions

Analyzes filtered transcription to identify stocks discussed by Pradip Halder,
including stock names, NSE/BSE symbols, and timestamps.

Uses OpenAI GPT-4o to extract:
- Stock names that Pradip analyzed
- Actual NSE/BSE stock symbols
- Start time when Pradip first commented on each stock

Input: 
  - analysis/detected_speakers.txt (from Step 6)
  - transcripts/filtered_transcription.txt (from Step 7)
Output: 
  - analysis/extracted_stocks.csv
"""

import os
from openai import OpenAI


def run(job_folder):
    """
    Extract stocks mentioned by Pradip with symbols and timestamps
    
    Args:
        job_folder: Path to job directory
        
    Returns:
        dict: Status, message, and output files
    """
    print("\n" + "="*60)
    print("STEP 8: Extract Stock Mentions")
    print(f"{'='*60}\n")

    try:
        # Input/Output paths
        detected_speakers_file = os.path.join(job_folder, "analysis", "detected_speakers.txt")
        filtered_transcript_file = os.path.join(job_folder, "transcripts", "filtered_transcription.txt")
        output_csv = os.path.join(job_folder, "analysis", "extracted_stocks.csv")
        
        # Verify input files exist
        if not os.path.exists(detected_speakers_file):
            return {
                'status': 'failed',
                'message': f'Detected speakers file not found: {detected_speakers_file}'
            }
        
        if not os.path.exists(filtered_transcript_file):
            return {
                'status': 'failed',
                'message': f'Filtered transcript file not found: {filtered_transcript_file}'
            }
        
        # Step 1: Load detected speakers
        print("📖 Reading detected speakers...")
        with open(detected_speakers_file, 'r', encoding='utf-8') as f:
            detected_lines = f.read().strip().splitlines()
        
        # Parse speaker mapping
        anchor_speaker = detected_lines[0].split(":")[1].strip()
        pradip_speaker = detected_lines[1].split(":")[1].strip()
        
        print(f"✅ Speaker Mapping:")
        print(f"   Anchor = {anchor_speaker}")
        print(f"   Pradip = {pradip_speaker}\n")
        
        # Step 2: Load filtered transcript
        print("📖 Reading filtered transcription...")
        with open(filtered_transcript_file, 'r', encoding='utf-8') as f:
            transcript_content = f.read()
        
        transcript_lines = transcript_content.strip().splitlines()
        print(f"✅ Loaded {len(transcript_lines)} lines of filtered transcript\n")
        
        # Step 3: Get OpenAI API key from database
        print("🔑 Retrieving OpenAI API key from database...")
        
        # Use direct psycopg2 connection like in step06
        import psycopg2
        
        try:
            conn = psycopg2.connect(os.environ['DATABASE_URL'])
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT key_value FROM api_keys 
                WHERE LOWER(provider) = 'openai' 
                LIMIT 1
            """)
            
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if not result:
                return {
                    'status': 'failed',
                    'message': 'OpenAI API key not found in database. Please add it in API Keys settings.'
                }
            
            openai_api_key = result[0]
            print("✅ OpenAI API key retrieved\n")
        
        except Exception as e:
            return {
                'status': 'failed',
                'message': f'Failed to fetch OpenAI API key: {str(e)}'
            }
        
        # Step 4: Create OpenAI client
        client = OpenAI(api_key=openai_api_key)
        
        # Step 5: Build GPT prompt
        print("🤖 Preparing GPT prompt for stock extraction...")
        
        prompt = f"""You are analyzing a transcript between a TV Anchor ({anchor_speaker})
and stock expert Mr. Pradip Halder ({pradip_speaker}).

Task:
- Identify all STOCK NAMES or COMPANY NAMES discussed by ({pradip_speaker}) Pradip and put it in STOCK NAME column.
- For all STOCK NAMES find out NSE/BSE STOCK SYMBOL and put it in STOCK SYMBOL column. For some companies, stock name and symbol name are different, so give me the actual Symbol (Very Very Important).
- Capture the START TIME from the transcript line where ({pradip_speaker}) Pradip first comments on each stock & put in START TIME column.

Return strictly as CSV with header:
STOCK NAME,STOCK SYMBOL,START TIME

No duplicates. Only those STOCKS on which ({pradip_speaker}) has given his analysis.

Transcript:
{transcript_content}
"""
        
        # Step 6: Call OpenAI GPT-4o
        print("🚀 Calling OpenAI GPT-4o for stock extraction...\n")
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system", 
                    "content": "You are a financial transcript analyzer. Extract stock names with actual NSE/BSE symbols and timestamps in CSV format."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            temperature=0.3
        )
        
        # Step 7: Extract CSV content
        csv_content = response.choices[0].message.content.strip()
        
        # Remove markdown code blocks if present
        if csv_content.startswith("```"):
            lines = csv_content.split('\n')
            csv_content = '\n'.join([line for line in lines if not line.startswith('```')])
            csv_content = csv_content.strip()
        
        print("✅ GPT-4o Response (Stock Extraction):")
        print("-" * 60)
        print(csv_content[:500] + "..." if len(csv_content) > 500 else csv_content)
        print("-" * 60)
        print()
        
        # Step 8: Save to CSV file
        print(f"💾 Saving extracted stocks to: {output_csv}")
        
        # Ensure analysis directory exists
        os.makedirs(os.path.dirname(output_csv), exist_ok=True)
        
        with open(output_csv, 'w', encoding='utf-8') as f:
            f.write(csv_content)
        
        # Count extracted stocks (excluding header)
        stock_count = len(csv_content.strip().splitlines()) - 1
        
        print(f"✅ Extracted {stock_count} stocks")
        print(f"✅ Saved to: analysis/extracted_stocks.csv\n")
        
        return {
            'status': 'success',
            'message': f'Extracted {stock_count} stocks from Pradip\'s analysis',
            'output_files': ['analysis/extracted_stocks.csv']
        }
    
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'status': 'failed',
            'message': f'Stock extraction failed: {str(e)}'
        }


if __name__ == "__main__":
    # Test the step
    import sys
    if len(sys.argv) > 1:
        test_folder = sys.argv[1]
    else:
        test_folder = "backend/job_files/test_job"
    
    result = run(test_folder)
    print(f"\n{'='*60}")
    print(f"Result: {result['status'].upper()}")
    print(f"Message: {result['message']}")
    if 'output_files' in result:
        print(f"Output Files: {result['output_files']}")
    print(f"{'='*60}")
