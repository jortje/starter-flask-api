from flask import Flask, render_template, request, send_file
from macrodata import main as generate_macro_data
from io import BytesIO  # Import BytesIO to handle byte streams
import traceback  # Import traceback to capture errors

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        year = request.form.get('year')
        month = request.form.get('month') or '12'
        try:
            byte_io = generate_macro_data(year, month)
            return send_file(file_path, as_attachment=True, download_name='MacroData.xlsx')
        except ValueError as e:
            return render_template('index.html', error=str(e))
        except Exception as e:
            # Capture the full traceback
            error_info = traceback.format_exc()
            # Display the detailed error message to the user
            return render_template('index.html', error=f"An error occurred while generating the file: {error_info}")

    return render_template('index.html', error=None)

if __name__ == '__main__':
    app.run(debug=True)
