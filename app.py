from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from psd_tools import PSDImage  # Keep the import for now
import io
from PIL import Image
import base64

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "https://testerofps.netlify.app"}})

def render_psd_preview(psd_image, size=(512, 512)):
    try:
        image = psd_image.composite()
        img_io = io.BytesIO()
        resized_image = image.resize(size)
        resized_image.save(img_io, 'PNG')
        img_io.seek(0)
        return img_io
    except Exception as e:
        print(f"Error rendering preview: {e}")
        return None

@app.route('/upload', methods=['POST'])
def upload_psd():
    # Simplified response for testing connectivity
    return jsonify({'status': 'success', 'message': 'Upload endpoint reached'})

@app.route('/update_text', methods=['POST'])
def update_text():
    data = request.get_json()
    layer_id = data.get('layer_id')
    new_text = data.get('text')
    uploaded_file = request.files.get('psdFile')

    if uploaded_file:
        try:
            psd = PSDImage.open(uploaded_file)
            found_layer = None
            text_layer_index = 0
            found_text_layer_count = 0
            for i, layer in enumerate(psd):
                if not layer.is_group() and layer.kind == 'type':
                    if found_text_layer_count == int(layer_id):
                        found_layer = layer
                        text_layer_index = i
                        break
                    found_text_layer_count += 1

            if found_layer:
                try:
                    found_layer.text = new_text
                    return jsonify({'success': True, 'message': 'Text updated'})
                except Exception as inner_e:
                    return jsonify({'error': f'Error during text update: {inner_e}'}), 500
            else:
                return jsonify({'error': 'Invalid text layer ID'}), 400
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'error': 'PSD file not provided for update'}), 400

@app.route('/save_psd', methods=['POST'])
def save_psd():
    uploaded_file = request.files.get('psdFile')
    if uploaded_file:
        try:
            psd = PSDImage.open(uploaded_file)
            buffer = io.BytesIO()
            psd.save(buffer)
            buffer.seek(0)
            return send_file(
                buffer,
                mimetype='image/vnd.adobe.photoshop',
                as_attachment=True,
                download_name='edited.psd'
            )
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'error': 'No PSD file to save'}), 400

@app.route('/health')
def health_check():
    return jsonify({'status': 'OK', 'message': 'Backend is healthy'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
