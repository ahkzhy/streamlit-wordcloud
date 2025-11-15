import pandas as pd
"""
    load_sentiment_data:加载情感数据
    get_top_n_by_score:获取按情感分排序的前N条数据
    *和文章数据合并：缺少文章数据
"""

def parse_sentiment_data(file_path):
    """
    Parses a sentiment analysis dataset from a CSV file.

    Args:
        file_path (str): The path to the CSV file containing the dataset.
    Returns:
        pd.DataFrame: A DataFrame containing the parsed sentiment data.

    """
    # Read the CSV file into a DataFrame
    df = pd.read_csv(file_path)

    # Check for required columns
    required_columns = {'id', 'score'}
    if not required_columns.issubset(df.columns):
        raise ValueError(f"Input file must contain the following columns: {required_columns}")

    # Clean and preprocess the data if necessary
    clean_sentiment_data(df)

    return df

def clean_sentiment_data(df):
    """
    Cleans the sentiment DataFrame by removing invalid entries.

    Args:
        df (pd.DataFrame): The DataFrame containing sentiment data.
    Returns:
        pd.DataFrame: A cleaned DataFrame with valid sentiment scores.
    """
    # Remove rows with NaN scores
    df = df.dropna(subset=['score'])
    # Remove rows with non-numeric scores
    df = df[pd.to_numeric(df['score'], errors='coerce').notnull()]

    return df

def load_sentiment_data():
    """
    Loads and parses sentiment data from a CSV file.
    Returns:
        pd.DataFrame: Two DataFrame containing the parsed sentiment data.

    """
    sentiment_df = pd.read_csv("sentiment.csv")  # 正文情感
    sentiment_title_df = pd.read_csv("sentiment_title.csv")  # 标题情感

    merged_df = pd.merge(
        sentiment_df,        
        sentiment_title_df, 
        on='id', 
        how='inner', #inner join, keep only matching rows
        suffixes=('_content', '_title')  
    )

    return merged_df

def get_top_n_by_score(df, top_n=10, ascending=False,content=True):
    """
    get top N results by score from dataframe
    
    Args:
        df: DataFrame, input dataframe
        top_n: int, get topN results
        ascending: bool, sort order
        content: bool, True for content score, False for title score
    
    Returns:
        top_df: DataFrame, sorted Dataframe with topN results
    """
    if df.empty:
        return pd.DataFrame()  # 若合并后无数据，返回空DataFrame
    
    if content:
        score_col='score_content'
    else:
        score_col='score_title'

    # check 'score' column exists
    if score_col not in df.columns:
        raise ValueError(f"DataFrame must contain {score_col} column.")
    
    # sort and get top N
    top_df = df.sort_values(
        by=score_col,
        ascending=ascending
    ).head(top_n).reset_index(drop=True)
    
    
    return top_df[['id',score_col]].rename(columns={score_col:'score'})