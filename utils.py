import cv2
import numpy as np
import json
import os
from pyzbar.pyzbar import decode
import logging
from datetime import datetime
import shutil
import barcode
from barcode.ean import EAN13
from barcode.writer import ImageWriter

logger = logging.getLogger(__name__)

MAPPING_FILE = 'mapping.json'

def load_mapping():
    """Load the mapping file or create if it doesn't exist."""
    if os.path.exists(MAPPING_FILE):
        with open(MAPPING_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_mapping(mapping):
    """Save the mapping file."""
    with open(MAPPING_FILE, 'w') as f:
        json.dump(mapping, f, indent=2)

def cleanup_directories():
    """Clean up and recreate all necessary directories."""
    directories = ['barcodes', 'features']
    for directory in directories:
        if os.path.exists(directory):
            shutil.rmtree(directory)
        os.makedirs(directory)
        logger.info(f"Cleaned up directory: {directory}")

    # Ensure clothing directory exists
    if not os.path.exists('clothing'):
        os.makedirs('clothing')
        logger.info("Created clothing directory")

def generate_barcodes_for_clothing():
    """Generate new barcodes for all clothing images."""
    cleanup_directories()  # Clean up directories first

    # Load existing mapping or create new
    mapping = {}  # Start with empty mapping since we're regenerating everything

    clothing_dir = 'clothing'
    if not os.path.exists(clothing_dir):
        os.makedirs(clothing_dir)
        logger.info("Created clothing directory")
        save_mapping(mapping)
        return

    # Process each clothing item
    for filename in os.listdir(clothing_dir):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            clothing_path = os.path.join(clothing_dir, filename)
            try:
                # Generate barcode
                barcode_id = generate_barcode(clothing_path)

                # Extract and save features
                features = extract_features(clothing_path)
                feature_path = os.path.join('features', f"{os.path.splitext(filename)[0]}.json")
                with open(feature_path, 'w') as f:
                    json.dump(features, f)

                logger.info(f"Processed clothing item: {filename}")

                # Update mapping
                barcode_path = f"barcodes/barcode_{os.path.splitext(filename)[0]}.png"
                if os.path.exists(barcode_path):
                    mapping[barcode_id] = {
                        'clothing_path': clothing_path,
                        'barcode_path': barcode_path,
                        'feature_path': feature_path
                    }
                    save_mapping(mapping)  # Save after each successful item
            except Exception as e:
                logger.error(f"Error processing {filename}: {str(e)}")

    # Save the final mapping
    save_mapping(mapping)
    logger.info(f"Generated barcodes and features for {len(mapping)} clothing items")

def generate_barcode(clothing_path):
    """Generate a unique EAN-13 barcode for a clothing item."""
    mapping = load_mapping()
    # Generate new unique barcode based on filename
    filename = os.path.basename(clothing_path)
    # Use hash of filename to ensure consistency
    counter = abs(hash(filename)) % 999999999999
    barcode_id = f"{counter:012}"  # pad with zeros to 12 digits

    # Create EAN-13 barcode with ImageWriter for better quality
    ean = EAN13(barcode_id, writer=ImageWriter())

    # Save barcode image with clothing filename reference
    clothing_filename = os.path.splitext(os.path.basename(clothing_path))[0]
    barcode_filename = f"barcode_{clothing_filename}"
    barcode_path = os.path.join('barcodes', barcode_filename)

    # Save the barcode image
    ean.save(barcode_path)

    return barcode_id

def is_barcode_image(img_path):
    """Check if an image contains a barcode."""
    try:
        img = cv2.imread(img_path)
        if img is None:
            return False
        decoded = decode(img)
        return len(decoded) > 0
    except Exception as e:
        logger.error(f"Error checking if image is barcode: {str(e)}")
        return False

def read_barcode(barcode_input):
    """Decode barcode data from an image with enhanced preprocessing."""
    try:
        img = cv2.imread(barcode_input)
        if img is None:
            return None

        # Resize image if too large
        max_size = 1000
        height, width = img.shape[:2]
        if height > max_size or width > max_size:
            scale = max_size / max(height, width)
            img = cv2.resize(img, None, fx=scale, fy=scale)

        # Try different preprocessing techniques
        for preprocessing in ['original', 'gray', 'binary', 'adaptive']:
            if preprocessing == 'original':
                processed = img
            elif preprocessing == 'gray':
                processed = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            elif preprocessing == 'binary':
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                _, processed = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY)
            else:  # adaptive
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                processed = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

            decoded = decode(processed)
            if decoded:
                barcode_data = decoded[0].data.decode('utf-8')
                logger.info(f"Successfully decoded barcode: {barcode_data}")
                return barcode_data

        return None
    except Exception as e:
        logger.error(f"Error reading barcode: {str(e)}")
        return None

def extract_features(img_input):
    """Extract image features using color analysis."""
    try:
        img = cv2.imread(img_input)
        if img is None:
            raise ValueError("Could not read image")

        # Resize for consistency
        img = cv2.resize(img, (200, 200))

        # Convert to RGB for better color analysis
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # Reshape the image to be a list of pixels
        pixels = img.reshape((-1, 3))

        # Convert to float
        pixels = np.float32(pixels)

        # Define criteria
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.2)
        k = 5
        _, labels, centers = cv2.kmeans(pixels, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)

        # Convert back to uint8
        centers = np.uint8(centers)

        # Get the histogram of labels
        hist = np.histogram(labels, bins=range(k + 1))[0]

        # Normalize histogram
        hist = hist.astype('float')
        hist /= hist.sum()

        return hist.tolist()
    except Exception as e:
        logger.error(f"Error extracting features: {str(e)}")
        raise

def get_recommendations(query_features, query_path, n=5):
    """Find similar clothing items."""
    scores = []
    mapping = load_mapping()

    for barcode_data, item_data in mapping.items():
        if item_data['clothing_path'] != query_path:
            if 'feature_path' in item_data and os.path.exists(item_data['feature_path']):
                with open(item_data['feature_path'], 'r') as f:
                    features = json.load(f)

                # Calculate similarity score
                score = np.sum(np.square(np.array(query_features) - np.array(features)))
                scores.append((score, item_data['clothing_path']))

    # Sort by similarity score
    scores.sort(key=lambda x: x[0])

    # Return exactly N recommendations (pad with None if not enough)
    recommendations = []
    for _, path in scores[:n]:
        recommendations.append({
            'path': path,
            'url': f"/clothing/{os.path.basename(path)}"
        })

    # Pad with placeholder recommendations if needed
    while len(recommendations) < n:
        recommendations.append({
            'path': None,
            'url': None
        })

    return recommendations[:n]  # Ensure exactly N recommendations

def find_matching_clothing(barcode_data):
    """Find matching clothing item for a barcode and get recommendations."""
    mapping = load_mapping()
    matching_item = None
    
    logger.info(f"Looking for barcode: {barcode_data}")
    logger.info(f"Available barcodes: {list(mapping.keys())}")
    
    # Try exact match first
    if barcode_data in mapping:
        matching_item = mapping[barcode_data]['clothing_path']
    else:
        # Try to find partial match
        for key in mapping.keys():
            if barcode_data in key or key in barcode_data:
                matching_item = mapping[key]['clothing_path']
                break
    
    if matching_item:
        logger.info(f"Found matching item: {matching_item}")
        # Get recommendations
        features = extract_features(matching_item)
        recommendations = get_recommendations(features, matching_item, 5)
        formatted_recommendations = []
        for rec in recommendations:
            if rec['path']:  # Only add if path exists
                formatted_recommendations.append({
                    'url': f"/clothing/{os.path.basename(rec['path'])}"
                })
        
        if formatted_recommendations:
            return {'recommendations': formatted_recommendations}
        
    logger.error(f"No match or recommendations found for barcode: {barcode_data}")
    return None