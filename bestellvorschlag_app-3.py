import streamlit as st
import pandas as pd
from sklearn.linear_model import LinearRegression
import pickle
from io import BytesIO

st.set_page_config(page_title="Bestellvorschlag Berechnung", layout="wide")

st.warning("⚠️ Hinweis: Dieses Modul zur Berechnung der Bestellvorschläge befindet sich in der Beta-Phase.")

def berechne_bestellvorschlag(bestand_df, abverkauf_df, artikelnummern, sicherheitsfaktor=0.1):
    def find_best_week_consumption(article_number, abverkauf_df):
        article_data = abverkauf_df[abverkauf_df['Artikelnummer'] == article_number]
        article_data['Menge Aktion'] = pd.to_numeric(article_data['Menge Aktion'], errors='coerce')
        return article_data['Menge Aktion'].max() if not article_data.empty else 0

    bestellvorschläge = []
    for artikelnummer in artikelnummern:
        if artikelnummer not in bestand_df['Artikelnummer'].values:
            continue
        bestand = bestand_df.loc[bestand_df['Artikelnummer'] == artikelnummer, 'Bestand Vortag in Stück (ST)'].values[0]
        gesamtverbrauch = find_best_week_consumption(artikelnummer, abverkauf_df)
        artikelname_values = abverkauf_df.loc[abverkauf_df['Artikelnummer'] == artikelnummer, 'Artikelname'].values
        artikelname = artikelname_values[0] if len(artikelname_values) > 0 else "Unbekannt"
        bestellvorschlag = max(gesamtverbrauch * (1 + sicherheitsfaktor) - bestand, 0)
        bestellvorschläge.append((int(artikelnummer), artikelname, gesamtverbrauch, bestand, bestellvorschlag))

    return pd.DataFrame(bestellvorschläge, columns=['Artikelnummer', 'Artikelname', 'Gesamtverbrauch', 'Aktueller Bestand', 'Bestellvorschlag'])

st.title("Bestellvorschlag Berechnung")
abverkauf_file = st.file_uploader("Abverkaufsdaten hochladen (Excel)", type=["xlsx"])
bestand_file = st.file_uploader("Bestände hochladen (Excel)", type=["xlsx"])

sicherheitsfaktor = st.slider("Sicherheitsfaktor", min_value=0.0, max_value=1.0, value=0.1, step=0.05)

if abverkauf_file and bestand_file:
    abverkauf_df = pd.read_excel(abverkauf_file)
    bestand_df = pd.read_excel(bestand_file)
    artikelnummern = bestand_df['Artikelnummer'].unique()
    result_df = berechne_bestellvorschlag(bestand_df, abverkauf_df, artikelnummern, sicherheitsfaktor)
    st.subheader("Bestellvorschläge")
    st.dataframe(result_df)
    output = BytesIO()
    result_df.to_excel(output, index=False, engine='openpyxl')
    output.seek(0)
    st.download_button(label="Download der Ergebnisse", data=output, file_name="bestellvorschlag.xlsx")
