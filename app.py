from flask import Flask, request, jsonify
from flask_cors import CORS
from psd_tools import PSDImage
import base64
from io import BytesIO

app = Flask(__name__)
CORS(app)

# In a real application, you would need a way to manage the uploaded file.
# This simplified example re-opens the file from the request on each update,
# which is inefficient for larger files or frequent updates.

@app.route('/health')
def health_check():
    return jsonify({"status": "healthy"})

@app.route('/upload', methods=['POST'])
def upload_psd():
    if 'psdFile' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400
    file = request.files['psdFile']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file:
        try:
            img = PSDImage.open(file)
            layers_data = []
            for layer in img.descendants():
                if layer.kind == 'type':
                    layers_data.append({
                        'id': layer.layer_id,
                        'name': layer.name,
                        'text': layer.text
                    })

            preview_image = None
            try:
                composite_image = img.composite()
                buffered = BytesIO()
                composite_image.save(buffered, format="PNG")
                preview_image = base64.b64encode(buffered.getvalue()).decode('utf-8')
            except Exception as e:
                print(f"Error compositing image: {e}")

            return jsonify({'layers': layers_data, 'preview': preview_image})

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return jsonify({'error': 'Something went wrong'}), 500

@app.route('/update_text', methods=['POST'])
def update_text():
    if 'psdFile' not in request.files:
        return jsonify({'error': 'No PSD file provided for update'}), 400
    file = request.files['psdFile']
    if file.filename == '':
        return jsonify({'error': 'No PSD file selected for update'}), 400

    layer_id = request.form.get('layer_id')
    text = request.form.get('text')

    if layer_id is None or text is None:
        return jsonify({'error': 'Missing layer_id or text in request'}), 400

    try:
        img = PSDImage.open(file)
        found_layer = None
        for layer in img.descendants():
            if layer.layer_id == int(layer_id) and layer.kind == 'type':
                print(f"Found layer: {layer.name}, ID: {layer.layer_id}, Kind: {layer.kind}")
                print(f"Layer has text attribute: {'text' in dir(layer)}")
                if 'text' in dir(layer):
                    print(f"Current layer.text value: '{layer.text}'")
                try:
                    layer.text = text
                    found_layer = layer
                except Exception as e:
                    print(f"Error setting text for layer {layer.name} ({layer.layer_id}): {e}")
                    return jsonify({'success': False, 'error': f"Can't set attribute: {e}"}), 500
                break

        if found_layer:
            preview_image = None
            try:
                composite_image = img.composite()
                buffered = BytesIO()
                composite_image.save(buffered, format="PNG")
                preview_image = base64.b64encode(buffered.getvalue()).decode('utf-8')
                return jsonify({'success': True, 'message': f'Text of layer {layer_id} updated to "{text}"', 'preview': preview_image})
            except Exception as e:
                print(f"Error compositing updated image: {e}")
                return jsonify({'success': True, 'message': f'Text of layer {layer_id} updated to "{text}", but preview update failed.'})
        else:
            return jsonify({'error': f'Layer with id {layer_id} not found or is not a text layer'}), 404

    except Exception as e:
        print(f"General error in /update_text: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/save_psd', methods=['POST'])
def save_psd():
    if 'psdFile' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400
    file = request.files['psdFile']
    # Placeholder - in a real application, you would process the changes and save.
    try:
        buffered = BytesIO(file.read())
        b64_psd = base64.b64encode(buffered.getvalue()).decode('utf-8')
        return jsonify({'psd_base64': b64_psd})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
