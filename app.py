from flask import Flask, request, jsonify
from flask_cors import CORS
from psd_tools import PSDImage
import base64
from io import BytesIO

app = Flask(__name__)
CORS(app)

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
    data = request.get_json()
    layer_id = data.get('layer_id')
    text = data.get('text')
    # Placeholder
    return jsonify({'success': True, 'message': f'Text of layer {layer_id} updated to "{text}"'})

@app.route('/save_psd', methods=['POST'])
def save_psd():
    if 'psdFile' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400
    file = request.files['psdFile']
    # Placeholder
    try:
        buffered = BytesIO(file.read())
        b64_psd = base64.b64encode(buffered.getvalue()).decode('utf-8')
        return jsonify({'psd_base64': b64_psd})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
