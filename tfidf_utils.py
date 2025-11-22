import re
import pandas as pd
"""
    load_tfidf_data:加载tfidf数据
"""
def get_english_stopwords():
    """获取英文停用词列表 (从 app.py 迁移过来)"""
    english_stopwords = {
        # 基础冠词、连词、介词
        'a', 'an', 'the', 'and', 'or', 'but', 'if', 'because', 'as', 'until', 'while', 
        'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into', 'through', 
        'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 
        'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here', 
        'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 
        'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 
        'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', 
        'should', 'now', 'd', 'll', 'm', 'o', 're', 've', 'y', 'ain', 'aren', 'couldn', 
        'didn', 'doesn', 'hadn', 'hasn', 'haven', 'isn', 'ma', 'mightn', 'mustn', 
        'needn', 'shan', 'shouldn', 'wasn', 'weren', 'won', 'wouldn',
        # 代词
        'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your', 
        'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', 'her', 
        'hers', 'herself', 'it', 'its', 'itself', 'they', 'them', 'their', 'theirs', 
        'themselves', 'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those', 
        'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 
        'having', 'do', 'does', 'did', 'doing',
        # 常见无意义词
        'would', 'could', 'should', 'via', 'per', 'eg', 'ie', 'etc', 'vs', 'us', 
        'using', 'used', 'make', 'made', 'making', 'see', 'saw', 'seen', 'get', 'got', 
        'getting', 'go', 'went', 'gone', 'come', 'came', 'coming', 'take', 'took', 
        'taken', 'say', 'said', 'saying', 'tell', 'told', 'telling', 'ask', 'asked', 
        'asking', 'give', 'gave', 'given', 'keep', 'kept', 'keeping', 'let', 'letting', 
        'put', 'putting', 'seem', 'seemed', 'seeming', 'look', 'looked', 'looking',
        # 常见动词/助词
        'may', 'might', 'must', 'shall', 'should', 'will', 'would', 'can', 'could',
        'say', 'says', 'said', 'mr', 'ms', 'mrs', 'one', 'two', 'three', 'four', 
        'five', 'first', 'second', 'third', 'new', 'old', 'good', 'bad', 'high', 
        'low', 'big', 'small', 'large', 'great', 'little', 'many', 'much', 'less', 
        'least', 'more', 'most', 'another', 'other', 'others', 'top', 'best', 'better'
    }
    return english_stopwords
def is_english_word(word):
    """检查单词是否只包含英文字母"""
    if not isinstance(word, str):
        return False
    # 使用正则表达式检查是否只包含英文字母（允许连字符和撇号）
    return bool(re.match(r'^[a-zA-Z\-\.\']+$', word))
def clean_with_stopwords(df):
    """
    使用停用词表清洗 DataFrame
    """
    if df is None or df.empty:
        return df, 0
        
    original_count = len(df)
    stopwords = get_english_stopwords()
    
    # 确保 word 列存在且转为小写进行比对
    if 'word' in df.columns:
        # 过滤掉停用词 (转换为小写比较)
        df_clean = df[~df['word'].str.lower().isin(stopwords)].copy()
        
        # 过滤掉纯数字或过短的词
        df_clean = df_clean[df_clean['word'].str.len() > 1] # 过滤单字母
        df_clean = df_clean[~df_clean['word'].str.isnumeric()] # 过滤纯数字
        
        removed_count = original_count - len(df_clean)
        return df_clean, removed_count
    
    return df, 0

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
    df=clean_with_stopwords(df)
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