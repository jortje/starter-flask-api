from flask import Flask, render_template, request, redirect
import os
import boto3
from macrodata import main as generate_macro_data, S3_BUCKET

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        year = request.form.get('year')
        month = request.form.get('month') or '12'
        try:
            file_path = generate_macro_data(year, month)
            # Generate a presigned URL for the S3 object
            s3_client = boto3.client('s3')
            presigned_url = s3_client.generate_presigned_url('get_object',
                                                             Params={'Bucket': S3_BUCKET,
                                                                     'Key': file_path},
                                                             ExpiresIn=3600)
            return redirect(presigned_url)
        except ValueError as e:
            return render_template('index.html', error=str(e))
        except Exception as e:
            return render_template('index.html', error=str(e))

    return render_template('index.html', error=None)

if __name__ == '__main__':
    app.run(debug=True)
