import pandas as pd

from article_utils import get_df_top_N_keywords, load_article_data, merge_with_article_info
from frequency_utils import load_frequency_data
from sentiment_utils import get_top_n_by_score, load_sentiment_data
from tfidf_utils import load_tfidf_data
from history_queue import HistoryDataQueue

class analysisData:
    """
    A class to handle analysis data operations.
    """
    def __init__(self):
        self.word_frequency_df=HistoryDataQueue()
        self.word_frequency_title_df=HistoryDataQueue()
        self.load_data()
        
    #-- Data Loading and Updating Methods --#
    def update_data(self):
        """
        Update and reload analysis data from CSV files.
        """
        self.load_data()

    def load_data(self):
        """
        Load and parse analysis data from CSV files.
        """
        self.article_df = load_article_data()

        self.sentiment_df = load_sentiment_data()

        word_frequency_df,word_frequency_title_df = load_frequency_data()
        self.word_frequency_df.add(word_frequency_df)
        self.word_frequency_title_df.add(word_frequency_title_df)

        self.tfidf_df, self.tfidf_title_df = load_tfidf_data()

        
    #-- Sentiment Analysis Methods --#
    def get_sentiment_content_top_10_desc(self):
        """
        Get top 10 content sentiment scores from sentiment data.
        """
        top_10_sentiments = get_top_n_by_score(self.sentiment_df, top_n=10, ascending=False,content=True)

        return top_10_sentiments
    
    def get_sentiment_title_top_10_desc(self):
        """
        Get top 10 title sentiment scores from sentiment data.
        """
        top_10_sentiments_title = get_top_n_by_score(self.sentiment_df, top_n=10, ascending=False,content=False)

        return top_10_sentiments_title

    def get_sentiment_content_top_10_asc(self):
        """
        Get top 10 content sentiment scores from sentiment data in ascending order.
        """  
        top_10_sentiments = get_top_n_by_score(self.sentiment_df, top_n=10, ascending=True,content=True)
        return top_10_sentiments
    
    def get_sentiment_title_top_10_asc(self):
        """
        Get top 10 title sentiment scores from sentiment data in ascending order.
        """
        top_10_sentiments_title = get_top_n_by_score(self.sentiment_df, top_n=10, ascending=True,content=False)

        return top_10_sentiments_title

    #-- Article Keyword Extraction Methods --#
    def get_top_5_keywords_of_article(self):
        """
        Get top 5 keywords of each article.
        """
        article_top_5=get_df_top_N_keywords(self.article_df, top_n=5)

        return article_top_5

if __name__ == "__main__":
    # Example usage
    analysis_data = analysisData()#初始化数据
    analysis_data.update_data()#刷新数据
    #获取情感内容/标题top10正负面
    print(analysis_data.get_sentiment_content_top_10_desc())
    print(analysis_data.get_sentiment_title_top_10_desc())
    print(analysis_data.get_sentiment_content_top_10_asc())
    print(analysis_data.get_sentiment_title_top_10_asc())