from flask import Flask, render_template, request, redirect
from macrodata import main as generate_macro_data
from comparator import comparator_blueprint  # Import the blueprint from comparator.py
import os

app = Flask(__name__)

# Register the blueprint with the main application
app.register_blueprint(comparator_blueprint, url_prefix='/comparator')

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        year = request.form.get('year')
        month = request.form.get('month') or '12'
        try:
            download_url = generate_macro_data(year, month)
            return redirect(download_url)
        except ValueError as e:
            return render_template('index.html', error=str(e))
        except Exception as e:
            return render_template('index.html', error=str(e))

    return render_template('index.html', error=None)

if __name__ == '__main__':
    app.run(debug=True)
