# My Flask App

This is a simple Flask application that demonstrates the structure and setup of a Flask project.

This project is an anti-spoofing face recognition system. The main idea is to detect faces, manage and store attendance records. The best feature is the ability to detect real versus fake faces. If a real face is detected, it matches the actual user's face and then stores their attendance.

Video link - [Add your video link here]
Presentation - [Add your presentation link here]

## Project Structure

```
.
├── app/
│   ├── static/
│   │   ├── images/               # Static assets like images
│   ├── templates/                # HTML templates
│   ├── __init__.py               # App initialization
│   ├── extensions.py             # Extensions for the app
│   ├── models.py                 # Database models
│   ├── routes.py                 # Application routes
├── faces/                        # Directory for storing face images
├── migrations/                   # Database migrations
├── instance/
│   ├── database.db               # SQLite database file
├── requirements.txt              # Python dependencies
├── run.py                        # Application entry point
├── Dockerfile                    # Docker configuration
├── docker-compose.yml            # Docker Compose setup
├── README.md                     # Project documentation
```

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/nikh27/anti_spof.git
   cd anti-spoof-face-reco
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   ```

3. Activate the virtual environment:
   - On Windows:
     ```
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```
     source venv/bin/activate
     ```

4. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

If you face issues downloading the face_recognition dlib file, I provide a precompiled version for Windows users: `dlib-19.24.1-cp311-cp311-win_amd64.whl`. Install this first to avoid dependencies issues.

Additionally, I have set up Docker for this project.

For better FPS, you can install CUDA to achieve the best performance.

## Configuration

Edit the `config.py` file to set up your configuration settings, such as database connection details and secret keys.

## Running the Application

To run the application, execute the following command:
```
python run.py
```

The application will be available at `http://127.0.0.1:5000/`.

## Usage

Visit the home page to see the application in action. You can modify the routes and models as needed to fit your requirements.

## License

This project is licensed under the MIT License.

Email: niikhilpandey.dev@gmail.com
GitHub: [nikh27](https://github.com/nikh27)