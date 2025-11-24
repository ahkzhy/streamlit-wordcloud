from datetime import datetime, timedelta
import re
import pandas as pd


def get_english_stopwords():
    """获取英文停用词列表"""
    english_stopwords = {
        # 基础冠词、连词、介词
        'a', 'an', 'the', 'and', 'or', 'but', 'if', 'because', 'as', 'until', 'while', 
        'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into', 'through', 
        'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 
        'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here', 
        'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 
        'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 
        'same', 'so', 'than', 'too', 'very', 'can', 'will', 'just', "don't", "should", 
        "now", "'s", "'t", "'m", "'re", "'ve", "'d", "'ll", "n't", 'be', 'is', 'are', 
        'was', 'were', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 
        'did', 'doing', 
        
        # 新增连词
        'also', 'although', 'though', 'since', 'unless', 'whether', 'while', 'whereas',
        'therefore', 'thus', 'hence', 'consequently', 'moreover', 'furthermore', 
        'however', 'nevertheless', 'nonetheless', 'otherwise', 'instead', 'meanwhile',
        
        # 时间相关词汇
        'year', 'years', 'month', 'months', 'week', 'weeks', 'day', 'days', 'hour', 
        'hours', 'minute', 'minutes', 'second', 'seconds', 'time', 'times', 'season',
        'seasons', 'today', 'tomorrow',
        'yesterday', 'now', 'then', 'when', 'before', 'after', 'during', 'while',
        'moment', 'period', 'date', 'calendar', 'clock', 'schedule',
        
        # 数字和序数词
        'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten',
        'first', 'second', 'third', 'fourth', 'fifth', 'sixth', 'seventh', 'eighth',
        'ninth', 'tenth', 'once', 'twice', 'thrice', 'single', 'double', 'triple',
        'number', 'numbers', 'count', 'total', 'amount', 'quantity',
        
        # 常见代词和人称
        'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them',
        'my', 'your', 'his', 'its', 'our', 'their', 'mine', 'yours', 'hers', 'ours',
        'theirs', 'myself', 'yourself', 'himself', 'herself', 'itself', 'ourselves',
        'yourselves', 'themselves',
        
        # 常见助动词和情态动词
        'may', 'might', 'must', 'shall', 'should', 'would', 'could', 'ought','said'
        
        # 标点符号和特殊字符
        '', ' ', '  ', ',', '.', '!', '?', ':', ';', '-', '(', ')', 
        '[', ']', '{', '}', '/', '\\', '|', '@', '#', '$', '%', '^', '&', '*', '+', '=', 
        '<', '>', '~', '_', '"', "'", '`',
        
        # 常见无意义词汇
        'very', 'really', 'quite', 'rather', 'pretty', 'just', 'even', 'still', 'yet',
        'already', 'almost', 'nearly', 'hardly', 'scarcely', 'simply', 'merely',
        'actually', 'basically', 'essentially', 'literally', 'virtually'
    }
    
    # 添加单个字母
    english_stopwords.update([chr(i) for i in range(97, 123)])
    english_stopwords.update([chr(i) for i in range(65, 91)])
    
    # 添加数字
    english_stopwords.update([str(i) for i in range(0, 100)])
    
    return english_stopwords

def is_english_word(word):
    """检查单词是否只包含英文字母"""
    if not isinstance(word, str):
        return False
    # 使用正则表达式检查是否只包含英文字母（允许连字符和撇号）
    return bool(re.match(r'^[a-zA-Z\-\.\']+$', word))

def clean_with_stopwords(df, word_col='word'):
    """使用停用词列表清理数据"""
    stop_words = get_english_stopwords()
    
    def is_valid_word(word):
        if pd.isna(word) or not isinstance(word, str):
            return False
        
        word_clean = word.strip().lower()
        
        # 检查是否是停用词
        if word_clean in stop_words:
            return False
        
        # 检查是否只包含英文字母
        if not is_english_word(word):
            return False
        
        # 检查单词长度
        if len(word_clean) <= 1:
            return False
        
        # 检查是否全是特殊字符
        if re.match(r'^[^\w\s]+$', word_clean):
            return False
            
        return True
    
    original_count = len(df)
    cleaned_df = df[df[word_col].apply(is_valid_word)].copy()
    return cleaned_df, original_count - len(cleaned_df)

def generate_simulated_sentiment_data():
    """
    仿真函数：包含情感趋势数据
    """

    # === 新增：伪造情感趋势数据 ===
    # 构造过去 10 个时间点的数据
    timestamps = [datetime.now() - timedelta(minutes=10*i) for i in range(10)][::-1]
    
    # 模拟一个“舆情先下降后上升”的趋势
    # Content: -0.2 -> -0.5 -> 0.1 -> 0.4
    content_scores = [-0.1, -0.2, -0.4, -0.5, -0.3, 0.0, 0.2, 0.4, 0.5, 0.6]
    # Title: 通常比正文更极端一点
    title_scores =   [-0.2, -0.3, -0.6, -0.8, -0.4, 0.1, 0.3, 0.5, 0.7, 0.8]
    
    sentiment_history = []
    for t, c, ti in zip(timestamps, content_scores, title_scores):
        sentiment_history.append({
            'timestamp': t,
            'avg_content': c,
            'avg_title': ti
        })
    
    sentiment_trend_df = pd.DataFrame(sentiment_history)
    
    # 注意：这里需要把 sentiment_trend_df 也返回出去
    # 但是原来的 main 函数只接收两个变量：trend_result, burst_df
    # 我们可以把 sentiment_trend_df 塞进 trend_result 或者作为一个新的返回值
    
    # 建议方案：把它塞进一个字典返回，或者修改 main 函数接收 3 个值
    # 这里我们修改 main 函数的调用方式
    
    return sentiment_trend_df