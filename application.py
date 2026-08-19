'''
A Program to load data relating to a specfic drivers race from the ground effect era (2022 - 2025)
Compares how the tires they are on and how long they have been on those tires affects their laptime
Written by Thomas McCaw as a Case Study for MUR Motorsports (Unimelb Formula Student Team)
Development Begin: 17/08/2026
Development Finish: 
'''

# Importing Libraries
import streamlit as st
import fastf1
from fastf1 import plotting
import plotly.graph_objects as go


# -------------------------------------------------------------------------------------------------
# LOADING DATA INTO CACHE
# -------------------------------------------------------------------------------------------------
# - - - Loading the list of the racing for a specific season - - -
@st.cache_data
def loadRaces(year):

    # Creating array to store the names of the races
    loadSeasonRaces = []
    # Getting the event scheduale for the whole year (includes practise, qualy etc...)
    scheduale = fastf1.get_event_schedule(year)
    # Appending just the names of the races
    for index, row in scheduale.iterrows():
        if (row["EventName"] != "Pre-Season Testing"):
            loadSeasonRaces.append(row["EventName"])

    # Outputting the array of races in selected season
    return loadSeasonRaces

# - - - Loading the results from the selected race - - -
@st.cache_data
def loadRace(year, race):

    # Choosing the specific session to load
    session = fastf1.get_session(year, race, "R")
    # Loading the specific section
    session.load()

    # Outputting the array with session data
    return session

# - - - Loading the drivers for the selected race - - -
@st.cache_data
def loadDrivers(year, race):

    # Loading the list of drivers for the selected race
    drivers = loadRace(year, race).results["FullName"].dropna().tolist()

    # Outputting the array of drivers
    return drivers


# -------------------------------------------------------------------------------------------------
# CREATING GRAPHICS
# -------------------------------------------------------------------------------------------------



# -------------------------------------------------------------------------------------------------
# SESSION STATES
# -------------------------------------------------------------------------------------------------
# Page status
if "page" not in st.session_state:
    st.session_state.page = "raceSelection"
# Year status
if "selectedYear" not in st.session_state:
    st.session_state.selectedYear = None
# Race status
if "selectedRace" not in st.session_state:
    st.session_state.selectedRace = None
# Driver status
if "selectedDriver" not in st.session_state:
    st.session_state.selectedDriver = None
# Lap status
if "selectedLap" not in st.session_state:
    st.session_state.selectedLap = None


# -------------------------------------------------------------------------------------------------
# PAGE SELECTION AND DISPLAY
# -------------------------------------------------------------------------------------------------
# - - - Race Selection Page - - -
if st.session_state.page == "raceSelection":
    # Selecting Year
    year = st.selectbox(
        "Select a season",
        range(2022, 2026)
    )

    # Headings
    st.title("Formula 1 Race Analysis")
    st.subheader(f"{year} Season")

    # Loading the racing of the season
    seasonRaces = loadRaces(year)

    # Creating buttons corresponding to each race of the year
    for race in seasonRaces:
        if st.button(race, key = race):
            # Changing selected race and year
            st.session_state.selectedRace = race
            st.session_state.selectedYear = year

            # Going to corresponding page
            st.session_state.page = "analysisSelection"

            st.rerun()

# - - - Analysis Selection Page - - -
elif st.session_state.page == "analysisSelection":
    # Headings
    st.title(f"{st.session_state.selectedYear} {st.session_state.selectedRace}")
    st.subheader("What would you like to analyse")

    col1, col2 = st.columns(2)

    # Driver Analysis
    with col1:
        if st.button("Driver Analysis"):
            st.session_state.page = "driverSelection"
            st.rerun()

    # Laps Analysis
    with col2:
        if st.button("Lap Analysis"):
            st.session_state.page = "lapAnalysis"
            st.rerun()

    # Back Button
    if st.button("Back to Race Selection"):
        st.session_state.page = "raceSelection"
        st.rerun()

# - - - Driver Analysis Page - - -
elif st.session_state.page == "driverSelection":
    # Headings
    st.title(f"{st.session_state.selectedYear} {st.session_state.selectedRace}")
    st.subheader("Which Driver would you like to analyse?")

    # Loading in drivers from the selected race
    drivers = loadDrivers(st.session_state.selectedYear, st.session_state.selectedRace)

    for driver in drivers:
        if st.button(driver, key = driver):
            # Changing selected driver
            st.session_state.selectedDriver = driver

            # Going to corresponding page
            st.session_state.page = "driverAnalysis"

    # Back Button
    if st.button("Back to Analysis Selection"):
        st.session_state.page = "analysisSelection"
        st.rerun()

# - - - Lap Analysis Page - - -
elif st.session_state.page == "lapAnalysis":
    # Headings
    st.title(f"{st.session_state.selectedYear} {st.session_state.selectedRace}")

    # Back Button
    if st.button("Back to Analysis Selection"):
        st.session_state.page = "analysisSelection"
        st.rerun()