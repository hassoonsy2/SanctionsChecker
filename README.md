# SanctionsChecker

[a link](sanctionschecker.azurewebsites.net)


## Overview
This application allows users to search for names within a sanctions list. It's built with Flask for the backend and Bootstrap for the frontend. The application uses fuzzy matching to find and score potential matches based on the input.

## Features
- Search by name with auto-suggestion.
- Filter by entity type (person or company).
- Specify the threshold for match scoring.

## Getting Started

### Prerequisites
- Python 3.9 or higher
- Pip package manager
- Virtualenv (optional but recommended for development)

### Installation
1. Clone the repository:
   ```sh
   git clone https://github.com/your-username/sanctions-search-app.git
   cd sanctions-search-app

2. Create a virtual environment (optional):
   ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`

3. Install the requirements:
   ```sh
    pip install -r requirements.txt

  ## Usage

1. Start the Flask app:
 ```sh
     flask run
```

## Configuration
The application can be configured via environment variables. For local development, these can be set in a .env file in the root of the project directory.

## Deployment
To deploy this application on Azure Web App, follow the provided CI/CD GitHub Actions workflow, which will automatically build and deploy your application to Azure.




