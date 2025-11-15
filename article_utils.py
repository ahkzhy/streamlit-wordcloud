import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

"""
    load_article_data:加载文章数据
    merge_with_article_info:将其他数据与文章信息通过id合并
    *get_df_top_N_keywords:根据词频分析每篇文章专注的核心词汇？获取每篇文章的top-N关键词(直接对content提取？获取新表？)
"""

def parse_article_data(file_path):
    """
    Parses an article dataset from a CSV file.

    Args:
        file_path (str): The path to the CSV file containing the dataset.
    Returns:
        pd.DataFrame: A DataFrame containing the parsed article data.
    """
    # Read the CSV file into a DataFrame
    df = pd.read_csv(file_path)

    # Check for required columns
    required_columns = {'id','country','platform','published_time','title','content','url'}
    if not required_columns.issubset(df.columns):
        raise ValueError(f"Input file must contain the following columns: {required_columns}")

    # Clean and preprocess the data if necessary
    clean_article_data(df)

    return df

def clean_article_data(df):
    """
    Cleans the article DataFrame by removing invalid entries.

    Args:
        df (pd.DataFrame): The DataFrame containing article data.
    Returns:
        pd.DataFrame: A cleaned DataFrame with valid articles.
    """
    # Remove rows with missing particular essential fields
    df = df.dropna(subset=['id','country','platform','published_time','title','content','url'])
    df['published_time'] = pd.to_datetime(df['published_time'], errors='coerce')
    return df

def load_article_data():
    """
    Loads and parses article data from a CSV file.
    Returns:
        pd.DataFrame: DataFrame containing the parsed article data.

    """
    article_df = pd.read_csv("articles.csv")  

    return article_df

def merge_with_article_info(df, article_df):
    """
    merge df_with_id with article information based on 'id' column.
    
    Args:
        df: DataFrame
        article_df: DataFrame
    
    Returns:
        merged_df: DataFrame,with article information merged
    """
    id_col='id'
    # check if id column exists in both dataframes
    if id_col not in df.columns:
        raise ValueError(f"dataframe does not contain ID column: {id_col}")
    if id_col not in article_df.columns:
        raise ValueError(f"article dataframe does not contain ID column: {id_col}")
    
    # merge dataframes on 'id' column
    merged_df = pd.merge(
        df,        
        article_df, 
        on=id_col, 
        how='inner' #inner join, keep only matching rows
    )
    
    return merged_df


def get_df_top_N_keywords(df, background_docs=None, top_n=5):
    """
    get top-N keywords for each row in the DataFrame using TF-IDF.
    
    Args:
        df: DataFrame，包含至少两列：id列（默认'id'）和文本列（默认'content'）
        background_docs: 列表，外部背景文档（用于计算IDF），若为None则用df中的所有文本作为背景
        top_n: 整数，返回的关键词数量（默认5）
    
    Returns:
        DataFrame: 包含两列：id_col（原id列）和 'top_keywords'（top-N关键词列表）
    """
    # --------------------------
    # 1. check and prepare data
    # --------------------------
    id_col = 'id'
    text_col = 'content'
    required_cols = [id_col, text_col]
    if not set(required_cols).issubset(df.columns):
        raise ValueError(f"DataFrame must contain {required_cols}")
    
    # get valid rows with non-empty text
    df_clean = df[[id_col, text_col]].dropna(subset=[text_col]).copy()
    if df_clean.empty:
        return pd.DataFrame(columns=[id_col, 'top_keywords'])
    
    # --------------------------
    # 2. background documents preparation
    # --------------------------
    all_texts = df_clean[text_col].tolist()  
    if background_docs is None:
        background_docs = all_texts
    else:
        background_docs = background_docs + all_texts
    
    # --------------------------
    # 3. initialize TF-IDF Vectorizer
    # --------------------------
    tfidf = TfidfVectorizer(stop_words='english')  # filter English stop words
    tfidf.fit(background_docs)  # fit on background documents
    vocab = tfidf.vocabulary_  # {vocab_word: index}
    index_to_word = {v: k for k, v in vocab.items()}  # switch to {index: word}
    
    # --------------------------
    # 4. get top-N keywords for each document
    # --------------------------
    def get_top_words(text):
        """辅助函数：为单条文本提取top-N关键词"""
        if not text or str(text).strip() == '':
            return []
        # turn text into tf-idf vector
        tfidf_vec = tfidf.transform([text])
        # get scores and top-N indices
        scores = tfidf_vec.toarray().flatten()
        top_indices = np.argsort(scores)[-top_n:][::-1]  
        # map indices to words, filter out zero-score words
        return [index_to_word[idx] for idx in top_indices if scores[idx] > 0]
    
    # apply to each row
    df_clean['top_keywords'] = df_clean[text_col].apply(get_top_words)
    
    # --------------------------
    # 5. return result with id and top_keywords
    # --------------------------
    return df_clean[[id_col, 'top_keywords']]