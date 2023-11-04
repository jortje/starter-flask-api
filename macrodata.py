import pandas as pd
import requests

# URLs for the datasets
UNEMPLOYMENT_URL = 'https://opendata.cbs.nl/ODataApi/odata/80590ned/UntypedDataSet'
GDP_URL = 'https://opendata.cbs.nl/ODataApi/odata/84106NED/UntypedDataSet'
HPI_URL = 'https://opendata.cbs.nl/ODataApi/odata/84064NED/UntypedDataSet'

def download_dataset(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def get_unemployment_data(year, month, dataset):
    period = f"{year}MM{month:02d}"  # Format the period as "YYYYMM"
    # Filter the dataset for the given period, age group, and gender
    monthly_data = next(
        (record for record in dataset 
         if record['Perioden'].strip() == period and
            record['Leeftijd'].strip() == '52052' and 
            record['Geslacht'].strip() == 'T001038'),
        None
    )
    if not monthly_data:
        return None
    return {
        'Jaar': year,
        'Maand': month,
        'Werkloosheidspercentage': monthly_data['Seizoengecorrigeerd_8'].strip()
    }

def get_gdp_data(year, dataset):
    year_str = f"{year}JJ00"  # Format the period as "YYYYJJ00"
    yearly_gdp_data = next((record for record in dataset if record['Perioden'] == year_str), None)
    if not yearly_gdp_data:
        return None
    return {
        'Jaar': year,
        'Bruto Binnenlands Product (Volumeontwikkeling)': yearly_gdp_data.get('BrutoBinnenlandsProduct_2', '').strip()
    }

def get_hpi_data(year, dataset):
    year_str = f"{year}JJ00"
    yearly_total_data = next((record for record in dataset if record['Perioden'] == year_str), None)
    if not yearly_total_data:
        return None
    return {
        'Jaar': year,
        'Prijsindex': yearly_total_data['PrijsindexVerkoopprijzen_1'].strip(),
        'Ontwikkeling t.o.v. een jaar eerder': yearly_total_data['OntwikkelingTOVEenJaarEerder_3'].strip(),
        'Aantal verkochte woningen': yearly_total_data['Aantal_4'].strip(),
        'Gemiddelde verkoopprijs': yearly_total_data['GemiddeldeVerkoopprijs_7'].strip(),
        'Totale waarde verkoopprijzen': yearly_total_data['TotaleWaardeVerkoopprijzen_8'].strip()
    }

def main(year, month):
    try:
        year = int(year)
        month = int(month)
        if not (1 <= month <= 12):
            raise ValueError("Month must be between 1 and 12")
    except ValueError as e:
        raise ValueError(f"Invalid input: {e}")

    # Download datasets
    unemployment_dataset = download_dataset(UNEMPLOYMENT_URL)
    gdp_dataset = download_dataset(GDP_URL)
    hpi_dataset = download_dataset(HPI_URL)
    
    # Process datasets
    unemployment_info = get_unemployment_data(year, month, unemployment_dataset['value'])
    gdp_info = get_gdp_data(year, gdp_dataset['value'])
    hpi_info = get_hpi_data(year, hpi_dataset['value'])

    # Prepare dataframes
    unemployment_df = pd.DataFrame([unemployment_info]) if unemployment_info else pd.DataFrame()
    gdp_df = pd.DataFrame([gdp_info]) if gdp_info else pd.DataFrame()
    hpi_df = pd.DataFrame([hpi_info]) if hpi_info else pd.DataFrame()

    # Define Excel file path
    excel_file_path = f'MacroData_{year}_{month}.xlsx'
    
        # Prepare the source information dataframe
    sources_info = {
        'Dataset': ['Unemployment', 'GDP', 'HPI'],
        'Source': [
            'CBS StatLine Arbeidsdeelname en werkloosheid per maand',
            'CBS Statline Bruto Binnenlands Product (BBP); volumeontwikkelingen, Nationale rekeningen',
            'CBS Statline Koopwoningen; prijzen, bestaande koopwoningen'
        ],
        'URL': [
            'https://opendata.cbs.nl/statline/#/CBS/nl/dataset/80590ned/table',
            'https://opendata.cbs.nl/statline/#/CBS/nl/dataset/84106NED/table',
            'https://opendata.cbs.nl/statline/#/CBS/nl/dataset/84064NED/table'
        ]
    }
    sources_df = pd.DataFrame(sources_info)

    # Create a Pandas Excel writer using XlsxWriter as the engine.
    excel_file_path = f'MacroData_{year}_{month:02d}.xlsx'
    with pd.ExcelWriter(excel_file_path, engine='xlsxwriter') as writer:
        if not unemployment_df.empty:
            unemployment_df.to_excel(writer, sheet_name='Unemployment', index=False)
        if not gdp_df.empty:
            gdp_df.to_excel(writer, sheet_name='GDP', index=False)
        if not hpi_df.empty:
            hpi_df.to_excel(writer, sheet_name='HPI', index=False)

        # Write the sources information in the same Excel file
        sources_df.to_excel(writer, sheet_name='Sources', index=False)

    print(f"Macro data for {year}-{month:02d} has been exported to the Excel file: {excel_file_path}")
    return excel_file_path

