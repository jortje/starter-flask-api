import io
import pandas as pd
import requests
import boto3
from botocore.exceptions import NoCredentialsError

# URLs for the datasets
UNEMPLOYMENT_URL = 'https://opendata.cbs.nl/ODataApi/odata/80590ned/UntypedDataSet'
GDP_URL = 'https://opendata.cbs.nl/ODataApi/odata/84106NED/UntypedDataSet'
HPI_URL = 'https://opendata.cbs.nl/ODataApi/odata/84064NED/UntypedDataSet'

# Your Cyclic S3 bucket name
S3_BUCKET = os.environ.get('CYCLIC_BUCKET_NAME')

# Initialize S3 client
s3_client = boto3.client('s3')

def upload_file_to_s3(file_name, bucket_name, object_name=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket_name: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = file_name

    # Upload the file
    try:
        response = s3_client.upload_file(file_name, bucket_name, object_name)
    except NoCredentialsError:
        print("Credentials not available")
        return False
    return True

def download_dataset(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def get_unemployment_data(year, month, dataset):
    period = f"{year}MM{month:02d}"  # Format the period as "YYYYMM"
    monthly_data = next(
        (record for record in dataset if record['Perioden'].strip() == period and
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

    # Create an in-memory bytes buffer for the Excel file
    output = io.BytesIO()

    # Write dataframes to the buffer
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        if not unemployment_df.empty:
            unemployment_df.to_excel(writer, sheet_name='Unemployment', index=False)
        if not gdp_df.empty:
            gdp_df.to_excel(writer, sheet_name='GDP', index=False)
        if not hpi_df.empty:
            hpi_df.to_excel(writer, sheet_name='HPI', index=False)
        sources_df.to_excel(writer, sheet_name='Sources', index=False)

    # Important: move the cursor to the start of the stream
    output.seek(0)

    # Get S3 client
    s3_client = boto3.client(
        's3',
        region_name='eu-west-3',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        aws_session_token=os.getenv('AWS_SESSION_TOKEN')  # if you are using temporary credentials
    )

    file_name = f'MacroData_{year}_{month:02d}.xlsx'
    bucket_name = os.getenv('CYCLIC_BUCKET_NAME')

    try:
        # Upload the file to S3
        s3_client.upload_fileobj(output, bucket_name, file_name)

        # Generate a URL to download the file
        url = s3_client.generate_presigned_url('get_object',
                                               Params={'Bucket': bucket_name,
                                                       'Key': file_name},
                                               ExpiresIn=3600)
    except NoCredentialsError:
        raise Exception("AWS credentials are not available")

    return url
