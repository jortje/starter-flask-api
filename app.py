from flask import Flask, render_template, request, send_file, after_this_request
from macrodata import main as generate_macro_data
import os
import tempfile

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        year = request.form.get('year')
        month = request.form.get('month') or '12'
        try:
            # Generate the file and store it in a temporary directory
            file_path = generate_macro_data(year, month)

            @after_this_request
            def remove_file(response):
                try:
                    os.remove(file_path)
                except Exception as error:
                    app.logger.error("Error removing downloaded file handle", error)
                return response

            return send_file(file_path, as_attachment=True)
        except ValueError as e:
            return render_template('index.html', error=str(e))
        except Exception as e:
            return render_template('index.html', error="An error occurred while generating the file."), 500

    return render_template('index.html', error=None)

if __name__ == '__main__':
    app.run(debug=True)
