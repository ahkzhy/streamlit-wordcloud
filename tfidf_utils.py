import pandas as pd
"""
    load_tfidf_data:加载tfidf数据
"""
def parse_tfidf_data(file_path):
    """
    Parses a tfidf analysis dataset from a CSV file.

    Args:
        file_path (str): The path to the CSV file containing the dataset.
    Returns:
        pd.DataFrame: A DataFrame containing the parsed tfidf data.
    """
    # Read the CSV file into a DataFrame
    df = pd.read_csv(file_path)

    # Check for required columns
    required_columns = {'word', 'score'}
    if not required_columns.issubset(df.columns):
        raise ValueError(f"Input file must contain the following columns: {required_columns}")

    # Clean and preprocess the data if necessary
    clean_tfidf_data(df)

    return df

def clean_tfidf_data(df):
    """
    Cleans the tfidf DataFrame by removing invalid entries.

    Args:
        df (pd.DataFrame): The DataFrame containing tfidf data.
    Returns:
        pd.DataFrame: A cleaned DataFrame with valid tfidf values.
    """
    # Remove rows with NaN scores
    df = df.dropna(subset=['score'])
    # Remove rows with non-numeric scores
    df = df[pd.to_numeric(df['score'], errors='coerce').notnull()]

    return df

def load_tfidf_data():
    """
    Loads and parses tfidf data from a CSV file.
    Returns:
        pd.DataFrame: Two DataFrame containing the parsed tfidf data.
    """
    tfidf_df = pd.read_csv("tfidf.csv")  
    tfidf_title_df = pd.read_csv("tfidf_title.csv")

    return tfidf_df,tfidf_title_df