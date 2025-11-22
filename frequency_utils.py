from collections import defaultdict
import re
import pandas as pd

import numpy as np
"""
    load_frequency_data:加载词频数据
    calculate_word_trends:计算词频变化趋势
    detect_burst_words:基于HistoryDataQueue检测热词突增
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

def parse_frequency_data(file_path):
    """
    Parses a frequency analysis dataset from a CSV file.

    Args:
        file_path (str): The path to the CSV file containing the dataset.
    Returns:
        pd.DataFrame: A DataFrame containing the parsed frequency data.
    """
    # Read the CSV file into a DataFrame
    df = pd.read_csv(file_path)

    # Check for required columns
    required_columns = {'word', 'frequency'}
    if not required_columns.issubset(df.columns):
        raise ValueError(f"Input file must contain the following columns: {required_columns}")

    # Clean and preprocess the data if necessary
    clean_frequency_data(df)

    return df

def clean_frequency_data(df):
    """
    Cleans the frequency DataFrame by removing invalid entries.

    Args:
        df (pd.DataFrame): The DataFrame containing frequency data.
    Returns:
        pd.DataFrame: A cleaned DataFrame with valid frequency values.
    """
    # Remove rows with NaN frequencies
    df = df.dropna(subset=['frequency'])
    # Remove rows with non-numeric frequencies
    df = df[pd.to_numeric(df['frequency'], errors='coerce').notnull()]
    df = clean_with_stopwords(df)
    return df

def load_frequency_data():
    """
    Loads and parses frequency data from a CSV file.
    Returns:
        pd.DataFrame: Two DataFrame containing the parsed frequency data.
    """
    frequency_df = pd.read_csv("word_frequency.csv")  
    frequency_title_df = pd.read_csv("word_frequency_title.csv")

    return frequency_df,frequency_title_df

def calculate_word_trends(old_freq, new_freq):
    """
    calculate word frequency trends between two batches.
    
    Returns:
        dict: A dictionary with keys 'common', 'new', 'lost', and 'all' containing DataFrames."""
    if old_freq is None or new_freq is None:
        return {}
    
    # combine old and new frequency data on 'word'
    merged = pd.merge(
        old_freq, new_freq,
        on='word',
        suffixes=('_old', '_new'),
        how='outer' # keep all words
    )
    # fill NaN frequencies with 0
    merged['count_old'] = merged['count_old'].fillna(0)
    merged['count_new'] = merged['count_new'].fillna(0)
    
    # calculate frequency change and rate
    merged['freq_change'] = merged['count_new'] - merged['count_old']
    merged['freq_change_rate'] = np.where(
        merged['count_old'] == 0,
        np.where(merged['count_new'] == 0, 0, 1), # if old freq is 0 and new freq > 0, rate is 1
        merged['freq_change'] / merged['count_old']
    )
    
    # identify new, lost, and common words
    merged['trend'] = np.where(
        (merged['count_old'] > 0) & (merged['count_new'] > 0),
        'common',  
        np.where(
            merged['count_old'] == 0,
            'new', 
            'lost'  
        )
    )
    
    return {
        'common': merged[merged['trend'] == 'common'],  
        'new': merged[merged['trend'] == 'new'],     
        'lost': merged[merged['trend'] == 'lost'],    
        'all': merged  
    }


def detect_burst_words(freq_queue, current_window_size=2, baseline_window_size=8, min_freq_now=3, min_freq_base=2, top_k=10):
    """
    check for burst words based on HistoryDataQueue.
    Args:
        freq_queue: HistoryDataQueue实例
        current_window_size: 当前窗口包含的更新次数
        baseline_window_size: 基线窗口包含的更新次数（需满足current + baseline <=历史队列长度）
        min_freq_now: 当前窗口最小总频次（过滤噪声）
        min_freq_base: 基线窗口标准化后最小频次（过滤历史低频词）
        top_k: 取前K个热词
    Returns:
        top_burst_words: 排序后的热词df（含词、频次、突增指标） word,freq_now, freq_base, fold_change,burst_score
    """
    # --------------------------
    # 1. check if enough data
    # --------------------------
    all_updates = freq_queue.get_all()
    if len(all_updates) < (current_window_size + baseline_window_size):
        #raise ValueError(f"lack of data. at least{current_window_size + baseline_window_size}times of updates required.")
        return pd.DataFrame()
    # --------------------------
    # 2. seperate windows
    # --------------------------
    baseline_updates = all_updates[:baseline_window_size]  
    current_updates = all_updates[-current_window_size:]   # latest

    # --------------------------
    # 3. aggregate frequencies in each window
    # --------------------------
    def aggregate_window(updates):
        """汇总窗口内所有更新的词频，返回{word: 总频次}"""
        word_total = defaultdict(int)
        for ts, freq_df in updates:
            # 遍历该次更新的词频DataFrame，累加总频次
            for _, row in freq_df.iterrows():
                word = row['word']
                word_total[word] += row['frequency']
        return word_total

    current_freq = aggregate_window(current_updates)
    baseline_freq_total = aggregate_window(baseline_updates)

    # --------------------------
    # 4. standardize baseline frequencies
    # --------------------------
    # when comparing different window sizes, standardize baseline frequencies by window size ratio
    window_ratio = baseline_window_size / current_window_size  # 8/2=4
    baseline_freq_normalized = {
        word: total / window_ratio 
        for word, total in baseline_freq_total.items()
    }

    # --------------------------
    # 5. calculate burst scores
    # --------------------------
    burst_words = []
    eps = 1e-6  

    for word, freq_now in current_freq.items():
        # get baseline freq (0 if not present)
        freq_base = baseline_freq_normalized.get(word, 0)

        # filter by min frequencies
        if freq_now < min_freq_now or freq_base < min_freq_base:
            continue

        # calculate burst metrics
        fold_change = (freq_now + eps) / (freq_base + eps)  
        burst_score = fold_change * np.log(freq_now + 1)    

        burst_words.append({
            'word': word,
            'freq_now': freq_now, 
            'freq_base': round(freq_base, 2),  
            'fold_change': round(fold_change, 2),  
            'burst_score': round(burst_score, 2)  
        })

    # --------------------------
    # 6. sort and return top K burst words
    # --------------------------
    burst_words=sorted(burst_words, key=lambda x: x['burst_score'], reverse=True)[:top_k]
    df = pd.DataFrame(burst_words, columns=['word', 'freq_now', 'freq_base','fold_change','burst_score'])
    return df

