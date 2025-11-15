from collections import defaultdict
import pandas as pd

import numpy as np
"""
    load_frequency_data:加载词频数据
    calculate_word_trends:计算词频变化趋势
    detect_burst_words:基于HistoryDataQueue检测热词突增
"""

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
        return None
    
    # combine old and new frequency data on 'word'
    merged = pd.merge(
        old_freq, new_freq,
        on='word',
        suffixes=('_old', '_new'),
        how='outer' # keep all words
    )
    # fill NaN frequencies with 0
    merged['frequency_old'] = merged['frequency_old'].fillna(0)
    merged['frequency_new'] = merged['frequency_new'].fillna(0)
    
    # calculate frequency change and rate
    merged['freq_change'] = merged['frequency_new'] - merged['frequency_old']
    merged['freq_change_rate'] = np.where(
        merged['frequency_old'] == 0,
        np.where(merged['frequency_new'] == 0, 0, 1), # if old freq is 0 and new freq > 0, rate is 1
        merged['freq_change'] / merged['frequency_old']
    )
    
    # identify new, lost, and common words
    merged['trend'] = np.where(
        (merged['frequency_old'] > 0) & (merged['frequency_new'] > 0),
        'common',  
        np.where(
            merged['frequency_old'] == 0,
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
        top_burst_words: 排序后的热词列表（含词、频次、突增指标）
    """
    # --------------------------
    # 1. check if enough data
    # --------------------------
    all_updates = freq_queue.get_all()
    if len(all_updates) < (current_window_size + baseline_window_size):
        raise ValueError(f"lack of data. at least{current_window_size + baseline_window_size}times of updates required.")

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
    return sorted(burst_words, key=lambda x: x['burst_score'], reverse=True)[:top_k]