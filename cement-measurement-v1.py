import streamlit as st
import cv2
import numpy as np
from datetime import datetime
from streamlit_drawable_canvas import st_canvas
import base64
import io
from PIL import Image

# Function to calculate Euclidean distance between two points
def calculate_distance(point1, point2):
    return np.sqrt((point2[0] - point1[0]) ** 2 + (point2[1] - point1[1]) ** 2)

# HTML/JavaScript for camera access with improved error handling
camera_html = """
<div>
    <p id="status">Opening camera...</p>
    <video id="video" width="100%" autoplay playsinline></video>
    <canvas id="canvas" style="display:none;"></canvas>
    <button id="capture" style="display:none; padding: 10px; margin: 10px auto; background-color: #4CAF50; color: white; border: none; border-radius: 5px;">Capture Image</button>
</div>
<script>
    const video = document.getElementById('video');
    const canvas = document.getElementById('canvas');
    const captureButton = document.getElementById('capture');
    const status = document.getElementById('status');
    let stream = null;

    // Dynamically set canvas dimensions based on video
    function setCanvasSize() {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
    }

    // Access camera
    navigator.mediaDevices.getUserMedia({ 
        video: { 
            facingMode: "environment",
            width: { ideal: 640 },
            height: { ideal: 480 }
        } 
    })
    .then(function(mediaStream) {
        stream = mediaStream;
        video.srcObject = stream;
        video.onloadedmetadata = function() {
            setCanvasSize();
            status.innerText = "Camera ready. Click below to capture.";
            captureButton.style.display = 'block';
        };
    })
    .catch(function(err) {
        console.error("Camera error: ", err);
        status.innerText = "Failed to access camera. Please allow camera permissions or upload an image. Error: " + err.message;
        video.style.display = 'none';
        captureButton.style.display = 'none';
    });

    // Capture image
    function captureImage() {
        setCanvasSize();
        canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
        const dataUrl = canvas.toDataURL('image/png');
        
        // Send image to Streamlit
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = 'captured_image';
        input.value = dataUrl;
        document.body.appendChild(input);
        
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = '';
        form.appendChild(input);
        document.body.appendChild(form);
        form.submit();
        
        // Stop camera stream
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
        }
    }

    captureButton.onclick = captureImage;
</script>
"""

# Main Streamlit app
def main():
    st.title("Smartphone Camera Measurement Tool")
    st.write("Use your smartphone camera to capture an image or upload an image, then measure the distance between two points.")

    # Initialize session state
    if 'points' not in st.session_state:
        st.session_state.points = []
    if 'distance' not in st.session_state:
        st.session_state.distance = None
    if 'frame' not in st.session_state:
        st.session_state.frame = None

    # Tabs for camera and upload
    tab1, tab2 = st.tabs(["Capture from Camera", "Upload Image"])

    with tab1:
        st.write("Allow camera permissions in your browser to see the live feed.")
        st.components.v1.html(camera_html, height=600)

        # Check for captured image
        if st.experimental_get_query_params().get("captured_image"):
            data_url = st.experimental_get_query_params()["captured_image"][0]
            img_data = base64.b64decode(data_url.split(',')[1])
            img = Image.open(io.BytesIO(img_data))
            st.session_state.frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            st.experimental_set_query_params()  # Clear query params

    with tab2:
        uploaded_file = st.file_uploader("Upload an image", type=["jpg", "png", "jpeg"])
        if uploaded_file is not None:
            file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
            st.session_state.frame = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

    # Process image if available
    if st.session_state.frame is not None:
        st.image(st.session_state.frame, channels="BGR", caption="Selected Image", use_column_width=True)

        # Automatic point detection
        st.subheader("Automatic Point Detection")
        if st.button("Detect Points Automatically"):
            # Convert to grayscale
            gray = cv2.cvtColor(st.session_state.frame, cv2.COLOR_BGR2GRAY)
            # Apply edge detection
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)
            # Detect lines using Hough Transform
            lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=100, minLineLength=100, maxLineGap=10)
            
            points = []
            if lines is not None:
                # Take the first detected line
                for line in lines[:1]:  # Limit to one line for simplicity
                    x1, y1, x2, y2 = line[0]
                    points = [(x1, y1), (x2, y2)]
                    break
            
            if len(points) == 2:
                st.session_state.points = points
                frame_copy = st.session_state.frame.copy()
                for point in points:
                    cv2.circle(frame_copy, point, 5, (0, 255, 0), -1)
                cv2.line(frame_copy, points[0], points[1], (0, 0, 255), 2)
                st.image(frame_copy, channels="BGR", caption="Detected Points", use_column_width=True)
            else:
                st.warning("Could not detect two points automatically. Please select manually.")

        # Manual point selection
        st.subheader("Manual Point Selection")
        st.write("Click on the image below to select two points (if automatic detection fails):")
        canvas_result = st_canvas(
            fill_color="rgba(0, 255, 0, 0.3)",
            stroke_width=3,
            stroke_color="rgba(0, 255, 0, 1)",
            background_image=st.session_state.frame,
            height=st.session_state.frame.shape[0],
            width=st.session_state.frame.shape[1],
            drawing_mode="point",
            key="canvas",
        )

        # Process canvas points
        if canvas_result.json_data is not None:
            points = []
            for obj in canvas_result.json_data["objects"]:
                if obj["type"] == "circle":
                    points.append((int(obj["left"]), int(obj["top"])))
            st.session_state.points = points[:2]  # Limit to 2 points

        # Calculate distance if 2 points are selected
        if len(st.session_state.points) == 2 and st.button("Calculate Distance"):
            point1, point2 = st.session_state.points
            st.session_state.distance = calculate_distance(point1, point2)

            frame_copy = st.session_state.frame.copy()
            cv2.circle(frame_copy, point1, 5, (0, 255, 0), -1)
            cv2.circle(frame_copy, point2, 5, (0, 255, 0), -1)
            cv2.line(frame_copy, point1, point2, (0, 0, 255), 2)
            mid_point = ((point1[0] + point2[0]) // 2, (point1[1] + point2[1]) // 2)
            cv2.putText(frame_copy, f"{st.session_state.distance:.2f} pixels",
                        (mid_point[0], mid_point[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            st.image(frame_copy, channels="BGR", caption="Measured Image", use_column_width=True)

    # Display and save distance
    if st.session_state.distance is not None:
        st.write(f"Measured Distance: {st.session_state.distance:.2f} pixels")
        if st.button("Save Measurement"):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            text_filename = f"measurement_{timestamp}.txt"
            with open(text_filename, "w") as f:
                f.write(f"Points: {st.session_state.points}\nDistance: {st.session_state.distance:.2f} pixels")
            image_filename = f"measurement_{timestamp}.png"
            frame_copy = st.session_state.frame.copy()
            for point in st.session_state.points:
                cv2.circle(frame_copy, point, 5, (0, 255, 0), -1)
            if len(st.session_state.points) == 2:
                cv2.line(frame_copy, st.session_state.points[0], st.session_state.points[1], (0, 0, 255), 2)
                cv2.putText(frame_copy, f"{st.session_state.distance:.2f} pixels",
                            (mid_point[0], mid_point[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.imwrite(image_filename, frame_copy)
            st.success(f"Measurement saved as {text_filename} and {image_filename}")

if __name__ == "__main__":
    main()
