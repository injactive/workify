# workify

This is a simple and efficient time tracking application that allows you to record and manage working hours for various projects. The application is built using Streamlit and an SQLite database, providing an intuitive user interface for time tracking and project management.

## Features

- **Project Management**: Create, edit, and delete projects you're working on.
- **Time Tracking**: Record work hours, specifying the start and end times, and associate them with the respective project.
- **Clear Statistics**: Visualize your work hours by project and month to gain insights into your productivity.
- **Daily View**: A tabular view displaying your daily work hours for each day in a specific week.
- **User-Friendly**: The user interface is designed to make time tracking as straightforward as possible.

## Getting Started

### Prerequisites

- Python 3.6 or higher
- Pip (Python package manager)

### Installation

1. Clone this repository to your local machine:

   ```
   git clone https://github.com/injactive/workify.git
   cd workify
   ```


2. Install the required Python packages:

   ```
   pip install -r requirements.txt
   ```

### Getting Started

1. Start the Streamlit application:

   ```
   streamlit run main.py
   ```

2. Open your web browser and navigate to http://localhost:8501 to access the application.

### Usage
* Create projects in the application to associate work hours with specific tasks.
* Record your work hours by selecting a project, specifying the start and end times, and saving the data.
* View your work hours by project and month in the statistics section.
* Use the daily view to see a detailed breakdown of your work hours for each day in a selected week.

### Technology Stack
* Streamlit: For developing the user interface.
* SQLite: For storing project and time tracking data.
* Python: The programming language for application logic.