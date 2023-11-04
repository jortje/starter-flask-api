from flask import Flask, render_template, request, send_file
from macrodata import main as generate_macro_data
import os

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
            # Log the error message for debugging purposes
            print(f"An error occurred: {e}")  # or use logging
            return render_template('index.html', error="An error occurred while generating the file.")
    return render_template('index.html', error=None)

if __name__ == '__main__':
    app.run(debug=True)
