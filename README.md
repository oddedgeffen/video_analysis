# Logo Replacement SaaS

A SaaS application that allows users to replace logos in various document formats (PDF, PPTX, Word).

## Features
- Document upload and processing
- Logo replacement in PDF, PPTX, and Word documents
- Modern React frontend
- Django REST API backend

## Setup Instructions

### Backend Setup
1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run migrations:
```bash
python manage.py migrate
```

4. Start the development server:
```bash
python manage.py runserver
```

### Frontend Setup
1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm start
```

## Development
- Backend runs on http://localhost:8000
- Frontend runs on http://localhost:3000 