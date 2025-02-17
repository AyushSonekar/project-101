import os
import logging
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import utils
import directories

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
PORT = int(os.environ.get("PORT", 5000))

# Configure upload settings
UPLOAD_FOLDER = 'clothing'  # Changed from 'uploads' to 'clothing'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create required directories
directories.create_directories()

# Generate barcodes for existing clothing items on startup
utils.generate_barcodes_for_clothing()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/clothing/<path:filename>')
def serve_clothing(filename):
    return send_from_directory('clothing', filename)

@app.route('/upload_clothing', methods=['POST'])
def upload_clothing():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Check if the uploaded file is a barcode
        if utils.is_barcode_image(filepath):
            os.remove(filepath)  # Clean up the uploaded file
            return jsonify({'error': 'Please upload a clothing image, not a barcode'}), 400

        # Extract features and get recommendations
        try:
            features = utils.extract_features(filepath)
            recommendations = utils.get_recommendations(features, filepath, 5)  # Ensure exactly 5 recommendations
            return jsonify({
                'success': True,
                'recommendations': recommendations
            })
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            return jsonify({'error': 'Error processing image'}), 400

    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/upload_barcode', methods=['POST'])
def upload_barcode():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        try:
            # Create uploads directory if it doesn't exist
            if not os.path.exists('uploads'):
                os.makedirs('uploads')
                
            filename = secure_filename(file.filename)
            filepath = os.path.join('uploads', filename)
            file.save(filepath)

            # Process barcode
            barcode_data = utils.read_barcode(filepath)
            if barcode_data:
                logger.debug(f"Found barcode data: {barcode_data}")
                result = utils.find_matching_clothing(barcode_data)
                if result:
                    if os.path.exists(filepath):
                        os.remove(filepath)  # Clean up uploaded file
                    return jsonify({
                        'success': True,
                        'recommendations': result['recommendations']
                    })

            if os.path.exists(filepath):
                os.remove(filepath)  # Clean up if no match found
            return jsonify({'error': 'Invalid or unrecognized barcode'}), 400
        except Exception as e:
            logger.error(f"Error processing barcode: {str(e)}")
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({'error': 'Error processing barcode'}), 400

    return jsonify({'error': 'Invalid file type'}), 400