# VibeDodo

A simple Flask web application with user registration and authentication.

## Features

- User registration
- User login/logout
- Authentication required pages
- Simple UI with CSS styling

## Installation

1. Clone the repository
2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Start the application:
   ```
   python run.py
   ```
2. Open your browser and navigate to http://127.0.0.1:5000/

## Project Structure

```
vibedodo/
├── app/
│   ├── models/
│   │   ├── __init__.py
│   │   └── user.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   └── main.py
│   ├── static/
│   │   └── css/
│   │       └── main.css
│   ├── templates/
│   │   ├── dashboard.html
│   │   ├── index.html
│   │   ├── layout.html
│   │   ├── login.html
│   │   └── register.html
│   ├── __init__.py
│   └── forms.py
├── README.md
├── requirements.txt
└── run.py
```

## License

MIT