from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from psd_tools import PSDImage
import io
from PIL import Image  # Pillow library for image manipulation

app = Flask(__name__)
CORS(app)

# In a real application, you might want to store the opened PSD
# in a session or a more persistent storage if you plan to do
# multiple edits without re-uploading. For this simple example,
# we'll re-open the file on each request.

def render_psd_preview(psd_image, size=(512, 512)):
    """A very basic function to render a flattened preview of the PSD."""
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
    if 'psdFile' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['psdFile']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file:
        try:
            psd = PSDImage.open(file)
            layers_data = []
            for i, layer in enumerate(psd.layers):
                layer_info = {
                    'id': i,  # Add a simple ID for layer identification
                    'name': layer.name,
                    'type': layer.kind,
                    'visible': layer.is_visible
                }
                if layer.kind == 'type':
                    try:
                        layer_info['text'] = layer.text
                    except AttributeError:
                        layer_info['text'] = "Could not read text"
                layers_data.append(layer_info)

            preview_io = render_psd_preview(psd)
            preview_base64 = None
            if preview_io:
                import base64
                preview_base64 = base64.b64encode(preview_io.read()).decode('utf-8')

            return jsonify({'layers': layers_data, 'preview': preview_base64})

        except Exception as e:
            return jsonify({'error': str(e)}), 500
    return jsonify({'error': 'Something went wrong'}), 500

@app.route('/update_text', methods=['POST'])
def update_text():
    data = request.get_json()
    layer_id = data.get('layer_id')
    new_text = data.get('text')
    uploaded_file = request.files.get('psdFile') # You might need to re-upload or manage state

    if uploaded_file:
        try:
            psd = PSDImage.open(uploaded_file)
            if layer_id is not None and 0 <= layer_id < len(psd.layers) and psd.layers[layer_id].kind == 'type':
                psd.layers[layer_id].text = new_text
                preview_io = render_psd_preview(psd)
                preview_base64 = None
                if preview_io:
                    import base64
                    preview_base64 = base64.b64encode(preview_io.read()).decode('utf-8')
                return jsonify({'success': True, 'preview': preview_base64})
            else:
                return jsonify({'error': 'Invalid layer ID or not a text layer'}), 400
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'error': 'PSD file not provided for update'}), 400

@app.route('/save_psd', methods=['POST'])
def save_psd():
    uploaded_file = request.files.get('psdFile') # You'll likely need to manage the modified PSD
    if uploaded_file:
        try:
            psd = PSDImage.open(uploaded_file) # Replace with your modified PSD object
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

if __name__ == '__main__':
    app.run(debug=True)
