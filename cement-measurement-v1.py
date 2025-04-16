import streamlit as st
import cv2
import numpy as np
from datetime import datetime
from streamlit_drawable_canvas import st_canvas

# Function to calculate Euclidean distance between two points
def calculate_distance(point1, point2):
    return np.sqrt((point2[0] - point1[0]) ** 2 + (point2[1] - point1[1]) ** 2)

# Main Streamlit app
def main():
    st.title("Image-Based Measurement Tool")
    st.write("Upload an image, click two points on the canvas to measure the distance between them.")

    # Initialize session state
    if 'points' not in st.session_state:
        st.session_state.points = []
    if 'distance' not in st.session_state:
        st.session_state.distance = None
    if 'frame' not in st.session_state:
        st.session_state.frame = None

    # Image upload
    uploaded_file = st.file_uploader("Upload an image", type=["jpg", "png", "jpeg"])
    if uploaded_file is not None:
        # Read the uploaded image
        file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
        st.session_state.frame = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        st.image(st.session_state.frame, channels="BGR", caption="Uploaded Image", use_column_width=True)

        # Interactive canvas for point selection
        st.write("Click on the image below to select two points:")
        canvas_result = st_canvas(
            fill_color="rgba(0, 255, 0, 0.3)",  # Green points
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

            # Draw points and line on the image
            frame_copy = st.session_state.frame.copy()
            cv2.circle(frame_copy, point1, 5, (0, 255, 0), -1)
            cv2.circle(frame_copy, point2, 5, (0, 255, 0), -1)
            cv2.line(frame_copy, point1, point2, (0, 0, 255), 2)
            mid_point = ((point1[0] + point2[0]) // 2, (point1[1] + point2[1]) // 2)
            cv2.putText(frame_copy, f"{st.session_state.distance:.2f} pixels",
                        (mid_point[0], mid_point[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            st.image(frame_copy, channels="BGR", caption="Measured Image", use_column_width=True)

    # Display distance if calculated
    if st.session_state.distance is not None:
        st.write(f"Measured Distance: {st.session_state.distance:.2f} pixels")
        if st.button("Save Measurement"):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            # Save text file
            text_filename = f"measurement_{timestamp}.txt"
            with open(text_filename, "w") as f:
                f.write(f"Points: {st.session_state.points}\nDistance: {st.session_state.distance:.2f} pixels")
            # Save image
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
