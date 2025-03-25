import streamlit as st
import pandas as pd
import uuid
import subprocess
from dotenv import load_dotenv
import os
import json
import git

load_dotenv()

# Wachtwoord importeren vanuit ander bestand in zelfde mappenstructuur (password.py)
PASSWORD = os.getenv("PASSWORD")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# Voeg de link naar het CSS-bestand toe
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

def commit_and_push_changes(data_url):
    """Function to commit and push changes to GitHub."""
    try:
        repo = git.Repo()
        repo.git.remote("set-url", "origin", f"https://{GITHUB_TOKEN}@github.com/EvaHuisman/stunning-cashew.git")
        repo.git.checkout('master')
        repo.remotes.origin.pull()

        # Add, commit, and push the changes to the repository
        repo.git.add(data_url)
        repo.index.commit(f'Update CSV {data_url}')
        repo.remotes.origin.push()

    except Exception as e:
        st.warning(f"Error saving data: {e}")
        print(e)

# Titel van de app
st.title("📅 DTT Rooster & Aanwezigheid")

# Initialiseer session state
def init_state():
    if 'planning' not in st.session_state:
        try:
            st.session_state.planning = pd.read_csv("planning.csv")
        except FileNotFoundError:
            st.session_state.planning = pd.DataFrame(columns=['Datum', 'Tijd', 'Beschrijving', 'Adres'], index=None)
    if 'personen' not in st.session_state:
        try:
            st.session_state.personen = pd.read_csv("personenbeheer.csv")
        except FileNotFoundError:
            st.session_state.personen = pd.DataFrame(columns=['Voornaam', 'Achternaam', 'UUID-nummer'], index=None)
    if 'page' not in st.session_state:
        st.session_state.page = "Vrijdagrooster overzicht"  # Standaard pagina instellen
    if 'checkbox_checked' not in st.session_state:
        st.session_state.checkbox_checked = {}

    if 'person_added' not in st.session_state:
        st.session_state['person_added'] = False  # Indicator voor of een persoon toegevoegd is

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
st.session_state.page = st.sidebar.radio("Ga naar", ["Vrijdagrooster overzicht", "Rooster toevoegen", "Rooster bewerken", "Personenbeheer"])

# Functie om de aanwezigheid bij te werken
def add_person(idx_planning, checkbox_key, checkbox_checked):
    """Update de aanwezigheid op basis van de checkbox status.""" 
    checkbox_checked[idx_planning][checkbox_key] = True

# Toevoegen van een nieuwe persoon
def add_new_person(new_person):
    """Voegt een nieuwe persoon toe aan de personenlijst en slaat deze op in de CSV."""
    if new_person:
        # Controleer of de persoon al bestaat
        if new_person not in st.session_state.personen['Voornaam'].values:
            # Nieuwe persoon toevoegen als DataFrame-rij
            voornaam = new_person.strip()
            new_person_data = pd.DataFrame([[voornaam, "", uuid.uuid4()]], columns=['Voornaam', 'Achternaam', 'UUID-nummer'])

            # Voeg de nieuwe persoon toe aan de DataFrame
            st.session_state.personen = pd.concat([st.session_state.personen, new_person_data], ignore_index=True)

            # Update de CSV
            update_personen_csv()
            commit_and_push_changes('personenbeheer.csv')  # Upload naar GIT

            # Zet de flag dat er een persoon is toegevoegd
            st.session_state['person_added'] = new_person

            # Herstart de pagina om de wijziging zichtbaar te maken
            st.session_state.page = "Personenbeheer"  # Forceer herladen van de pagina
            st.rerun()  # Herstart de pagina zodat de verandering zichtbaar is
        else:
            st.warning("Deze persoon bestaat al.") # Waarschuwing als de persoon al bestaat
    else:
        st.warning("Voer een geldige naam in.") # Waarschuwing als de naam leeg is

# Verwijderen van een persoon
def remove_person_from_list(person_name):
    """Verwijdert een persoon op basis van de voornaam uit de lijst."""
    if person_name:
        # Verwijder de persoon uit de DataFrame
        st.session_state.personen = st.session_state.personen[st.session_state.personen['Voornaam'] != person_name]

        # Update de CSV
        update_personen_csv()
        commit_and_push_changes('personenbeheer.csv')

        # Zet de flag dat er een persoon is verwijderd
        st.session_state['person_removed'] = person_name

        # Herstart de pagina om de wijziging zichtbaar te maken
        st.session_state.page = "Personenbeheer"  # Forceer herladen van de pagina
        st.rerun()  # Herstart de pagina zodat de verandering zichtbaar is

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
            new_entry = pd.DataFrame([[datum, tijd, taak, adres]], index=None,
                                     columns=['Datum', 'Tijd', 'Beschrijving', 'Adres'])
            st.session_state.planning = pd.concat([st.session_state.planning, new_entry], ignore_index=True)
            update_planning_csv()  # Sla de planning op
            commit_and_push_changes("planning.csv")  # Push git
            st.success("Nieuw rooster toegevoegd!")  # Succesmelding
            st.session_state.page = "Vrijdagrooster overzicht"  # Forceer herladen van de pagina

# Vrijdagrooster overzicht 
elif st.session_state.page == "Vrijdagrooster overzicht":
    st.header("📊 Overzicht Planning")

    # Verwijder de 'Aanwezigheid' kolom uit de planning
    st.session_state.planning = st.session_state.planning.drop(columns=['Aanwezigheid'], errors='ignore')

    st.dataframe(st.session_state.planning, hide_index=True)

    # Optie om de planning te downloaden
    def convert_df(df):
        return df.to_csv(index=False).encode('utf-8')

    csv = convert_df(st.session_state.planning)
    st.download_button("📥 Download Planning", data=csv, file_name="planning.csv", mime='text/csv')

# Personenbeheer
elif st.session_state.page == "Personenbeheer":
    st.header("👥 Beheer Personenlijst")

    # Lijst weergeven
    st.subheader("📋 Personenlijst")
    st.write(st.session_state.personen)

    # Voeg een succesmelding toe als een persoon is toegevoegd
    if st.session_state.get('person_added', False):
        st.success(f"{st.session_state['person_added']} toegevoegd!")  # Melding dat de persoon is toegevoegd

        # Reset de flag na het tonen van de melding
        st.session_state['person_added'] = False

    # Voeg een succesmelding toe als een persoon is verwijderd
    if st.session_state.get('person_removed', False):
        st.success(f"{st.session_state['person_removed']} verwijderd!")  # Melding dat de persoon is verwijderd

        # Reset de flag na het tonen van de melding
        st.session_state['person_removed'] = False

    # Toevoegen van een nieuwe persoon
    new_person = st.text_input("Voeg een nieuwe persoon toe")
    if st.button("Toevoegen"):
        add_new_person(new_person)  # Update CSV en herlees personenlijst

    # Verwijderen van een persoon
    remove_person = st.selectbox("Verwijder een persoon", st.session_state.personen['Voornaam'])
    if st.button("Verwijderen"):
        remove_person_from_list(remove_person)  # Verwijder de persoon uit de lijst en update de CSV

# Rooster bewerken
elif st.session_state.page == "Rooster bewerken":
    st.header("✏️ Bewerk of Verwijder een planning")

    # Controleer of er planningen zijn
    if st.session_state.planning.empty:
        st.write("🚫 Er zijn geen openstaande planningen om te bewerken.")
    else:
        # Kies een planning om te bewerken of verwijderen
        planning_select = st.selectbox("Kies een planning", st.session_state.planning['Beschrijving'])

        # Vind de geselecteerde planning op basis van de beschrijving
        planning_idx = st.session_state.planning[st.session_state.planning['Beschrijving'] == planning_select].index[0]

        # Haal de huidige waarden voor de geselecteerde planning
        datum = pd.to_datetime(st.session_state.planning.at[planning_idx, 'Datum']).date()
        tijd_value = st.session_state.planning.at[planning_idx, 'Tijd']
        if isinstance(tijd_value, str):  # Als het een string is, converteer het naar time
            tijd_value = pd.to_datetime(tijd_value).time()
        tijd = st.time_input("Tijd", value=tijd_value)
        taak = st.text_input("Beschrijving", value=st.session_state.planning.at[planning_idx, 'Beschrijving'])
        adres = st.text_input("Adres", value=st.session_state.planning.at[planning_idx, 'Adres'])

        # Als de gebruiker de gegevens wijzigt, moeten we de DataFrame updaten
        if st.button("Opslaan"):
            # Werk de planning bij in de DataFrame
            st.session_state.planning.at[planning_idx, 'Datum'] = datum
            st.session_state.planning.at[planning_idx, 'Tijd'] = tijd
            st.session_state.planning.at[planning_idx, 'Beschrijving'] = taak
            st.session_state.planning.at[planning_idx, 'Adres'] = adres

            # Sla de wijzigingen op in de CSV en update de GIT
            update_planning_csv()
            commit_and_push_changes('planning.csv')

            # Bevestigingsbericht
            st.success(f"Rooster is bewerkt!")

            # Direct de wijzigingen weergeven
            st.session_state.page = "Vrijdagrooster overzicht"  # Forceer herladen van de pagina

        # Verwijder planning
        if st.button("Verwijder deze planning"):
            # Verwijder de geselecteerde planning uit de DataFrame
            st.session_state.planning = st.session_state.planning[st.session_state.planning['Beschrijving'] != planning_select]

            # Update de CSV en GIT
            update_planning_csv()
            commit_and_push_changes("planning.csv")
            st.success(f"Rooster is verwijderd!")

            # Direct de wijzigingen weergeven
            st.session_state.page = "Vrijdagrooster overzicht"  # Forceer herladen van de pagina
