import threading
import time
import pandas as pd

from article_utils import get_df_top_N_keywords, load_article_data, merge_with_article_info
from frequency_utils import calculate_word_trends, detect_burst_words, load_frequency_data
from sentiment_utils import get_top_n_by_score, load_sentiment_data
from tfidf_utils import load_tfidf_data
from history_queue import HistoryDataQueue
from updater import start_download_thread
"""
    对读取到的数据进行处理，并更新数据
"""
class analysisData:
    """
    A class to handle analysis data operations.
    """
    def __init__(self):
        self.word_frequency_df=HistoryDataQueue()
        self.word_frequency_title_df=HistoryDataQueue()
        self.load_data()
        self.data_lock = threading.Lock()
        
    #-- Data Loading and Updating Methods --#
    def update_data(self,file="all"):
        """
        Update and reload analysis data from CSV files.
        """
        with self.data_lock:
            self.load_data(file)

    def load_data(self,file="all"):
        """
        Load and parse analysis data from CSV files.
        """
        if file=="articles.csv" or file=="all":
            self.article_df = load_article_data()
        if file=="sentiment.csv" or file=="all":
            self.sentiment_df = load_sentiment_data()
        
        word_frequency_df,word_frequency_title_df = load_frequency_data()
        if file=="word_frequency.csv" or file=="all":
            self.word_frequency_df.add(word_frequency_df)
        if file=="word_frequency_title.csv" or file=="all":
            self.word_frequency_title_df.add(word_frequency_title_df)

        tfidf_df,tfidf_title_df = load_tfidf_data()
        if file=="tfidf.csv" or file=="all":
            self.tfidf_df=tfidf_df
        if file=="tfidf_title.csv" or file=="all":
            self.tfidf_title_df=tfidf_title_df

        
    #-- Sentiment Analysis Methods --#
    def get_sentiment_content_top_10_desc(self):
        """
        Get top 10 content sentiment scores from sentiment data.
        """
        with self.data_lock:
            top_10_sentiments = get_top_n_by_score(self.sentiment_df, top_n=10, ascending=False,content=True)

        return top_10_sentiments
    
    def get_sentiment_title_top_10_desc(self):
        """
        Get top 10 title sentiment scores from sentiment data.
        """
        with self.data_lock:
            top_10_sentiments_title = get_top_n_by_score(self.sentiment_df, top_n=10, ascending=False,content=False)

        return top_10_sentiments_title

    def get_sentiment_content_top_10_asc(self):
        """
        Get top 10 content sentiment scores from sentiment data in ascending order.
        """  
        with self.data_lock:
            top_10_sentiments = get_top_n_by_score(self.sentiment_df, top_n=10, ascending=True,content=True)
        return top_10_sentiments
    
    def get_sentiment_title_top_10_asc(self):
        """
        Get top 10 title sentiment scores from sentiment data in ascending order.
        """
        with self.data_lock:
            top_10_sentiments_title = get_top_n_by_score(self.sentiment_df, top_n=10, ascending=True,content=False)

        return top_10_sentiments_title

    #-- Article Keyword Extraction Methods --#
    def get_top_5_keywords_of_article(self):
        """
        Get top 5 keywords of each article.
        """
        with self.data_lock:
            article_top_5=get_df_top_N_keywords(self.article_df, top_n=5)

        return article_top_5


    # --- Frequency trend Methods ---#
    def get_word_trends_analysis(self):
        """
        计算词频趋势（对比最近两次更新）
        Returns: 
            dict: A dictionary with keys 'common', 'new', 'lost', and 'all' containing DataFrames.
        """
        with self.data_lock:
            # 获取最近两份数据
            recent_data = self.word_frequency_df.get_recent(2)
        
            if len(recent_data) < 2:
                return {} # 数据不足，无法对比
                
            # recent_data 是 [(ts1, df1), (ts2, df2)]
            prev_df = recent_data[0][1]
            curr_df = recent_data[1][1]
        
        # 调用 frequency_utils 中的函数
        return calculate_word_trends(prev_df, curr_df)

    

    def get_burst_words_analysis(self):
        """
        
        Returns: top_burst_words: 排序后的热词df（含词、频次、突增指标）word,freq_now, freq_base, fold_change,burst_score
        """
        with self.data_lock:
            df=self.word_frequency_df
        return detect_burst_words(df)


if __name__ == "__main__":
    # Example usage
    # analysis_data = analysisData()#初始化数据
    # start_download_thread(analysis_data)#刷新数据
    # #获取情感内容/标题top10正负面

    # while True:
    #     print("working..."+str(analysis_data.word_frequency_df.size()))
    #     time.sleep(5)
    pass