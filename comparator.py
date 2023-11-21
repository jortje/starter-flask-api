from flask import Blueprint, render_template_string, request, jsonify
from difflib import Differ

# Create a Blueprint for the comparator feature
comparator_blueprint = Blueprint('comparator', __name__)


def extract_file_names(contents, ignore_special_chars=False):
    """Extracts file names from the directory listing. If 'ignore_special_chars' is True,
    it ignores lines starting with special characters like '|', '\\', and '-'.
    """
    special_chars = '|\\-'
    file_names = []
    for line in contents:
        line = line.strip()
        if ignore_special_chars and any(line.startswith(char) for char in special_chars):
            # Skip lines starting with special characters
            continue
        if line.endswith('.png') or line.endswith('.txt'):
            file_names.append(line)
    return file_names
    """
    Extracts file names from the directory listing, ignoring lines that don't represent files.
    """
    file_names = []
    for line in contents:
        line = line.strip()
        if line.endswith('.png') or line.endswith('.txt'):
            file_names.append(line)
    return file_names

@comparator_blueprint.route('/', methods=['GET'])
def comparator_index():
    return render_template_string("""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>File Tree Comparator</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
<style>
    body {
        background-color: #f8f9fa;
    }
    .container {
        background-color: #fff;
        padding: 2rem;
        border-radius: .5rem;
        box-shadow: 0 .5rem 1rem rgba(0, 0, 0, .1);
        margin-top: 3rem;
    }
    textarea {
        font-family: monospace;
    }
    #results {
        white-space: pre-wrap;
        background-color: #e9ecef;
        border: 1px solid #ced4da;
        border-radius: .25rem;
        padding: 1rem;
    }
</style>
</head>
<body>
<div class="container">
    <h2 class="mb-4 text-center">File Tree Comparator</h2>
    <form id="compareForm">
        <div class="row g-3">
            <div class="col-md">
                <div class="form-floating">
                    <textarea class="form-control" id="fileTree1" placeholder="Paste the first file tree here..." style="height: 250px" required></textarea>
                    <label for="fileTree1">File Tree 1</label>
                </div>
            </div>
            <div class="col-md">
                <div class="form-floating">
                    <textarea class="form-control" id="fileTree2" placeholder="Paste the second file tree here..." style="height: 250px" required></textarea>
                    <label for="fileTree2">File Tree 2</label>
                </div>
            </div>
        </div>
        <div class="d-grid gap-2 mt-4">
            <button type="submit" class="btn btn-primary btn-lg">Compare Trees</button>
        </div>
    </form>
    <div id="results" class="mt-4"></div>
        <p class="my-4 text-center">Version 1.0.1</p>
</div>
<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
<script>
$(document).ready(function() {
    $('#compareForm').on('submit', function(e) {
        e.preventDefault();
        $('#results').html('');
        $.ajax({
            url: '/comparator/compare',  // Updated URL to match the Blueprint's prefix
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                file_tree1: $('#fileTree1').val(),
                file_tree2: $('#fileTree2').val()
            }),
            success: function(data) {
                var resultText = '<div class="fw-bold text-success">Added to File Tree 2:</div><div class="mb-3"><pre>' + data.added_to_file_tree2.join('\\n') +
                                 '</pre></div><div class="fw-bold text-danger">Removed from File Tree 1:</div><pre>' + data.removed_from_file_tree1.join('\\n') + '</pre>';
                $('#results').html(resultText);
            },
            error: function(error) {
                console.error(error);
                $('#results').html('<div class="alert alert-danger" role="alert">An error occurred.</div>');
            }
        });
    });
});
</script>
</body>
</html>
    """)

@comparator_blueprint.route('/compare', methods=['POST'])
def compare_file_trees():
    data = request.get_json()
    file_tree1 = data.get('file_tree1', '').splitlines()
    file_tree2 = data.get('file_tree2', '').splitlines()

    file1_names = extract_file_names(file_tree1)
    file2_names = extract_file_names(file_tree2)

    d = Differ()
    diff = list(d.compare(file1_names, file2_names))

    added = [line[2:] for line in diff if line.startswith('+ ')]
    removed = [line[2:] for line in diff if line.startswith('- ')]

    return jsonify({
        'added_to_file_tree2': added,
        'removed_from_file_tree1': removed
    })