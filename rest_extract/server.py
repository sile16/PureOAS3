import os
from flask import Flask, request, redirect, url_for, send_from_directory, flash
import rest_extract

ROOT_DIR = '/usr/share/pureswagger/html'
ALLOWED_EXTENSIONS = set(['pdf', 'json'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = ROOT_DIR
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def root():
  return send_from_directory(ROOT_DIR,"index.html")

@app.route('/<path:file>')
def get_file(file):
    return send_from_directory(ROOT_DIR,file)

@app.route('/swagify', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            if "pdf" in file.filename:
                filename = "rest.pdf"
            else:
                filename = "swagger.json"

            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if os.path.exists(filepath):
                os.remove(filepath)
            
            
            file.save(filepath)
    
            rest_extract.main()
            return redirect('/')

    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form action=/swagify method=post enctype=multipart/form-data>
      <p><input type=file name=file>
         <input type=submit value=Upload>
    </form>
    '''

@app.after_request
def add_header(r):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r


if __name__ == "__main__":
    app.run(host='0.0.0.0')