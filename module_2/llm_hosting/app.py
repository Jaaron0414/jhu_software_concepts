#!/usr/bin/env python3
"""
Mini LLM Standardizer: Local language model for university and program name standardization.
Uses TinyLlama 1.1B via llama-cpp-python for fast, offline cleaning of Grad Cafe data.
"""

import json
import sys
import os
import argparse
from pathlib import Path
from difflib import SequenceMatcher
import re

try:
    from llama_cpp import Llama
except ImportError:
    Llama = None

try:
    from huggingface_hub import hf_hub_download
except ImportError:
    hf_hub_download = None

try:
    from flask import Flask, request, jsonify
except ImportError:
    Flask = None


def load_canonical_lists():
    """Load canonical university and program names."""
    base_dir = Path(__file__).parent
    
    universities = []
    programs = []
    
    unis_file = base_dir / "canon_universities.txt"
    if unis_file.exists():
        universities = [line.strip() for line in unis_file.read_text().split('\n') if line.strip()]
    
    progs_file = base_dir / "canon_programs.txt"
    if progs_file.exists():
        programs = [line.strip() for line in progs_file.read_text().split('\n') if line.strip()]
    
    return universities, programs


def fuzzy_match(text, candidates, threshold=0.6):
    """Find best matching canonical name using fuzzy matching."""
    if not text or not candidates:
        return None
    
    text = text.lower().strip()
    best_match = None
    best_score = threshold
    
    for candidate in candidates:
        score = SequenceMatcher(None, text, candidate.lower()).ratio()
        if score > best_score:
            best_score = score
            best_match = candidate
    
    return best_match


def parse_with_llm(model, entry):
    """Use LLM to standardize program and university names."""
    if not model:
        return entry
    
    program_text = entry.get('program', '') or ''
    university_text = entry.get('university', '') or ''
    
    prompt = f"""You are a data standardizer. Given program and university names from a grad school database, output standardized names.

Respond ONLY with valid JSON, no other text. Use these exact keys:
- "program": standardized program name
- "university": standardized university name

Input:
- Program: {program_text}
- University: {university_text}

JSON output:"""
    
    try:
        response = model(
            prompt,
            max_tokens=200,
            temperature=0.1,
            top_p=0.9,
            stop=["}\n"],
        )
        
        response_text = response['choices'][0]['text'].strip()
        
        # Try to parse JSON response
        if '{' in response_text:
            json_str = response_text[response_text.index('{'):]
            if '}' not in json_str:
                json_str += '}'
            result = json.loads(json_str)
            entry['llm_generated_program'] = result.get('program', program_text)
            entry['llm_generated_university'] = result.get('university', university_text)
        else:
            entry['llm_generated_program'] = program_text
            entry['llm_generated_university'] = university_text
    except Exception as e:
        print(f"LLM error: {e}", file=sys.stderr)
        entry['llm_generated_program'] = program_text
        entry['llm_generated_university'] = university_text
    
    return entry


def standardize_with_fallback(entry, universities, programs):
    """Standardize using fuzzy matching as fallback."""
    program_text = entry.get('program', '') or ''
    university_text = entry.get('university', '') or ''
    
    # Try fuzzy matching
    entry['llm_generated_program'] = fuzzy_match(program_text, programs) or program_text
    entry['llm_generated_university'] = fuzzy_match(university_text, universities) or university_text
    
    return entry


def process_file(input_file, output_mode='stdout', use_llm=True):
    """Process JSON file and standardize names."""
    print(f"Loading canonical lists...", file=sys.stderr)
    universities, programs = load_canonical_lists()
    print(f"  Universities: {len(universities)}", file=sys.stderr)
    print(f"  Programs: {len(programs)}", file=sys.stderr)
    
    model = None
    if use_llm and Llama and hf_hub_download:
        print(f"Initializing LLM model (first run may take a minute to download)...", file=sys.stderr)
        try:
            model_repo = os.getenv('MODEL_REPO', 'TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF')
            model_file = os.getenv('MODEL_FILE', 'tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf')
            n_gpu_layers = int(os.getenv('N_GPU_LAYERS', 0))
            n_ctx = int(os.getenv('N_CTX', 2048))
            
            # Download model if needed
            model_path = hf_hub_download(repo_id=model_repo, filename=model_file)
            
            # Load model
            model = Llama(
                model_path=model_path,
                n_ctx=n_ctx,
                n_gpu_layers=n_gpu_layers,
                verbose=False
            )
            print(f"LLM loaded successfully", file=sys.stderr)
        except Exception as e:
            print(f"Failed to load LLM: {e}", file=sys.stderr)
            print(f"Falling back to fuzzy matching...", file=sys.stderr)
            model = None
    elif not use_llm:
        print(f"Using fuzzy matching (LLM disabled)...", file=sys.stderr)
    else:
        print(f"LLM dependencies not available, using fuzzy matching...", file=sys.stderr)
    
    # Load and process data
    print(f"Loading data from {input_file}...", file=sys.stderr)
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        data = [data]
    
    print(f"Processing {len(data)} entries...", file=sys.stderr)
    
    processed = []
    for i, entry in enumerate(data):
        if i % 100 == 0:
            print(f"  Progress: {i}/{len(data)}", file=sys.stderr)
        
        if model:
            entry = parse_with_llm(model, entry)
        else:
            entry = standardize_with_fallback(entry, universities, programs)
        
        processed.append(entry)
    
    # Output results
    if output_mode == 'stdout':
        for entry in processed:
            print(json.dumps(entry, ensure_ascii=False))
    elif output_mode == 'jsonl':
        for entry in processed:
            print(json.dumps(entry, ensure_ascii=False))
    else:  # json
        print(json.dumps(processed, ensure_ascii=False, indent=2))
    
    print(f"Done! Processed {len(processed)} entries.", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description='LLM-based name standardizer for Grad Cafe data')
    
    # Mode selection
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument('--file', type=str, help='Input JSON file to process')
    mode_group.add_argument('--serve', action='store_true', help='Run as Flask server')
    
    # Output options
    parser.add_argument('--stdout', action='store_true', help='Output to stdout (default for --file)')
    parser.add_argument('--output', type=str, help='Output file path')
    parser.add_argument('--format', choices=['json', 'jsonl'], default='jsonl', help='Output format')
    parser.add_argument('--no-llm', action='store_true', help='Use fuzzy matching only (skip LLM)')
    
    args = parser.parse_args()
    
    if args.file:
        # CLI mode
        output_mode = 'stdout' if args.stdout else 'jsonl'
        process_file(args.file, output_mode=output_mode, use_llm=not args.no_llm)
    
    elif args.serve:
        # Flask server mode
        if not Flask:
            print("Flask not installed. Run: pip install flask")
            sys.exit(1)
        
        app = Flask(__name__)
        
        # Load LLM and canonical lists at startup
        print("Initializing server...", file=sys.stderr)
        universities, programs = load_canonical_lists()
        
        model = None
        if Llama and hf_hub_download and not args.no_llm:
            try:
                model_repo = os.getenv('MODEL_REPO', 'TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF')
                model_file = os.getenv('MODEL_FILE', 'tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf')
                n_gpu_layers = int(os.getenv('N_GPU_LAYERS', 0))
                n_ctx = int(os.getenv('N_CTX', 2048))
                
                model_path = hf_hub_download(repo_id=model_repo, filename=model_file)
                model = Llama(model_path=model_path, n_ctx=n_ctx, n_gpu_layers=n_gpu_layers, verbose=False)
            except Exception as e:
                print(f"Warning: Could not load LLM: {e}", file=sys.stderr)
        
        @app.route('/standardize', methods=['POST'])
        def standardize():
            try:
                data = request.get_json()
                if not isinstance(data, list):
                    data = [data]
                
                result = []
                for entry in data:
                    if model:
                        entry = parse_with_llm(model, entry)
                    else:
                        entry = standardize_with_fallback(entry, universities, programs)
                    result.append(entry)
                
                return jsonify(result)
            except Exception as e:
                return jsonify({'error': str(e)}), 400
        
        @app.route('/health', methods=['GET'])
        def health():
            return jsonify({'status': 'ok'})
        
        print("Starting Flask server on http://0.0.0.0:8000", file=sys.stderr)
        app.run(host='0.0.0.0', port=8000, debug=False)
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
