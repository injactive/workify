import streamlit as st
import sqlite3
import pandas as pd
import datetime
import math
import numpy as np


# Verbindung zur SQLite-Datenbank herstellen oder erstellen (falls nicht vorhanden)
conn = sqlite3.connect('arbeitszeiten.db')

# Datenbanktabelle für Projekte erstellen (falls nicht vorhanden)
conn.execute('''
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        Name TEXT,
        Cost_Id TEXT
    )
''')

# Datenbanktabelle für Arbeitszeiten erstellen (falls nicht vorhanden)
conn.execute('''
    CREATE TABLE IF NOT EXISTS work_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        Datum TEXT,
        Uhrzeit TEXT,
        Projekt_id INTEGER,
        Comment TEXT,
        FOREIGN KEY (Projekt_id) REFERENCES projects(id)
    )
''')

conn.execute('''
    CREATE TABLE IF NOT EXISTS workday_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        Datum TEXT,
        Uhrzeit TEXT,
        Status TEXT
    )
''')

# Streamlit-App-Titel
st.title("Arbeitszeiten-Verwaltung")

# Sidebar mit Seitenwechsel
page = st.sidebar.selectbox("Seiten", ["Overview", "Projekte", "Arbeitszeiten", "Statistik"])

# Funktion zum Verbinden zur Datenbank
def get_connection():
    return sqlite3.connect('arbeitszeiten.db', check_same_thread=False)

# Funktion zum Erstellen des Tabelle-Datenframes
def create_timetable_df(selected_week):
    current_year = datetime.datetime.now().year
    first_day_of_week = datetime.datetime.fromisocalendar(current_year, int(selected_week), 1)
    dates_of_week = [first_day_of_week]
    for i in range(1, 5):
        date = first_day_of_week + datetime.timedelta(days=i)
        dates_of_week.append(date)


    weekdays = ["Mo (" + dates_of_week[0].strftime("%d.%m.") + ")"]
    weekdays.append("Di (" + dates_of_week[1].strftime("%d.%m.") + ")")
    weekdays.append("Mi (" + dates_of_week[2].strftime("%d.%m.") + ")")
    weekdays.append("Do (" + dates_of_week[3].strftime("%d.%m.") + ")")
    weekdays.append("Fr (" + dates_of_week[4].strftime("%d.%m.") + ")")
    
    # Erstellen Sie eine Liste von Uhrzeiten im 30-Minuten-Takt von 07:30 bis 20:00 Uhr
    times = [datetime.datetime.strptime("07:30", "%H:%M")]
    while times[-1] < datetime.datetime.strptime("20:00", "%H:%M"):
        times.append(times[-1] + datetime.timedelta(minutes=30))

    # Erstellen Sie einen leeren DataFrame mit den Wochentagen als Spalten
    timetable_df = pd.DataFrame(columns=weekdays, index=[time.strftime("%H:%M") for time in times])    
    timetable_df = timetable_df.replace(np.nan, '', regex=True)

    # Laden Sie die Arbeitszeiten aus der Datenbank basierend auf der ausgewählten Kalenderwoche
#    with get_connection() as conn:
    query = """
        SELECT Datum, Uhrzeit, projects.Name AS Projekt
        FROM work_log
        LEFT JOIN projects ON work_log.Projekt_id = projects.id
        WHERE strftime('%W', Datum) = ?
    """
    df = pd.read_sql(query, conn, params=(selected_week,))
    print(df)
    
    english_weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

    # Füllen Sie die Tabelle mit den Arbeitszeiten
    for index, row in df.iterrows():
        date = row["Datum"]
        time = row["Uhrzeit"]
        time_str = datetime.datetime.strptime(time, '%H:%M')
        project = row["Projekt"]
        date_obj = datetime.datetime.strptime(date, '%Y-%m-%d')
        weekday = weekdays[english_weekdays.index(date_obj.strftime("%A"))]
            
        # Setzen Sie den Wert in die entsprechende Zelle
        timetable_df.loc[time_str.strftime("%H:%M"), weekday] = project
    
    query = """
        SELECT Datum, Uhrzeit, Status
        FROM workday_log
        WHERE strftime('%W', Datum) = ?
    """
    df = pd.read_sql(query, conn, params=(selected_week,))
    for index, row in df.iterrows():
        date_obj = datetime.datetime.strptime(row["Datum"], '%Y-%m-%d')
        weekday = weekdays[english_weekdays.index(date_obj.strftime("%A"))]
        tmp_time = row["Uhrzeit"]
        if int(tmp_time[3]) < 3:
            tmp_time = tmp_time[:3] + "00"
        elif int(tmp_time[3]) < 6:
            tmp_time = tmp_time[:3] + "30"
        else:
            tmp_time = tmp_time[:4] + "0"
        time_obj = datetime.datetime.strptime(tmp_time, '%H:%M')
        if row["Status"] == "Start":
            timetable_df.loc[times[times.index(time_obj) - 1].strftime("%H:%M"), weekday] = row["Uhrzeit"]
            for time in times[:times.index(time_obj) - 1]:
                timetable_df.loc[time.strftime("%H:%M"), weekday] = "/"
        if row["Status"] == "Ende":
            timetable_df.loc[times[times.index(time_obj)+1].strftime("%H:%M"), weekday] = row["Uhrzeit"]
            for time in times[times.index(time_obj)+2:]:
                timetable_df.loc[time.strftime("%H:%M"), weekday] = "/"

    return timetable_df

def cell_class(cell):
    if math.isnan(cell): # Modify this condition to check for your specific condition
        return "red-cell"
    else:
        return "green-cell"

# Seite "Tabelle"
if page == "Overview":
    st.header("Arbeitszeiten-Tabelle")

    # Dropdown-Menü zur Auswahl der Kalenderwoche
    current_week = datetime.datetime.now().strftime("%U")
    selected_week = st.selectbox("Kalenderwoche auswählen:", range(1, 53), index=int(current_week)-1)
    
    # Erstellen Sie den Tabelle-Datenframe für die ausgewählte Woche
    timetable_df = create_timetable_df(str(selected_week))
    
    # Anzeigen der Tabelle mit benutzerdefinierten Zellfarben
#    st.markdown('<style>table td {text-align: center; padding: 3px;} .red-cell {background-color: red; color: white;} .green-cell {background-color: green; color: white;} .empty-cell {background-color: white;}</style>', unsafe_allow_html=True)
#    cell_classes = [cell_class(cell) for cell in timetable_df.to_numpy().flatten()]
#    styled_df = timetable_df.style.applymap(lambda x: f"background-color: {cell_class(x)}", subset=pd.IndexSlice[:, :])
#    st.write(styled_df.to_html(escape=False, header="true"), unsafe_allow_html=True)
    st.write(timetable_df.to_html(escape=False, header="true"), unsafe_allow_html=True)


# Seite "Projekte"
if page == "Projekte":
    st.header("Projekte verwalten")

    # Eingabeformular für neue Projekte
    new_project = st.text_input("Neues Projekt hinzufügen:")
    new_cid = st.text_input("Cost_Id hinzufügen:")
    if st.button("Projekt hinzufügen"):
        with get_connection() as conn:
            conn.execute("INSERT INTO projects (Name, Cost_Id) VALUES (?, ?)", (new_project, new_cid))
            conn.commit()
        st.success("Projekt hinzugefügt!")

    # Eingabeformular zum Entfernen von Projekten
    project_names = [row[0] for row in get_connection().execute("SELECT Name FROM projects").fetchall()]
    project_to_remove = st.selectbox("Projekt zum Entfernen auswählen:", project_names)
    if st.button("Projekt entfernen"):
        with get_connection() as conn:
            conn.execute("DELETE FROM projects WHERE Name=?", (project_to_remove,))
            conn.commit()
        st.success("Projekt entfernt!")

    # Liste der aktuellen Projekte
    st.subheader("Aktuelle Projekte:")
    projects = [row[0] + ": " + row[1] for row in get_connection().execute("SELECT Name, Cost_Id FROM projects").fetchall()]


    if projects:
        st.text("\n".join(projects))

# Seite "Arbeitszeiten"
elif page == "Arbeitszeiten":
    st.header("Arbeitszeiten erfassen")

    # Dropdown-Menü zur Auswahl des Projekts
    with get_connection() as conn:
        project_names = pd.read_sql("SELECT Name FROM projects", conn)["Name"].tolist()
    selected_project = st.selectbox("Projekt auswählen:", project_names)

    # Eingabeformular für neue Arbeitszeit
    date = st.date_input("Datum:", datetime.date.today())
    time = st.time_input("Uhrzeit:")#, datetime.datetime.now().time())

    date_str = date.strftime("%d/%m/%Y")
    time_str = time.strftime("%H:%M")

    if (int(time_str[3]) != 0) and (int(time_str[3]) != 3):
        if int(time_str[3]) < 3:
            time_str = time_str[:3] + "00"
        elif int(time_str[3]) < 6:
            time_str = time_str[:3] + "30"

    time_str = time_str[:4] + "0"

    # Hinzufügen des Eintrags zur Datenbank
    if st.button("Eintrag hinzufügen"):
        with get_connection() as conn:
            cursor = conn.cursor()
            project_id = cursor.execute("SELECT id FROM projects WHERE Name=?", (selected_project,)).fetchone()
            
            if project_id is not None:
                project_id = project_id[0]
                cursor.execute("INSERT INTO work_log (Datum, Uhrzeit, Projekt_id) VALUES (?, ?, ?)", (date, time_str, project_id))
                conn.commit()
                st.success("Eintrag hinzugefügt: Am " + date_str + " um " + time_str)
            else:
                st.error("Projekt nicht gefunden.")

    st.text("\nBeginn Arbeitstag erfassen:\n")
    time_begin = st.time_input("Arbeitsbeginn:")
    time_begin_str = time_begin.strftime("%H:%M")     
    # Hinzufügen des Eintrags zur Datenbank
    if st.button("Arbeitsbeginn hinzufügen"):
        with get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("INSERT INTO workday_log (Datum, Uhrzeit, Status) VALUES (?, ?, ?)", (date, time_begin_str, "Start"))
            conn.commit()
            st.success("Arbeitsbeginn erfasst: " + time_begin_str + " Uhr")


    st.text("\nEnde Arbeitstag erfassen:\n")
    time_end = st.time_input("Arbeitsende")
    time_end_str = time_end.strftime("%H:%M")

    if st.button("Arbeitsende hinzufügen"):
        with get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("INSERT INTO workday_log (Datum, Uhrzeit, Status) VALUES (?, ?, ?)", (date, time_end_str, "Ende"))
            conn.commit()
            st.success("Arbeitsende erfasst: " + time_end_str + " Uhr")

# Seite "Statistik"
elif page == "Statistik":
    st.header("Arbeitszeit-Statistik")

    selected_week = st.selectbox("Kalenderwoche auswählen:", range(1, 53), index=int(current_week)-1)

    # Arbeitszeit-Statistik abrufen
    query = """
    SELECT projects.Name AS Projekt, SUM(work_log.Uhrzeit) AS Arbeitszeit
    FROM work_log
    JOIN projects ON work_log.Projekt_id = projects.id
    GROUP BY Projekt
    """
    statistics = pd.read_sql(query, conn)

    if not statistics.empty:
        st.bar_chart(statistics.set_index("Projekt"))

# Datenbankverbindung schließen
conn.close()
