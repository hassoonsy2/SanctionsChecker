from flask import Flask, request, jsonify, render_template, send_from_directory, flash, session
import pandas as pd
from fuzzywuzzy import fuzz, process
import os
import uuid



app = Flask(__name__, template_folder='templates')
app.secret_key = 'your_secret_key'

# Load initial sanctions data
SANCTIONS_FILE_PATH = '20231027 Consolidated Sanctions List v1.1.csv'
def load_sanctions():
    df = pd.read_csv(SANCTIONS_FILE_PATH, sep=';', low_memory=False)
    persons = process_sanctions(df, 'P')
    enterprises = process_sanctions(df, 'E')
    return persons, enterprises

def process_sanctions(df, subject_type):
    sanctions = df.loc[df['Entity_SubjectType'] == subject_type]
    columns = ['NameAlias_WholeName', 'NameAlias_FirstName', 'NameAlias_MiddleName', 'NameAlias_LastName']
    sanctions = sanctions[columns]
    sanctions = sanctions.sort_values(by=['NameAlias_WholeName'])
    sanctions = sanctions.dropna(subset=['NameAlias_WholeName'])
    return sanctions['NameAlias_WholeName'].tolist()  # Return list of names for easier processing later


PERSONS, ENTERPRISES = load_sanctions()

def find_matches(name, data_list, threshold):
    return [match for match in process.extract(name, data_list, scorer=fuzz.WRatio) if match[1] >= threshold]

@app.route('/')
def index():
    return render_template('search.html')
@app.route('/health')
def health_check():
    return 'OK', 200
@app.route('/search', methods=['POST'])
def search():
    try:
        data = request.get_json()
        names = data['names']
        entity_type = data['type']
        threshold = int(data['threshold'])
        results = []

        for name in names:
            if entity_type.lower() == 'person':
                matches = find_matches(name, PERSONS, threshold)
            elif entity_type.lower() == 'enterprise':
                matches = find_matches(name, ENTERPRISES, threshold)
            else:
                matches = []

            results.append({'name': name, 'matches': matches})

        return jsonify(results)
    except KeyError as e:
        return jsonify({'error': f'Missing parameter: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@app.route('/upload', methods=['POST'])
def upload_and_process():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ['.csv', '.xls', '.xlsx']:
        return jsonify({'error': 'Invalid file format'}), 400

    upload_dir = 'uploads'
    os.makedirs(upload_dir, exist_ok=True)

    temp_filename = f"temp_{uuid.uuid4().hex}{file_ext}"
    filepath = os.path.join(upload_dir, temp_filename)
    file.save(filepath)

    session['uploaded_file'] = filepath
    df = read_file(filepath, file_ext)
    if df is None:
        return jsonify({'error': 'Failed to process the file'}), 500

    return jsonify({'message': 'File uploaded successfully', 'columns': df.columns.tolist()})


def read_file(filepath, file_ext):
    try:
        if file_ext == '.csv':
            return pd.read_csv(filepath)
        elif file_ext in ['.xls', '.xlsx']:
            return pd.read_excel(filepath)
    except Exception as e:
        print(f"Error reading the file: {e}")
        return None

@app.route('/process', methods=['POST'])
def process_file():
    data = request.get_json()
    file_path = session.get('uploaded_file')

    if not file_path or not os.path.exists(file_path):
        app.logger.error("File not found in session or missing on disk.")
        return jsonify({'error': 'File not found. Please upload again.'}), 404

    # Read the Excel file, assuming the extension check and file read are correct
    try:
        df = pd.read_excel(file_path)  # Adjust based on actual file format handling
    except Exception as e:
        app.logger.error(f"Failed to read the file: {str(e)}")
        return jsonify({'error': 'Failed to read the file'}), 500

    # Data processing
    try:
        name_column = data['nameColumn']
        entity_type = data['type'].lower()
        threshold = int(data['threshold'])
        data_list = PERSONS if entity_type == 'person' else ENTERPRISES

        df['Matched'] = 'No'
        df['Matched Name'] = ''
        for index, row in df.iterrows():
            print(index)
            if pd.notna(row[name_column]):
                matches = find_matches(row[name_column], data_list, threshold)
                if matches:
                    df.at[index, 'Matched'] = 'Yes'
                    df.at[index, 'Matched Name'] = matches[0][0]
    except KeyError as e:
        app.logger.error(f"Data processing error: {str(e)}")
        return jsonify({'error': f'Missing data parameter: {e}'}), 400

    # Save to Excel
    output_filename = f"output_{uuid.uuid4().hex}.xlsx"
    output_filepath = os.path.join(app.root_path, 'downloads', output_filename)
    os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
    df.to_excel(output_filepath, index=False)

    return send_excel_file(output_filepath, output_filename)

def send_excel_file(path, filename):
    """Send the Excel file with appropriate headers."""
    try:
        response = send_from_directory(os.path.dirname(path), filename, as_attachment=True)
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'
        app.logger.debug(f'Sending file {filename} with MIME type {response.headers["Content-Type"]}')
        return response
    except Exception as e:
        app.logger.error(f"Error sending file: {str(e)}")
        return jsonify({'error': 'Error sending file'}), 500

if __name__ == "__main__":
    app.run(debug=True)
