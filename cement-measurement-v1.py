import streamlit as st
import cv2
import numpy as np
import time
import os
from datetime import datetime

# Function to calculate Euclidean distance between two points
def calculate_distance(point1, point2):
    return np.sqrt((point2[0] - point1[0]) ** 2 + (point2[1] - point1[1]) ** 2)

# Function to handle mouse clicks for selecting points
def mouse_callback(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        if len(param['points']) < 2:
            param['points'].append((x, y))
            if len(param['points']) == 2:
                param['distance'] = calculate_distance(param['points'][0], param['points'][1])

# Main Streamlit app
def main():
    st.title("Camera-Based Measurement Tool")

    # Instructions
    st.write("Click the button to start the camera. Left-click to select two points. Press 'q' to capture and exit.")

    # Button to start the camera
    if st.button("Open Camera"):
        # Initialize OpenCV video capture
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            st.error("Error: Could not open camera.")
            return

        # Create a window for OpenCV
        cv2.namedWindow("Camera Feed")
        
        # Dictionary to store points and distance
        data = {'points': [], 'distance': None}
        cv2.setMouseCallback("Camera Feed", mouse_callback, data)

        # Placeholder for displaying the image in Streamlit
        image_placeholder = st.empty()

        while True:
            ret, frame = cap.read()
            if not ret:
                st.error("Error: Could not read frame.")
                break

            # Draw selected points and line
            for point in data['points']:
                cv2.circle(frame, point, 5, (0, 255, 0), -1)
            if len(data['points']) == 2:
                cv2.line(frame, data['points'][0], data['points'][1], (0, 0, 255), 2)
                # Display distance on the frame
                mid_point = ((data['points'][0][0] + data['points'][1][0]) // 2,
                             (data['points'][0][1] + data['points'][1][1]) // 2)
                cv2.putText(frame, f"Distance: {data['distance']:.2f} pixels",
                           (mid_point[0], mid_point[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            # Convert frame to RGB for Streamlit display
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image_placeholder.image(frame_rgb, caption="Camera Feed", use_column_width=True)

            # Display distance in Streamlit if calculated
            if data['distance'] is not None:
                st.write(f"Measured Distance: {data['distance']:.2f} pixels")

            # Show frame in OpenCV window
            cv2.imshow("Camera Feed", frame)

            # Check for 'q' key to exit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                if data['distance'] is not None:
                    # Save the final frame with measurements
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"measurement_{timestamp}.png"
                    cv2.imwrite(filename, frame)
                    st.success(f"Measurement captured and saved as {filename}")
                break

        # Release resources
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
