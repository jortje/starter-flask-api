from flask import Flask, render_template, request, send_file
from macrodata import main as generate_macro_data
import os
import traceback  # Import the traceback module

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        year = request.form.get('year')
        month = request.form.get('month') or '12'
        try:
            file_path = generate_macro_data(year, month)
            return send_file(file_path, as_attachment=True)
        except ValueError as e:
            return render_template('index.html', error=str(e))
        except Exception as e:
            # Capture the full traceback
            error_info = traceback.format_exc()
            # Log the detailed error message
            print(f"An error occurred: {error_info}")  # This will print the full traceback
            # Return the error message to the user
            return render_template('index.html', error="An error occurred while generating the file. Please check the server logs for more details.")
    return render_template('index.html', error=None)

if __name__ == '__main__':
    app.run(debug=True)
