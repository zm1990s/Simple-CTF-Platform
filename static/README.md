# Static Files Directory

This directory contains static files for the CTF platform.

## Current Files
- `style.css` - Custom CSS styles
- `logo_placeholder.txt` - Instructions for adding logo

## Adding Files
Place your static files here:
- Images: logo.png, banner.jpg, etc.
- JavaScript files (if needed)
- Additional CSS files (if needed)
- Fonts (if needed)

## Usage in Templates
Reference static files in templates:
```html
<link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
<img src="{{ url_for('static', filename='logo.png') }}" alt="Logo">
<script src="{{ url_for('static', filename='script.js') }}"></script>
```

## Uploaded Files
User-uploaded files (submissions, challenge images) are stored in the `uploads/` directory, not here.
