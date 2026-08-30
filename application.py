'''
A Program to load and analyse data relating to a specfic drivers race from the ground effect era (2022 - 2025)
Written by Thomas McCaw as a Case Study for MUR Motorsports (Unimelb Formula Student Team)
Development Begin: 17/08/2026
Submitted: 30/08/2026
Development Finish: STILL IN DEVELOPMENT
'''

# Importing Libraries
import streamlit as st
import fastf1
from fastf1 import plotting
import matplotlib.pyplot as plt
import seaborn as sns
import os
import pandas as pd
import numpy as np
from numpy.polynomial import Polynomial

# Setting up matplotlib for FastF1
plotting.setup_mpl(mpl_timedelta_support=True, color_scheme=fastf1)
# Setting matplotlib theme
plt.style.use("dark_background")

# Setting up cache for FastF1
if not os.path.exists(".cache"):
    os.makedirs(".cache", exist_ok = True)
fastf1.Cache.enable_cache(".cache")

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
        if (row["EventFormat"] != "testing"):
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
@st.cache_data(show_spinner="Dowloading driver data | This may take a bit on the first load...")
def loadDrivers(year, race):

    # Loading the list of drivers for the selected race
    drivers = loadRace(year, race).results["FullName"].dropna().tolist()

    # Outputting the array of drivers
    return drivers

# - - - Loading lap data for the selected driver - - -
@st.cache_data
def loadDriverLaps(year, race, driver):

    session = loadRace(year, race)

    driverNumber = session.results.loc[session.results["FullName"] == driver, "DriverNumber"].iloc[0]

    driverLaps = session.laps.pick_drivers(driverNumber).reset_index()

    return driverLaps

# - - - Converting Laptime timedelta data types into string for display to streamlit - - -
def timeDeltaToString(timedelta):
    if pd.isna(timedelta):
        return None

    # Converting timedelta datatype into seconds
    totalSeconds = timedelta.total_seconds()

    # Organising into standard lap time format mm:ss
    minutes = int(totalSeconds // 60)
    seconds = float(totalSeconds % 60)

    # Outputting the converted time delta
    return f"{minutes}:{seconds:2.3f}"

# -------------------------------------------------------------------------------------------------
# CREATING GRAPHICS
# -------------------------------------------------------------------------------------------------
# - - - Lap Time Graph - - -
def makeLapTimeGraph(driverLaps, race):

    # Creating the graph object
    lapTimeGraph, ax = plt.subplots(figsize=(8, 8))

    # Creating the scatter plot
    sns.scatterplot(
        data = driverLaps,
        x = "LapNumber",
        y = "LapTime",
        ax = ax,
        hue = "Compound",
        palette = plotting.get_compound_mapping(session = race),
        s = 80,
        linewidth = 0,
        legend = "auto"
    )

    # Formatting
    ax.set_facecolor("#0e1117")
    ax.set_xlabel("Lap Number")
    ax.set_ylabel("Lap Time")
    #ax.xaxis.label.set_color("#fafafa")
    #ax.yaxis.label.set_color("#fafafa")
    plt.grid(color='w', which='major', axis='both')
    sns.despine(left=True, bottom=True)
    plt.tight_layout()

    return lapTimeGraph

# - - - Stint Analysis - - -
def makeStintAnalysisData(driverLaps):

    # Creating the data structure
    stintAnalysisData = driverLaps.groupby("Stint").agg(
        FirstLap = ("LapTime", "first"),
        LastLap = ("LapTime", "last"),
        AverageLap = ("LapTime", "mean"),
        StintLength = ("LapTime", "count"),
        Compound = ("Compound", "first")
    ).reset_index()

    return stintAnalysisData

# - - - Tyre Degredation Analysis - - -
def makeTyreDegData(driverLaps):

    tyreDegDict = {}

    # Calculating tyre degredation for each stint
    for stint in driverLaps["Stint"].unique():
        # Retrieving data from the stint
        stintLaps = driverLaps[driverLaps["Stint"] == stint].copy()

        # Getting the stint tyre compound
        compound = stintLaps["Compound"].iloc[0]

        # Remove the first and last lap of the stint
        if len(stintLaps) > 2:
            stintLaps = stintLaps.iloc[1:-1]

        # Removing laps with no laptime
        stintLaps = stintLaps.dropna(subset = ["LapTime"])

        # Using IQR to removve outliers from the dataset (incedents, yellow flags, trafic etc)
        lapTimes = stintLaps["LapTime"].dt.total_seconds()
        Q1 = lapTimes.quantile(0.25)
        Q3 = lapTimes.quantile(0.75)
        IQR = Q3 - Q1
        loBound = Q1 - (1.5 * IQR)
        hiBound = Q3 + (1.5 * IQR)
        stintLaps = stintLaps[(lapTimes >= loBound) & (lapTimes <= hiBound)]

        if len(stintLaps) < 2:
            tyreDegDict[stint] = {
                "Compound": compound,
                "Degredation": "N/A"
            }
            break

        # Retriving each lap and associated lapTime from the stint
        lapNums = stintLaps["LapNumber"].values
        lapTimes = stintLaps["LapTime"].dt.total_seconds().values

        # Calculating the average pace lost per lap
        lapDegPolynomial = Polynomial.fit(lapNums, lapTimes, 1)
        degPerLap = lapDegPolynomial.convert().coef[1]

        # Organising into a dictionary
        tyreDegDict[stint] = {
            "Compound": compound,
            "Degredation": f"{degPerLap:.3} s/lap"
        }

    return tyreDegDict


# -------------------------------------------------------------------------------------------------
# SESSION STATES
# -------------------------------------------------------------------------------------------------
# Page status
if "page" not in st.session_state:
    st.session_state.page = "Race Selection"
# Previous Page status
if "pageHistory" not in st.session_state:
    st.session_state.pageHistory = []
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
# - - - Genearl back Button Function - - -
def backButton():
    if st.session_state.pageHistory:
        previousPage = st.session_state.pageHistory[-1]

        if st.button(f"Back to {previousPage}", type = "primary", icon = "↩"):
            st.session_state.page = st.session_state.pageHistory.pop()
            st.rerun()

# - - - Race Selection Page - - -
if st.session_state.page == "Race Selection":

    # Selecting Year
    year = st.selectbox(
        "Select a season",
        range(2022, 2026)
    )

    # Headings
    st.title("Formula 1 Race Analysis")
    st.header(f"{year} Season")

    # Loading the racing of the season
    seasonRaces = loadRaces(year)

    # Creating buttons corresponding to each race of the year
    for race in seasonRaces:
        if st.button(race, key = race):
            # Changing selected race and year
            st.session_state.selectedRace = race
            st.session_state.selectedYear = year

            # Going to corresponding page
            st.session_state.pageHistory.append(st.session_state.page)
            st.session_state.page = "Driver Selection"

            st.rerun()

# - - - Analysis Selection Page - - -
#elif st.session_state.page == "Analysis Selection":
#    # Headings
#    st.title(f"{st.session_state.selectedYear} {st.session_state.selectedRace}")
#    st.header("What would you like to analyse")
#
#    col1, col2 = st.columns(2)
#
#    # Driver Analysis
#    with col1:
#        if st.button("Driver Analysis"):
#            st.session_state.pageHistory.append(st.session_state.page)
#            st.session_state.page = "Driver Selection"
#            st.rerun()
#
#    # Laps Analysis
#    with col2:
#        if st.button("Lap Analysis"):
#            st.session_state.pageHistory.append(st.session_state.page)
#            st.session_state.page = "Lap Analysis"
#            st.rerun()
#
#    # Back Button
#    backButton()

# - - - Driver Selection Page - - -
elif st.session_state.page == "Driver Selection":
    # Headings
    st.title(f"{st.session_state.selectedYear} {st.session_state.selectedRace}")
    st.header("Which Driver would you like to analyse?")

    # Loading in drivers from the selected race
    drivers = loadDrivers(st.session_state.selectedYear, st.session_state.selectedRace)

    for driver in drivers:
        if st.button(driver, key = driver):
            # Changing selected driver
            st.session_state.selectedDriver = driver

            # Going to corresponding page
            st.session_state.pageHistory.append(st.session_state.page)
            st.session_state.page = "Driver Analysis"
            st.rerun()

    # Back Button
    backButton()

# - - - Driver Analysis Page - - -
elif st.session_state.page == "Driver Analysis":
    # Title
    st.title(f"{st.session_state.selectedDriver}")
    st.header(f"{st.session_state.selectedYear} {st.session_state.selectedRace}")

    # Getting selected year, race and driver
    year = st.session_state.selectedYear
    race = st.session_state.selectedRace
    driver = st.session_state.selectedDriver

    # Creating Graphics
    driverLapsGraph = makeLapTimeGraph(loadDriverLaps(year, race, driver), loadRace(year, race))
    stintAnalysisDict = makeStintAnalysisData(loadDriverLaps(year, race, driver))
    tyreDegDict = makeTyreDegData(loadDriverLaps(year, race, driver))

    # Displaying Graphics
    st.subheader("Lap Times and Tyre Compounds:")
    st.write(f"General visualisation of {driver}'s race")
    st.pyplot(driverLapsGraph, use_container_width = True)

    st.subheader("Race Stints:")
    st.write("Lap time analysis for race stints")
    lapTimeColumns = ["FirstLap", "LastLap", "AverageLap"]
    for column in enumerate(lapTimeColumns):
        stintAnalysisDict[column[1]] = stintAnalysisDict[lapTimeColumns[column[0]]].apply(timeDeltaToString)
    st.dataframe(
        stintAnalysisDict, use_container_width = True,
        hide_index = True,
        column_config = {
            "Stint": "Stint",
            "FirstLap": "First Lap Time",
            "LastLap": "Last Lap Time",
            "AverageLap": "Average Lap Time",
            "StintLength": "Stint Length",
            "Compound": "Compound"
        }
        )

    st.subheader("Tyre Degredation Analysis")
    st.write("Estimated pace lost per lap for each stint of the race")
    st.dataframe(tyreDegDict)

    # Back Button
    backButton()

# - - - Lap Analysis Page - - -
#elif st.session_state.page == "Lap Analysis":
#    # Headings
#    st.title(f"{st.session_state.selectedYear} {st.session_state.selectedRace}")
#
#    # Back Button
#    backButton()