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
        self.sentiment_history = []
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
            if self.sentiment_df is not None and not self.sentiment_df.empty:
                timestamp = pd.Timestamp.now()
                avg_content = self.sentiment_df['score_content'].mean() if 'score_content' in self.sentiment_df.columns else 0
                avg_title = self.sentiment_df['score_title'].mean() if 'score_title' in self.sentiment_df.columns else 0
                self.sentiment_history.append({
                    'timestamp': timestamp,
                    'avg_content': avg_content,
                    'avg_title': avg_title
                })
                if len(self.sentiment_history) > 50:
                    self.sentiment_history.pop(0)
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
    def get_sentiment_trend(self):
        """返回情感趋势 DataFrame"""
        with self.data_lock:
            if not self.sentiment_history:
                return pd.DataFrame()
            return pd.DataFrame(self.sentiment_history)
        
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

    def get_history_trends_analysis(self):
        """
        新增功能：计算当前词频 vs 历史平均词频的趋势
        符合 'Compare to previous 24 hours' 的要求
        """
        with self.data_lock:
            # 1. 获取所有历史数据
            all_history = self.word_frequency_df.get_all()
            
            # 至少需要 2 份数据才能做对比（1份当前，1份历史）
            if len(all_history) < 2:
                return {} 
            
            # 2. 分离当前数据和历史背景数据
            # current_entry 是 (timestamp, df)
            current_entry = all_history[-1] 
            curr_df = current_entry[1]
            
            # 历史背景 = 除了最新这一份之外的所有
            past_entries = all_history[:-1]
            past_dfs = [entry[1] for entry in past_entries]
            
            # 3. 【关键步骤】聚合历史数据作为 Baseline
            # 将过去所有的 DataFrame 合并，然后按 word 分组取平均值
            # 这样我们就得到了一个“平滑”的历史基准线
            if past_dfs:
                baseline_df = pd.concat(past_dfs).groupby('word', as_index=False)['count'].mean()
            else:
                return {}

        # 4. 复用 frequency_utils 里的计算逻辑
        # 因为逻辑一样：都是算 New - Old
        return calculate_word_trends(baseline_df, curr_df)
    

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