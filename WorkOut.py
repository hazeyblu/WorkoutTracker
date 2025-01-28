import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import datetime

# File to store workout data
DATA_FILE = "workout_data.csv"

# Initialize CSV file if it doesn't exist
if not os.path.exists(DATA_FILE):
    pd.DataFrame(columns=["Date", "Day", "Exercise", "Sets", "Reps", "Weight", "BodyWeight"]).to_csv(DATA_FILE,
                                                                                                     index=False)


# Load workout data
def load_data():
    return pd.read_csv(DATA_FILE)


# Save workout data
def save_data(df):
    df.to_csv(DATA_FILE, index=False)


# Workout schedule
WORKOUT_SCHEDULE = {
    "Day 1": ["Bench Press", "Incline Dumbbell Press", "Lateral Raises", "Tricep Dips", "Cable Crunches"],
    "Day 2": ["Pull-Ups", "Barbell Row", "Face Pulls", "Barbell Curls", "Plank Hold"],
    "Day 3": ["Back Squats", "Bulgarian Split Squats", "Romanian Deadlifts", "Seated Calf Raises", "Hanging Leg Raises"],
    "Day 4": ["Deadlifts", "Hip Thrusts", "Front Squats", "Donkey Calf Raises", "Russian Twists"],
    "Day 5": ["Bench Press", "Pull-Ups", "Overhead Press", "Lunges", "Cable Woodchoppers"]
}

# Target reps, sets, and weight for scoring
TARGET_VALUES = {
    "Bench Press": {"sets": 4, "reps": 8, "weight": 60},
    "Incline Dumbbell Press": {"sets": 4, "reps": 10, "weight": 25},
    "Lateral Raises": {"sets": 3, "reps": 12, "weight": 10},
    "Tricep Dips": {"sets": 3, "reps": 10, "weight": 0},  # Body weight
    "Cable Crunches": {"sets": 3, "reps": 20, "weight": 30},
    # Add target values for other exercises
}


# Get today's workout day
def get_todays_workout():
    today = datetime.today().weekday()  # Monday = 0, Sunday = 6
    if today < 5:  # Only weekdays (Monday to Friday)
        return f"Day {today + 1}"
    else:
        return "Rest Day"


# Calculate workout score
def calculate_score(exercise, total_reps, avg_weight):
    target = TARGET_VALUES.get(exercise, {"sets": 4, "reps": 8, "weight": 60})  # Default target
    target_score = target["sets"] * target["reps"] * target["weight"]
    if target_score == 0:
        return 0
    return (total_reps * avg_weight) / target_score * 100


# Streamlit app
def main():
    st.title("Workout Tracker 💪")

    # Load existing data
    df = load_data()

    # Sidebar for navigation
    st.sidebar.header("Navigation")
    option = st.sidebar.radio("Choose an option", ["Today's Workout", "View Progress"])
    st.sidebar.subheader("Log Body Weight")
    body_weight = st.sidebar.number_input("Enter your body weight (kg)", min_value=0.00, max_value=300.00, value=90.00)
    if st.sidebar.button("Log Weight"):
        new_weight_entry = pd.DataFrame({
            "Date": [datetime.today().strftime("%Y-%m-%d")],
            "Day": [get_todays_workout()],
            "Exercise": ["Body Weight Log"],
            "Sets": [0],
            "Reps": [0],
            "Weight": [0],
            "BodyWeight": [body_weight]
        })
        df = pd.concat([df, new_weight_entry], ignore_index=True)
        save_data(df)
        st.sidebar.success(f"Body weight logged as {body_weight} kg!")

    if option == "Today's Workout":
        st.header("Today's Workout Routine")

        # Get today's workout day
        workout_day = get_todays_workout()
        if workout_day == "Rest Day":
            st.write("It's a rest day! Take a break and recover.")
        else:
            st.write(f"**{workout_day} Routine**")
            exercises = WORKOUT_SCHEDULE[workout_day]

            # Log workout for each exercise
            for exercise in exercises:
                st.subheader(exercise)

                # Fetch last workout stats for this exercise
                last_workout = df[df["Exercise"] == exercise]
                if not last_workout.empty:
                    last_date = last_workout["Date"].max()
                    last_data = last_workout[last_workout["Date"] == last_date]
                    total_sets = last_data["Sets"].max()
                    avg_reps = int(last_data["Reps"].mean())
                    avg_weight = int(last_data["Weight"].mean())
                    st.write(f"Last time: {total_sets} sets, {avg_reps} avg reps, {avg_weight} avg weight")

                # Input fields for today's workout
                sets = st.number_input(f"Sets for {exercise}", min_value=1, max_value=10, value=1, key=f"{exercise}_sets")
                reps_list = []
                weight_list = []
                for i in range(sets):
                    reps = st.number_input(f"Reps for Set {i+1}", min_value=0, max_value=20, value=0,
                                           key=f"{exercise}_reps_{i}")
                    weight = st.number_input(f"Weight (kg) for Set {i+1}", min_value=0, max_value=1000, value=0,
                                             key=f"{exercise}_weight_{i}")
                    reps_list.append(reps)
                    weight_list.append(weight)

                # Log workout button
                if st.button(f"Log {exercise}"):
                    for i in range(sets):
                        new_entry = pd.DataFrame({
                            "Date": [datetime.today().strftime("%Y-%m-%d")],
                            "Day": [workout_day],
                            "Exercise": [exercise],
                            "Sets": [i + 1],
                            "Reps": [reps_list[i]],
                            "Weight": [weight_list[i]]
                        })
                        df = pd.concat([df, new_entry], ignore_index=True)
                    save_data(df)
                    st.success(f"{exercise} logged successfully!")

    elif option == "View Progress":
        st.header("Your Progress")

        # Show all logged workouts
        st.write("### Workout History")
        st.dataframe(df)

        # Progress visualization
        st.write("### Progress Over Time")
        if not df.empty:
            # Calculate scores for each workout
            df["Total Reps"] = df.groupby(["Date", "Exercise"])["Reps"].transform("sum")
            df["Avg Weight"] = df.groupby(["Date", "Exercise"])["Weight"].transform("mean")
            df["Score"] = df.apply(lambda row: calculate_score(row["Exercise"], row["Total Reps"], row["Avg Weight"]),
                                   axis=1)

            # Group by date and exercise
            progress_df = df.groupby(["Date", "Exercise"]).agg({"Score": "mean"}).reset_index()

            # Plot progress for each exercise
            exercises = df["Exercise"].unique()
            selected_exercise = st.selectbox("Select Exercise to Visualize", exercises)

            exercise_data = progress_df[progress_df["Exercise"] == selected_exercise]
            if not exercise_data.empty:
                fig, ax = plt.subplots()
                ax.plot(exercise_data["Date"], exercise_data["Score"], marker="o")
                ax.set_xlabel("Date")
                ax.set_ylabel("Score")
                ax.set_title(f"Progress for {selected_exercise}")
                st.pyplot(fig)
            else:
                st.warning("No data available for this exercise.")
        else:
            st.warning("No workout data found. Log some workouts to see progress!")

        st.write("### Body Weight History")
        weight_history = df[["Date", "BodyWeight"]].dropna()
        st.line_chart(weight_history.set_index("Date"))


# Run the app
if __name__ == "__main__":
    main()
