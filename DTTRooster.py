import streamlit as st
import pandas as pd
import uuid
import subprocess
from dotenv import load_dotenv
import os

load_dotenv()

# Wachtwoord importeren vanuit ander bestand in zelfde mappenstructuur (password.py)
PASSWORD = os.getenv("PASSWORD")

# Voeg de link naar het CSS-bestand toe aan het eind van de code
with open("style.css", encoding="utf-8") as cssBron:
    st.markdown(f"<style>{cssBron.read()}</style>", unsafe_allow_html=True)

# Functie om de personenlijst op te slaan in de CSV
def update_personen_csv():
    """Slaat de huidige personenlijst op in de CSV."""
    st.session_state.personen.to_csv("personenbeheer.csv", index=False)

# Functie om de planninglijst op te slaan in de CSV
def update_planning_csv():
    """Slaat de huidige planninglijst op in de CSV."""
    st.session_state.planning.to_csv("planning.csv", index=False)

# Functie die automatisch naar Git pushed
def push_to_git():
    # Stel Git-instellingen in
    subprocess.run(["git", "config", "--global", "user.name", "streamlit-bot"])
    subprocess.run(["git", "config", "--global", "user.email", "streamlit-bot@example.com"])

    # Voeg alle wijzigingen toe en commit
    subprocess.run(["git", "add", "."])
    subprocess.run(["git", "commit", "-m", "Automatische update van Streamlit app"])

    # Push naar de remote repository
    result = subprocess.run(["git", "push", "origin", "master"], capture_output=True)
    print(result)

# Titel van de app
st.title("📅 DTT Rooster & Aanwezigheid")

# Initialiseer session state
def init_state():
    if 'planning' not in st.session_state:
        try:
            st.session_state.planning = pd.read_csv("planning.csv")
        except FileNotFoundError:
            st.session_state.planning = pd.DataFrame(columns=['Datum', 'Tijd', 'Beschrijving', 'Adres', 'Aanwezigheid'], index=None)
    if 'personen' not in st.session_state:
        try:
            st.session_state.personen = pd.read_csv("personenbeheer.csv")
        except FileNotFoundError:
            st.session_state.personen = pd.DataFrame(columns=['Voornaam', 'Achternaam', 'UUID-nummer'], index=None)
    if 'page' not in st.session_state:
        st.session_state.page = "Vrijdagrooster overzicht"  # Standaard pagina instellen
    if 'checkbox_checked' not in st.session_state:
        st.session_state.checkbox_checked = {}

init_state()

# Wachtwoordcontrole
def password_entered():
    """Checkt of het ingevoerde wachtwoord juist is."""
    st.session_state["password_correct"] = st.session_state["password"] == PASSWORD

def check_password():
    """Retourneert True als het wachtwoord correct is."""
    if "password" not in st.session_state:
        st.session_state["password"] = ""

    if "password_correct" in st.session_state and st.session_state["password_correct"]:
        return True

    st.text_input("Voer het wachtwoord in", type="password", on_change=password_entered, key="password")
    if st.button("Inloggen", key="password_button"):
        password_entered()

    if "password_correct" in st.session_state and not st.session_state["password_correct"] and st.session_state["password"]:
        st.error("❌ Onjuist wachtwoord")

    return False

if not check_password():
    st.stop()

# Sidebar navigatie
st.sidebar.image("DTT-logo.png", width=175)
st.sidebar.title("Menu")
st.session_state.page = st.sidebar.radio("Ga naar", ["Vrijdagrooster overzicht", "Rooster toevoegen", "Rooster bewerken", "Aanwezigheid personen", "Personenbeheer"])

# Functie om de aanwezigheid bij te werken
def add_person(idx_planning, checkbox_key):
    """Update de aanwezigheid op basis van de checkbox status."""
    st.session_state.checkbox_checked[idx_planning][checkbox_key] = True

def remove_person(idx_planning, checkbox_key):
     st.session_state.checkbox_checked[idx_planning][checkbox_key] = False

# Toevoegen van een nieuwe persoon
def add_new_person(new_person):
    """Voegt een nieuwe persoon toe aan de personenlijst en slaat deze op in de CSV."""
    if new_person:
        # Controleer of de persoon al bestaat
        if new_person not in st.session_state.personen['Voornaam'].values:
            # Nieuwe persoon toevoegen als DataFrame-rij
            voornaam = new_person.strip()
            new_person_data = pd.DataFrame([[voornaam, uuid.uuid4()]], columns=['Voornaam', 'UUID-nummer'])

            # Voeg de nieuwe persoon toe aan de DataFrame
            st.session_state.personen = pd.concat([st.session_state.personen, new_person_data], ignore_index=True)

            # Update de CSV
            update_personen_csv()
            st.success(f"{new_person} toegevoegd!") # Succesbericht na toevoegen van de persoon
            st.rerun()  # Herlaad de app om de lijst te updaten
        else:
            st.warning("Deze persoon bestaat al.") # Waarschuwing als de persoon al bestaat
    else:
        st.warning("Voer een geldige naam in.") # Waarschuwing als de naam leeg is

# Rooster toevoegen
if st.session_state.page == "Rooster toevoegen":
    st.header("➕ Voeg een nieuwe planning toe")
    with st.form("planning_form"):
        datum = st.date_input("Datum")
        tijd = st.time_input("Tijd")
        taak = st.text_input("Beschrijving")
        adres = st.text_input("Adres")
        submit = st.form_submit_button("Toevoegen")

        if submit:
            new_entry = pd.DataFrame([[datum, tijd, taak, adres, 0]], index=None,
                                     columns=['Datum', 'Tijd', 'Beschrijving', 'Adres', 'Aanwezigheid'])
            st.session_state.planning = pd.concat([st.session_state.planning, new_entry], ignore_index=True)
            update_planning_csv()  # Sla de planning op
            push_to_git()  # Push git
            st.success("Planning toegevoegd!")
            st.rerun()  # Herlaad de app om de lijst te updaten

# Vrijdagrooster overzicht 
elif st.session_state.page == "Vrijdagrooster overzicht":
    st.header("📊 Overzicht Planning")
    st.dataframe(st.session_state.planning, hide_index=True)

    # Optie om de planning te downloaden
    def convert_df(df):
        return df.to_csv(index=False).encode('utf-8')

    csv = convert_df(st.session_state.planning)
    st.download_button("📥 Download Planning", data=csv, file_name="planning.csv", mime='text/csv')

# Aanwezigheid personen pagina
elif st.session_state.page == "Aanwezigheid personen":
    st.header("📝 Geef de aanwezigheid van personen aan")

    if st.session_state.personen.empty:
        st.warning("Er zijn nog geen personen toegevoegd. Voeg eerst personen toe via de pagina 'Personenbeheer'.")
    else:
        data_changed = False

        for idx_planning, row_planning in st.session_state.planning.iterrows():
            datum = row_planning['Datum']
            tijd = row_planning['Tijd']
            beschrijving = row_planning['Beschrijving']
            adres = row_planning['Adres']

            with st.expander(f"📅 {datum} - ⏰ {tijd} - 📝 {beschrijving} - 🗺️ {adres}", expanded=False):
                if idx_planning not in st.session_state.checkbox_checked:
                    st.session_state.checkbox_checked[idx_planning] = {}

                aanwezigheid_count = 0  

                for idx_personen, row_personen in st.session_state.personen.iterrows():
                    voornaam = row_personen['Voornaam']
                    nummer = row_personen['UUID-nummer']

                    # Zorg dat de aanwezigheid dictionary correct geïnitialiseerd is
                    if idx_planning not in st.session_state.checkbox_checked or not isinstance(st.session_state.checkbox_checked[idx_planning], dict):
                        st.session_state.checkbox_checked[idx_planning] = {}

                    # Zorg ervoor dat de sleutel (UUID-nummer) aanwezig is
                    if nummer not in st.session_state.checkbox_checked[idx_planning]:
                        st.session_state.checkbox_checked[idx_planning][nummer] = False

                    previous_value = st.session_state.checkbox_checked[idx_planning][nummer]

                    # Checkbox tonen
                    new_value = st.checkbox(f"{voornaam} aanwezig", key=f"aanwezig_{nummer}_{idx_planning}", value=previous_value)

                    # Als waarde verandert, opslaan
                    if new_value != previous_value:
                        st.session_state.checkbox_checked[idx_planning][nummer] = new_value
                        data_changed = True

                    # Tel aanwezigen
                    if new_value:
                        aanwezigheid_count += 1  

                # Update aanwezigheid per planning
                st.session_state.planning.at[idx_planning, 'Aanwezigheid'] = str(st.session_state.checkbox_checked[idx_planning])

                # Toon het aantal aanwezigen
                st.markdown(f"**✅ Aantal aanwezigen: {aanwezigheid_count}**")

        # Alleen opslaan als er iets is veranderd
        if data_changed:
            update_planning_csv()
            push_to_git()

        # Toon de bijgewerkte planning met aanwezigheid
        st.dataframe(st.session_state.planning, hide_index=True)

# Personenbeheer
elif st.session_state.page == "Personenbeheer":
    # Lees de bestaande personenlijst in
    csv_bestand = pd.read_csv("personenbeheer.csv")
    st.session_state.personen = csv_bestand
    st.header("👥 Beheer Personenlijst")

    # Lijst weergeven
    st.subheader("📋 Personenlijst")
    st.write(st.session_state.personen)

    # Toevoegen van een nieuwe persoon
    new_person = st.text_input("Voeg een nieuwe persoon toe")
    if st.button("Toevoegen"):
        add_new_person(new_person)  # Update CSV
        push_to_git()  # Upload naar GIT

        st.rerun()  # Herlaad de app

    # Verwijderen van een persoon
    remove_person = st.selectbox("Verwijder een persoon", st.session_state.personen['Voornaam'])
    if st.button("Verwijderen"):
        if remove_person:
            # Verwijder de persoon uit de DataFrame
            voornaam, achternaam = remove_person.split(" ")[0], " ".join(remove_person.split(" ")[1:])
            st.session_state.personen = st.session_state.personen[st.session_state.personen['Voornaam'] != remove_person]

            # Update de CSV en GIT
            update_personen_csv()
            push_to_git()

            st.success(f"{remove_person} verwijderd!")
            st.rerun()  # Herlaad de app om de lijst te updaten
