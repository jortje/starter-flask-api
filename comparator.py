
from flask import Blueprint, render_template, request, jsonify
from difflib import Differ
import re

# Create a Blueprint for the comparator feature
comparator_blueprint = Blueprint('comparator', __name__)

# Function to remove special characters for indirect comparison
def clean_special_chars(line):
    return re.sub(r'[-|\\]', '', line).strip()

def extract_file_names(contents, comparison_type):
    """
    Extracts file names from the directory listing, ignoring lines that don't represent files.
    If comparison_type is 'indirect', special characters will be ignored.
    """
    file_names = []
    for line in contents:
        line = line.strip()
        if comparison_type == 'indirect':
            line = clean_special_chars(line)
        if line.endswith('.png') or line.endswith('.txt'):
            file_names.append(line)
    return file_names

@comparator_blueprint.route('/', methods=['GET'])
def comparator_index():
    return render_template('comparison.html')

@comparator_blueprint.route('/compare', methods=['POST'])
def compare_file_trees():
    data = request.get_json()
    file_tree1 = data.get('file_tree1', '').splitlines()
    file_tree2 = data.get('file_tree2', '').splitlines()
    comparison_type = data.get('comparison_type', 'direct')

    file1_names = extract_file_names(file_tree1, comparison_type)
    file2_names = extract_file_names(file_tree2, comparison_type)

    d = Differ()
    diff = list(d.compare(file1_names, file2_names))

    added = [line[2:] for line in diff if line.startswith('+ ')]
    removed = [line[2:] for line in diff if line.startswith('- ')]

    return jsonify({
        'added_to_file_tree2': added,
        'removed_from_file_tree1': removed
    })
