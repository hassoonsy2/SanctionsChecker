from flask import Flask, request, jsonify, render_template
import pandas as pd
from fuzzywuzzy import fuzz, process

app = Flask(__name__, template_folder='templates')
print(app.template_folder)


# File path and data loading
SANCTIONS_FILE_PATH = '20231027 Consolidated Sanctions List v1.1.csv'
def process_sanctions(df, subject_type):
    sanctions = df.loc[df['Entity_SubjectType'] == subject_type]
    columns = ['NameAlias_WholeName', 'NameAlias_FirstName', 'NameAlias_MiddleName', 'NameAlias_LastName']
    sanctions = sanctions[columns]
    sanctions = sanctions.sort_values(by=['NameAlias_WholeName'])
    sanctions = sanctions.dropna(subset=['NameAlias_WholeName'])
    return sanctions['NameAlias_WholeName'].tolist()  # Return list of names for easier processing later

def load_sanctions():
    df = pd.read_csv(SANCTIONS_FILE_PATH, sep=';', low_memory=False)
    sanctions_persons = process_sanctions(df, 'P')  # Assuming 'P' stands for Persons
    sanctions_enterprise = process_sanctions(df, 'E')  # Assuming 'E' stands for Enterprises
    return sanctions_persons, sanctions_enterprise

# Load data once to improve performance
PERSONS, ENTERPRISES = load_sanctions()

def find_matches(name, data_list, threshold):
    print(process.extract(name, data_list, scorer=fuzz.partial_ratio))
    return [match for match in process.extract(name, data_list, scorer=fuzz.WRatio) if match[1] >= threshold]

@app.route('/')
def index():
    return render_template('search.html')

@app.route('/search', methods=['POST'])
def search():
    names = request.form['names'].split(',')
    entity_type = request.form['type']
    threshold = int(request.form['threshold'])
    results = []

    for name in names:
        if entity_type.lower() == 'person':
            print(threshold)
            matches = find_matches(name, PERSONS, threshold)
        elif entity_type.lower() == 'enterprise':
            matches = find_matches(name, ENTERPRISES, threshold)
        else:
            matches = []
        results.append({'name': name, 'matches': matches})
        print(results)

    return jsonify(results)

if __name__ == "__main__":
    app.run(debug=True)
