import streamlit as st
import sqlite3
import pandas as pd
import datetime
import numpy as np

pd.options.mode.copy_on_write = True

# CONSTANTS
PATH_TO_DB = 'workinghours.db'

# FUNCTIONS


def get_connection(path_to_db: str) -> sqlite3.Connection:
    '''
    Connection to database PATH_TO_DB
    
    Parameters
    -----------
    path_to_db : str
        string gives the path to the database

    Returns
    -------
    sqlite.Connection
        connection to sqllite database 
    '''
    return sqlite3.connect(path_to_db, check_same_thread=False)


def create_timetable_df(selected_week: int, path_to_db: str) -> pd.DataFrame:
    '''
    Creates the timetable of the desired week
    
    Parameters
    -----------
    selected_week : int
        week number of the desired week

    Returns
    -------
    pd.DataFrame
        consists of all projects hourwise 
    ''' 

    current_year = datetime.datetime.now().year
    selected_week = int(selected_week)
    first_day_of_week = datetime.datetime.fromisocalendar(current_year, selected_week, 1)
    dates_of_week = [first_day_of_week + datetime.timedelta(days=i) for i in range(5)]

    weekdays = [f"{date.strftime('%a (%d.%m.)')}" for date in dates_of_week]
    
    # Create a list of times in 30-minute increments from 7:30 a.m. to 8:00 p.m
    times = [datetime.datetime.strptime("07:30", "%H:%M")]
    while times[-1] < datetime.datetime.strptime("20:00", "%H:%M"):
        times.append(times[-1] + datetime.timedelta(minutes=30))

    # Create an empty DataFrame with the days of the week as columns
    timetable_df = pd.DataFrame(columns=weekdays, index=[time.strftime("%H:%M") for time in times])
    timetable_df = timetable_df.replace(np.nan, '', regex=True)

    # Load working hours from the database based on the selected calendar week
    query = """
        SELECT date, time, comment, projects.name AS Projekt
        FROM work_log
        LEFT JOIN projects ON work_log.projekt_id = projects.id
    """
    with get_connection(path_to_db) as conn:
        df = pd.read_sql(query, conn)

    df["week"] = 0    
    for ix, row in df.iterrows():
        df.loc[ix, "week"] = datetime.datetime.strptime(row["date"], "%Y-%m-%d").isocalendar().week

    df = df[df["week"] == selected_week].reset_index()
    
    english_weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

    # Fill DataFrame with working hours
    for index, row in df.iterrows():
        date = row["date"]
        time = row["time"]
        time_str = datetime.datetime.strptime(time, '%H:%M')
        project = row["Projekt"]
        date_obj = datetime.datetime.strptime(date, '%Y-%m-%d')
        weekday = weekdays[english_weekdays.index(date_obj.strftime("%A"))]
            
        # Setzen Sie den Wert in die entsprechende Zelle
        cell_input = project
        if row["comment"] is not None:
            cell_input += ": "
            cell_input += row["comment"]
        timetable_df.loc[time_str.strftime("%H:%M"), weekday] = cell_input
    
    query = """
        SELECT date, time, status
        FROM workday_log
        WHERE strftime('%W', date) = ?
    """
    with get_connection(path_to_db) as conn:
        df = pd.read_sql(query, conn, params=(selected_week,))

    for _, row in df.iterrows():
        date_obj = datetime.datetime.strptime(row["date"], '%Y-%m-%d')
        weekday = weekdays[english_weekdays.index(date_obj.strftime("%A"))]
        tmp_time = row["time"]
        if int(tmp_time[3]) < 3:
            tmp_time = tmp_time[:3] + "00"
        elif int(tmp_time[3]) < 6:
            tmp_time = tmp_time[:3] + "30"
        else:
            tmp_time = tmp_time[:4] + "0"
        time_obj = datetime.datetime.strptime(tmp_time, '%H:%M')
        if row["status"] == "Start":
            timetable_df.loc[times[times.index(time_obj) - 1].strftime("%H:%M"), weekday] = row["time"]
            for time in times[:times.index(time_obj) - 1]:
                timetable_df.loc[time.strftime("%H:%M"), weekday] = "/"
        if row["status"] == "Ende":
            timetable_df.loc[times[times.index(time_obj)+1].strftime("%H:%M"), weekday] = row["time"]
            for time in times[times.index(time_obj)+2:]:
                timetable_df.loc[time.strftime("%H:%M"), weekday] = "/"

    return timetable_df

def check_db_connection(path_to_db: str) -> None:
    '''
    Checks existence of SQL database. If no existence, create a DB
    
    Parameters
    -----------
    path_to_db : str
        string gives the path to the database
    ''' 

    with get_connection(path_to_db) as conn:

        # SQL table "projects" for name and cost-id
        conn.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                cost_id TEXT
            )
        ''')

        # SQL table "work_log" for connecting time and work
        conn.execute('''
            CREATE TABLE IF NOT EXISTS work_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                time TEXT,
                projekt_id INTEGER,
                comment TEXT,
                FOREIGN KEY (projekt_id) REFERENCES projects(id)
            )
        ''')

        # SQL table "workday_log" to log start and end of day
        conn.execute('''
            CREATE TABLE IF NOT EXISTS workday_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                time TEXT,
                status TEXT
            )
        ''')


check_db_connection(PATH_TO_DB)

# Define Streamlit App
st.title("Worktime Management")

page = st.sidebar.selectbox(
    "Pages", 
    [
        "Overview", 
        "Projects", 
        "Working Time", 
        "Statistics"
    ]
)

if page == "Overview":
    """
    Page gives an overview about the inserted working hours of a week
    """

    st.header("Workinghour table")

    # Select number of week, current week is default
    current_week = datetime.datetime.now().strftime("%U")
    selected_week = st.selectbox("Select Week Number:", range(1, 53), index=int(current_week)-1)
    
    # Create and display desired workinghour tabel from SQL DB
    timetable_df = create_timetable_df(str(selected_week), PATH_TO_DB)
    st.write(timetable_df.to_html(escape=False, header="true"), unsafe_allow_html=True)

if page == "Projects":
    """
    Page gives an overview about the inserted projects
    """

    st.header("Manage Projects")

    # Insert project informations
    new_project = st.text_input("Add new project:")
    new_cid = st.text_input("Add corresponding:")
    if st.button("Submit new project"):
        with get_connection(PATH_TO_DB) as conn:
            conn.execute("INSERT INTO projects (name, cost_id) VALUES (?, ?)", (new_project, new_cid))
            conn.commit()
        st.success("Project submitted!")

    # List of all projects
    st.subheader("Aktuelle Projekte:")
    projects = [row[0] + ": " + row[1] for row in get_connection(PATH_TO_DB).execute("SELECT name, cost_id FROM projects").fetchall()]
    if projects:
        st.text("\n".join(projects))

elif page == "Working Time":
    """
    Record working time with the corresponding projects
    """

    st.header("Insert Working Time")

    # Record date and time
    date = st.date_input("date:", datetime.date.today())
    date_str = date.strftime("%d/%m/%Y")
    time = st.time_input("time:")
    time_str = time.strftime("%H:%M")

    # Select corresponding project
    with get_connection(PATH_TO_DB) as conn:
        project_names = pd.read_sql("SELECT name FROM projects", conn)["name"].tolist()
    selected_project = st.selectbox("Projekt auswählen:", project_names)

    comment = st.text_input("Add a comment:")

    st.text("Choose Action:")
    if st.button("Record Working Time and Project"):

        # Round time
        minutes = time.minute
        if minutes <= 20:
            rounded_minutes = 0
        elif minutes <= 50:
            rounded_minutes = 30
        else:
            rounded_minutes = 0
            time = time.replace(hour=time.hour + 1)

        time = time.replace(minute=rounded_minutes)
        time_str = time.strftime("%H:%M")

        with get_connection(PATH_TO_DB) as conn:
            cursor = conn.cursor()
            project_id = cursor.execute("SELECT id FROM projects WHERE name=?", (selected_project,)).fetchone()
            
            if project_id is not None:
                project_id = project_id[0]
                cursor.execute("INSERT INTO work_log (date, time, projekt_id, comment) VALUES (?, ?, ?, ?)", (date, time_str, project_id, comment))
                conn.commit()
                st.success("Eintrag hinzugefügt: Am " + date_str + " um " + time_str)
            else:
                st.error("Projekt nicht gefunden.")

    if st.button("Record Start of Working Day"):
        time_str = time.strftime("%H:%M")
        with get_connection(PATH_TO_DB) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO workday_log (date, time, status) VALUES (?, ?, ?)", (date, time_str, "Start"))
            conn.commit()
            st.success("Start of Working Day recorded: " + time_str)

    if st.button("Record End of Working Day"):
        time_str = time.strftime("%H:%M")
        with get_connection(PATH_TO_DB) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO workday_log (date, time, status) VALUES (?, ?, ?)", (date, time_str, "Ende"))
            conn.commit()
            st.success("End of Working Day recorded: " + time_str)

# Seite "Statistik"
elif page == "Statistics":
    st.header("Worktime Statistics")
    current_month = datetime.datetime.now().strftime("%m")

    selected_month = st.selectbox("Choose Calender No.:", range(1, 13), index=int(current_month)-1)

    # Arbeitszeit-Statistik abrufen
    query = """
    SELECT date, projects.name AS Projekt
    FROM work_log
    JOIN projects ON work_log.projekt_id = projects.id
    """
    with get_connection(PATH_TO_DB) as conn:
        df = pd.read_sql(query, conn)

    df["month"] = 0    
    for ix, row in df.iterrows():
        df.loc[ix, "month"] = datetime.datetime.strptime(row["date"], "%Y-%m-%d").month

    df = df[df["month"] == selected_month].reset_index()
    
    total_number = df.shape[0]
    project_list = np.unique(df["Projekt"].values).tolist()
#    project_list.remove()
    statistics = pd.DataFrame(index = project_list , columns = ["Zeit"])

    for project in project_list:
        statistics.loc[project, "Zeit"] = df[df["Projekt"] == project]["Projekt"].count()*100/total_number

    if not statistics.empty:
        st.bar_chart(statistics)
