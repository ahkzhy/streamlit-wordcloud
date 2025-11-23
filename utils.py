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
